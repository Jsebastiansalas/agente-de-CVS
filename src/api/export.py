"""Utilidades de exportación de resultados de evaluación a CSV compatible con Excel (HU-4.1)."""

import csv
import io

from src.storage.database import StoredEvaluation


def export_evaluations_to_csv(items: list[StoredEvaluation]) -> bytes:
    """Serializa una lista de evaluaciones a CSV UTF-8 con BOM para Excel."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "evaluation_id",
            "vacancy_title",
            "source_file",
            "candidate_id",
            "candidate_name",
            "candidate_email",
            "verdict",
            "overall_score",
            "exp_score",
            "must_have_score",
            "nice_to_have_score",
            "edu_lang_score",
            "human_verdict",
            "prompt_injection_detected",
            "inconsistent_dates_warning",
            "detected_gaps",
            "executive_summary",
            "created_at",
        ]
    )

    for stored in items:
        ev = stored.evaluation
        pii = stored.contact_pii
        cats = ev.category_scores
        human_verdict = (
            stored.latest_feedback.human_verdict.value if stored.latest_feedback else ""
        )
        writer.writerow(
            [
                ev.evaluation_id,
                ev.vacancy_title,
                stored.source_file or "",
                ev.candidate_id,
                pii.full_name or "",
                pii.email or "",
                ev.verdict.value,
                ev.overall_score,
                cats.relevant_experience.score,
                cats.must_have_skills.score,
                cats.nice_to_have_skills.score,
                cats.education_and_languages.score,
                human_verdict,
                ev.security_flags.prompt_injection_detected,
                ev.security_flags.inconsistent_dates_warning,
                " | ".join(ev.detected_gaps),
                ev.executive_summary,
                stored.created_at,
            ]
        )

    return buffer.getvalue().encode("utf-8-sig")
