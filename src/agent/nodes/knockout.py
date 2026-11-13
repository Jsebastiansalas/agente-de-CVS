"""Nodo 1: Evaluador de Requisitos Excluyentes (Knock-out) (HU-2.2)."""

from pydantic import BaseModel, Field

from src.agent.prompts import (
    KNOCKOUT_SYSTEM_INSTRUCTION,
    serialize_candidate_for_prompt,
    serialize_vacancy_for_prompt,
)
from src.agent.state import AgentState
from src.config import Settings, get_settings
from src.llm.gemini_client import GeminiClient
from src.schemas.evaluation import KnockoutEvaluation


class _KnockoutBatchResponse(BaseModel):
    """Respuesta estructurada con la evaluación de todos los requisitos excluyentes."""

    knockout_requirements: list[KnockoutEvaluation] = Field(default_factory=list)


def _build_knockout_prompt(state: AgentState) -> str:
    vacancy = state["vacancy"]
    candidate = state["candidate"]
    return (
        "Evalúa estrictamente cada uno de los requisitos excluyentes de la vacante.\n"
        f"Experiencia total calculada en código: {candidate.total_experience_months} meses "
        f"({candidate.total_experience_months / 12:.2f} años).\n\n"
        f"{serialize_vacancy_for_prompt(vacancy)}\n\n"
        f"{serialize_candidate_for_prompt(candidate)}"
    )


def evaluate_knockout_node(
    state: AgentState,
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> dict[str, list[KnockoutEvaluation]]:
    """Evalúa cada requisito excluyente de la vacante de forma síncrona."""
    vacancy = state["vacancy"]
    if not vacancy.knockout_requirements:
        return {"knockout_results": []}

    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    response = client.generate_structured(
        model=cfg.gemini_pro_model,
        system_instruction=KNOCKOUT_SYSTEM_INSTRUCTION,
        contents=_build_knockout_prompt(state),
        response_schema=_KnockoutBatchResponse,
    )
    return {"knockout_results": response.knockout_requirements}


async def aevaluate_knockout_node(
    state: AgentState,
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> dict[str, list[KnockoutEvaluation]]:
    """Evalúa cada requisito excluyente de la vacante de forma asíncrona."""
    vacancy = state["vacancy"]
    if not vacancy.knockout_requirements:
        return {"knockout_results": []}

    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    response = await client.agenerate_structured(
        model=cfg.gemini_pro_model,
        system_instruction=KNOCKOUT_SYSTEM_INSTRUCTION,
        contents=_build_knockout_prompt(state),
        response_schema=_KnockoutBatchResponse,
    )
    return {"knockout_results": response.knockout_requirements}
