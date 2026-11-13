"""Parser multi-formato (PDF, DOCX, TXT) con fallback OCR multimodal en Gemini (HU-1.1)."""

import re
from pathlib import Path

import pymupdf
import pymupdf4llm
from docx import Document
from google.genai import types
from pydantic import BaseModel, Field

from src.config import Settings, get_settings
from src.llm.gemini_client import GeminiClient

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MIN_USEFUL_PDF_CHARS = 100

OCR_SYSTEM_INSTRUCTION = (
    "Eres un extractor documental de alta precisión para hojas de vida. "
    "Transcribe fielmente TODO el contenido del documento en Markdown limpio, "
    "preservando el orden de lectura lógico, secciones, fechas, cargos y habilidades. "
    "No resumas, no inventes datos ni traduzcas el contenido."
)


class DocumentParseError(Exception):
    """Error base en el parsing de documentos."""


class UnsupportedFileTypeError(DocumentParseError):
    """El formato del archivo no está soportado."""


class FileTooLargeError(DocumentParseError):
    """El archivo supera el límite máximo permitido."""


class CorruptedDocumentError(DocumentParseError):
    """El archivo está vacío, corrupto o protegido por contraseña."""


class ParsedDocument(BaseModel):
    """Resultado estandarizado de la extracción de texto de un documento."""

    file_name: str = Field(..., min_length=1)
    source_format: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    used_ocr_fallback: bool = Field(default=False)
    char_count: int = Field(..., ge=1)


def _useful_char_count(text: str) -> int:
    """Cuenta caracteres visibles excluyendo espacios en blanco."""
    return len(re.sub(r"\s+", "", text))


def _extract_docx_text(path: Path) -> str:
    """Extrae texto de párrafos y tablas de un archivo DOCX."""
    try:
        doc = Document(str(path))
    except Exception as exc:
        raise CorruptedDocumentError(
            f"No se pudo leer el archivo DOCX '{path.name}': {exc}"
        ) from exc

    blocks: list[str] = []
    for paragraph in doc.paragraphs:
        clean = paragraph.text.strip()
        if clean:
            blocks.append(clean)

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                blocks.append(" | ".join(cells))

    return "\n".join(blocks).strip()


def _extract_pdf_text(
    path: Path,
    gemini_client: GeminiClient | None,
    settings: Settings,
) -> tuple[str, bool]:
    """Extrae Markdown de un PDF y activa fallback Vision en Gemini si es escaneado."""
    try:
        doc = pymupdf.open(str(path))
    except Exception as exc:
        raise CorruptedDocumentError(
            f"Archivo PDF corrupto o ilegible '{path.name}': {exc}"
        ) from exc

    try:
        if doc.needs_pass:
            raise CorruptedDocumentError(
                f"El PDF '{path.name}' está protegido con contraseña y no puede leerse."
            )
        if doc.page_count == 0:
            raise CorruptedDocumentError(f"El PDF '{path.name}' no contiene páginas.")

        markdown_text = pymupdf4llm.to_markdown(doc).strip()
    finally:
        doc.close()

    if _useful_char_count(markdown_text) >= MIN_USEFUL_PDF_CHARS:
        return markdown_text, False

    client = gemini_client or GeminiClient(settings=settings)
    pdf_bytes = path.read_bytes()
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
    ocr_text = client.generate_text(
        model=settings.gemini_flash_model,
        system_instruction=OCR_SYSTEM_INSTRUCTION,
        contents=[
            pdf_part,
            "Transcribe íntegramente esta hoja de vida a Markdown limpio respetando columnas.",
        ],
    )
    if _useful_char_count(ocr_text) == 0:
        raise CorruptedDocumentError(
            f"No fue posible extraer texto del PDF '{path.name}' ni mediante OCR multimodal."
        )
    return ocr_text, True


def parse_document(
    file_path: str | Path,
    *,
    gemini_client: GeminiClient | None = None,
    settings: Settings | None = None,
) -> ParsedDocument:
    """Extrae texto limpio de un archivo PDF, DOCX, TXT o MD con validaciones de integridad."""
    cfg = settings or get_settings()
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Extensión '{ext}' no soportada. Formatos válidos: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    size_bytes = path.stat().st_size
    if size_bytes == 0:
        raise CorruptedDocumentError(f"El archivo '{path.name}' está vacío.")

    max_bytes = cfg.max_file_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(
            f"El archivo '{path.name}' ({size_bytes / (1024 * 1024):.2f} MB) "
            f"supera el límite de {cfg.max_file_size_mb} MB."
        )

    used_ocr = False
    if ext in {".txt", ".md"}:
        try:
            text = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1").strip()
    elif ext == ".docx":
        text = _extract_docx_text(path)
    else:
        text, used_ocr = _extract_pdf_text(path, gemini_client=gemini_client, settings=cfg)

    if _useful_char_count(text) == 0:
        raise CorruptedDocumentError(f"El archivo '{path.name}' no contiene texto extraíble.")

    return ParsedDocument(
        file_name=path.name,
        source_format=ext.lstrip("."),
        text=text,
        used_ocr_fallback=used_ocr,
        char_count=len(text),
    )
