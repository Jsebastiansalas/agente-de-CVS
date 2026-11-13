"""CLI directo para evaluar archivos de Hojas de Vida contra una Vacante desde terminal."""

import argparse
import json
from pathlib import Path

from src.agent.batch import evaluate_batch
from src.agent.graph import evaluate_cv_file_against_vacancy
from src.ingestion.vacancy_extractor import extract_vacancy, extract_vacancy_from_file
from src.llm.gemini_client import GeminiClient
from src.schemas.evaluation import EvaluationResultSchema


def _format_human_verdict(result: EvaluationResultSchema, source_name: str) -> str:
    """Formatea un dictamen legible para consola."""
    lines = [
        f"=== Dictamen: {source_name} ===",
        f"Vacante: {result.vacancy_title}",
        f"Veredicto: {result.verdict.value} | Puntaje: {result.overall_score:.2f}/100",
        f"Resumen: {result.executive_summary}",
    ]
    if result.knockout_requirements:
        lines.append("Requisitos Excluyentes:")
        for ko in result.knockout_requirements:
            lines.append(f"  - [{ko.status.value}] {ko.requirement}")
    if result.detected_gaps:
        lines.append("Brechas detectadas:")
        for gap in result.detected_gaps:
            lines.append(f"  - {gap}")
    if result.suggested_interview_questions:
        lines.append("Preguntas sugeridas:")
        for q in result.suggested_interview_questions:
            lines.append(f"  - {q}")
    return "\n".join(lines)


def run_cli(argv: list[str] | None = None) -> int:
    """Ejecuta evaluación individual o en lote desde argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Evalúa archivos de Hojas de Vida (PDF/DOCX/TXT/Imagen) contra una Vacante."
    )
    vac_group = parser.add_mutually_exclusive_group(required=True)
    vac_group.add_argument(
        "--vacancy",
        type=Path,
        help="Ruta al archivo de la vacante (PDF, DOCX, TXT, MD o imagen).",
    )
    vac_group.add_argument(
        "--vacancy-text",
        type=str,
        help="Texto libre de la vacante.",
    )
    parser.add_argument(
        "--cv",
        type=Path,
        nargs="+",
        required=True,
        help="Una o más rutas a archivos de Hoja de Vida.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Concurrencia máxima para evaluación de múltiples CVs.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime el resultado completo en formato JSON.",
    )
    args = parser.parse_args(argv)

    client = GeminiClient()
    if args.vacancy is not None:
        vacancy = extract_vacancy_from_file(args.vacancy, gemini_client=client)
    else:
        vacancy = extract_vacancy(args.vacancy_text, gemini_client=client)

    if len(args.cv) == 1:
        evaluation, _ = evaluate_cv_file_against_vacancy(
            vacancy=vacancy,
            cv_path=args.cv[0],
            gemini_client=client,
        )
        if args.json:
            print(json.dumps(evaluation.model_dump(mode="json"), indent=2, ensure_ascii=False))
        else:
            print(_format_human_verdict(evaluation, args.cv[0].name))
        return 0

    batch = evaluate_batch(
        vacancy=vacancy,
        cv_paths=args.cv,
        max_concurrency=args.concurrency,
        gemini_client=client,
    )
    if args.json:
        print(json.dumps(batch.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        for item in batch.ranked_candidates:
            print(f"#{item.rank}")
            print(_format_human_verdict(item.evaluation, item.source_file))
            print()
        if batch.errors:
            print("Errores:")
            for err in batch.errors:
                print(f"  - {err.source_file}: {err.error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
