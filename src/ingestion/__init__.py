"""Capa de ingesta documental, extracción estructurada, privacidad y seguridad."""

from src.ingestion.document_parser import (
    CorruptedDocumentError,
    DocumentParseError,
    FileTooLargeError,
    ParsedDocument,
    UnsupportedFileTypeError,
    parse_document,
)

__all__ = [
    "CorruptedDocumentError",
    "DocumentParseError",
    "FileTooLargeError",
    "ParsedDocument",
    "UnsupportedFileTypeError",
    "parse_document",
]
