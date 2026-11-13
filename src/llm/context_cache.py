"""Gestión de Context Caching en Gemini y caché local de rúbricas de vacante (HU-3.2)."""

import hashlib
import logging
from typing import Any

from google.genai import types

from src.schemas.vacancy import VacancySchema

logger = logging.getLogger(__name__)

# Gemini requiere al menos ~1024-2048 tokens para activar Context Caching en servidor
MIN_REMOTE_CACHE_TOKENS = 1024


def _estimate_tokens(text: str) -> int:
    """Estimación conservadora (~4 caracteres por token)."""
    return max(1, len(text) // 4)


class VacancyCacheManager:
    """Administra caché local de rúbricas y Context Caching remoto en Gemini."""

    def __init__(self, *, min_remote_tokens: int = MIN_REMOTE_CACHE_TOKENS) -> None:
        self._min_remote_tokens = min_remote_tokens
        self._local_vacancies: dict[str, VacancySchema] = {}
        self._remote_cache_names: dict[str, str] = {}

    @staticmethod
    def hash_text(raw_text: str) -> str:
        """Calcula hash estable del texto de la vacante."""
        return hashlib.sha256(raw_text.strip().encode("utf-8")).hexdigest()[:16]

    def get_local_vacancy(self, raw_text: str) -> VacancySchema | None:
        """Obtiene una VacancySchema previamente extraída en memoria."""
        return self._local_vacancies.get(self.hash_text(raw_text))

    def put_local_vacancy(self, raw_text: str, vacancy: VacancySchema) -> None:
        """Guarda una VacancySchema en el caché local para evitar re-extracciones en lotes."""
        self._local_vacancies[self.hash_text(raw_text)] = vacancy

    def get_or_create_remote_cache(
        self,
        *,
        genai_client: Any,
        model: str,
        system_instruction: str,
        vacancy_context: str,
        ttl_seconds: int = 1800,
    ) -> str | None:
        """Crea o reutiliza un Context Cache en Gemini si el contexto supera el mínimo."""
        combined = f"{system_instruction}\n{vacancy_context}"
        if _estimate_tokens(combined) < self._min_remote_tokens:
            return None

        cache_key = f"{model}:{self.hash_text(combined)}"
        if cache_key in self._remote_cache_names:
            return self._remote_cache_names[cache_key]

        try:
            created = genai_client.caches.create(
                model=model,
                config=types.CreateCachedContentConfig(
                    system_instruction=system_instruction,
                    contents=[vacancy_context],
                    ttl=f"{ttl_seconds}s",
                ),
            )
            cache_name = getattr(created, "name", None)
            if cache_name:
                self._remote_cache_names[cache_key] = cache_name
                logger.info("Gemini Context Cache creado: %s", cache_name)
                return cache_name
        except Exception as exc:
            logger.debug(
                "Context Caching remoto no disponible (%s); continuando sin caché remoto.",
                exc,
            )
        return None
