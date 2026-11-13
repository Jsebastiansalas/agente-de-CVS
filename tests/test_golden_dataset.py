"""Pruebas de integridad del Golden Dataset (HU-0.3)."""

from evals.validate_dataset import validate_golden_dataset
from src.schemas.evaluation import Verdict


def test_golden_dataset_integrity_and_coverage() -> None:
    dataset = validate_golden_dataset()
    assert len(dataset.cases) >= 30

    verdicts = {case.expected_verdict for case in dataset.cases}
    assert verdicts == {
        Verdict.ACEPTABLE,
        Verdict.ACEPTABLE_CON_RESERVAS,
        Verdict.NO_ACEPTABLE,
    }
