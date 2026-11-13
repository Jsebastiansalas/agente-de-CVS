"""Suite automatizada de benchmark contra el Golden Dataset (HU-3.1)."""

import argparse
import asyncio
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

from evals.validate_dataset import DEFAULT_DATASET_DIR, GoldenCase, validate_golden_dataset
from src.agent.graph import aevaluate_cv_file_against_vacancy
from src.config import Settings, get_settings
from src.ingestion.vacancy_extractor import extract_vacancy_from_file
from src.llm.context_cache import VacancyCacheManager
from src.llm.gemini_client import GeminiClient
from src.llm.telemetry import UsageSummary
from src.schemas.evaluation import Verdict
from src.schemas.vacancy import VacancySchema

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


class CaseEvalOutcome(BaseModel):
    """Resultado de un caso individual en el benchmark."""

    case_id: str
    vacancy_file: str
    cv_file: str
    expected_verdict: Verdict
    predicted_verdict: Verdict | None = None
    overall_score: float | None = None
    is_exact_match: bool = False
    is_critical_fn: bool = False
    is_false_positive: bool = False
    latency_seconds: float = 0.0
    error: str | None = None


class ConsistencyItem(BaseModel):
    """Resultado de repetibilidad sobre N ejecuciones del mismo CV."""

    case_id: str
    scores: list[float]
    verdicts: list[Verdict]
    spread: float
    is_within_3pct: bool


class EvalBenchmarkReport(BaseModel):
    """Reporte consolidado de calidad, latencia, consistencia y costo."""

    total_cases: int
    evaluated_cases: int
    failed_cases: int
    exact_matches: int
    accuracy_pct: float
    critical_false_negatives: int
    critical_fn_rate_pct: float
    false_positives: int
    avg_latency_seconds: float
    confusion_matrix: dict[str, dict[str, int]] = Field(default_factory=dict)
    outcomes: list[CaseEvalOutcome] = Field(default_factory=list)
    consistency_checks: list[ConsistencyItem] = Field(default_factory=list)
    usage_summary: UsageSummary = Field(default_factory=UsageSummary)


def compute_benchmark_metrics(
    outcomes: list[CaseEvalOutcome],
    *,
    consistency_checks: list[ConsistencyItem] | None = None,
    usage_summary: UsageSummary | None = None,
) -> EvalBenchmarkReport:
    """Calcula métricas agregadas de precisión, matriz de confusión y falsos negativos."""
    evaluated = [o for o in outcomes if o.error is None and o.predicted_verdict is not None]
    failed = len(outcomes) - len(evaluated)
    exact_matches = sum(1 for o in evaluated if o.is_exact_match)
    accuracy = round((exact_matches / len(evaluated)) * 100, 2) if evaluated else 0.0

    acceptable_expected = [
        o for o in evaluated if o.expected_verdict == Verdict.ACEPTABLE
    ]
    critical_fns = sum(1 for o in evaluated if o.is_critical_fn)
    critical_fn_rate = (
        round((critical_fns / len(acceptable_expected)) * 100, 2)
        if acceptable_expected
        else 0.0
    )
    false_positives = sum(1 for o in evaluated if o.is_false_positive)
    avg_latency = (
        round(sum(o.latency_seconds for o in evaluated) / len(evaluated), 2)
        if evaluated
        else 0.0
    )

    matrix: dict[str, dict[str, int]] = defaultdict(
        lambda: {v.value: 0 for v in Verdict}
    )
    for item in evaluated:
        assert item.predicted_verdict is not None
        matrix[item.expected_verdict.value][item.predicted_verdict.value] += 1

    return EvalBenchmarkReport(
        total_cases=len(outcomes),
        evaluated_cases=len(evaluated),
        failed_cases=failed,
        exact_matches=exact_matches,
        accuracy_pct=accuracy,
        critical_false_negatives=critical_fns,
        critical_fn_rate_pct=critical_fn_rate,
        false_positives=false_positives,
        avg_latency_seconds=avg_latency,
        confusion_matrix={k: dict(v) for k, v in matrix.items()},
        outcomes=outcomes,
        consistency_checks=consistency_checks or [],
        usage_summary=usage_summary or UsageSummary(),
    )


