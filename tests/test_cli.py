"""Pruebas unitarias para el CLI de evaluación directa de archivos."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.cli import run_cli
from src.schemas import (
    CandidateContactPII,
    CategoryScore,
    CategoryScores,
    EvaluationResultSchema,
    SeniorityLevel,
    VacancySchema,
    Verdict,
)


def _dummy_eval() -> EvaluationResultSchema:
    cats = CategoryScores(
        relevant_experience=CategoryScore(
            score=90, weight=0.40, weighted=36.0, justification="OK"
        ),
        must_have_skills=CategoryScore(
            score=85, weight=0.35, weighted=29.75, justification="OK"
        ),
        nice_to_have_skills=CategoryScore(
            score=70, weight=0.15, weighted=10.5, justification="OK"
        ),
        education_and_languages=CategoryScore(
            score=80, weight=0.10, weighted=8.0, justification="OK"
        ),
    )
    return EvaluationResultSchema(
        evaluation_id="eval_cli_01",
        vacancy_title="Backend Senior",
        candidate_id="cand_cli_01",
        verdict=Verdict.ACEPTABLE,
        overall_score=84.25,
        category_scores=cats,
        executive_summary="Candidato compatible.",
    )


def test_cli_evaluates_vacancy_file_and_cv_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    vac_file = tmp_path / "vac.txt"
    cv_file = tmp_path / "cv.txt"
    vac_file.write_text("Vacante Backend", encoding="utf-8")
    cv_file.write_text("CV Backend", encoding="utf-8")

    monkeypatch.setattr("src.cli.GeminiClient", lambda: MagicMock())
    monkeypatch.setattr(
        "src.cli.extract_vacancy_from_file",
        lambda *a, **kw: VacancySchema(
            vacancy_id="v1", title="Backend Senior", seniority=SeniorityLevel.SENIOR
        ),
    )
    monkeypatch.setattr(
        "src.cli.evaluate_cv_file_against_vacancy",
        lambda **kw: (_dummy_eval(), CandidateContactPII(candidate_id="cand_cli_01")),
    )

    code = run_cli(["--vacancy", str(vac_file), "--cv", str(cv_file), "--json"])
    assert code == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["verdict"] == "ACEPTABLE"
    assert parsed["overall_score"] == 84.25
