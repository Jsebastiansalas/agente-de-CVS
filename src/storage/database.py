"""Repositorio SQLite para historial de evaluaciones y feedback Human-in-the-Loop (HU-4.3)."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.schemas.candidate import CandidateContactPII
from src.schemas.evaluation import EvaluationResultSchema, Verdict


class FeedbackRecord(BaseModel):
    """Registro de revisión o corrección humana sobre un veredicto."""

    id: int | None = None
    evaluation_id: str
    agrees_with_agent: bool
    human_verdict: Verdict
    comment: str = Field(default="")
    created_at: str


class StoredEvaluation(BaseModel):
    """Evaluación persistida junto con metadatos de archivo, PII y feedback."""

    evaluation: EvaluationResultSchema
    contact_pii: CandidateContactPII
    source_file: str | None = None
    created_at: str
    latest_feedback: FeedbackRecord | None = None


class EvaluationRepository:
    """Almacén SQLite thread-safe para evaluaciones y retroalimentación humana."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    vacancy_title TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    source_file TEXT,
                    verdict TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    evaluation_json TEXT NOT NULL,
                    pii_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_id TEXT NOT NULL,
                    agrees_with_agent INTEGER NOT NULL,
                    human_verdict TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (evaluation_id)
                        REFERENCES evaluations(evaluation_id)
                        ON DELETE CASCADE
                );
                """
            )

    def save_evaluation(
        self,
        *,
        evaluation: EvaluationResultSchema,
        contact_pii: CandidateContactPII,
        source_file: str | None = None,
    ) -> StoredEvaluation:
        """Guarda o actualiza una evaluación completa en SQLite."""
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluations (
                    evaluation_id, vacancy_title, candidate_id, source_file,
                    verdict, overall_score, evaluation_json, pii_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evaluation_id) DO UPDATE SET
                    vacancy_title = excluded.vacancy_title,
                    verdict = excluded.verdict,
                    overall_score = excluded.overall_score,
                    evaluation_json = excluded.evaluation_json,
                    pii_json = excluded.pii_json
                """,
                (
                    evaluation.evaluation_id,
                    evaluation.vacancy_title,
                    evaluation.candidate_id,
                    source_file,
                    evaluation.verdict.value,
                    evaluation.overall_score,
                    evaluation.model_dump_json(),
                    contact_pii.model_dump_json(),
                    created_at,
                ),
            )
        stored = self.get_evaluation(evaluation.evaluation_id)
        assert stored is not None
        return stored

    def get_evaluation(self, evaluation_id: str) -> StoredEvaluation | None:
        """Recupera una evaluación por ID junto con su último feedback si existe."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evaluations WHERE evaluation_id = ?",
                (evaluation_id,),
            ).fetchone()
            if row is None:
                return None

            fb_row = conn.execute(
                """
                SELECT * FROM feedback
                WHERE evaluation_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (evaluation_id,),
            ).fetchone()

        return self._row_to_stored(row, fb_row)

    def list_evaluations(
        self,
        *,
        verdict: Verdict | None = None,
        limit: int = 100,
    ) -> list[StoredEvaluation]:
        """Lista evaluaciones ordenadas por puntaje descendente."""
        query = "SELECT * FROM evaluations"
        params: list[object] = []
        if verdict is not None:
            query += " WHERE verdict = ?"
            params.append(verdict.value)
        query += " ORDER BY overall_score DESC, created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            results: list[StoredEvaluation] = []
            for row in rows:
                fb_row = conn.execute(
                    """
                    SELECT * FROM feedback
                    WHERE evaluation_id = ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (row["evaluation_id"],),
                ).fetchone()
                results.append(self._row_to_stored(row, fb_row))
        return results

    def add_feedback(
        self,
        *,
        evaluation_id: str,
        agrees_with_agent: bool,
        human_verdict: Verdict,
        comment: str = "",
    ) -> FeedbackRecord:
        """Registra una validación o corrección humana sobre una evaluación existente."""
        if self.get_evaluation(evaluation_id) is None:
            raise KeyError(f"Evaluación no encontrada: {evaluation_id}")

        created_at = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO feedback (
                    evaluation_id, agrees_with_agent, human_verdict, comment, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    evaluation_id,
                    1 if agrees_with_agent else 0,
                    human_verdict.value,
                    comment.strip(),
                    created_at,
                ),
            )
            feedback_id = int(cursor.lastrowid or 0)

        return FeedbackRecord(
            id=feedback_id,
            evaluation_id=evaluation_id,
            agrees_with_agent=agrees_with_agent,
            human_verdict=human_verdict,
            comment=comment.strip(),
            created_at=created_at,
        )

    def list_feedback(self, evaluation_id: str) -> list[FeedbackRecord]:
        """Devuelve todo el historial de feedback para una evaluación."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM feedback WHERE evaluation_id = ? ORDER BY id DESC",
                (evaluation_id,),
            ).fetchall()
        return [self._row_to_feedback(r) for r in rows]

    @staticmethod
    def _row_to_feedback(row: sqlite3.Row) -> FeedbackRecord:
        return FeedbackRecord(
            id=int(row["id"]),
            evaluation_id=str(row["evaluation_id"]),
            agrees_with_agent=bool(row["agrees_with_agent"]),
            human_verdict=Verdict(row["human_verdict"]),
            comment=str(row["comment"]),
            created_at=str(row["created_at"]),
        )

    @classmethod
    def _row_to_stored(
        cls,
        row: sqlite3.Row,
        fb_row: sqlite3.Row | None,
    ) -> StoredEvaluation:
        return StoredEvaluation(
            evaluation=EvaluationResultSchema.model_validate_json(row["evaluation_json"]),
            contact_pii=CandidateContactPII.model_validate_json(row["pii_json"]),
            source_file=row["source_file"],
            created_at=str(row["created_at"]),
            latest_feedback=cls._row_to_feedback(fb_row) if fb_row else None,
        )
