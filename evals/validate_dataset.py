"""Validador de integridad del Golden Dataset de calibración (HU-0.3)."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.evaluation import Verdict

DEFAULT_DATASET_DIR = Path(__file__).resolve().parent / "golden_dataset"


class GoldenCase(BaseModel):
    """Un par (vacante, hoja de vida) etiquetado por criterio humano."""

    case_id: str = Field(..., min_length=1)
    vacancy_file: str = Field(..., min_length=1)
    cv_file: str = Field(..., min_length=1)
    expected_verdict: Verdict
    reason: str = Field(..., min_length=10)
    difficulty_tags: list[
        Literal[
            "standard",
            "two_column_pdf",
            "scanned_image_pdf",
            "docx_format",
            "equivalent_technologies",
            "missing_knockout_info",
            "overlapping_dates",
        ]
    ] = Field(default_factory=lambda: ["standard"])


class GroundTruthDataset(BaseModel):
    """Estructura raíz del archivo ground_truth.json."""

    version: str = Field(..., min_length=1)
    cases: list[GoldenCase] = Field(..., min_length=1)


def validate_golden_dataset(dataset_dir: Path = DEFAULT_DATASET_DIR) -> GroundTruthDataset:
    """Valida que ground_truth.json y todos sus archivos referenciados existan y sean legibles."""
    gt_path = dataset_dir / "ground_truth.json"
    if not gt_path.exists():
        raise FileNotFoundError(f"No se encontró ground_truth.json en {dataset_dir}")

    data = json.loads(gt_path.read_text(encoding="utf-8"))
    dataset = GroundTruthDataset.model_validate(data)

    vacancies_seen: set[str] = set()
    cvs_seen: set[str] = set()
    tags_seen: set[str] = set()

    for case in dataset.cases:
        vac_path = dataset_dir / case.vacancy_file
        cv_path = dataset_dir / case.cv_file

        if not vac_path.is_file() or vac_path.stat().st_size == 0:
            raise FileNotFoundError(
                f"Vacante faltante o vacía para {case.case_id}: {vac_path}"
            )
        if not cv_path.is_file() or cv_path.stat().st_size == 0:
            raise FileNotFoundError(
                f"Hoja de vida faltante o vacía para {case.case_id}: {cv_path}"
            )

        vacancies_seen.add(case.vacancy_file)
        cvs_seen.add(case.cv_file)
        tags_seen.update(case.difficulty_tags)

    if len(vacancies_seen) < 5:
        raise ValueError(f"Se requieren al menos 5 vacantes (actual: {len(vacancies_seen)})")
    if len(cvs_seen) < 30:
        raise ValueError(f"Se requieren al menos 30 CVs (actual: {len(cvs_seen)})")

    required_hard_tags = {"two_column_pdf", "scanned_image_pdf", "equivalent_technologies"}
    missing_tags = required_hard_tags - tags_seen
    if missing_tags:
        raise ValueError(f"Faltan casos difíciles requeridos: {sorted(missing_tags)}")

    return dataset


if __name__ == "__main__":
    validated = validate_golden_dataset()
    print(f"Golden Dataset válido: {len(validated.cases)} casos verificados.")
