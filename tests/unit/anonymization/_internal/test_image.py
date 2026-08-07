"""Tests for image OCR coordinate transformations."""

from __future__ import annotations

from source_docs_processor.features.anonymization._internal.image import _map_box_to_original


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

    from source_docs_processor.features.anonymization._internal.config import AnonymizationConfig
    from source_docs_processor.features.anonymization._internal.image import (
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
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
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


def test_raster_redaction_uses_fuzzy_included_ocr_matching(monkeypatch) -> None:
    """Verify one OCR substitution still redacts a configured included word.

    Protected risk: low-quality scans may recognize `Квантовая` as
    `Кванговая`, which must not remain visible when fuzzy OCR matching is enabled.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        ConfiguredTextAnalyzer,
    )
    from source_docs_processor.features.anonymization._internal.image import (
        OcrPage,
        OcrWord,
        redact_pil_image,
    )

    recognized = "Кванговая"
    page = OcrPage(
        text=recognized,
        words=(
            OcrWord(
                text=recognized,
                start=0,
                end=len(recognized),
                left=20,
                top=30,
                width=90,
                height=20,
                confidence=72.0,
            ),
        ),
        rotation_degrees=0,
        original_width=160,
        original_height=100,
    )
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._ocr_page",
        lambda image, lang, angle: page,
    )
    config = AnonymizationConfig(
        included=("Квантовая",),
        included_fuzzy=True,
        included_fuzzy_max_errors=1,
    )
    analyzer = ConfiguredTextAnalyzer(None, config)

    redacted, detected = redact_pil_image(
        Image.new("RGB", (160, 100), "white"),
        analyzer,
        config=config,
    )

    assert detected == 1
    assert redacted.getpixel((60, 40)) == (0, 0, 0)


def test_raster_replacement_covers_source_and_draws_target(monkeypatch) -> None:
    """Verify source-format raster output visibly replaces a configured value.

    Protected risk: replacement rules must not silently degrade to black masks in
    PDF and image output, while the original OCR region must still be covered.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        ConfiguredTextAnalyzer,
        ReplacementRule,
    )
    from source_docs_processor.features.anonymization._internal.image import (
        OcrPage,
        OcrWord,
        redact_pil_image,
    )

    recognized = "Квантовая"
    page = OcrPage(
        text=recognized,
        words=(
            OcrWord(
                text=recognized,
                start=0,
                end=len(recognized),
                left=20,
                top=30,
                width=100,
                height=24,
                confidence=90.0,
            ),
        ),
        rotation_degrees=0,
        original_width=180,
        original_height=100,
    )
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._ocr_page",
        lambda image, lang, angle: page,
    )
    config = AnonymizationConfig(
        included_and_replaced=(ReplacementRule("Квантовая", "цифровая"),),
        included_fuzzy=True,
        included_fuzzy_max_errors=1,
    )

    transformed, detected = redact_pil_image(
        Image.new("RGB", (180, 100), "white"),
        ConfiguredTextAnalyzer(None, config),
        config=config,
    )

    crop = transformed.crop((16, 26, 124, 58)).convert("L")
    minimum, maximum = crop.getextrema()
    assert detected == 1
    assert minimum < 80
    assert maximum > 240


def _make_stacked_passenger_page(label_words: tuple[str, ...], name_words: tuple[str, ...]):
    """Build synthetic OCR lines with a passenger label above its value."""
    from source_docs_processor.features.anonymization._internal.image import OcrPage, OcrWord

    words = []
    text_parts = []
    offset = 0
    for line_number, (values, top) in enumerate(((label_words, 20), (name_words, 55)), start=1):
        left = 20
        for value in values:
            if text_parts:
                text_parts.append(" ")
                offset += 1
            start = offset
            text_parts.append(value)
            offset += len(value)
            width = max(30, len(value) * 9)
            words.append(
                OcrWord(
                    text=value,
                    start=start,
                    end=offset,
                    left=left,
                    top=top,
                    width=width,
                    height=18,
                    confidence=92.0,
                    layout_left=left,
                    layout_top=top,
                    layout_width=width,
                    layout_height=18,
                    block_number=1,
                    paragraph_number=1,
                    line_number=line_number,
                )
            )
            left += width + 10
    return OcrPage(
        text="".join(text_parts),
        words=tuple(words),
        rotation_degrees=0,
        original_width=500,
        original_height=180,
        layout_width=500,
        layout_height=180,
    )


def test_ocr_detects_english_passenger_name_below_label(monkeypatch) -> None:
    """Verify an English passenger name is masked when its label is above it.

    Protected risk: boarding-pass layouts often place `Passenger name` on one
    line and the actual name on the next, which flat-text NER can miss.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import AnonymizationConfig
    from source_docs_processor.features.anonymization._internal.image import _choose_ocr_page

    page = _make_stacked_passenger_page(("Passenger", "name"), ("SMITH/JOHN", "MR"))
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._ocr_page",
        lambda image, lang, angle: page,
    )

    class EmptyAnalyzer:
        """Return no generic entities so the structured OCR rule is isolated."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    _selected, entities = _choose_ocr_page(
        Image.new("RGB", (500, 180), "white"),
        EmptyAnalyzer(),
        "rus+eng",
        AnonymizationConfig(entity_detection_mode="automatic"),
    )

    assert len(entities) == 1
    assert page.text[entities[0].start : entities[0].end] == "SMITH/JOHN MR"


def test_ocr_detects_english_name_below_russian_passenger_label(monkeypatch) -> None:
    """Verify a Russian passenger label can anchor an English passenger name.

    Protected risk: localized boarding passes may label the field in Russian
    while printing the passenger value in Latin characters.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import AnonymizationConfig
    from source_docs_processor.features.anonymization._internal.image import _choose_ocr_page

    page = _make_stacked_passenger_page(("Фамилия", "пассажира"), ("JOHN", "SMITH"))
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._ocr_page",
        lambda image, lang, angle: page,
    )

    class EmptyAnalyzer:
        """Return no generic entities so the structured OCR rule is isolated."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    _selected, entities = _choose_ocr_page(
        Image.new("RGB", (500, 180), "white"),
        EmptyAnalyzer(),
        "rus+eng",
        AnonymizationConfig(entity_detection_mode="combined"),
    )

    assert len(entities) == 1
    assert page.text[entities[0].start : entities[0].end] == "JOHN SMITH"


def test_stacked_passenger_name_rule_is_disabled_in_configured_mode(monkeypatch) -> None:
    """Verify the OCR label rule follows the configured entity-detection mode.

    Protected risk: configured-only anonymization must not silently enable an
    automatic passenger-name heuristic.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import AnonymizationConfig
    from source_docs_processor.features.anonymization._internal.image import _choose_ocr_page

    page = _make_stacked_passenger_page(("Passenger", "name"), ("JOHN", "SMITH"))
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._ocr_page",
        lambda image, lang, angle: page,
    )

    class EmptyAnalyzer:
        """Return no configured entities."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    _selected, entities = _choose_ocr_page(
        Image.new("RGB", (500, 180), "white"),
        EmptyAnalyzer(),
        "rus+eng",
        AnonymizationConfig(entity_detection_mode="configured"),
    )

    assert entities == []
