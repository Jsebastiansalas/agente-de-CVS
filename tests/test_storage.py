"""Pruebas unitarias para el repositorio SQLite y feedback Human-in-the-Loop (HU-4.3)."""

from pathlib import Path

import pytest

from src.schemas import (
    CandidateContactPII,
    CategoryScore,
    CategoryScores,
    EvaluationResultSchema,
    Verdict,
)
from src.storage import EvaluationRepository


def _sample_evaluation(eval_id: str, score: float, verdict: Verdict) -> EvaluationResultSchema:
    cats = CategoryScores(
        relevant_experience=CategoryScore(
            score=score, weight=0.40, weighted=round(score * 0.40, 2), justification="OK"
        ),
        must_have_skills=CategoryScore(
            score=score, weight=0.35, weighted=round(score * 0.35, 2), justification="OK"
        ),
        nice_to_have_skills=CategoryScore(
            score=score, weight=0.15, weighted=round(score * 0.15, 2), justification="OK"
        ),
        education_and_languages=CategoryScore(
            score=score, weight=0.10, weighted=round(score * 0.10, 2), justification="OK"
        ),
    )
    return EvaluationResultSchema(
        evaluation_id=eval_id,
        vacancy_title="Backend Senior",
        candidate_id=f"cand_{eval_id}",
        verdict=verdict,
        overall_score=score,
        category_scores=cats,
        executive_summary="Resumen ejecutivo.",
    )


def test_repository_saves_lists_and_stores_feedback(tmp_path: Path) -> None:
    repo = EvaluationRepository(tmp_path / "test_evals.db")

    e1 = _sample_evaluation("eval_1", 88.0, Verdict.ACEPTABLE)
    e2 = _sample_evaluation("eval_2", 68.0, Verdict.ACEPTABLE_CON_RESERVAS)
    repo.save_evaluation(
        evaluation=e1,
        contact_pii=CandidateContactPII(candidate_id="cand_eval_1", full_name="Ana"),
        source_file="ana.pdf",
    )
    repo.save_evaluation(
        evaluation=e2,
        contact_pii=CandidateContactPII(candidate_id="cand_eval_2", full_name="Luis"),
        source_file="luis.pdf",
    )

    all_items = repo.list_evaluations()
    assert [item.evaluation.evaluation_id for item in all_items] == ["eval_1", "eval_2"]

    filtered = repo.list_evaluations(verdict=Verdict.ACEPTABLE_CON_RESERVAS)
    assert len(filtered) == 1
    assert filtered[0].contact_pii.full_name == "Luis"

    fb = repo.add_feedback(
        evaluation_id="eval_2",
        agrees_with_agent=False,
        human_verdict=Verdict.ACEPTABLE,
        comment="Validado nivel de inglés B2 en llamada telefónica.",
    )
    assert fb.human_verdict == Verdict.ACEPTABLE

    fetched = repo.get_evaluation("eval_2")
    assert fetched is not None
    assert fetched.latest_feedback is not None
    assert fetched.latest_feedback.agrees_with_agent is False


def test_repository_add_feedback_raises_for_missing_evaluation(tmp_path: Path) -> None:
    repo = EvaluationRepository(tmp_path / "test_evals.db")
    with pytest.raises(KeyError, match="no encontrada"):
        repo.add_feedback(
            evaluation_id="missing_id",
            agrees_with_agent=True,
            human_verdict=Verdict.ACEPTABLE,
        )
