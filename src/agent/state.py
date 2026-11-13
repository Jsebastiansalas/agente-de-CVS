"""Definición del estado compartido (AgentState) del grafo en LangGraph (HU-2.1)."""

from typing import TypedDict

from pydantic import BaseModel, Field

from src.schemas.candidate import CandidateSchema
from src.schemas.evaluation import (
    CategoryScores,
    EvaluationResultSchema,
    KnockoutEvaluation,
    SecurityFlags,
    SkillEvaluation,
    Verdict,
)
from src.schemas.vacancy import VacancySchema


class SubscoresOutput(BaseModel):
    """Sub-puntajes crudos (0-100) producidos por el comparador semántico."""

    relevant_experience_score: float = Field(..., ge=0.0, le=100.0)
    relevant_experience_justification: str = Field(..., min_length=1)
    must_have_skills_score: float = Field(..., ge=0.0, le=100.0)
    must_have_skills_justification: str = Field(..., min_length=1)
    nice_to_have_skills_score: float = Field(..., ge=0.0, le=100.0)
    nice_to_have_skills_justification: str = Field(..., min_length=1)
    education_and_languages_score: float = Field(..., ge=0.0, le=100.0)
    education_and_languages_justification: str = Field(..., min_length=1)


class AgentState(TypedDict, total=False):
    """Estado tipado que fluye por los nodos del grafo de evaluación."""

    evaluation_id: str
    vacancy: VacancySchema
    candidate: CandidateSchema
    security_flags: SecurityFlags
    knockout_results: list[KnockoutEvaluation]
    skills_matrix: list[SkillEvaluation]
    subscores: SubscoresOutput
    category_scores: CategoryScores
    overall_score: float
    verdict: Verdict
    final_evaluation: EvaluationResultSchema
