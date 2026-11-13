"""Pruebas unitarias para telemetría, caché, batch ranking y evals (HU-3.1 y HU-3.2)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from evals.run_evals import (
    CaseEvalOutcome,
    compute_benchmark_metrics,
    format_markdown_report,
)
from src.agent.batch import aevaluate_batch
from src.config import Settings
from src.llm.context_cache import VacancyCacheManager
from src.llm.gemini_client import GeminiClient
from src.llm.telemetry import UsageTracker, estimate_cost_usd
from src.schemas import (
    CategoryScore,
    CategoryScores,
    EvaluationResultSchema,
    SeniorityLevel,
    VacancySchema,
    Verdict,
)


def _dummy_eval(candidate_id: str, verdict: Verdict, score: float) -> EvaluationResultSchema:
    cat = CategoryScores(
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
        evaluation_id=f"eval_{candidate_id}",
        vacancy_title="Backend Senior",
        candidate_id=candidate_id,
        verdict=verdict,
        overall_score=score,
        category_scores=cat,
        executive_summary="Resumen breve.",
    )


def test_usage_tracker_and_gemini_telemetry() -> None:
    mock_sdk = MagicMock()
    mock_sdk.models.generate_content.return_value = SimpleNamespace(
        parsed=None,
        text='{"vacancy_id": "v1", "title": "Dev", "seniority": "MID"}',
        usage_metadata=SimpleNamespace(
            prompt_token_count=1000,
            candidates_token_count=200,
            cached_content_token_count=0,
            total_token_count=1200,
        ),
    )

    tracker = UsageTracker()
    client = GeminiClient(
        settings=Settings(gemini_api_key="test-key"),
        client=mock_sdk,
        usage_tracker=tracker,
    )
    client.generate_structured(contents="Vacante", response_schema=VacancySchema)

    summary = client.get_usage_summary()
    assert summary.total_calls == 1
    assert summary.total_prompt_tokens == 1000
    assert summary.total_output_tokens == 200
    assert summary.total_estimated_cost_usd > 0
    assert estimate_cost_usd("gemini-2.5-flash", 1000, 200, cached_tokens=800) < (
        estimate_cost_usd("gemini-2.5-flash", 1000, 200, cached_tokens=0)
    )


def test_vacancy_cache_manager_local_and_remote_threshold() -> None:
    mgr = VacancyCacheManager(min_remote_tokens=100)
    vac = VacancySchema(vacancy_id="v1", title="Python Dev", seniority=SeniorityLevel.MID)
    mgr.put_local_vacancy("  Vacante Python  ", vac)
    assert mgr.get_local_vacancy("Vacante Python") == vac

    # Contexto corto (< min_remote_tokens) no intenta crear caché remoto
    assert (
        mgr.get_or_create_remote_cache(
            genai_client=MagicMock(),
            model="gemini-2.5-flash",
            system_instruction="sys",
            vacancy_context="corto",
        )
        is None
    )

    # Contexto largo (>= min_remote_tokens) crea y reutiliza el caché remoto
    mock_genai = MagicMock()
    mock_genai.caches.create.return_value = SimpleNamespace(name="cachedContents/abc123")
    long_text = "requisito " * 200
    cache_name_1 = mgr.get_or_create_remote_cache(
        genai_client=mock_genai,
        model="gemini-2.5-flash",
        system_instruction="sys",
        vacancy_context=long_text,
    )
    cache_name_2 = mgr.get_or_create_remote_cache(
        genai_client=mock_genai,
        model="gemini-2.5-flash",
        system_instruction="sys",
        vacancy_context=long_text,
    )
    assert cache_name_1 == "cachedContents/abc123"
    assert cache_name_2 == "cachedContents/abc123"
    mock_genai.caches.create.assert_called_once()


@pytest.mark.asyncio
async def test_aevaluate_batch_sorts_ranking_and_isolates_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cv1 = tmp_path / "cv_low.txt"
    cv2 = tmp_path / "cv_best.txt"
    cv3 = tmp_path / "cv_mid.txt"
    cv_bad = tmp_path / "cv_bad.txt"
    for p in (cv1, cv2, cv3, cv_bad):
        p.write_text("dummy", encoding="utf-8")

    async def fake_eval(*, cv_path: Path, candidate_id: str, **_: object) -> tuple:
        name = Path(cv_path).name
        if name == "cv_bad.txt":
            raise RuntimeError("Archivo corrupto simulado")
        mapping = {
            "cv_low.txt": _dummy_eval(candidate_id, Verdict.NO_ACEPTABLE, 45.0),
            "cv_best.txt": _dummy_eval(candidate_id, Verdict.ACEPTABLE, 92.0),
            "cv_mid.txt": _dummy_eval(candidate_id, Verdict.ACEPTABLE_CON_RESERVAS, 70.0),
        }
        return mapping[name], {"candidate_id": candidate_id}

    monkeypatch.setattr("src.agent.batch.aevaluate_cv_file_against_vacancy", fake_eval)

    vac = VacancySchema(vacancy_id="v1", title="Backend Senior")
    batch = await aevaluate_batch(
        vacancy=vac,
        cv_paths=[cv1, cv2, cv3, cv_bad],
        max_concurrency=2,
        gemini_client=MagicMock(get_usage_summary=lambda: {}),
        settings=Settings(gemini_api_key="test-key"),
    )

    assert len(batch.ranked_candidates) == 3
    assert len(batch.errors) == 1
    assert batch.ranked_candidates[0].source_file == "cv_best.txt"
    assert batch.ranked_candidates[0].rank == 1
    assert batch.ranked_candidates[1].source_file == "cv_mid.txt"
    assert batch.ranked_candidates[2].source_file == "cv_low.txt"


def test_compute_benchmark_metrics_and_markdown_format() -> None:
    outcomes = [
        CaseEvalOutcome(
            case_id="c1",
            vacancy_file="v1",
            cv_file="cv1",
            expected_verdict=Verdict.ACEPTABLE,
            predicted_verdict=Verdict.ACEPTABLE,
            overall_score=88.0,
            is_exact_match=True,
            latency_seconds=6.0,
        ),
        CaseEvalOutcome(
            case_id="c2",
            vacancy_file="v1",
            cv_file="cv2",
            expected_verdict=Verdict.ACEPTABLE,
            predicted_verdict=Verdict.NO_ACEPTABLE,
            overall_score=50.0,
            is_exact_match=False,
            is_critical_fn=True,
            latency_seconds=8.0,
        ),
        CaseEvalOutcome(
            case_id="c3",
            vacancy_file="v1",
            cv_file="cv3",
            expected_verdict=Verdict.NO_ACEPTABLE,
            predicted_verdict=Verdict.NO_ACEPTABLE,
            overall_score=30.0,
            is_exact_match=True,
            latency_seconds=4.0,
        ),
    ]

    report = compute_benchmark_metrics(outcomes)
    assert report.accuracy_pct == 66.67
    assert report.critical_false_negatives == 1
    assert report.critical_fn_rate_pct == 50.0
    assert report.avg_latency_seconds == 6.0

    md = format_markdown_report(report)
    assert "Matriz de Confusión" in md
    assert "c1" in md
