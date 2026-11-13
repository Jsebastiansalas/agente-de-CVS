"""Capa de ingesta documental, extracción estructurada, privacidad y seguridad."""

from src.ingestion.candidate_extractor import (
    ExtractedCandidateBundle,
    extract_candidate,
    extract_candidate_from_file,
)
from src.ingestion.document_parser import (
    CorruptedDocumentError,
    DocumentParseError,
    FileTooLargeError,
    ParsedDocument,
    UnsupportedFileTypeError,
    parse_document,
)
from src.ingestion.experience_calculator import (
    ExperienceCalculationResult,
    calculate_candidate_experience,
)
from src.ingestion.pii_anonymizer import (
    anonymize_candidate,
    detect_residual_pii,
    scrub_text_pii,
)
from src.ingestion.prompt_guard import (
    inspect_pdf_hidden_text,
    run_prompt_guard,
    scan_prompt_injection_patterns,
    wrap_candidate_xml,
)
from src.ingestion.vacancy_extractor import extract_vacancy, extract_vacancy_from_file

__all__ = [
    "CorruptedDocumentError",
    "DocumentParseError",
    "ExperienceCalculationResult",
    "ExtractedCandidateBundle",
    "FileTooLargeError",
    "ParsedDocument",
    "UnsupportedFileTypeError",
    "anonymize_candidate",
    "calculate_candidate_experience",
    "detect_residual_pii",
    "extract_candidate",
    "extract_candidate_from_file",
    "extract_vacancy",
    "extract_vacancy_from_file",
    "inspect_pdf_hidden_text",
    "parse_document",
    "run_prompt_guard",
    "scan_prompt_injection_patterns",
    "scrub_text_pii",
    "wrap_candidate_xml",
]
