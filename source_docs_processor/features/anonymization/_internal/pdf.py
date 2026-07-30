"""Rasterized PDF anonymization which removes hidden text and metadata."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

from .config import AnonymizationConfig, EMPTY_ANONYMIZATION_CONFIG
from .image import ParagraphRedactionState, redact_pil_image
from .models import TextEntityAnalyzer, UnitProgressCallback


PDF_RENDER_DPI = 220


def _pixmap_to_image(pixmap: fitz.Pixmap) -> Image.Image:
    """Convert a PyMuPDF pixmap to a detached Pillow RGB image."""
    mode = "RGBA" if pixmap.alpha else "RGB"
    image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
    return image.convert("RGB")


def anonymize_pdf_file(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    dpi: int = PDF_RENDER_DPI,
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
    progress_callback: UnitProgressCallback | None = None,
) -> int:
    """Render, redact, and rebuild a PDF without source text layers or metadata."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = fitz.open()
    detected = 0
    paragraph_state = ParagraphRedactionState()
    try:
        with fitz.open(source) as document:
            if document.needs_pass:
                raise ValueError("Password-protected PDF files are not supported")
            matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
            page_count = document.page_count
            for page_index, page in enumerate(document, start=1):
                if progress_callback is not None:
                    progress_callback("page", page_index, page_count)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image = _pixmap_to_image(pixmap)
                redacted, page_detected = redact_pil_image(
                    image,
                    analyzer=analyzer,
                    lang=lang,
                    config=config,
                    paragraph_state=paragraph_state,
                )
                detected += page_detected
                buffer = BytesIO()
                redacted.save(buffer, format="PNG", optimize=True)
                output_page = output.new_page(
                    width=page.rect.width,
                    height=page.rect.height,
                )
                output_page.insert_image(output_page.rect, stream=buffer.getvalue())

        output.set_metadata({})
        output.save(
            destination,
            garbage=4,
            deflate=True,
            clean=True,
        )
    finally:
        output.close()
    return detected
