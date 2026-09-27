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


def _make_line_redaction_page(
    *,
    rotation_degrees: int = 0,
) -> "OcrPage":
    """Build five deterministic OCR lines for structural-redaction tests."""
    from source_docs_processor.features.anonymization._internal.image import OcrPage, OcrWord

    words = []
    text_parts = []
    offset = 0
    for line_number in range(1, 6):
        value = f"Line{line_number}"
        if text_parts:
            text_parts.append(" ")
            offset += 1
        start = offset
        text_parts.append(value)
        offset += len(value)
        layout_top = 10 + (line_number - 1) * 20
        if rotation_degrees == 90:
            left = 10 + (line_number - 1) * 20
            top = 15
            width = 12
            height = 50
        else:
            left = 20
            top = layout_top
            width = 80
            height = 12
        words.append(
            OcrWord(
                text=value,
                start=start,
                end=offset,
                left=left,
                top=top,
                width=width,
                height=height,
                confidence=95.0,
                layout_left=20,
                layout_top=layout_top,
                layout_width=80,
                layout_height=12,
                block_number=1,
                paragraph_number=1,
                line_number=line_number,
            )
        )
    return OcrPage(
        text="".join(text_parts),
        words=tuple(words),
        rotation_degrees=rotation_degrees,
        original_width=140,
        original_height=120,
        layout_width=140,
        layout_height=120,
    )


def test_configured_bottom_lines_redact_exact_ocr_lines_when_detection_disabled(
    monkeypatch,
) -> None:
    """Verify bottom line rules remain active when entity detection is disabled.

    Protected risk: structural page redaction is an explicit user instruction and
    must not depend on Presidio/configured entity-source selection.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page()
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the structural-only regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    config = AnonymizationConfig(
        entity_detection_mode="disabled",
        redact_lines=(LineRedactionRule(page=1, direction="bottom", lines=2),),
    )
    redacted, detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=config,
        page_number=1,
        padding=0,
    )

    assert detected == 2
    assert redacted.getpixel((40, 55)) == (255, 255, 255)
    assert redacted.getpixel((40, 75)) == (0, 0, 0)
    assert redacted.getpixel((40, 95)) == (0, 0, 0)


def test_line_redaction_respects_page_number_and_caps_at_available_lines(
    monkeypatch,
) -> None:
    """Verify page selectors are 1-based and oversized counts redact available lines.

    Protected risk: a rule for another page must not affect the current page,
    while requesting more lines than exist must remain deterministic and safe.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page()
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the structural-only regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    config = AnonymizationConfig(
        entity_detection_mode="disabled",
        redact_lines=(LineRedactionRule(page=2, direction="top", lines=20),),
    )
    first, first_detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=config,
        page_number=1,
        padding=0,
    )
    second, second_detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=config,
        page_number=2,
        padding=0,
    )

    assert first_detected == 0
    assert first.getpixel((40, 15)) == (255, 255, 255)
    assert second_detected == 5
    assert second.getpixel((40, 15)) == (0, 0, 0)
    assert second.getpixel((40, 95)) == (0, 0, 0)


def test_rotated_page_selects_bottom_line_in_upright_layout(monkeypatch) -> None:
    """Verify top/bottom selection follows upright OCR coordinates after rotation.

    Protected risk: a sideways source must redact the visual bottom line selected
    after OCR orientation correction, then map that line back to source pixels.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page(rotation_degrees=90)
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the rotation regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    config = AnonymizationConfig(
        entity_detection_mode="disabled",
        redact_lines=(LineRedactionRule(page=1, direction="bottom", lines=1),),
    )
    redacted, detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=config,
        page_number=1,
        padding=0,
    )

    assert detected == 1
    assert redacted.getpixel((15, 30)) == (255, 255, 255)
    assert redacted.getpixel((95, 30)) == (0, 0, 0)


def test_line_range_redaction_masks_inclusive_anchor_lines_when_detection_disabled(
    monkeypatch,
) -> None:
    """Verify anchored ranges mask every OCR line from start through end.

    Protected risk: a configured structural range must include both anchor lines
    and remain active when entity detection itself is disabled.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRangeRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page()
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the structural-only regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    config = AnonymizationConfig(
        entity_detection_mode="disabled",
        redact_line_ranges=(
            LineRangeRedactionRule(page=1, start="line2", end="LINE4"),
        ),
    )
    redacted, detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=config,
        page_number=1,
        padding=0,
    )

    assert detected == 3
    assert redacted.getpixel((40, 15)) == (255, 255, 255)
    assert redacted.getpixel((40, 35)) == (0, 0, 0)
    assert redacted.getpixel((40, 55)) == (0, 0, 0)
    assert redacted.getpixel((40, 75)) == (0, 0, 0)
    assert redacted.getpixel((40, 95)) == (255, 255, 255)


