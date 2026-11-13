"""Endpoints REST de FastAPI para vacantes, evaluaciones, batch y feedback (HU-4.1, HU-4.3)."""

import asyncio
import json
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.agent.batch import BatchEvaluationResult, aevaluate_batch
from src.agent.graph import aevaluate_cv_file_against_vacancy
from src.api.export import export_evaluations_to_csv
from src.config import Settings, get_settings
from src.ingestion.document_parser import DocumentParseError
from src.ingestion.vacancy_extractor import extract_vacancy, extract_vacancy_from_file
from src.llm.context_cache import VacancyCacheManager
from src.llm.gemini_client import GeminiClient
from src.schemas.candidate import CandidateContactPII
from src.schemas.evaluation import EvaluationResultSchema, Verdict
from src.schemas.vacancy import VacancySchema
from src.storage.database import EvaluationRepository, FeedbackRecord, StoredEvaluation

MAX_BATCH_FILES = 50

router = APIRouter()


@lru_cache
def _default_cache_manager() -> VacancyCacheManager:
    return VacancyCacheManager()


def get_app_settings() -> Settings:
    """Dependencia inyectable para Settings."""
    return get_settings()


def get_gemini_client(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> GeminiClient:
    """Dependencia inyectable para GeminiClient."""
    return GeminiClient(settings=settings)


def get_repository(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> EvaluationRepository:
    """Dependencia inyectable para el repositorio SQLite."""
    return EvaluationRepository(settings.database_path)


class SingleEvaluationResponse(BaseModel):
    """Respuesta de evaluación individual."""

    source_file: str
    evaluation: EvaluationResultSchema
    contact_pii: CandidateContactPII


class FeedbackCreateRequest(BaseModel):
    """Payload para registrar revisión humana de un veredicto."""

    agrees_with_agent: bool
    human_verdict: Verdict
    comment: str = Field(default="", max_length=2000)


def _safe_filename(raw_name: str | None, fallback: str) -> str:
    """Sanitiza nombres de archivo subidos para evitar path traversal."""
    if not raw_name:
        return fallback
    name = Path(raw_name).name.strip()
    return name or fallback


async def _write_upload_to_dir(upload: UploadFile, target_dir: Path, fallback_name: str) -> Path:
    """Persiste temporalmente un UploadFile en disco para ser procesado por el parser."""
    filename = _safe_filename(upload.filename, fallback_name)
    dest = target_dir / filename
    # Si se suben dos archivos con el mismo nombre en un lote, desambiguar
    counter = 1
    while dest.exists():
        dest = target_dir / f"{Path(filename).stem}_{counter}{Path(filename).suffix}"
        counter += 1
    content = await upload.read()
    dest.write_bytes(content)
    return dest


async def _resolve_vacancy(
    *,
    vacancy_json: str | None,
    vacancy_text: str | None,
    gemini_client: GeminiClient,
    settings: Settings,
) -> VacancySchema:
    """Construye VacancySchema desde JSON pre-estructurado o texto libre."""
    if vacancy_json and vacancy_json.strip():
        try:
            return VacancySchema.model_validate_json(vacancy_json)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"vacancy_json inválido: {exc}",
            ) from exc

    if vacancy_text and vacancy_text.strip():
        return await asyncio.to_thread(
            extract_vacancy,
            vacancy_text,
            gemini_client=gemini_client,
            settings=settings,
            cache_manager=_default_cache_manager(),
        )

    raise HTTPException(
        status_code=400,
        detail="Debes proporcionar 'vacancy_json' o 'vacancy_text'.",
    )


@router.get("/health")
def health_check() -> dict[str, str]:
    """Endpoint de verificación de estado del servicio."""
    return {"status": "ok"}


@router.post("/api/v1/vacancies/parse", response_model=VacancySchema)
async def parse_vacancy_endpoint(
    vacancy_text: Annotated[str | None, Form()] = None,
    overrides_json: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    gemini_client: GeminiClient = Depends(get_gemini_client),  # noqa: B008
    settings: Settings = Depends(get_app_settings),  # noqa: B008
) -> VacancySchema:
    """Extrae y devuelve la rúbrica estructurada de una vacante desde texto o archivo."""
    overrides: dict[str, Any] | None = None
    if overrides_json and overrides_json.strip():
        try:
            parsed_ov = json.loads(overrides_json)
            if not isinstance(parsed_ov, dict):
                raise ValueError("Debe ser un objeto JSON")
            overrides = parsed_ov
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"overrides_json inválido: {exc}") from exc

    if file is not None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            saved_path = await _write_upload_to_dir(file, Path(tmp_dir), "vacancy.txt")
            try:
                return await asyncio.to_thread(
                    extract_vacancy_from_file,
                    saved_path,
                    overrides=overrides,
                    gemini_client=gemini_client,
                    settings=settings,
                    cache_manager=_default_cache_manager(),
                )
            except DocumentParseError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

    if vacancy_text and vacancy_text.strip():
        return await asyncio.to_thread(
            extract_vacancy,
            vacancy_text,
            overrides=overrides,
            gemini_client=gemini_client,
            settings=settings,
            cache_manager=_default_cache_manager(),
        )

    raise HTTPException(
        status_code=400,
        detail="Debes enviar 'vacancy_text' o adjuntar un archivo de vacante.",
    )


