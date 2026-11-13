"""Pruebas de integración del grafo LangGraph y nodos (HU-2.1, HU-2.2, HU-2.3, HU-2.5)."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agent.graph import aevaluate_candidate, evaluate_candidate
from src.agent.nodes.knockout import _KnockoutBatchResponse
from src.agent.nodes.reporter import _clamp_words, _NarrativeReportOutput
from src.agent.nodes.skills_matcher import _SkillsAndSubscoresResponse
from src.agent.state import SubscoresOutput
from src.config import Settings
from src.schemas import (
    CandidateSchema,
    KnockoutEvaluation,
    KnockoutStatus,
    SeniorityLevel,
    SkillEvaluation,
    SkillMatchLevel,
    SkillType,
    VacancySchema,
    Verdict,
    WorkExperience,
)


def _sample_vacancy() -> VacancySchema:
    return VacancySchema(
        vacancy_id="vac_01",
        title="Desarrollador Backend Senior (Python)",
        seniority=SeniorityLevel.SENIOR,
        min_years_experience=4.0,
        knockout_requirements=["4+ años en Python", "Inglés B2"],
        must_have_skills=["FastAPI", "PostgreSQL"],
        nice_to_have_skills=["Kubernetes"],
    )


def _sample_candidate() -> CandidateSchema:
    return CandidateSchema(
        candidate_id="cand_anon_01",
        total_experience_months=56,
        work_experiences=[
            WorkExperience(
                role="Senior Python Developer",
                company="FinTech",
                start_date="2021-01",
                is_current=True,
                calculated_months=56,
                technologies=["Python", "FastAPI", "MySQL", "Docker"],
                achievements=["Lideró microservicios FastAPI sobre MySQL."],
            )
        ],
    )


def _dispatch_schema_response(*, response_schema: type[Any], **_: Any) -> Any:
    if response_schema is _KnockoutBatchResponse:
        return _KnockoutBatchResponse(
            knockout_requirements=[
                KnockoutEvaluation(
                    requirement="4+ años en Python",
                    status=KnockoutStatus.CUMPLIDO,
                    calculated_months=56,
                    evidence="Senior Python Developer en FinTech (56 meses).",
                ),
                KnockoutEvaluation(
                    requirement="Inglés B2",
                    status=KnockoutStatus.NO_MENCIONADO_EN_CV,
                ),
            ]
        )
    if response_schema is _SkillsAndSubscoresResponse:
        return _SkillsAndSubscoresResponse(
            skills_matrix=[
                SkillEvaluation(
                    skill="FastAPI",
                    skill_type=SkillType.MUST_HAVE,
                    match_level=SkillMatchLevel.EXACTO,
                    proven_in_work_experience=True,
                    evidence="Lideró microservicios FastAPI sobre MySQL.",
                    explanation="Uso directo en producción.",
                ),
                SkillEvaluation(
                    skill="PostgreSQL",
                    skill_type=SkillType.MUST_HAVE,
                    match_level=SkillMatchLevel.PARCIAL_EQUIVALENTE,
                    proven_in_work_experience=True,
                    evidence="Lideró microservicios FastAPI sobre MySQL.",
                    explanation="MySQL es relacional equivalente a PostgreSQL.",
                ),
            ],
            subscores=SubscoresOutput(
                relevant_experience_score=90.0,
                relevant_experience_justification="56 meses comprobados en Python.",
                must_have_skills_score=85.0,
                must_have_skills_justification="Cubre FastAPI exacto y SQL relacional.",
                nice_to_have_skills_score=60.0,
                nice_to_have_skills_justification="Usa Docker sin Kubernetes.",
                education_and_languages_score=50.0,
                education_and_languages_justification="No especifica inglés.",
            ),
        )
    if response_schema is _NarrativeReportOutput:
        return _NarrativeReportOutput(
            executive_summary=(
                "Candidato sólido con 56 meses de experiencia en Python y FastAPI. "
                "Queda con reservas porque no especifica su nivel de inglés."
            ),
            detected_gaps=[
                "Nivel de inglés B2 no mencionado en el CV.",
                "Sin experiencia directa en Kubernetes.",
            ],
            suggested_interview_questions=[
                "¿Cuál es tu nivel actual de inglés hablado y escrito?",
                "¿Qué diferencias conoces entre MySQL y PostgreSQL en producción?",
                "¿Has trabajado con orquestadores además de Docker?",
            ],
        )
    raise AssertionError(f"Esquema inesperado en mock: {response_schema}")


def _build_mock_gemini() -> MagicMock:
    mock_client = MagicMock()
    mock_client.generate_structured.side_effect = _dispatch_schema_response
    mock_client.agenerate_structured = AsyncMock(side_effect=_dispatch_schema_response)
    return mock_client


def test_evaluate_candidate_sync_end_to_end() -> None:
    mock_client = _build_mock_gemini()
    result = evaluate_candidate(
        vacancy=_sample_vacancy(),
        candidate=_sample_candidate(),
        evaluation_id="eval_test_01",
        gemini_client=mock_client,
        settings=Settings(gemini_api_key="test-key"),
    )

    assert result.evaluation_id == "eval_test_01"
    assert result.overall_score == 79.75
    assert result.verdict == Verdict.ACEPTABLE_CON_RESERVAS
    assert len(result.suggested_interview_questions) == 3
    assert mock_client.generate_structured.call_count == 3


@pytest.mark.asyncio
async def test_evaluate_candidate_async_end_to_end() -> None:
    mock_client = _build_mock_gemini()
    result = await aevaluate_candidate(
        vacancy=_sample_vacancy(),
        candidate=_sample_candidate(),
        evaluation_id="eval_async_01",
        gemini_client=mock_client,
        settings=Settings(gemini_api_key="test-key"),
    )
    assert result.evaluation_id == "eval_async_01"
    assert result.verdict == Verdict.ACEPTABLE_CON_RESERVAS
    assert mock_client.agenerate_structured.call_count == 3


def test_clamp_words_limits_summary_to_150_words() -> None:
    long_text = " ".join(["palabra"] * 200)
    clamped = _clamp_words(long_text, max_words=150)
    assert len(clamped.split()) == 150
    assert clamped.endswith("...")
