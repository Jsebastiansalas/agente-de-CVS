"""Wrapper sobre el SDK oficial google-genai con async, telemetría y caché (HU-3.2)."""

import asyncio
import logging
import time
from typing import Any, TypeVar

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel

from src.config import Settings, get_settings
from src.llm.telemetry import (
    UsageSummary,
    UsageTracker,
    extract_usage_from_response,
)

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class GeminiClientError(RuntimeError):
    """Error lanzado cuando Gemini falla tras agotar los reintentos configurados."""


class GeminiClient:
    """Cliente encapsulado para invocar modelos Gemini (sync/async) con telemetría."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: genai.Client | None = None,
        usage_tracker: UsageTracker | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.usage_tracker = usage_tracker or UsageTracker()
        if client is not None:
            self._client = client
        else:
            if not self.settings.gemini_api_key:
                raise GeminiClientError(
                    "GEMINI_API_KEY no está configurada. "
                    "Define la variable de entorno o agrégala en tu archivo .env."
                )
            self._client = genai.Client(
                api_key=self.settings.gemini_api_key,
                http_options=types.HttpOptions(api_version=self.settings.gemini_api_version),
            )

    @property
    def raw_client(self) -> genai.Client:
        """Expone el cliente subyacente para operaciones avanzadas como Context Caching."""
        return self._client

    def get_usage_summary(self) -> UsageSummary:
        """Devuelve el resumen acumulado de tokens, latencia y costo."""
        return self.usage_tracker.summary()

    def reset_usage(self) -> None:
        """Reinicia los contadores de telemetría."""
        self.usage_tracker.reset()

    def _build_config(
        self,
        *,
        temperature: float | None,
        system_instruction: str | None,
        response_schema: type[BaseModel] | None = None,
        cached_content: str | None = None,
    ) -> types.GenerateContentConfig:
        """Construye GenerateContentConfig unificando modo texto, JSON y caché remoto."""
        target_temp = (
            self.settings.gemini_temperature if temperature is None else temperature
        )
        kwargs: dict[str, Any] = {"temperature": target_temp}
        if cached_content:
            kwargs["cached_content"] = cached_content
        elif system_instruction:
            kwargs["system_instruction"] = system_instruction

        if response_schema is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = response_schema

        return types.GenerateContentConfig(**kwargs)

    def generate_structured(
        self,
        *,
        contents: Any,
        response_schema: type[SchemaT],
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        cached_content: str | None = None,
    ) -> SchemaT:
        """Invoca Gemini exigiendo respuesta JSON validada contra un esquema Pydantic."""
        target_model = model or self.settings.gemini_flash_model
        config = self._build_config(
            temperature=temperature,
            system_instruction=system_instruction,
            response_schema=response_schema,
            cached_content=cached_content,
        )
        response = self._call_with_retries(
            model=target_model,
            contents=contents,
            config=config,
            operation=f"structured:{response_schema.__name__}",
        )
        try:
            return self._parse_response(response, response_schema)
        except Exception as exc:
            raise GeminiClientError(
                f"Fallo parseando respuesta estructurada de Gemini: {exc}"
            ) from exc

    async def agenerate_structured(
        self,
        *,
        contents: Any,
        response_schema: type[SchemaT],
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        cached_content: str | None = None,
    ) -> SchemaT:
        """Versión asíncrona de generate_structured usando client.aio."""
        target_model = model or self.settings.gemini_flash_model
        config = self._build_config(
            temperature=temperature,
            system_instruction=system_instruction,
            response_schema=response_schema,
            cached_content=cached_content,
        )
        response = await self._acall_with_retries(
            model=target_model,
            contents=contents,
            config=config,
            operation=f"structured:{response_schema.__name__}",
        )
        try:
            return self._parse_response(response, response_schema)
        except Exception as exc:
            raise GeminiClientError(
                f"Fallo parseando respuesta estructurada de Gemini: {exc}"
            ) from exc

    def generate_text(
        self,
        *,
        contents: Any,
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        cached_content: str | None = None,
    ) -> str:
        """Invoca Gemini (texto o multimodal) y devuelve el texto plano generado."""
        target_model = model or self.settings.gemini_flash_model
        config = self._build_config(
            temperature=temperature,
            system_instruction=system_instruction,
            cached_content=cached_content,
        )
        response = self._call_with_retries(
            model=target_model,
            contents=contents,
            config=config,
            operation="text",
        )
        return self._extract_non_empty_text(response)

    async def agenerate_text(
        self,
        *,
        contents: Any,
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
        cached_content: str | None = None,
    ) -> str:
        """Versión asíncrona de generate_text usando client.aio."""
        target_model = model or self.settings.gemini_flash_model
        config = self._build_config(
            temperature=temperature,
            system_instruction=system_instruction,
            cached_content=cached_content,
        )
        response = await self._acall_with_retries(
            model=target_model,
            contents=contents,
            config=config,
            operation="text",
        )
        return self._extract_non_empty_text(response)

    def _call_with_retries(
        self,
        *,
        model: str,
        contents: Any,
        config: types.GenerateContentConfig,
        operation: str,
    ) -> Any:
        """Ejecuta generate_content síncrono con backoff exponencial y telemetría."""
        last_error: Exception | None = None
        for attempt in range(1, self.settings.gemini_max_retries + 1):
            started = time.perf_counter()
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                elapsed_ms = (time.perf_counter() - started) * 1000
                self.usage_tracker.record(
                    extract_usage_from_response(
                        response,
                        model=model,
                        operation=operation,
                        latency_ms=elapsed_ms,
                    )
                )
                return response
            except APIError as exc:
                last_error = exc
                status_code = getattr(exc, "code", None)
                if (
                    status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.settings.gemini_max_retries
                ):
                    delay = self.settings.gemini_retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Error transitorio en Gemini (HTTP %s), reintento %d/%d en %.1fs",
                        status_code,
                        attempt,
                        self.settings.gemini_max_retries,
                        delay,
                    )
                    time.sleep(delay)
                    continue
                raise GeminiClientError(
                    f"Error en API de Gemini ({status_code}): {exc}"
                ) from exc
            except Exception as exc:
                raise GeminiClientError(
                    f"Fallo inesperado invocando Gemini: {exc}"
                ) from exc

        raise GeminiClientError(
            f"Se agotaron los reintentos ({self.settings.gemini_max_retries}) "
            f"en Gemini: {last_error}"
        )

    async def _acall_with_retries(
        self,
        *,
        model: str,
        contents: Any,
        config: types.GenerateContentConfig,
        operation: str,
    ) -> Any:
        """Ejecuta generate_content asíncrono con backoff exponencial y telemetría."""
        last_error: Exception | None = None
        for attempt in range(1, self.settings.gemini_max_retries + 1):
            started = time.perf_counter()
            try:
                response = await self._client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                elapsed_ms = (time.perf_counter() - started) * 1000
                self.usage_tracker.record(
                    extract_usage_from_response(
                        response,
                        model=model,
                        operation=operation,
                        latency_ms=elapsed_ms,
                    )
                )
                return response
            except APIError as exc:
                last_error = exc
                status_code = getattr(exc, "code", None)
                if (
                    status_code in RETRYABLE_STATUS_CODES
                    and attempt < self.settings.gemini_max_retries
                ):
                    delay = self.settings.gemini_retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "Error transitorio async en Gemini (HTTP %s), reintento %d/%d en %.1fs",
                        status_code,
                        attempt,
                        self.settings.gemini_max_retries,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise GeminiClientError(
                    f"Error en API de Gemini ({status_code}): {exc}"
                ) from exc
            except Exception as exc:
                raise GeminiClientError(
                    f"Fallo inesperado invocando Gemini async: {exc}"
                ) from exc

        raise GeminiClientError(
            f"Se agotaron los reintentos ({self.settings.gemini_max_retries}) "
            f"en Gemini async: {last_error}"
        )

    @staticmethod
    def _extract_non_empty_text(response: Any) -> str:
        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise GeminiClientError("Gemini devolvió una respuesta de texto vacía.")
        return text.strip()

    @staticmethod
    def _parse_response(response: Any, response_schema: type[SchemaT]) -> SchemaT:
        """Valida la respuesta de Gemini contra el modelo Pydantic esperado."""
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, response_schema):
            return parsed
        if parsed is not None:
            return response_schema.model_validate(parsed)

        raw_text = getattr(response, "text", None)
        if not raw_text:
            raise ValueError("Gemini devolvió una respuesta vacía sin texto JSON.")
        return response_schema.model_validate_json(raw_text)
