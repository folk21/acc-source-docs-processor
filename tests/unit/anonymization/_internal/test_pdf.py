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


def test_pdf_anonymization_passes_one_based_page_numbers_to_structural_redaction(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify PDF page-line rules receive stable 1-based page indices.

    Protected risk: configured page selectors must not shift by one when PyMuPDF
    iterates its internally zero-based page collection.
    """
    source = tmp_path / "source.pdf"
    output = tmp_path / "output.pdf"
    document = fitz.open()
    document.new_page(width=200, height=120)
    document.new_page(width=200, height=120)
    document.save(source)
    document.close()
    page_numbers: list[int | None] = []

    def fake_redact(image: Image.Image, analyzer, lang: str, **kwargs):
        page_numbers.append(kwargs.get("page_number"))
        return image.copy(), 0

    monkeypatch.setattr(pdf_module, "redact_pil_image", fake_redact)

    pdf_module.anonymize_pdf_file(source, output, EmptyAnalyzer())

    assert page_numbers == [1, 2]
