"""Pruebas de integración de la API REST FastAPI, Dashboard y Feedback (HU-4.1, HU-4.2, HU-4.3)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.routes import get_app_settings, get_gemini_client, get_repository
from src.config import Settings
from src.schemas import (
    CandidateContactPII,
    CategoryScore,
    CategoryScores,
    EvaluationResultSchema,
    SeniorityLevel,
    VacancySchema,
    Verdict,
)
from src.storage import EvaluationRepository


def _dummy_vacancy() -> VacancySchema:
    return VacancySchema(
        vacancy_id="vac_api_01",
        title="Backend Python Senior",
        seniority=SeniorityLevel.SENIOR,
        min_years_experience=4.0,
        knockout_requirements=["4+ años Python"],
        must_have_skills=["FastAPI", "PostgreSQL"],
    )


def _dummy_eval(eval_id: str, verdict: Verdict, score: float) -> EvaluationResultSchema:
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
        vacancy_title="Backend Python Senior",
        candidate_id=f"cand_{eval_id}",
        verdict=verdict,
        overall_score=score,
        category_scores=cats,
        executive_summary="Resumen ejecutivo de prueba.",
        detected_gaps=["Sin Kubernetes"],
        suggested_interview_questions=["¿Experiencia con contenedores?"],
    )


@pytest.fixture
def api_client(tmp_path: Path) -> tuple[TestClient, EvaluationRepository]:
    app = create_app()
    settings = Settings(gemini_api_key="test-key", database_path=str(tmp_path / "api.db"))
    repo = EvaluationRepository(settings.database_path)
    mock_gemini = MagicMock()
    mock_gemini.get_usage_summary.return_value = {}

    app.dependency_overrides[get_app_settings] = lambda: settings
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_gemini_client] = lambda: mock_gemini

    return TestClient(app), repo


def test_health_and_dashboard_html(api_client: tuple[TestClient, EvaluationRepository]) -> None:
    client, _ = api_client
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    home = client.get("/")
    assert home.status_code == 200
    assert "Agente Comparador de CVs vs. Vacante" in home.text


def test_parse_vacancy_endpoint(
    api_client: tuple[TestClient, EvaluationRepository],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = api_client
    monkeypatch.setattr("src.api.routes.extract_vacancy", lambda *a, **kw: _dummy_vacancy())

    res = client.post(
        "/api/v1/vacancies/parse",
        data={"vacancy_text": "Vacante Backend Python Senior 4 años FastAPI"},
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Backend Python Senior"


def test_single_evaluation_persists_and_supports_feedback_and_csv(
    api_client: tuple[TestClient, EvaluationRepository],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = api_client

    async def fake_eval(**_: object) -> tuple[EvaluationResultSchema, CandidateContactPII]:
        return (
            _dummy_eval("eval_single_1", Verdict.ACEPTABLE, 89.5),
            CandidateContactPII(
                candidate_id="cand_eval_single_1",
                full_name="Sofía Ríos",
                email="sofia@example.com",
            ),
        )

    monkeypatch.setattr("src.api.routes.aevaluate_cv_file_against_vacancy", fake_eval)

    res = client.post(
        "/api/v1/evaluations/single",
        data={"vacancy_json": _dummy_vacancy().model_dump_json()},
        files={"file": ("sofia.txt", b"CV Python Senior FastAPI", "text/plain")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["evaluation"]["verdict"] == "ACEPTABLE"
    assert body["contact_pii"]["full_name"] == "Sofía Ríos"

    # Feedback Human-in-the-Loop
    fb_res = client.post(
        "/api/v1/evaluations/eval_single_1/feedback",
        json={
            "agrees_with_agent": True,
            "human_verdict": "ACEPTABLE",
            "comment": "Pasa a entrevista técnica.",
        },
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["agrees_with_agent"] is True

    # Historial y exportación CSV
    listed = client.get("/api/v1/evaluations")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["latest_feedback"]["comment"] == "Pasa a entrevista técnica."

    csv_res = client.get("/api/v1/evaluations/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.content.decode("utf-8-sig")
    assert "eval_single_1" in csv_text
    assert "Sofía Ríos" in csv_text


def test_batch_evaluation_and_missing_feedback_404(
    api_client: tuple[TestClient, EvaluationRepository],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = api_client

    async def fake_eval(*, cv_path: Path, candidate_id: str, **_: object) -> tuple:
        if "b.txt" in cv_path.name:
            return (
                _dummy_eval("eval_b", Verdict.ACEPTABLE, 91.0),
                CandidateContactPII(candidate_id=candidate_id, full_name="Candidato B"),
            )
        return (
            _dummy_eval("eval_a", Verdict.NO_ACEPTABLE, 40.0),
            CandidateContactPII(candidate_id=candidate_id, full_name="Candidato A"),
        )

    monkeypatch.setattr("src.agent.batch.aevaluate_cv_file_against_vacancy", fake_eval)

    res = client.post(
        "/api/v1/evaluations/batch",
        data={"vacancy_json": _dummy_vacancy().model_dump_json(), "max_concurrency": "2"},
        files=[
            ("files", ("a.txt", b"CV A", "text/plain")),
            ("files", ("b.txt", b"CV B", "text/plain")),
        ],
    )
    assert res.status_code == 200
    ranked = res.json()["ranked_candidates"]
    assert len(ranked) == 2
    assert ranked[0]["evaluation"]["evaluation_id"] == "eval_b"
    assert ranked[0]["rank"] == 1

    not_found = client.post(
        "/api/v1/evaluations/nonexistent/feedback",
        json={"agrees_with_agent": True, "human_verdict": "ACEPTABLE"},
    )
    assert not_found.status_code == 404


def test_single_evaluation_accepts_vacancy_file_upload(
    api_client: tuple[TestClient, EvaluationRepository],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = api_client
    monkeypatch.setattr(
        "src.api.routes.extract_vacancy_from_file",
        lambda *a, **kw: _dummy_vacancy(),
    )

    async def fake_eval(**_: object) -> tuple[EvaluationResultSchema, CandidateContactPII]:
        return (
            _dummy_eval("eval_vac_file", Verdict.ACEPTABLE, 85.0),
            CandidateContactPII(candidate_id="cand_vac_file"),
        )

    monkeypatch.setattr("src.api.routes.aevaluate_cv_file_against_vacancy", fake_eval)

    res = client.post(
        "/api/v1/evaluations/single",
        files=[
            ("vacancy_file", ("vacante.txt", b"Vacante Python Senior", "text/plain")),
            ("file", ("cv.txt", b"CV Python Senior", "text/plain")),
        ],
    )
    assert res.status_code == 200
    assert res.json()["evaluation"]["evaluation_id"] == "eval_vac_file"


def test_api_key_authentication_protection(tmp_path: Path) -> None:
    app = create_app()
    secured_settings = Settings(
        gemini_api_key="test-key",
        database_path=str(tmp_path / "secured.db"),
        api_auth_key="secret-api-token",
    )
    repo = EvaluationRepository(secured_settings.database_path)
    app.dependency_overrides[get_app_settings] = lambda: secured_settings
    app.dependency_overrides[get_repository] = lambda: repo

    client = TestClient(app)

    # Health check is public
    health = client.get("/health")
    assert health.status_code == 200

    # API v1 without key fails with 401
    unauth = client.get("/api/v1/evaluations")
    assert unauth.status_code == 401
    assert "No autorizado" in unauth.json()["detail"]

    # API v1 with invalid key fails with 401
    invalid = client.get("/api/v1/evaluations", headers={"X-API-Key": "wrong-token"})
    assert invalid.status_code == 401

    # API v1 with correct key succeeds with 200
    valid = client.get("/api/v1/evaluations", headers={"X-API-Key": "secret-api-token"})
    assert valid.status_code == 200