def test_line_range_without_end_redacts_remaining_lines(monkeypatch) -> None:
    """Verify omitting the end fragment masks from start through page end.

    Protected risk: the documented open-ended form must not stop after only the
    anchor line or require an artificial second marker.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRangeRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page()
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the open-ended range regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    config = AnonymizationConfig(
        entity_detection_mode="disabled",
        redact_line_ranges=(LineRangeRedactionRule(page=1, start="Line3"),),
    )
    redacted, detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=config,
        page_number=1,
        padding=0,
    )

    assert detected == 3
    assert redacted.getpixel((40, 35)) == (255, 255, 255)
    assert redacted.getpixel((40, 55)) == (0, 0, 0)
    assert redacted.getpixel((40, 95)) == (0, 0, 0)


def test_line_range_requires_explicit_anchors_to_match(monkeypatch) -> None:
    """Verify missing configured anchors fail closed instead of weakening masking.

    Protected risk: OCR drift in an explicit structural rule must not silently
    produce a partially anonymized output that the user assumes was redacted.
    """
    from PIL import Image
    import pytest

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRangeRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page()
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the fail-closed anchor regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    image = Image.new("RGB", (140, 120), "white")
    with pytest.raises(ValueError, match="start fragment was not found on page 1"):
        redact_pil_image(
            image,
            EmptyAnalyzer(),
            config=AnonymizationConfig(
                entity_detection_mode="disabled",
                redact_line_ranges=(
                    LineRangeRedactionRule(page=1, start="Missing"),
                ),
            ),
            page_number=1,
        )

    with pytest.raises(ValueError, match="end fragment was not found after start"):
        redact_pil_image(
            image,
            EmptyAnalyzer(),
            config=AnonymizationConfig(
                entity_detection_mode="disabled",
                redact_line_ranges=(
                    LineRangeRedactionRule(
                        page=1,
                        start="Line2",
                        end="Missing",
                    ),
                ),
            ),
            page_number=1,
        )


def test_rotated_page_line_range_uses_upright_line_order(monkeypatch) -> None:
    """Verify anchored ranges use upright OCR lines before mapping back to pixels.

    Protected risk: a sideways scan must redact the intended visual range rather
    than a source-coordinate range from the wrong page orientation.
    """
    from PIL import Image

    from source_docs_processor.features.anonymization._internal.config import (
        AnonymizationConfig,
        LineRangeRedactionRule,
    )
    from source_docs_processor.features.anonymization._internal.image import redact_pil_image

    page = _make_line_redaction_page(rotation_degrees=90)
    monkeypatch.setattr(
        "source_docs_processor.features.anonymization._internal.image._choose_ocr_page",
        lambda image, analyzer, lang, config: (page, []),
    )

    class EmptyAnalyzer:
        """Return no entities for the rotation regression."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    redacted, detected = redact_pil_image(
        Image.new("RGB", (140, 120), "white"),
        EmptyAnalyzer(),
        config=AnonymizationConfig(
            entity_detection_mode="disabled",
            redact_line_ranges=(LineRangeRedactionRule(page=1, start="Line4"),),
        ),
        page_number=1,
        padding=0,
    )

    assert detected == 2
    assert redacted.getpixel((55, 30)) == (255, 255, 255)
    assert redacted.getpixel((75, 30)) == (0, 0, 0)
    assert redacted.getpixel((95, 30)) == (0, 0, 0)


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
