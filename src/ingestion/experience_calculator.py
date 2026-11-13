"""Calculadora determinista de meses de experiencia laboral sin traslapes (HU-1.4)."""

import re
import unicodedata
from datetime import date

from pydantic import BaseModel, Field

from src.schemas.candidate import CandidateSchema, WorkExperience

CURRENT_MARKERS = {
    "actual",
    "actualidad",
    "presente",
    "hoy",
    "en curso",
    "vigente",
    "present",
    "current",
    "now",
    "today",
    "to date",
    "ongoing",
}

MONTH_MAP: dict[str, int] = {
    "ene": 1,
    "enero": 1,
    "jan": 1,
    "january": 1,
    "feb": 2,
    "febrero": 2,
    "february": 2,
    "mar": 3,
    "marzo": 3,
    "march": 3,
    "abr": 4,
    "abril": 4,
    "apr": 4,
    "april": 4,
    "may": 5,
    "mayo": 5,
    "jun": 6,
    "junio": 6,
    "june": 6,
    "jul": 7,
    "julio": 7,
    "july": 7,
    "ago": 8,
    "agosto": 8,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "septiembre": 9,
    "setiembre": 9,
    "september": 9,
    "oct": 10,
    "octubre": 10,
    "october": 10,
    "nov": 11,
    "noviembre": 11,
    "november": 11,
    "dic": 12,
    "diciembre": 12,
    "dec": 12,
    "december": 12,
}


class ExperienceCalculationResult(BaseModel):
    """Resultado del cálculo determinista de experiencia laboral."""

    candidate: CandidateSchema
    total_months: int = Field(..., ge=0)
    inconsistent_dates_warning: bool = Field(default=False)
    warnings: list[str] = Field(default_factory=list)


def _normalize_text(value: str) -> str:
    """Limpia tildes, puntuación sobrante y pasa a minúsculas."""
    nfkd = unicodedata.normalize("NFKD", value)
    ascii_str = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[.,]+", " ", ascii_str).strip().lower()


def is_current_marker(value: str | None) -> bool:
    """Indica si una cadena representa la fecha actual (Presente/Actualidad)."""
    if value is None:
        return False
    return _normalize_text(value) in CURRENT_MARKERS


def parse_year_month(
    raw: str | None,
    *,
    is_end: bool = False,
    reference_date: date | None = None,
) -> tuple[int, int] | None:
    """Convierte múltiples formatos de fecha a una tupla (año, mes)."""
    if raw is None:
        return None
    ref = reference_date or date.today()
    cleaned = _normalize_text(raw)
    if not cleaned:
        return None
    if cleaned in CURRENT_MARKERS:
        return (ref.year, ref.month)

    # YYYY-MM o YYYY/MM
    match_ym = re.fullmatch(r"(\d{4})[-/\s]+(\d{1,2})(?:[-/\s]+\d{1,2})?", cleaned)
    if match_ym:
        year, month = int(match_ym.group(1)), int(match_ym.group(2))
        if 1950 <= year <= 2100 and 1 <= month <= 12:
            return (year, month)
        return None

    # MM/YYYY o MM-YYYY
    match_my = re.fullmatch(r"(\d{1,2})[-/\s]+(\d{4})", cleaned)
    if match_my:
        month, year = int(match_my.group(1)), int(match_my.group(2))
        if 1950 <= year <= 2100 and 1 <= month <= 12:
            return (year, month)
        return None

    # Solo año YYYY
    match_y = re.fullmatch(r"(\d{4})", cleaned)
    if match_y:
        year = int(match_y.group(1))
        if 1950 <= year <= 2100:
            if is_end:
                month = min(12, ref.month) if year == ref.year else 12
                return (year, month)
            return (year, 1)
        return None

    # Nombre de mes + año (ej. "ene 2022", "marzo de 2023")
    tokens = [tok for tok in cleaned.split() if tok not in {"de", "del", "of"}]
    if len(tokens) >= 2:
        month_num = None
        year_num = None
        for tok in tokens:
            if tok in MONTH_MAP:
                month_num = MONTH_MAP[tok]
            elif re.fullmatch(r"\d{4}", tok):
                year_num = int(tok)
        if month_num and year_num and 1950 <= year_num <= 2100:
            return (year_num, month_num)

    return None


def _to_month_index(ym: tuple[int, int]) -> int:
    """Convierte (año, mes) a un índice entero lineal de meses."""
    return ym[0] * 12 + (ym[1] - 1)


def merge_month_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Fusiona intervalos cerrados de meses traslapados o contiguos."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda pair: (pair[0], pair[1]))
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end + 1:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def calculate_candidate_experience(
    candidate: CandidateSchema,
    *,
    reference_date: date | None = None,
) -> ExperienceCalculationResult:
    """Calcula meses por experiencia y total acumulado sin traslapes."""
    ref = reference_date or date.today()
    ref_idx = _to_month_index((ref.year, ref.month))

    updated_experiences: list[WorkExperience] = []
    intervals: list[tuple[int, int]] = []
    warnings: list[str] = []
    inconsistent = False

    for exp in candidate.work_experiences:
        start_ym = parse_year_month(exp.start_date, is_end=False, reference_date=ref)
        if exp.is_current or exp.end_date is None or is_current_marker(exp.end_date):
            end_ym: tuple[int, int] | None = (ref.year, ref.month)
        else:
            end_ym = parse_year_month(exp.end_date, is_end=True, reference_date=ref)

        if start_ym is None or end_ym is None:
            inconsistent = True
            warnings.append(
                f"No se pudieron interpretar fechas en '{exp.role} | {exp.company}': "
                f"inicio='{exp.start_date}', fin='{exp.end_date}'."
            )
            updated_experiences.append(exp.model_copy(update={"calculated_months": 0}))
            continue

        start_idx = _to_month_index(start_ym)
        end_idx = _to_month_index(end_ym)

        if start_idx > ref_idx:
            inconsistent = True
            warnings.append(
                f"Fecha de inicio futura en '{exp.role} | {exp.company}': {exp.start_date}."
            )
            updated_experiences.append(exp.model_copy(update={"calculated_months": 0}))
            continue

        if end_idx < start_idx:
            inconsistent = True
            warnings.append(
                f"Fecha fin anterior a fecha inicio en '{exp.role} | {exp.company}': "
                f"{exp.start_date} -> {exp.end_date}."
            )
            updated_experiences.append(exp.model_copy(update={"calculated_months": 0}))
            continue

        if end_idx > ref_idx:
            end_idx = ref_idx

        months = end_idx - start_idx + 1
        intervals.append((start_idx, end_idx))
        updated_experiences.append(exp.model_copy(update={"calculated_months": months}))

    merged = merge_month_intervals(intervals)
    total_months = sum((end - start + 1) for start, end in merged)

    updated_candidate = candidate.model_copy(
        update={
            "work_experiences": updated_experiences,
            "total_experience_months": total_months,
        }
    )

    return ExperienceCalculationResult(
        candidate=updated_candidate,
        total_months=total_months,
        inconsistent_dates_warning=inconsistent,
        warnings=warnings,
    )
