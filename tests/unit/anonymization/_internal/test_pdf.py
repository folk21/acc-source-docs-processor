"""Tests for rasterized PDF anonymization."""

from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image

from source_docs_processor.features.anonymization._internal import pdf as pdf_module


class EmptyAnalyzer:
    """Provide the analyzer protocol for a patched image redactor."""

    def analyze(self, text: str):
        """Return no text spans."""
        return []


def test_pdf_anonymization_rebuilds_pages_without_text_layer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify output PDFs contain only sanitized page images.

    Protected risk: drawing rectangles over native PDF text can leave the hidden
    text layer searchable and recoverable.
    """
    source = tmp_path / "source.pdf"
    output = tmp_path / "output.pdf"
    document = fitz.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((30, 60), "Ivan Petrov 123456789012")
    document.set_metadata({"author": "Ivan Petrov"})
    document.save(source)
    document.close()

    def fake_redact(image: Image.Image, analyzer, lang: str, **kwargs):
        return Image.new("RGB", image.size, "black"), 1

    monkeypatch.setattr(pdf_module, "redact_pil_image", fake_redact)

    detected = pdf_module.anonymize_pdf_file(source, output, EmptyAnalyzer())

    with fitz.open(output) as anonymized:
        assert detected == 1
        assert anonymized.page_count == 1
        assert anonymized[0].get_text().strip() == ""
        assert anonymized.metadata.get("author", "") == ""
