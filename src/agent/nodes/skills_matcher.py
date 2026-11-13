"""Nodo 2: Comparador semántico de habilidades y sub-puntajes (HU-2.3)."""

from pydantic import BaseModel, Field

from src.agent.prompts import (
    SKILLS_MATCHER_SYSTEM_INSTRUCTION,
    serialize_candidate_for_prompt,
    serialize_vacancy_for_prompt,
)
from src.agent.state import AgentState, SubscoresOutput
from src.config import Settings, get_settings
from src.llm.gemini_client import GeminiClient
from src.schemas.evaluation import SkillEvaluation


class _SkillsAndSubscoresResponse(BaseModel):
    """Respuesta estructurada del comparador semántico."""

    skills_matrix: list[SkillEvaluation] = Field(default_factory=list)
    subscores: SubscoresOutput


def _build_skills_prompt(state: AgentState) -> str:
    vacancy = state["vacancy"]
    candidate = state["candidate"]
    return (
        "Evalúa la matriz de habilidades y asigna los 4 sub-puntajes (0-100).\n"
        f"Experiencia total calculada: {candidate.total_experience_months} meses "
        f"(requerida por vacante: {vacancy.min_years_experience} años).\n\n"
        f"{serialize_vacancy_for_prompt(vacancy)}\n\n"
        f"{serialize_candidate_for_prompt(candidate)}"
    )


def match_skills_node(
    state: AgentState,
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    """Evalúa habilidades y sub-puntajes de forma síncrona."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    response = client.generate_structured(
        model=cfg.gemini_pro_model,
        system_instruction=SKILLS_MATCHER_SYSTEM_INSTRUCTION,
        contents=_build_skills_prompt(state),
        response_schema=_SkillsAndSubscoresResponse,
    )
    return {
        "skills_matrix": response.skills_matrix,
        "subscores": response.subscores,
    }


async def amatch_skills_node(
    state: AgentState,
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> dict[str, object]:
    """Evalúa habilidades y sub-puntajes de forma asíncrona."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    response = await client.agenerate_structured(
        model=cfg.gemini_pro_model,
        system_instruction=SKILLS_MATCHER_SYSTEM_INSTRUCTION,
        contents=_build_skills_prompt(state),
        response_schema=_SkillsAndSubscoresResponse,
    )
    return {
        "skills_matrix": response.skills_matrix,
        "subscores": response.subscores,
    }
