"""Configuración centralizada del agente (modelos Gemini, umbrales y pesos)."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScoringWeights(BaseSettings):
    """Pesos de la fórmula determinista de puntaje ponderado."""

    relevant_experience: float = Field(default=0.40, ge=0.0, le=1.0)
    must_have_skills: float = Field(default=0.35, ge=0.0, le=1.0)
    nice_to_have_skills: float = Field(default=0.15, ge=0.0, le=1.0)
    education_and_languages: float = Field(default=0.10, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_sum_equals_one(self) -> "ScoringWeights":
        """Garantiza que la suma de los pesos sea exactamente 1.0."""
        total = (
            self.relevant_experience
            + self.must_have_skills
            + self.nice_to_have_skills
            + self.education_and_languages
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Los pesos de scoring deben sumar 1.0 (actual: {total:.4f})")
        return self


class Settings(BaseSettings):
    """Configuración general cargada desde variables de entorno o archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", description="Clave de API de Google Gemini")
    gemini_flash_model: str = Field(default="gemini-2.5-flash")
    gemini_pro_model: str = Field(default="gemini-2.5-pro")
    gemini_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    gemini_max_retries: int = Field(default=3, ge=1, le=10)
    gemini_retry_base_delay: float = Field(default=1.0, gt=0.0)

    # Umbrales de decisión
    acceptable_threshold: float = Field(default=75.0, ge=0.0, le=100.0)
    reservations_threshold: float = Field(default=60.0, ge=0.0, le=100.0)

    # Límites de ingesta
    max_file_size_mb: int = Field(default=10, ge=1, le=50)

    weights: ScoringWeights = Field(default_factory=ScoringWeights)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "Settings":
        """Asegura que el umbral de ACEPTABLE sea mayor al de ACEPTABLE_CON_RESERVAS."""
        if self.acceptable_threshold <= self.reservations_threshold:
            raise ValueError(
                "acceptable_threshold debe ser mayor que reservations_threshold"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Devuelve la instancia cacheada de configuración."""
    return Settings()
