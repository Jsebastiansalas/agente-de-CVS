"""Pruebas unitarias para el parser multi-formato y fallback OCR (HU-1.1)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from evals.validate_dataset import DEFAULT_DATASET_DIR
from src.config import Settings
from src.ingestion.document_parser import (
    CorruptedDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    parse_document,
)


def test_parse_txt_document() -> None:
    txt_path = DEFAULT_DATASET_DIR / "cvs" / "cv_01_backend_acep_senior.txt"
    parsed = parse_document(txt_path)
    assert parsed.source_format == "txt"
    assert parsed.used_ocr_fallback is False
    assert "FastAPI" in parsed.text


def test_parse_docx_document() -> None:
    docx_path = DEFAULT_DATASET_DIR / "cvs" / "cv_07_frontend_acep_docx.docx"
    parsed = parse_document(docx_path)
    assert parsed.source_format == "docx"
    assert parsed.used_ocr_fallback is False
    assert "TypeScript" in parsed.text
    assert "React" in parsed.text


def test_parse_two_column_pdf_preserves_both_columns() -> None:
    pdf_path = DEFAULT_DATASET_DIR / "cvs" / "cv_02_backend_acep_2col.pdf"
    parsed = parse_document(pdf_path)
    assert parsed.source_format == "pdf"
    assert parsed.used_ocr_fallback is False
    assert "HABILIDADES" in parsed.text
    assert "EXPERIENCIA LABORAL" in parsed.text
    assert "FastAPI" in parsed.text


def test_parse_scanned_pdf_triggers_gemini_ocr_fallback() -> None:
    scanned_pdf = DEFAULT_DATASET_DIR / "cvs" / "cv_09_frontend_reservas_scan.pdf"
    mock_gemini = MagicMock()
    mock_gemini.generate_text.return_value = (
        "CANDIDATO ANONIMO 09\nDesarrollador Web | Agencia Creativa\nReact y JavaScript"
    )

    parsed = parse_document(
        scanned_pdf,
        gemini_client=mock_gemini,
        settings=Settings(gemini_api_key="test-key"),
    )

    assert parsed.used_ocr_fallback is True
    assert "React" in parsed.text
    mock_gemini.generate_text.assert_called_once()


def test_parse_image_cv_uses_gemini_vision(tmp_path: Path) -> None:
    from PIL import Image

    img_path = tmp_path / "cv_foto.png"
    Image.new("RGB", (200, 100), color="white").save(img_path)

    mock_gemini = MagicMock()
    mock_gemini.generate_text.return_value = "CANDIDATO\nPython Developer\nFastAPI"

    parsed = parse_document(
        img_path,
        gemini_client=mock_gemini,
        settings=Settings(gemini_api_key="test-key"),
    )
    assert parsed.source_format == "png"
    assert parsed.used_ocr_fallback is True
    assert "FastAPI" in parsed.text


def test_parse_rejects_unsupported_extension(tmp_path: Path) -> None:
    bad_file = tmp_path / "cv.exe"
    bad_file.write_bytes(b"binary")
    with pytest.raises(UnsupportedFileTypeError):
        parse_document(bad_file)


def test_parse_rejects_empty_and_corrupted_files(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(CorruptedDocumentError):
        parse_document(empty_file)

    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"not a valid pdf")
    with pytest.raises(CorruptedDocumentError):
        parse_document(corrupt_pdf)


def test_parse_rejects_file_too_large(tmp_path: Path) -> None:
    big_file = tmp_path / "big.txt"
    big_file.write_bytes(b"a" * (2 * 1024 * 1024))
    with pytest.raises(FileTooLargeError):
        parse_document(big_file, settings=Settings(max_file_size_mb=1))
