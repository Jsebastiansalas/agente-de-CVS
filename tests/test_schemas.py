"""Pruebas para los contratos Pydantic v2 (HU-0.2)."""

import pytest
from pydantic import ValidationError

from src.schemas import (
    CandidateSchema,
    CategoryScore,
    CategoryScores,
    EvaluationResultSchema,
    KnockoutEvaluation,
    KnockoutStatus,
    SecurityFlags,
    SeniorityLevel,
    SkillEvaluation,
    SkillMatchLevel,
    SkillType,
    VacancySchema,
    Verdict,
    WorkExperience,
)


def test_vacancy_schema_valid() -> None:
    vacancy = VacancySchema(
        vacancy_id="vac_01",
        title="Backend Python Senior",
        seniority=SeniorityLevel.SENIOR,
        min_years_experience=4.0,
        knockout_requirements=["4+ años en Python", "Inglés B2"],
        must_have_skills=["FastAPI", "PostgreSQL"],
        nice_to_have_skills=["Kubernetes"],
    )
    assert vacancy.seniority == SeniorityLevel.SENIOR
    assert vacancy.min_years_experience == 4.0


def test_candidate_schema_rejects_negative_months() -> None:
    with pytest.raises(ValidationError):
        CandidateSchema(
            candidate_id="cand_01",
            total_experience_months=-5,
        )

    exp = WorkExperience(
        role="Backend Dev",
        company="FinTech",
        start_date="2022-01",
        is_current=True,
        calculated_months=36,
        technologies=["Python", "FastAPI"],
    )
    cand = CandidateSchema(
        candidate_id="cand_01",
        total_experience_months=36,
        work_experiences=[exp],
    )
    assert cand.work_experiences[0].calculated_months == 36


def test_skill_evaluation_requires_evidence_for_exact_or_partial() -> None:
    with pytest.raises(ValidationError, match="evidencia textual"):
        SkillEvaluation(
            skill="FastAPI",
            skill_type=SkillType.MUST_HAVE,
            match_level=SkillMatchLevel.EXACTO,
            proven_in_work_experience=True,
            evidence=None,
            explanation="Usado en trabajo reciente.",
        )

    valid_skill = SkillEvaluation(
        skill="PostgreSQL",
        skill_type=SkillType.MUST_HAVE,
        match_level=SkillMatchLevel.PARCIAL_EQUIVALENTE,
        proven_in_work_experience=True,
        evidence="Implementó servicios SQLAlchemy sobre MySQL en producción.",
        explanation="Experiencia transferible en base de datos relacional.",
    )
    assert valid_skill.match_level == SkillMatchLevel.PARCIAL_EQUIVALENTE


def test_knockout_requires_evidence_when_met() -> None:
    with pytest.raises(ValidationError, match="evidencia textual"):
        KnockoutEvaluation(
            requirement="Inglés B2",
            status=KnockoutStatus.CUMPLIDO,
            evidence="   ",
        )


def test_evaluation_result_schema_roundtrip() -> None:
    cat = CategoryScores(
        relevant_experience=CategoryScore(
            score=90, weight=0.40, weighted=36.0, justification="5 años en Python"
        ),
        must_have_skills=CategoryScore(
            score=85, weight=0.35, weighted=29.75, justification="Cubre FastAPI y SQL"
        ),
        nice_to_have_skills=CategoryScore(
            score=60, weight=0.15, weighted=9.0, justification="Docker sin K8s"
        ),
        education_and_languages=CategoryScore(
            score=90, weight=0.10, weighted=9.0, justification="Inglés C1"
        ),
    )

    result = EvaluationResultSchema(
        evaluation_id="eval_001",
        vacancy_title="Backend Python Senior",
        candidate_id="cand_anon_01",
        verdict=Verdict.ACEPTABLE,
        overall_score=83.75,
        category_scores=cat,
        knockout_requirements=[
            KnockoutEvaluation(
                requirement="4+ años Python",
                status=KnockoutStatus.CUMPLIDO,
                calculated_months=60,
                evidence="FinTech (2021-01 - Actualidad)",
            )
        ],
        skills_matrix=[
            SkillEvaluation(
                skill="FastAPI",
                skill_type=SkillType.MUST_HAVE,
                match_level=SkillMatchLevel.EXACTO,
                proven_in_work_experience=True,
                evidence="Migró APIs a FastAPI en FinTech.",
                explanation="Uso directo en producción.",
            )
        ],
        executive_summary="Candidato sólido con 5 años en backend Python y FastAPI.",
        detected_gaps=["Sin experiencia en Kubernetes"],
        suggested_interview_questions=["¿Cómo gestionarías un despliegue en Kubernetes?"],
        security_flags=SecurityFlags(),
    )

    serialized = result.model_dump_json()
    restored = EvaluationResultSchema.model_validate_json(serialized)
    assert restored.verdict == Verdict.ACEPTABLE
    assert restored.overall_score == 83.75
