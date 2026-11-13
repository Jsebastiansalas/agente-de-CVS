"""Wrapper sobre el SDK oficial google-genai con Structured Outputs y reintentos."""

import logging
import time
from typing import Any, TypeVar

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class GeminiClientError(RuntimeError):
    """Error lanzado cuando Gemini falla tras agotar los reintentos configurados."""


class GeminiClient:
    """Cliente encapsulado para invocar modelos Gemini con salidas tipadas o texto."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: genai.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if client is not None:
            self._client = client
        else:
            if not self.settings.gemini_api_key:
                raise GeminiClientError(
                    "GEMINI_API_KEY no está configurada. "
                    "Define la variable de entorno o agrégala en tu archivo .env."
                )
            self._client = genai.Client(api_key=self.settings.gemini_api_key)

    def generate_structured(
        self,
        *,
        contents: Any,
        response_schema: type[SchemaT],
        model: str | None = None,
        system_instruction: str | None = None,
        temperature: float | None = None,
    ) -> SchemaT:
        """Invoca Gemini exigiendo respuesta JSON validada contra un esquema Pydantic."""
        target_model = model or self.settings.gemini_flash_model
        target_temp = (
            self.settings.gemini_temperature if temperature is None else temperature
        )

        config = types.GenerateContentConfig(
            temperature=target_temp,
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction,
        )

        response = self._call_with_retries(
            model=target_model,
            contents=contents,
            config=config,
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
    ) -> str:
        """Invoca Gemini (texto o multimodal) y devuelve el texto plano generado."""
        target_model = model or self.settings.gemini_flash_model
        target_temp = (
            self.settings.gemini_temperature if temperature is None else temperature
        )

        config = types.GenerateContentConfig(
            temperature=target_temp,
            system_instruction=system_instruction,
        )
        response = self._call_with_retries(
            model=target_model,
            contents=contents,
            config=config,
        )
        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise GeminiClientError("Gemini devolvió una respuesta de texto vacía.")
        return text.strip()

    def _call_with_retries(
        self,
        *,
        model: str,
        contents: Any,
        config: types.GenerateContentConfig,
    ) -> Any:
        """Ejecuta generate_content con backoff exponencial ante errores transitorios."""
        last_error: Exception | None = None
        for attempt in range(1, self.settings.gemini_max_retries + 1):
            try:
                return self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
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
