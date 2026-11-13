"""Pruebas unitarias para la calculadora determinista de experiencia (HU-1.4)."""

from datetime import date

from src.ingestion.experience_calculator import (
    calculate_candidate_experience,
    parse_year_month,
)
from src.schemas.candidate import CandidateSchema, WorkExperience


def test_parse_year_month_formats() -> None:
    ref = date(2026, 11, 13)
    assert parse_year_month("2023-02") == (2023, 2)
    assert parse_year_month("05/2021") == (2021, 5)
    assert parse_year_month("Ene 2022") == (2022, 1)
    assert parse_year_month("marzo de 2024") == (2024, 3)
    assert parse_year_month("Actualidad", reference_date=ref) == (2026, 11)
    assert parse_year_month("Present", reference_date=ref) == (2026, 11)


def test_calculate_experience_merges_overlapping_intervals() -> None:
    ref = date(2025, 10, 1)
    candidate = CandidateSchema(
        candidate_id="cand_04",
        work_experiences=[
            WorkExperience(
                role="Consultor Freelance",
                company="Varios",
                start_date="2023-06",
                end_date="2025-10",
                is_current=False,
            ),
            WorkExperience(
                role="Backend Developer",
                company="TechCorp",
                start_date="2023-01",
                end_date="Actualidad",
                is_current=True,
            ),
        ],
    )

    res = calculate_candidate_experience(candidate, reference_date=ref)
    assert res.inconsistent_dates_warning is False
    # 2023-06 a 2025-10 = 29 meses
    assert res.candidate.work_experiences[0].calculated_months == 29
    # 2023-01 a 2025-10 = 34 meses
    assert res.candidate.work_experiences[1].calculated_months == 34
    # Sin traslape duplicado debe ser 34 meses, NO 63
    assert res.total_months == 34
    assert res.candidate.total_experience_months == 34


def test_calculate_experience_handles_gaps_correctly() -> None:
    ref = date(2025, 10, 1)
    candidate = CandidateSchema(
        candidate_id="cand_gap",
        work_experiences=[
            WorkExperience(
                role="Dev 1",
                company="A",
                start_date="2020-01",
                end_date="2020-12",  # 12 meses
            ),
            WorkExperience(
                role="Dev 2",
                company="B",
                start_date="2022-01",
                end_date="2022-12",  # 12 meses
            ),
        ],
    )

    res = calculate_candidate_experience(candidate, reference_date=ref)
    assert res.total_months == 24


def test_calculate_experience_flags_inconsistent_and_future_dates() -> None:
    ref = date(2025, 10, 1)
    candidate = CandidateSchema(
        candidate_id="cand_bad_dates",
        work_experiences=[
            WorkExperience(
                role="Dev",
                company="X",
                start_date="2024-05",
                end_date="2023-01",
            ),
            WorkExperience(
                role="Future Dev",
                company="Y",
                start_date="2028-01",
                end_date="2028-06",
            ),
        ],
    )

    res = calculate_candidate_experience(candidate, reference_date=ref)
    assert res.inconsistent_dates_warning is True
    assert len(res.warnings) == 2
    assert res.total_months == 0
