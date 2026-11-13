"""Contratos de datos Pydantic v2 para Vacantes, Candidatos y Evaluaciones."""

from src.schemas.candidate import (
    CandidateContactPII,
    CandidateSchema,
    EducationEntry,
    LanguageSkill,
    WorkExperience,
)
from src.schemas.evaluation import (
    CategoryScore,
    CategoryScores,
    EvaluationResultSchema,
    KnockoutEvaluation,
    KnockoutStatus,
    SecurityFlags,
    SkillEvaluation,
    SkillMatchLevel,
    SkillType,
    Verdict,
)
from src.schemas.vacancy import LanguageRequirement, SeniorityLevel, VacancySchema

__all__ = [
    "CandidateContactPII",
    "CandidateSchema",
    "CategoryScore",
    "CategoryScores",
    "EducationEntry",
    "EvaluationResultSchema",
    "KnockoutEvaluation",
    "KnockoutStatus",
    "LanguageRequirement",
    "LanguageSkill",
    "SecurityFlags",
    "SeniorityLevel",
    "SkillEvaluation",
    "SkillMatchLevel",
    "SkillType",
    "VacancySchema",
    "Verdict",
    "WorkExperience",
]
