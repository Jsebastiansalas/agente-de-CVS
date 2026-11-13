"""Nodo 3: Motor determinista de scoring ponderado y veredicto (HU-2.4)."""

from src.agent.state import AgentState, SubscoresOutput
from src.config import Settings, get_settings
from src.schemas.evaluation import (
    CategoryScore,
    CategoryScores,
    KnockoutEvaluation,
    KnockoutStatus,
    Verdict,
)


def compute_weighted_scores(
    subscores: SubscoresOutput,
    settings: Settings,
) -> tuple[CategoryScores, float]:
    """Calcula en Python puro los puntajes ponderados y el puntaje global (0-100)."""
    w = settings.weights

    exp_weighted = round(subscores.relevant_experience_score * w.relevant_experience, 2)
    must_weighted = round(subscores.must_have_skills_score * w.must_have_skills, 2)
    nice_weighted = round(subscores.nice_to_have_skills_score * w.nice_to_have_skills, 2)
    edu_weighted = round(
        subscores.education_and_languages_score * w.education_and_languages, 2
    )

    category_scores = CategoryScores(
        relevant_experience=CategoryScore(
            score=round(subscores.relevant_experience_score, 2),
            weight=w.relevant_experience,
            weighted=exp_weighted,
            justification=subscores.relevant_experience_justification,
        ),
        must_have_skills=CategoryScore(
            score=round(subscores.must_have_skills_score, 2),
            weight=w.must_have_skills,
            weighted=must_weighted,
            justification=subscores.must_have_skills_justification,
        ),
        nice_to_have_skills=CategoryScore(
            score=round(subscores.nice_to_have_skills_score, 2),
            weight=w.nice_to_have_skills,
            weighted=nice_weighted,
            justification=subscores.nice_to_have_skills_justification,
        ),
        education_and_languages=CategoryScore(
            score=round(subscores.education_and_languages_score, 2),
            weight=w.education_and_languages,
            weighted=edu_weighted,
            justification=subscores.education_and_languages_justification,
        ),
    )

    total = round(
        min(100.0, max(0.0, exp_weighted + must_weighted + nice_weighted + edu_weighted)),
        2,
    )
    return category_scores, total


def determine_verdict(
    *,
    overall_score: float,
    knockout_results: list[KnockoutEvaluation],
    settings: Settings,
) -> Verdict:
    """Aplica las reglas de negocio deterministas para emitir el veredicto final."""
    has_failed_knockout = any(
        item.status == KnockoutStatus.NO_CUMPLIDO for item in knockout_results
    )
    if has_failed_knockout:
        return Verdict.NO_ACEPTABLE

    if overall_score < settings.reservations_threshold:
        return Verdict.NO_ACEPTABLE

    has_unmentioned_knockout = any(
        item.status == KnockoutStatus.NO_MENCIONADO_EN_CV for item in knockout_results
    )
    if has_unmentioned_knockout or overall_score < settings.acceptable_threshold:
        return Verdict.ACEPTABLE_CON_RESERVAS

    return Verdict.ACEPTABLE


def score_and_verdict_node(
    state: AgentState,
    *,
    settings: Settings | None = None,
) -> dict[str, object]:
    """Calcula el puntaje ponderado final y emite el veredicto sin intervención del LLM."""
    cfg = settings or get_settings()
    subscores = state["subscores"]
    knockout_results = state.get("knockout_results", [])

    category_scores, overall_score = compute_weighted_scores(subscores, cfg)
    verdict = determine_verdict(
        overall_score=overall_score,
        knockout_results=knockout_results,
        settings=cfg,
    )

    return {
        "category_scores": category_scores,
        "overall_score": overall_score,
        "verdict": verdict,
    }