@router.post("/api/v1/evaluations/single", response_model=SingleEvaluationResponse)
async def evaluate_single_endpoint(
    file: Annotated[UploadFile, File()],
    vacancy_json: Annotated[str | None, Form()] = None,
    vacancy_text: Annotated[str | None, Form()] = None,
    gemini_client: GeminiClient = Depends(get_gemini_client),  # noqa: B008
    settings: Settings = Depends(get_app_settings),  # noqa: B008
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> SingleEvaluationResponse:
    """Evalúa un CV individual contra una vacante y guarda el resultado."""
    vacancy = await _resolve_vacancy(
        vacancy_json=vacancy_json,
        vacancy_text=vacancy_text,
        gemini_client=gemini_client,
        settings=settings,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        cv_path = await _write_upload_to_dir(file, Path(tmp_dir), "candidate_cv.pdf")
        try:
            evaluation, contact_pii = await aevaluate_cv_file_against_vacancy(
                vacancy=vacancy,
                cv_path=cv_path,
                gemini_client=gemini_client,
                settings=settings,
            )
        except DocumentParseError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo.save_evaluation(
        evaluation=evaluation,
        contact_pii=contact_pii,
        source_file=cv_path.name,
    )
    return SingleEvaluationResponse(
        source_file=cv_path.name,
        evaluation=evaluation,
        contact_pii=contact_pii,
    )


@router.post("/api/v1/evaluations/batch", response_model=BatchEvaluationResult)
async def evaluate_batch_endpoint(
    files: Annotated[list[UploadFile], File()],
    vacancy_json: Annotated[str | None, Form()] = None,
    vacancy_text: Annotated[str | None, Form()] = None,
    max_concurrency: Annotated[int, Form(ge=1, le=10)] = 3,
    gemini_client: GeminiClient = Depends(get_gemini_client),  # noqa: B008
    settings: Settings = Depends(get_app_settings),  # noqa: B008
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> BatchEvaluationResult:
    """Evalúa un lote de 1 a 50 CVs en paralelo y devuelve el ranking ordenado."""
    if not files:
        raise HTTPException(status_code=400, detail="Debes adjuntar al menos un CV.")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"El lote supera el máximo de {MAX_BATCH_FILES} archivos.",
        )

    vacancy = await _resolve_vacancy(
        vacancy_json=vacancy_json,
        vacancy_text=vacancy_text,
        gemini_client=gemini_client,
        settings=settings,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        cv_paths = [
            await _write_upload_to_dir(upload, tmp_path, f"cv_{idx}.pdf")
            for idx, upload in enumerate(files, start=1)
        ]
        batch_result = await aevaluate_batch(
            vacancy=vacancy,
            cv_paths=cv_paths,
            max_concurrency=max_concurrency,
            gemini_client=gemini_client,
            settings=settings,
        )

    for item in batch_result.ranked_candidates:
        repo.save_evaluation(
            evaluation=item.evaluation,
            contact_pii=item.contact_pii,
            source_file=item.source_file,
        )

    return batch_result


@router.get("/api/v1/evaluations", response_model=list[StoredEvaluation])
def list_evaluations_endpoint(
    verdict: Annotated[Verdict | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> list[StoredEvaluation]:
    """Lista evaluaciones persistidas ordenadas por puntaje."""
    return repo.list_evaluations(verdict=verdict, limit=limit)


@router.get("/api/v1/evaluations/export/csv")
def export_evaluations_csv_endpoint(
    verdict: Annotated[Verdict | None, Query()] = None,
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> Response:
    """Exporta las evaluaciones guardadas en formato CSV compatible con Excel."""
    items = repo.list_evaluations(verdict=verdict, limit=500)
    csv_bytes = export_evaluations_to_csv(items)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="evaluaciones_cv.csv"'},
    )


@router.get("/api/v1/evaluations/{evaluation_id}", response_model=StoredEvaluation)
def get_evaluation_endpoint(
    evaluation_id: str,
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> StoredEvaluation:
    """Obtiene el detalle completo de una evaluación almacenada."""
    stored = repo.get_evaluation(evaluation_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    return stored


@router.post(
    "/api/v1/evaluations/{evaluation_id}/feedback",
    response_model=FeedbackRecord,
)
def add_feedback_endpoint(
    evaluation_id: str,
    payload: FeedbackCreateRequest,
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> FeedbackRecord:
    """Registra aprobación o corrección humana sobre un veredicto (Human-in-the-Loop)."""
    try:
        return repo.add_feedback(
            evaluation_id=evaluation_id,
            agrees_with_agent=payload.agrees_with_agent,
            human_verdict=payload.human_verdict,
            comment=payload.comment,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/api/v1/evaluations/{evaluation_id}/feedback",
    response_model=list[FeedbackRecord],
)
def list_feedback_endpoint(
    evaluation_id: str,
    repo: EvaluationRepository = Depends(get_repository),  # noqa: B008
) -> list[FeedbackRecord]:
    """Devuelve el historial de revisiones humanas para una evaluación."""
    if repo.get_evaluation(evaluation_id) is None:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    return repo.list_feedback(evaluation_id)
