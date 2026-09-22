"""OCR fallback for scanned PDFs (spec §4)."""
from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


def ocr_pdf(path: str, max_pages: int = 10, dpi: int = 200) -> str:
    """Best-effort OCR. Returns '' if OCR dependencies are unavailable."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except Exception as exc:  # pragma: no cover
        logger.warning("OCR dependencies unavailable: %s", exc)
        return ""
    try:
        images = convert_from_path(path, dpi=dpi, first_page=1, last_page=max_pages)
    except Exception as exc:  # pragma: no cover - depends on poppler
        logger.warning("pdf2image failed: %s", exc)
        return ""
    parts: list[str] = []
    for img in images:
        try:
            parts.append(pytesseract.image_to_string(img))
        except Exception as exc:  # pragma: no cover
            logger.warning("tesseract failed on a page: %s", exc)
    return "\n".join(parts).strip()
