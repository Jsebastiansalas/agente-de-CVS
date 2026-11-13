"""Extractor estructurado de Hojas de Vida con separación de PII y cálculo de tiempo (HU-1.3)."""

import uuid
from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from src.config import Settings, get_settings
from src.ingestion.document_parser import parse_document
from src.ingestion.experience_calculator import calculate_candidate_experience
from src.ingestion.pii_anonymizer import anonymize_candidate
from src.llm.gemini_client import GeminiClient
from src.schemas.candidate import (
    CandidateContactPII,
    CandidateSchema,
    EducationEntry,
    LanguageSkill,
    WorkExperience,
)

CANDIDATE_EXTRACTION_INSTRUCTION = (
    "Eres un extractor estructurado de Hojas de Vida de alta precisión.\n"
    "Extrae los datos profesionales y separa los datos de contacto en los campos PII.\n"
    "Reglas estrictas:\n"
    "1. Coloca nombre, email, teléfono y ciudad/ubicación únicamente en los campos PII.\n"
    "2. NO incluyas edad, fecha de nacimiento, género, estado civil, foto ni documento ID.\n"
    "3. Para cada experiencia laboral extrae start_date y end_date en formato YYYY-MM cuando "
    "esté disponible (o 'Actualidad' / is_current=true si sigue vigente).\n"
    "4. Distingue entre tecnologías usadas dentro de una experiencia laboral (technologies) "
    "y habilidades sueltas en una sección general (listed_skills).\n"
    "5. NO inventes ni completes información que no aparezca explícitamente en el CV."
)


class _RawCandidateExtraction(BaseModel):
    """Esquema intermedio para extraer perfil y PII por separado desde Gemini."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    work_experiences: list[WorkExperience] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    languages: list[LanguageSkill] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    listed_skills: list[str] = Field(default_factory=list)


class ExtractedCandidateBundle(BaseModel):
    """Resultado completo de ingesta de un CV: perfil anonimizado + PII separado."""

    candidate: CandidateSchema
    contact_pii: CandidateContactPII
    inconsistent_dates_warning: bool = Field(default=False)
    date_warnings: list[str] = Field(default_factory=list)


def extract_candidate(
    raw_text: str,
    *,
    candidate_id: str | None = None,
    reference_date: date | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> ExtractedCandidateBundle:
    """Extrae el perfil estructurado, calcula meses exactos y anonimiza el CV."""
    cleaned = raw_text.strip()
    if not cleaned:
        raise ValueError("El texto de la hoja de vida no puede estar vacío.")

    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    assigned_id = candidate_id or f"cand_anon_{uuid.uuid4().hex[:8]}"

    raw_extracted = client.generate_structured(
        model=cfg.gemini_flash_model,
        system_instruction=CANDIDATE_EXTRACTION_INSTRUCTION,
        contents=f"<raw_cv>\n{cleaned}\n</raw_cv>",
        response_schema=_RawCandidateExtraction,
    )

    contact_pii = CandidateContactPII(
        candidate_id=assigned_id,
        full_name=raw_extracted.full_name,
        email=raw_extracted.email,
        phone=raw_extracted.phone,
        location=raw_extracted.location,
    )

    candidate_profile = CandidateSchema(
        candidate_id=assigned_id,
        summary=raw_extracted.summary,
        work_experiences=raw_extracted.work_experiences,
        education=raw_extracted.education,
        languages=raw_extracted.languages,
        certifications=raw_extracted.certifications,
        listed_skills=raw_extracted.listed_skills,
    )

    exp_result = calculate_candidate_experience(
        candidate_profile,
        reference_date=reference_date,
    )
    anonymized = anonymize_candidate(exp_result.candidate, contact_pii=contact_pii)

    return ExtractedCandidateBundle(
        candidate=anonymized,
        contact_pii=contact_pii,
        inconsistent_dates_warning=exp_result.inconsistent_dates_warning,
        date_warnings=exp_result.warnings,
    )


def extract_candidate_from_file(
    file_path: str | Path,
    *,
    candidate_id: str | None = None,
    reference_date: date | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> ExtractedCandidateBundle:
    """Parsea un archivo de CV (PDF/DOCX/TXT) y devuelve el perfil anonimizado."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    parsed = parse_document(file_path, gemini_client=client, settings=cfg)
    return extract_candidate(
        parsed.text,
        candidate_id=candidate_id,
        reference_date=reference_date,
        gemini_client=client,
        settings=cfg,
    )
