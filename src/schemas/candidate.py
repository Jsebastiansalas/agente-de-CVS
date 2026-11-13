"""Esquemas Pydantic v2 para el perfil estructurado y anonimizado de un Candidato."""

from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    """Experiencia laboral individual extraída de la hoja de vida."""

    role: str = Field(..., min_length=1, description="Cargo desempeñado")
    company: str = Field(..., min_length=1, description="Empresa u organización")
    start_date: str = Field(
        ..., min_length=1, description="Fecha de inicio (preferiblemente YYYY-MM)"
    )
    end_date: str | None = Field(
        default=None, description="Fecha de fin (YYYY-MM) o None si es actual"
    )
    is_current: bool = Field(default=False, description="Indica si trabaja allí actualmente")
    calculated_months: int = Field(
        default=0, ge=0, description="Duración en meses calculada de forma determinista"
    )
    technologies: list[str] = Field(
        default_factory=list, description="Tecnologías o herramientas aplicadas en este cargo"
    )
    achievements: list[str] = Field(
        default_factory=list, description="Responsabilidades, logros o métricas de impacto"
    )


class EducationEntry(BaseModel):
    """Registro de formación académica."""

    degree: str = Field(..., min_length=1, description="Título o programa cursado")
    institution: str = Field(..., min_length=1, description="Institución educativa")
    field_of_study: str | None = Field(default=None)
    end_year: int | None = Field(default=None, ge=1950, le=2100)
    is_completed: bool = Field(default=True)


class LanguageSkill(BaseModel):
    """Idioma reportado en la hoja de vida."""

    language: str = Field(..., min_length=1)
    level: str = Field(..., min_length=1, description="Nivel reportado (ej. B2, Avanzado)")


class CandidateSchema(BaseModel):
    """Perfil del candidato anonimizado (sin PII) para evaluación objetiva."""

    candidate_id: str = Field(..., min_length=1, description="ID anónimo del candidato")
    summary: str | None = Field(default=None, description="Perfil profesional resumido")
    total_experience_months: int = Field(
        default=0,
        ge=0,
        description="Meses totales de experiencia laboral sin contar traslapes",
    )
    work_experiences: list[WorkExperience] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    languages: list[LanguageSkill] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    listed_skills: list[str] = Field(
        default_factory=list,
        description="Habilidades mencionadas en sección de skills sin contexto laboral explícito",
    )


class CandidateContactPII(BaseModel):
    """Datos personales (PII) separados del flujo evaluador para mitigar sesgos."""

    candidate_id: str = Field(..., min_length=1)
    full_name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    location: str | None = Field(default=None)
