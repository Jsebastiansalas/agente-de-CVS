"""Nodo 4: Generador de resumen ejecutivo, brechas y preguntas de entrevista (HU-2.5)."""

import json
import uuid

from pydantic import BaseModel, Field

from src.agent.prompts import (
    REPORTER_SYSTEM_INSTRUCTION,
    serialize_candidate_for_prompt,
)
from src.agent.state import AgentState
from src.config import Settings, get_settings
from src.llm.gemini_client import GeminiClient
from src.schemas.evaluation import EvaluationResultSchema, SecurityFlags

MAX_SUMMARY_WORDS = 150


class _NarrativeReportOutput(BaseModel):
    """Salida narrativa estructurada generada por Gemini."""

    executive_summary: str = Field(..., min_length=1)
    detected_gaps: list[str] = Field(default_factory=list)
    suggested_interview_questions: list[str] = Field(default_factory=list)


def _clamp_words(text: str, max_words: int = MAX_SUMMARY_WORDS) -> str:
    """Garantiza que el resumen ejecutivo no supere el máximo de palabras."""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."


def generate_report_node(
    state: AgentState,
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> dict[str, EvaluationResultSchema]:
    """Redacta el resumen ejecutivo, brechas y preguntas y ensambla el resultado final."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)

    vacancy = state["vacancy"]
    candidate = state["candidate"]
    knockout_results = state.get("knockout_results", [])
    skills_matrix = state.get("skills_matrix", [])
    category_scores = state["category_scores"]
    overall_score = state["overall_score"]
    verdict = state["verdict"]
    security_flags = state.get("security_flags", SecurityFlags())
    evaluation_id = state.get("evaluation_id") or f"eval_{uuid.uuid4().hex[:8]}"

    eval_context = {
        "vacancy_title": vacancy.title,
        "verdict": verdict.value,
        "overall_score": overall_score,
        "category_scores": category_scores.model_dump(mode="json"),
        "knockout_requirements": [k.model_dump(mode="json") for k in knockout_results],
        "skills_matrix": [s.model_dump(mode="json") for s in skills_matrix],
    }

    prompt = (
        "Redacta el resumen ejecutivo (máximo 150 palabras), lista las brechas detectadas "
        "y propón entre 3 y 5 preguntas de entrevista personalizadas.\n\n"
        f"<evaluation_facts>\n{json.dumps(eval_context, ensure_ascii=False, indent=2)}\n"
        "</evaluation_facts>\n\n"
        f"{serialize_candidate_for_prompt(candidate)}"
    )

    narrative = client.generate_structured(
        model=cfg.gemini_flash_model,
        system_instruction=REPORTER_SYSTEM_INSTRUCTION,
        contents=prompt,
        response_schema=_NarrativeReportOutput,
    )

    final_result = EvaluationResultSchema(
        evaluation_id=evaluation_id,
        vacancy_title=vacancy.title,
        candidate_id=candidate.candidate_id,
        verdict=verdict,
        overall_score=overall_score,
        category_scores=category_scores,
        knockout_requirements=knockout_results,
        skills_matrix=skills_matrix,
        executive_summary=_clamp_words(narrative.executive_summary),
        detected_gaps=narrative.detected_gaps,
        suggested_interview_questions=narrative.suggested_interview_questions[:5],
        security_flags=security_flags,
    )

    return {"final_evaluation": final_result}