async def _evaluate_single_case(
    case: GoldenCase,
    vacancy: VacancySchema,
    *,
    dataset_dir: Path,
    gemini_client: GeminiClient,
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> CaseEvalOutcome:
    cv_path = dataset_dir / case.cv_file
    async with semaphore:
        started = time.perf_counter()
        try:
            result, _ = await aevaluate_cv_file_against_vacancy(
                vacancy=vacancy,
                cv_path=cv_path,
                candidate_id=f"eval_{case.case_id}",
                gemini_client=gemini_client,
                settings=settings,
            )
            elapsed = round(time.perf_counter() - started, 2)
            pred = result.verdict
            exp = case.expected_verdict
            return CaseEvalOutcome(
                case_id=case.case_id,
                vacancy_file=case.vacancy_file,
                cv_file=case.cv_file,
                expected_verdict=exp,
                predicted_verdict=pred,
                overall_score=result.overall_score,
                is_exact_match=(pred == exp),
                is_critical_fn=(
                    exp == Verdict.ACEPTABLE and pred == Verdict.NO_ACEPTABLE
                ),
                is_false_positive=(
                    exp == Verdict.NO_ACEPTABLE and pred == Verdict.ACEPTABLE
                ),
                latency_seconds=elapsed,
            )
        except Exception as exc:
            elapsed = round(time.perf_counter() - started, 2)
            return CaseEvalOutcome(
                case_id=case.case_id,
                vacancy_file=case.vacancy_file,
                cv_file=case.cv_file,
                expected_verdict=case.expected_verdict,
                latency_seconds=elapsed,
                error=str(exc),
            )


async def run_golden_evals(
    *,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    limit: int | None = None,
    max_concurrency: int = 3,
    consistency_sample: int = 0,
    consistency_runs: int = 3,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
    mock: bool = False,
) -> EvalBenchmarkReport:
    """Ejecuta el benchmark completo contra el Golden Dataset y genera el reporte."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    cache_manager = VacancyCacheManager()

    dataset = validate_golden_dataset(dataset_dir)
    cases = dataset.cases[:limit] if limit else dataset.cases

    if mock:
        mock_outcomes: list[CaseEvalOutcome] = []
        for idx, case in enumerate(cases):
            pred = case.expected_verdict
            if pred == Verdict.ACEPTABLE:
                score = 86.0 + (idx % 9)
            elif pred == Verdict.ACEPTABLE_CON_RESERVAS:
                score = 66.0 + (idx % 6)
            else:
                score = 42.0 + (idx % 12)

            mock_outcomes.append(
                CaseEvalOutcome(
                    case_id=case.case_id,
                    vacancy_file=case.vacancy_file,
                    cv_file=case.cv_file,
                    expected_verdict=case.expected_verdict,
                    predicted_verdict=pred,
                    overall_score=round(score, 1),
                    is_exact_match=True,
                    is_critical_fn=False,
                    is_false_positive=False,
                    latency_seconds=1.25,
                )
            )

        mock_consistency: list[ConsistencyItem] = []
        if consistency_sample > 0 and consistency_runs > 1:
            for case in cases[:consistency_sample]:
                base_s = 85.0 if case.expected_verdict == Verdict.ACEPTABLE else 55.0
                scores = [base_s, round(base_s + 0.4, 1), round(base_s - 0.3, 1)][:consistency_runs]
                mock_consistency.append(
                    ConsistencyItem(
                        case_id=case.case_id,
                        scores=scores,
                        verdicts=[case.expected_verdict] * len(scores),
                        spread=0.7,
                        is_within_3pct=True,
                    )
                )

        return compute_benchmark_metrics(
            mock_outcomes,
            consistency_checks=mock_consistency,
            usage_summary=UsageSummary(
                total_calls=len(cases) * 3,
                total_tokens=len(cases) * 2800,
                total_estimated_cost_usd=round(len(cases) * 0.0004, 4),
            ),
        )

    # Pre-extraer cada vacante única una sola vez usando VacancyCacheManager
    vacancies_by_file: dict[str, VacancySchema] = {}
    for case in cases:
        if case.vacancy_file not in vacancies_by_file:
            vac_path = dataset_dir / case.vacancy_file
            vacancies_by_file[case.vacancy_file] = await asyncio.to_thread(
                extract_vacancy_from_file,
                vac_path,
                vacancy_id=Path(case.vacancy_file).stem,
                gemini_client=client,
                settings=cfg,
                cache_manager=cache_manager,
            )

    semaphore = asyncio.Semaphore(max(1, max_concurrency))
    outcomes = await asyncio.gather(
        *[
            _evaluate_single_case(
                case,
                vacancies_by_file[case.vacancy_file],
                dataset_dir=dataset_dir,
                gemini_client=client,
                settings=cfg,
                semaphore=semaphore,
            )
            for case in cases
        ]
    )

    consistency_checks: list[ConsistencyItem] = []
    if consistency_sample > 0 and consistency_runs > 1:
        for case in cases[:consistency_sample]:
            scores: list[float] = []
            verdicts: list[Verdict] = []
            for _ in range(consistency_runs):
                outcome = await _evaluate_single_case(
                    case,
                    vacancies_by_file[case.vacancy_file],
                    dataset_dir=dataset_dir,
                    gemini_client=client,
                    settings=cfg,
                    semaphore=semaphore,
                )
                if outcome.overall_score is not None and outcome.predicted_verdict is not None:
                    scores.append(outcome.overall_score)
                    verdicts.append(outcome.predicted_verdict)
            if scores:
                spread = round(max(scores) - min(scores), 2)
                consistency_checks.append(
                    ConsistencyItem(
                        case_id=case.case_id,
                        scores=scores,
                        verdicts=verdicts,
                        spread=spread,
                        is_within_3pct=(spread < 3.0),
                    )
                )

    return compute_benchmark_metrics(
        outcomes,
        consistency_checks=consistency_checks,
        usage_summary=client.get_usage_summary(),
    )


def format_markdown_report(report: EvalBenchmarkReport) -> str:
    """Formatea el reporte del benchmark en Markdown legible."""
    lines = [
        "# Reporte de Evaluación — Golden Dataset",
        "",
        "## Resumen General",
        f"- **Casos evaluados:** {report.evaluated_cases}/{report.total_cases} "
        f"(fallidos: {report.failed_cases})",
        f"- **Accuracy exacto:** {report.accuracy_pct:.2f}% "
        f"({report.exact_matches}/{report.evaluated_cases})",
        f"- **Falsos Negativos Críticos:** {report.critical_false_negatives} "
        f"({report.critical_fn_rate_pct:.2f}%)",
        f"- **Falsos Positivos:** {report.false_positives}",
        f"- **Latencia promedio por CV:** {report.avg_latency_seconds:.2f} s",
        f"- **Tokens totales:** {report.usage_summary.total_tokens} "
        f"(costo estimado: ${report.usage_summary.total_estimated_cost_usd:.4f} USD)",
        "",
        "## Matriz de Confusión (Esperado vs. Predicho)",
        "| Esperado \\ Predicho | ACEPTABLE | ACEPTABLE_CON_RESERVAS | NO_ACEPTABLE |",
        "| :--- | :---: | :---: | :---: |",
    ]

    for exp_key in [v.value for v in Verdict]:
        row = report.confusion_matrix.get(exp_key, {})
        lines.append(
            f"| **{exp_key}** | {row.get('ACEPTABLE', 0)} | "
            f"{row.get('ACEPTABLE_CON_RESERVAS', 0)} | {row.get('NO_ACEPTABLE', 0)} |"
        )

    lines.extend(["", "## Detalle por Caso", "| Case ID | Esperado | Predicho | Score | OK |"])
    lines.append("| :--- | :--- | :--- | :---: | :---: |")
    for item in report.outcomes:
        pred_str = item.predicted_verdict.value if item.predicted_verdict else f"ERR: {item.error}"
        score_str = f"{item.overall_score:.1f}" if item.overall_score is not None else "-"
        ok_str = "✅" if item.is_exact_match else "❌"
        lines.append(
            f"| {item.case_id} | {item.expected_verdict.value} | "
            f"{pred_str} | {score_str} | {ok_str} |"
        )

    if report.consistency_checks:
        lines.extend(["", "## Consistencia (Repetibilidad)"])
        for chk in report.consistency_checks:
            std = round(statistics.pstdev(chk.scores), 2) if len(chk.scores) > 1 else 0.0
            lines.append(
                f"- **{chk.case_id}**: scores={chk.scores}, spread={chk.spread} "
                f"(std={std}), <3%? {'✅' if chk.is_within_3pct else '❌'}"
            )

    return "\n".join(lines) + "\n"


def save_report(report: EvalBenchmarkReport, reports_dir: Path = REPORTS_DIR) -> tuple[Path, Path]:
    """Guarda el reporte en JSON y Markdown dentro de evals/reports/."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "latest_eval_report.json"
    md_path = reports_dir / "latest_eval_report.md"

    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(format_markdown_report(report), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark del agente contra el Golden Dataset.")
    parser.add_argument("--limit", type=int, default=None, help="Limitar cantidad de casos.")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrencia máxima.")
    parser.add_argument(
        "--consistency-sample",
        type=int,
        default=0,
        help="Cantidad de CVs para prueba de repetibilidad.",
    )
    parser.add_argument(
        "--consistency-runs",
        type=int,
        default=3,
        help="Número de repeticiones por CV en prueba de repetibilidad.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Ejecutar benchmark en modo simulado para CI / sin consumir cuota de API.",
    )
    args = parser.parse_args()

    report = asyncio.run(
        run_golden_evals(
            limit=args.limit,
            max_concurrency=args.concurrency,
            consistency_sample=args.consistency_sample,
            consistency_runs=args.consistency_runs,
            mock=args.mock,
        )
    )
    json_path, md_path = save_report(report)
    print(format_markdown_report(report))
    print(f"Reportes guardados en: {json_path} y {md_path}")


if __name__ == "__main__":
    main()
