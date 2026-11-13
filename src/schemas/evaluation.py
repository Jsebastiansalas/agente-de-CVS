"""Esquemas Pydantic v2 para el resultado auditable de evaluación CV vs. Vacante."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Verdict(StrEnum):
    """Veredicto final emitido sobre la compatibilidad candidato-vacante."""

    ACEPTABLE = "ACEPTABLE"
    ACEPTABLE_CON_RESERVAS = "ACEPTABLE_CON_RESERVAS"
    NO_ACEPTABLE = "NO_ACEPTABLE"


class KnockoutStatus(StrEnum):
    """Estado de cumplimiento de un requisito excluyente."""

    CUMPLIDO = "CUMPLIDO"
    NO_CUMPLIDO = "NO_CUMPLIDO"
    NO_MENCIONADO_EN_CV = "NO_MENCIONADO_EN_CV"


class SkillMatchLevel(StrEnum):
    """Nivel de coincidencia semántica para una habilidad requerida."""

    EXACTO = "EXACTO"
    PARCIAL_EQUIVALENTE = "PARCIAL_EQUIVALENTE"
    SOLO_LISTADO = "SOLO_LISTADO"
    NO_EVIDENCIADO = "NO_EVIDENCIADO"


class SkillType(StrEnum):
    """Clasificación de la habilidad respecto a la vacante."""

    MUST_HAVE = "MUST_HAVE"
    NICE_TO_HAVE = "NICE_TO_HAVE"


class KnockoutEvaluation(BaseModel):
    """Evaluación individual de un requisito excluyente."""

    requirement: str = Field(..., min_length=1)
    status: KnockoutStatus
    calculated_months: int | None = Field(default=None, ge=0)
    evidence: str | None = Field(
        default=None, description="Cita textual o referencia del CV que respalda el estado"
    )
    notes: str | None = Field(default=None)

    @model_validator(mode="after")
    def require_evidence_when_met(self) -> "KnockoutEvaluation":
        """Exige evidencia textual cuando un requisito excluyente se marca como CUMPLIDO."""
        if self.status == KnockoutStatus.CUMPLIDO and not (self.evidence and self.evidence.strip()):
            raise ValueError(
                "Todo requisito excluyente CUMPLIDO debe incluir evidencia textual del CV"
            )
        return self


class SkillEvaluation(BaseModel):
    """Evaluación individual de una habilidad requerida o deseable."""

    skill: str = Field(..., min_length=1)
    skill_type: SkillType
    match_level: SkillMatchLevel
    proven_in_work_experience: bool = Field(
        default=False,
        description="True si se usó en un cargo real; False si solo aparece en lista de skills",
    )
    evidence: str | None = Field(
        default=None, description="Cita exacta del CV donde se demuestra la habilidad"
    )
    explanation: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def require_evidence_for_matched_skill(self) -> "SkillEvaluation":
        """Exige cita de evidencia si la habilidad es EXACTO o PARCIAL_EQUIVALENTE."""
        if self.match_level in {
            SkillMatchLevel.EXACTO,
            SkillMatchLevel.PARCIAL_EQUIVALENTE,
        } and not (self.evidence and self.evidence.strip()):
            raise ValueError(
                f"La habilidad '{self.skill}' con nivel {self.match_level.value} "
                "debe incluir evidencia textual del CV"
            )
        return self


class CategoryScore(BaseModel):
    """Puntaje de una dimensión individual del modelo de scoring."""

    score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted: float = Field(..., ge=0.0, le=100.0)
    justification: str = Field(..., min_length=1)


class CategoryScores(BaseModel):
    """Desglose completo de puntajes por categoría."""

    relevant_experience: CategoryScore
    must_have_skills: CategoryScore
    nice_to_have_skills: CategoryScore
    education_and_languages: CategoryScore


class SecurityFlags(BaseModel):
    """Alertas de seguridad e integridad detectadas en el CV."""

    prompt_injection_detected: bool = Field(default=False)
    inconsistent_dates_warning: bool = Field(default=False)
    details: list[str] = Field(default_factory=list)


class EvaluationResultSchema(BaseModel):
    """Resultado completo, estructurado y explicable de la evaluación."""

    evaluation_id: str = Field(..., min_length=1)
    vacancy_title: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    verdict: Verdict
    overall_score: float = Field(..., ge=0.0, le=100.0)
    category_scores: CategoryScores
    knockout_requirements: list[KnockoutEvaluation] = Field(default_factory=list)
    skills_matrix: list[SkillEvaluation] = Field(default_factory=list)
    executive_summary: str = Field(..., min_length=1)
    detected_gaps: list[str] = Field(default_factory=list)
    suggested_interview_questions: list[str] = Field(default_factory=list)
    security_flags: SecurityFlags = Field(default_factory=SecurityFlags)
