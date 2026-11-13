"""Pruebas unitarias para el motor determinista de scoring y veredicto (HU-2.4)."""

from src.agent.nodes.scorer import compute_weighted_scores, determine_verdict
from src.agent.state import SubscoresOutput
from src.config import Settings
from src.schemas.evaluation import KnockoutEvaluation, KnockoutStatus, Verdict


def _subscores(exp: float, must: float, nice: float, edu: float) -> SubscoresOutput:
    return SubscoresOutput(
        relevant_experience_score=exp,
        relevant_experience_justification="Justificación exp",
        must_have_skills_score=must,
        must_have_skills_justification="Justificación must",
        nice_to_have_skills_score=nice,
        nice_to_have_skills_justification="Justificación nice",
        education_and_languages_score=edu,
        education_and_languages_justification="Justificación edu",
    )


def test_compute_weighted_scores_exact_math() -> None:
    settings = Settings()
    subs = _subscores(90, 80, 60, 100)
    # 90*0.40 + 80*0.35 + 60*0.15 + 100*0.10 = 36 + 28 + 9 + 10 = 83.0
    categories, total = compute_weighted_scores(subs, settings)
    assert categories.relevant_experience.weighted == 36.0
    assert categories.must_have_skills.weighted == 28.0
    assert categories.nice_to_have_skills.weighted == 9.0
    assert categories.education_and_languages.weighted == 10.0
    assert total == 83.0


def test_determine_verdict_knockout_failed_overrides_high_score() -> None:
    settings = Settings()
    verdict = determine_verdict(
        overall_score=92.0,
        knockout_results=[
            KnockoutEvaluation(
                requirement="Mínimo 4 años en Python",
                status=KnockoutStatus.NO_CUMPLIDO,
                calculated_months=12,
                notes="Solo tiene 1 año.",
            )
        ],
        settings=settings,
    )
    assert verdict == Verdict.NO_ACEPTABLE


def test_determine_verdict_unmentioned_knockout_caps_at_reservations() -> None:
    settings = Settings()
    verdict = determine_verdict(
        overall_score=88.0,
        knockout_results=[
            KnockoutEvaluation(
                requirement="Inglés B2",
                status=KnockoutStatus.NO_MENCIONADO_EN_CV,
            )
        ],
        settings=settings,
    )
    assert verdict == Verdict.ACEPTABLE_CON_RESERVAS


def test_determine_verdict_thresholds() -> None:
    settings = Settings()
    met = [
        KnockoutEvaluation(
            requirement="4+ años Python",
            status=KnockoutStatus.CUMPLIDO,
            evidence="5 años en TechCorp",
        )
    ]

    assert determine_verdict(overall_score=75.0, knockout_results=met, settings=settings) == (
        Verdict.ACEPTABLE
    )
    assert determine_verdict(overall_score=74.9, knockout_results=met, settings=settings) == (
        Verdict.ACEPTABLE_CON_RESERVAS
    )
    assert determine_verdict(overall_score=60.0, knockout_results=met, settings=settings) == (
        Verdict.ACEPTABLE_CON_RESERVAS
    )
    assert determine_verdict(overall_score=59.9, knockout_results=met, settings=settings) == (
        Verdict.NO_ACEPTABLE
    )
