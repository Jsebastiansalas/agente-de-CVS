"""Pruebas unitarias para extracción de candidato y anonimización PII (HU-1.3)."""

from datetime import date
from unittest.mock import MagicMock

from src.config import Settings
from src.ingestion.candidate_extractor import _RawCandidateExtraction, extract_candidate
from src.ingestion.pii_anonymizer import (
    anonymize_candidate,
    detect_residual_pii,
    scrub_text_pii,
)
from src.schemas.candidate import CandidateContactPII, CandidateSchema, WorkExperience


def test_scrub_text_pii_removes_sensitive_attributes() -> None:
    pii = CandidateContactPII(
        candidate_id="cand_01",
        full_name="María Fernanda Gómez",
        email="maria.gomez@example.com",
        phone="+57 300 555 1234",
        location="Bogotá",
    )
    raw = (
        "Soy María Fernanda Gómez, Edad: 29 años, Género: Femenino, "
        "correo maria.gomez@example.com, cel +57 300 555 1234 en Bogotá. "
        "Perfil: https://www.linkedin.com/in/maria-gomez-dev"
    )

    scrubbed = scrub_text_pii(raw, contact_pii=pii)
    assert "María" not in scrubbed
    assert "Gómez" not in scrubbed
    assert "maria.gomez@example.com" not in scrubbed
    assert "300 555 1234" not in scrubbed
    assert "29 años" not in scrubbed
    assert "Femenino" not in scrubbed
    assert "Bogotá" not in scrubbed
    assert "linkedin.com/in" not in scrubbed


def test_anonymize_candidate_cleans_nested_fields() -> None:
    pii = CandidateContactPII(
        candidate_id="cand_02",
        full_name="Carlos Pérez",
        email="carlos@mail.com",
    )
    cand = CandidateSchema(
        candidate_id="cand_02",
        summary="Carlos Pérez, Edad: 34 años, desarrollador Python (carlos@mail.com).",
        work_experiences=[
            WorkExperience(
                role="Backend Dev",
                company="FinTech",
                start_date="2022-01",
                is_current=True,
                achievements=["Carlos Pérez lideró migración de APIs."],
            )
        ],
    )

    clean = anonymize_candidate(cand, contact_pii=pii)
    assert detect_residual_pii(clean, contact_pii=pii) == []
    assert "carlos@mail.com" not in (clean.summary or "")
    assert "Carlos" not in clean.work_experiences[0].achievements[0]


def test_extract_candidate_separates_pii_and_calculates_experience() -> None:
    mock_client = MagicMock()
    mock_client.generate_structured.return_value = _RawCandidateExtraction(
        full_name="Ana Sofía Ruiz",
        email="ana.ruiz@correo.com",
        phone="+57 311 222 3344",
        location="Medellín",
        summary="Ana Sofía Ruiz, Edad: 31 años. Ingeniera Backend Python.",
        work_experiences=[
            WorkExperience(
                role="Python Developer",
                company="CloudCo",
                start_date="2022-01",
                end_date="2024-12",
                technologies=["Python", "FastAPI"],
                achievements=["Ana Sofía Ruiz diseñó microservicios REST."],
            )
        ],
        listed_skills=["Docker"],
    )

    bundle = extract_candidate(
        "CV de Ana Sofía Ruiz...",
        candidate_id="cand_anon_99",
        reference_date=date(2025, 1, 1),
        gemini_client=mock_client,
        settings=Settings(gemini_api_key="test-key"),
    )

    assert bundle.contact_pii.full_name == "Ana Sofía Ruiz"
    assert bundle.contact_pii.email == "ana.ruiz@correo.com"
    assert bundle.candidate.candidate_id == "cand_anon_99"
    assert bundle.candidate.total_experience_months == 36
    assert detect_residual_pii(bundle.candidate, contact_pii=bundle.contact_pii) == []
