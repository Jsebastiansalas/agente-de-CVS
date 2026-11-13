"""Esquemas Pydantic v2 para la rúbrica estructurada de una Vacante."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SeniorityLevel(StrEnum):
    """Nivel de experiencia esperado por la vacante."""

    INTERN = "INTERN"
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    OPERATIONAL = "OPERATIONAL"
    UNSPECIFIED = "NO_ESPECIFICADO"


class LanguageRequirement(BaseModel):
    """Requisito de idioma para la vacante."""

    language: str = Field(..., min_length=1, description="Nombre del idioma (ej. Inglés)")
    min_level: str = Field(
        ..., min_length=1, description="Nivel mínimo requerido (ej. B2, C1, Nativo)"
    )


class VacancySchema(BaseModel):
    """Representación estructurada de los requisitos de una vacante."""

    vacancy_id: str = Field(..., min_length=1, description="Identificador único de la vacante")
    title: str = Field(..., min_length=1, description="Título del cargo")
    seniority: SeniorityLevel = Field(default=SeniorityLevel.UNSPECIFIED)
    min_years_experience: float = Field(
        default=0.0, ge=0.0, description="Años mínimos de experiencia requeridos"
    )
    knockout_requirements: list[str] = Field(
        default_factory=list,
        description="Requisitos excluyentes duros cuyo incumplimiento descarta al candidato",
    )
    must_have_skills: list[str] = Field(
        default_factory=list,
        description="Habilidades técnicas o funcionales obligatorias",
    )
    nice_to_have_skills: list[str] = Field(
        default_factory=list,
        description="Habilidades deseables o complementarias",
    )
    required_languages: list[LanguageRequirement] = Field(default_factory=list)
    required_education: str | None = Field(
        default=None, description="Nivel o título académico requerido"
    )
    responsibilities: list[str] = Field(default_factory=list)
