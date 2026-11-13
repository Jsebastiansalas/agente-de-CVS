"""Procesamiento en lote con concurrencia controlada y ranking ordenado (HU-3.2)."""

import asyncio
import time
from pathlib import Path

from pydantic import BaseModel, Field

from src.agent.graph import aevaluate_cv_file_against_vacancy
from src.config import Settings, get_settings
from src.llm.gemini_client import GeminiClient
from src.llm.telemetry import UsageSummary
from src.schemas.candidate import CandidateContactPII
from src.schemas.evaluation import EvaluationResultSchema, Verdict
from src.schemas.vacancy import VacancySchema

VERDICT_PRIORITY: dict[Verdict, int] = {
    Verdict.ACEPTABLE: 0,
    Verdict.ACEPTABLE_CON_RESERVAS: 1,
    Verdict.NO_ACEPTABLE: 2,
}


class BatchCandidateItem(BaseModel):
    """Resultado individual dentro de un lote rankeado."""

    rank: int = Field(..., ge=1)
    source_file: str
    evaluation: EvaluationResultSchema
    contact_pii: CandidateContactPII
    duration_seconds: float = Field(..., ge=0.0)


class BatchEvaluationErrorItem(BaseModel):
    """Error capturado para un archivo individual sin abortar el lote completo."""

    source_file: str
    error: str


class BatchEvaluationResult(BaseModel):
    """Resultado consolidado del procesamiento en lote."""

    vacancy: VacancySchema
    ranked_candidates: list[BatchCandidateItem] = Field(default_factory=list)
    errors: list[BatchEvaluationErrorItem] = Field(default_factory=list)
    total_duration_seconds: float = Field(..., ge=0.0)
    usage_summary: UsageSummary = Field(default_factory=UsageSummary)


async def aevaluate_batch(
    *,
    vacancy: VacancySchema,
    cv_paths: list[str | Path],
    max_concurrency: int = 4,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> BatchEvaluationResult:
    """Evalúa múltiples CVs en paralelo con semáforo y devuelve el ranking ordenado."""
    cfg = settings or get_settings()
    client = gemini_client or GeminiClient(settings=cfg)
    semaphore = asyncio.Semaphore(max(1, max_concurrency))
    batch_started = time.perf_counter()

    async def _process_one(
        idx: int, path_item: str | Path
    ) -> tuple[BatchCandidateItem | None, BatchEvaluationErrorItem | None]:
        path_obj = Path(path_item)
        async with semaphore:
            item_started = time.perf_counter()
            try:
                evaluation, pii = await aevaluate_cv_file_against_vacancy(
                    vacancy=vacancy,
                    cv_path=path_obj,
                    candidate_id=f"cand_{idx:03d}_{path_obj.stem[:16]}",
                    gemini_client=client,
                    settings=cfg,
                )
                elapsed = round(time.perf_counter() - item_started, 3)
                return (
                    BatchCandidateItem(
                        rank=1,
                        source_file=path_obj.name,
                        evaluation=evaluation,
                        contact_pii=pii,
                        duration_seconds=elapsed,
                    ),
                    None,
                )
            except Exception as exc:
                return (
                    None,
                    BatchEvaluationErrorItem(source_file=path_obj.name, error=str(exc)),
                )

    raw_results = await asyncio.gather(
        *[_process_one(idx, path) for idx, path in enumerate(cv_paths, start=1)]
    )

    items: list[BatchCandidateItem] = []
    errors: list[BatchEvaluationErrorItem] = []
    for item, err in raw_results:
        if item is not None:
            items.append(item)
        if err is not None:
            errors.append(err)

    items.sort(
        key=lambda row: (
            VERDICT_PRIORITY[row.evaluation.verdict],
            -row.evaluation.overall_score,
        )
    )
    ranked = [
        item.model_copy(update={"rank": rank_idx})
        for rank_idx, item in enumerate(items, start=1)
    ]

    total_elapsed = round(time.perf_counter() - batch_started, 3)
    return BatchEvaluationResult(
        vacancy=vacancy,
        ranked_candidates=ranked,
        errors=errors,
        total_duration_seconds=total_elapsed,
        usage_summary=client.get_usage_summary(),
    )


def evaluate_batch(
    *,
    vacancy: VacancySchema,
    cv_paths: list[str | Path],
    max_concurrency: int = 4,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> BatchEvaluationResult:
    """Wrapper síncrono para evaluar un lote de CVs."""
    return asyncio.run(
        aevaluate_batch(
            vacancy=vacancy,
            cv_paths=cv_paths,
            max_concurrency=max_concurrency,
            gemini_client=gemini_client,
            settings=settings,
        )
    )
