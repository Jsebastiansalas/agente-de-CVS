"""Pruebas unitarias para el extractor de vacantes (HU-1.2)."""

from unittest.mock import MagicMock

import pytest

from evals.validate_dataset import DEFAULT_DATASET_DIR
from src.config import Settings
from src.ingestion.vacancy_extractor import extract_vacancy, extract_vacancy_from_file
from src.schemas.vacancy import SeniorityLevel, VacancySchema


def _sample_vacancy() -> VacancySchema:
    return VacancySchema(
        vacancy_id="vac_temp",
        title="Desarrollador Backend Senior (Python)",
        seniority=SeniorityLevel.SENIOR,
        min_years_experience=4.0,
        knockout_requirements=["Mínimo 4 años en Python", "Inglés B2"],
        must_have_skills=["FastAPI", "PostgreSQL", "Docker"],
        nice_to_have_skills=["Kubernetes", "RabbitMQ"],
    )


def test_extract_vacancy_applies_id_and_overrides() -> None:
    mock_client = MagicMock()
    mock_client.generate_structured.return_value = _sample_vacancy()

    result = extract_vacancy(
        "Vacante Backend Python Senior con 4 años de experiencia...",
        vacancy_id="vac_01",
        overrides={"min_years_experience": 5.0, "nice_to_have_skills": ["Kubernetes"]},
        gemini_client=mock_client,
        settings=Settings(gemini_api_key="test-key"),
    )

    assert result.vacancy_id == "vac_01"
    assert result.min_years_experience == 5.0
    assert result.nice_to_have_skills == ["Kubernetes"]
    mock_client.generate_structured.assert_called_once()


def test_extract_vacancy_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="vacío"):
        extract_vacancy("   ", gemini_client=MagicMock())


def test_extract_vacancy_from_file_uses_parser() -> None:
    mock_client = MagicMock()
    mock_client.generate_structured.return_value = _sample_vacancy()
    vac_path = DEFAULT_DATASET_DIR / "vacancies" / "vac_01_backend_python.txt"

    result = extract_vacancy_from_file(
        vac_path,
        vacancy_id="vac_file_01",
        gemini_client=mock_client,
        settings=Settings(gemini_api_key="test-key"),
    )

    assert result.vacancy_id == "vac_file_01"
    assert result.title == "Desarrollador Backend Senior (Python)"
