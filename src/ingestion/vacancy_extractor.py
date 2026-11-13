"""Extractor estructurado de rúbrica de vacantes usando Gemini Flash (HU-1.2)."""

import uuid
from pathlib import Path
from typing import Any

from src.config import Settings, get_settings
from src.ingestion.document_parser import parse_document
from src.llm.context_cache import VacancyCacheManager
from src.llm.gemini_client import GeminiClient
from src.schemas.vacancy import VacancySchema

VACANCY_EXTRACTION_INSTRUCTION = (
    "Eres un especialista senior en Atracción de Talento. "
    "Analiza la descripción de la vacante y extrae una rúbrica estructurada exacta.\n"
    "Reglas estrictas:\n"
    "1. knockout_requirements: incluye únicamente requisitos excluyentes duros "
    "(años mínimos obligatorios, idiomas mínimos excluyentes, títulos o tecnologías críticas "
    "marcadas explícitamente como indispensables).\n"
    "2. must_have_skills: habilidades técnicas o funcionales obligatorias.\n"
    "3. nice_to_have_skills: habilidades deseables, valoradas o plus.\n"
    "4. min_years_experience: número decimal o entero de años mínimos requeridos "
    "(0.0 si no se especifica).\n"
    "5. No inventes requisitos que no estén en el texto original."
)


def extract_vacancy(
    raw_text: str,
    *,
    vacancy_id: str | None = None,
    overrides: dict[str, Any] | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
    cache_manager: VacancyCacheManager | None = None,
) -> VacancySchema:
    """Extrae una VacancySchema desde texto libre usando Gemini con soporte de overrides."""
    cleaned = raw_text.strip()
    if not cleaned:
        raise ValueError("El texto de la vacante no puede estar vacío.")

    cfg = settings or get_settings()
    assigned_id = vacancy_id or f"vac_{uuid.uuid4().hex[:8]}"

    extracted: VacancySchema | None = None
    if cache_manager is not None:
        extracted = cache_manager.get_local_vacancy(cleaned)

    if extracted is None:
        client = gemini_client or GeminiClient(settings=cfg)
        prompt = (
            f"Usa exactamente vacancy_id='{assigned_id}'.\n"
            f"Descripción de la vacante:\n<vacancy_text>\n{cleaned}\n</vacancy_text>"
        )
        extracted = client.generate_structured(
            model=cfg.gemini_flash_model,
            system_instruction=VACANCY_EXTRACTION_INSTRUCTION,
            contents=prompt,
            response_schema=VacancySchema,
        )
        if cache_manager is not None:
            cache_manager.put_local_vacancy(cleaned, extracted)

    if vacancy_id and extracted.vacancy_id != vacancy_id:
        extracted = extracted.model_copy(update={"vacancy_id": vacancy_id})

    if overrides:
        merged = extracted.model_dump()
        merged.update(overrides)
        extracted = VacancySchema.model_validate(merged)

    return extracted


def extract_vacancy_from_file(
    file_path: str | Path,
    *,
    vacancy_id: str | None = None,
    overrides: dict[str, Any] | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
    cache_manager: VacancyCacheManager | None = None,
) -> VacancySchema:
    """Lee un archivo de vacante (PDF/DOCX/TXT) y extrae su rúbrica estructurada."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    parsed = parse_document(file_path, gemini_client=client, settings=cfg)
    return extract_vacancy(
        parsed.text,
        vacancy_id=vacancy_id,
        overrides=overrides,
        gemini_client=client,
        settings=cfg,
        cache_manager=cache_manager,
    )
