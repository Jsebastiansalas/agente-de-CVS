"""Construcción y ejecución paralela/asíncrona del grafo LangGraph (HU-2.1, HU-3.2)."""

import asyncio
import uuid
from functools import partial
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.agent.nodes.knockout import aevaluate_knockout_node, evaluate_knockout_node
from src.agent.nodes.reporter import agenerate_report_node, generate_report_node
from src.agent.nodes.scorer import score_and_verdict_node
from src.agent.nodes.skills_matcher import amatch_skills_node, match_skills_node
from src.agent.state import AgentState
from src.config import Settings, get_settings
from src.ingestion.candidate_extractor import aextract_candidate, extract_candidate
from src.ingestion.document_parser import parse_document
from src.ingestion.prompt_guard import run_prompt_guard
from src.llm.gemini_client import GeminiClient
from src.schemas.candidate import CandidateContactPII, CandidateSchema
from src.schemas.evaluation import EvaluationResultSchema, SecurityFlags
from src.schemas.vacancy import VacancySchema


def _compile_graph(
    *,
    knockout_fn: Any,
    skills_fn: Any,
    scorer_fn: Any,
    reporter_fn: Any,
) -> Any:
    """Compila el grafo con fan-out paralelo: [knockout, skills] -> scorer -> reporter."""
    graph = StateGraph(AgentState)
    graph.add_node("knockout_node", knockout_fn)
    graph.add_node("skills_matcher_node", skills_fn)
    graph.add_node("scorer_node", scorer_fn)
    graph.add_node("reporter_node", reporter_fn)

    # Ejecución paralela de Knockout y Comparador Semántico para reducir latencia
    graph.add_edge(START, "knockout_node")
    graph.add_edge(START, "skills_matcher_node")
    graph.add_edge(["knockout_node", "skills_matcher_node"], "scorer_node")
    graph.add_edge("scorer_node", "reporter_node")
    graph.add_edge("reporter_node", END)

    return graph.compile()


def build_evaluation_graph(
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> Any:
    """Compila el grafo síncrono de evaluación en LangGraph."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    return _compile_graph(
        knockout_fn=partial(evaluate_knockout_node, gemini_client=client, settings=cfg),
        skills_fn=partial(match_skills_node, gemini_client=client, settings=cfg),
        scorer_fn=partial(score_and_verdict_node, settings=cfg),
        reporter_fn=partial(generate_report_node, gemini_client=client, settings=cfg),
    )


def build_async_evaluation_graph(
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> Any:
    """Compila el grafo asíncrono de evaluación con concurrencia real en Gemini."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    return _compile_graph(
        knockout_fn=partial(aevaluate_knockout_node, gemini_client=client, settings=cfg),
        skills_fn=partial(amatch_skills_node, gemini_client=client, settings=cfg),
        scorer_fn=partial(score_and_verdict_node, settings=cfg),
        reporter_fn=partial(agenerate_report_node, gemini_client=client, settings=cfg),
    )


def _initial_state(
    *,
    vacancy: VacancySchema,
    candidate: CandidateSchema,
    security_flags: SecurityFlags | None = None,
    evaluation_id: str | None = None,
) -> AgentState:
    return {
        "evaluation_id": evaluation_id or f"eval_{uuid.uuid4().hex[:8]}",
        "vacancy": vacancy,
        "candidate": candidate,
        "security_flags": security_flags or SecurityFlags(),
    }


def evaluate_candidate(
    *,
    vacancy: VacancySchema,
    candidate: CandidateSchema,
    security_flags: SecurityFlags | None = None,
    evaluation_id: str | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> EvaluationResultSchema:
    """Ejecuta de forma síncrona el grafo completo sobre perfiles ya estructurados."""
    compiled = build_evaluation_graph(gemini_client=gemini_client, settings=settings)
    state = _initial_state(
        vacancy=vacancy,
        candidate=candidate,
        security_flags=security_flags,
        evaluation_id=evaluation_id,
    )
    final_state = compiled.invoke(state)
    return final_state["final_evaluation"]


async def aevaluate_candidate(
    *,
    vacancy: VacancySchema,
    candidate: CandidateSchema,
    security_flags: SecurityFlags | None = None,
    evaluation_id: str | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> EvaluationResultSchema:
    """Ejecuta de forma asíncrona el grafo completo con nodos paralelos."""
    compiled = build_async_evaluation_graph(gemini_client=gemini_client, settings=settings)
    state = _initial_state(
        vacancy=vacancy,
        candidate=candidate,
        security_flags=security_flags,
        evaluation_id=evaluation_id,
    )
    final_state = await compiled.ainvoke(state)
    return final_state["final_evaluation"]


def evaluate_cv_file_against_vacancy(
    *,
    vacancy: VacancySchema,
    cv_path: str | Path,
    candidate_id: str | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> tuple[EvaluationResultSchema, CandidateContactPII]:
    """Pipeline completo síncrono desde un archivo CV hasta el veredicto final."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)

    parsed = parse_document(cv_path, gemini_client=client, settings=cfg)
    bundle = extract_candidate(
        parsed.text,
        candidate_id=candidate_id,
        gemini_client=client,
        settings=cfg,
    )
    security_flags = run_prompt_guard(
        parsed.text,
        file_path=cv_path,
        inconsistent_dates_warning=bundle.inconsistent_dates_warning,
        date_warnings=bundle.date_warnings,
    )
    evaluation = evaluate_candidate(
        vacancy=vacancy,
        candidate=bundle.candidate,
        security_flags=security_flags,
        gemini_client=client,
        settings=cfg,
    )
    return evaluation, bundle.contact_pii


async def aevaluate_cv_file_against_vacancy(
    *,
    vacancy: VacancySchema,
    cv_path: str | Path,
    candidate_id: str | None = None,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> tuple[EvaluationResultSchema, CandidateContactPII]:
    """Pipeline completo asíncrono desde un archivo CV hasta el veredicto final."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)

    parsed = await asyncio.to_thread(
        parse_document,
        cv_path,
        gemini_client=client,
        settings=cfg,
    )
    bundle = await aextract_candidate(
        parsed.text,
        candidate_id=candidate_id,
        gemini_client=client,
        settings=cfg,
    )
    security_flags = await asyncio.to_thread(
        run_prompt_guard,
        parsed.text,
        file_path=cv_path,
        inconsistent_dates_warning=bundle.inconsistent_dates_warning,
        date_warnings=bundle.date_warnings,
    )
    evaluation = await aevaluate_candidate(
        vacancy=vacancy,
        candidate=bundle.candidate,
        security_flags=security_flags,
        gemini_client=client,
        settings=cfg,
    )
    return evaluation, bundle.contact_pii
