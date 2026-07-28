"""Tests for image OCR coordinate transformations."""

from __future__ import annotations

from source_docs_processor.anonymization.image import _map_box_to_original


def test_clockwise_rotation_box_maps_back_to_original_coordinates() -> None:
    """Verify redaction boxes found on a rotated scan cover the original pixels.

    Protected risk: OCR may select a 90-degree orientation while the output file
    remains in its original orientation.
    """
    mapped = _map_box_to_original(
        left=70,
        top=20,
        width=15,
        height=30,
        angle=90,
        original_width=200,
        original_height=100,
    )

    assert mapped == (20, 15, 30, 15)


def test_configured_heading_redacts_page_remainder_and_later_pages(monkeypatch) -> None:
    """Verify a configured section heading covers stamps below it and later pages.

    Protected risk: OCR-based entity detection alone cannot identify private data
    embedded inside a stamp or signature image.
    """
    from PIL import Image

    from source_docs_processor.anonymization.config import AnonymizationConfig
    from source_docs_processor.anonymization.image import (
        OcrPage,
        OcrWord,
        ParagraphRedactionState,
        redact_pil_image,
    )

    words = tuple(
        OcrWord(
            text=value,
            start=index,
            end=index + len(value),
            left=10 + index * 20,
            top=30,
            width=18,
            height=10,
            confidence=90.0,
        )
        for index, value in enumerate(
            ["9.", "Реквизиты", "и", "подписи", "сторон"]
        )
    )
    page = OcrPage(
        text="9. Реквизиты и подписи сторон",
        words=words,
        rotation_degrees=0,
        original_width=200,
        original_height=120,
    )

    monkeypatch.setattr(
        "source_docs_processor.anonymization.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no default entities."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    state = ParagraphRedactionState()
    config = AnonymizationConfig(
        included_paragraphs=("9. Реквизиты и подписи сторон",)
    )
    source = Image.new("RGB", (200, 120), "white")

    first, detected = redact_pil_image(
        source,
        EmptyAnalyzer(),
        config=config,
        paragraph_state=state,
    )
    second, second_detected = redact_pil_image(
        source,
        EmptyAnalyzer(),
        config=config,
        paragraph_state=state,
    )

    assert detected == 1
    assert first.getpixel((100, 100)) == (0, 0, 0)
    assert first.getpixel((100, 20)) == (255, 255, 255)
    assert second_detected == 0
    assert second.getbbox() is None
