"""Guardrail anti-Prompt Injection y detector de texto oculto en PDFs (HU-1.5)."""

import re
from pathlib import Path

import pymupdf

from src.schemas.evaluation import SecurityFlags

INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Intento de anular instrucciones previas (EN)",
        re.compile(
            r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior|above)\s+"
            r"(?:instructions|prompts|rules)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Intento de anular instrucciones previas (ES)",
        re.compile(
            r"\bignora(?:r)?\s+(?:todas\s+)?(?:las\s+)?instrucciones\s+"
            r"(?:anteriores|previas)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Intento de manipular veredicto o puntaje",
        re.compile(
            r"\b(?:clasifica(?:r)?\s+(?:este\s+cv|al\s+candidato)\s+como\s+"
            r"(?:100%?|aceptable)|score\s+(?:this\s+cv|candidate)\s+(?:as\s+)?100)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Intento de suplantar rol de sistema",
        re.compile(
            r"\b(?:you\s+are\s+now|act\s+as\s+system|ahora\s+eres|system\s+prompt|"
            r"developer\s+instruction)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Intento de cierre o escape de delimitadores XML",
        re.compile(r"</?\s*(?:candidate_profile|raw_cv|system|instruction)\s*>", re.IGNORECASE),
    ),
]


def inspect_pdf_hidden_text(pdf_path: str | Path) -> list[str]:
    """Inspecciona spans de un PDF en busca de texto diminuto, blanco o fuera de página."""
    path = Path(pdf_path)
    if path.suffix.lower() != ".pdf" or not path.is_file():
        return []

    findings: list[str] = []
    doc = pymupdf.open(str(path))
    try:
        for page_idx, page in enumerate(doc, start=1):
            rect = page.rect
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = str(span.get("text", "")).strip()
                        if not span_text:
                            continue

                        size = float(span.get("size", 10.0))
                        if size < 2.0:
                            findings.append(
                                f"Texto con tamaño diminuto ({size:.1f}pt) en página {page_idx}."
                            )

                        color = int(span.get("color", 0))
                        red = (color >> 16) & 0xFF
                        green = (color >> 8) & 0xFF
                        blue = color & 0xFF
                        if red >= 245 and green >= 245 and blue >= 245:
                            findings.append(
                                f"Texto blanco/invisible detectado en página {page_idx}."
                            )

                        bbox = span.get("bbox")
                        if bbox and len(bbox) == 4:
                            x0, y0, x1, y1 = bbox
                            if x1 < 0 or x0 > rect.width or y1 < 0 or y0 > rect.height:
                                findings.append(
                                    f"Texto fuera del área visible en página {page_idx}."
                                )
    finally:
        doc.close()

    # Deduplicar preservando orden
    return list(dict.fromkeys(findings))


def scan_prompt_injection_patterns(text: str) -> list[str]:
    """Detecta patrones textuales típicos de Prompt Injection."""
    findings: list[str] = []
    for label, pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


def wrap_candidate_xml(payload: str) -> str:
    """Envuelve datos del candidato en tags XML estrictos neutralizando tags internos."""
    sanitized = re.sub(
        r"</?\s*candidate_profile\s*>",
        "[TAG_NEUTRALIZADO]",
        payload,
        flags=re.IGNORECASE,
    )
    return f"<candidate_profile>\n{sanitized}\n</candidate_profile>"


def run_prompt_guard(
    text: str,
    *,
    file_path: str | Path | None = None,
    inconsistent_dates_warning: bool = False,
    date_warnings: list[str] | None = None,
) -> SecurityFlags:
    """Ejecuta todos los controles de seguridad sobre el texto y archivo de un CV."""
    details: list[str] = []
    if file_path is not None:
        details.extend(inspect_pdf_hidden_text(file_path))

    details.extend(scan_prompt_injection_patterns(text))
    injection_detected = len(details) > 0

    if date_warnings:
        details.extend(date_warnings)

    return SecurityFlags(
        prompt_injection_detected=injection_detected,
        inconsistent_dates_warning=inconsistent_dates_warning,
        details=details,
    )
