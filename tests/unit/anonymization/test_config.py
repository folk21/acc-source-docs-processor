"""Tests for anonymization configuration rules."""

from __future__ import annotations

from pathlib import Path

from source_docs_processor.anonymization.config import (
    AnonymizationConfig,
    ConfiguredTextAnalyzer,
    find_heading_text_span,
    load_anonymization_config,
    mask_after_heading,
)
from source_docs_processor.anonymization.models import DetectedEntity
from source_docs_processor.anonymization.text import mask_text


class WholeTextAnalyzer:
    """Detect the complete text for deterministic exclusion tests."""

    def analyze(self, text: str) -> list[DetectedEntity]:
        """Return one entity covering all text."""
        return [DetectedEntity(0, len(text), "TEST")]


class ExplodingAnalyzer:
    """Fail when included-only mode unexpectedly calls the default analyzer."""

    def analyze(self, text: str) -> list[DetectedEntity]:
        """Raise because the default analyzer must be bypassed."""
        raise AssertionError("The default analyzer must not run in included-only mode")


def test_config_loader_reads_comma_separated_and_multiline_rules(
    tmp_path: Path,
) -> None:
    """Verify the INI format accepts literal and section rule lists.

    Protected risk: configuration parsing must preserve Russian literal values,
    including multiword entries, while ignoring empty list entries.
    """
    path = tmp_path / "anonymization.ini"
    path.write_text(
        "[anonymization]\n"
        "excluded = стороны, сторона\n"
        "included =\n"
        "    Иван Петров\n"
        "    Учебная корпорация развития области\n"
        "includedParagraphs = 9. Реквизиты и подписи сторон\n",
        encoding="utf-8",
    )

    config = load_anonymization_config(path)

    assert config.excluded == ("стороны", "сторона")
    assert config.included == (
        "Иван Петров",
        "Учебная корпорация развития области",
    )
    assert config.included_paragraphs == ("9. Реквизиты и подписи сторон",)
    assert config.included_only is True


def test_included_only_mode_ignores_default_analyzer_and_exclusions() -> None:
    """Verify a non-empty included list becomes the only literal redaction source.

    Protected risk: Presidio or an excluded rule must not redact or preserve text
    outside the explicit allowlist-style anonymization mode.
    """
    text = "стороны Иван Петров остаются видимыми"
    analyzer = ConfiguredTextAnalyzer(
        ExplodingAnalyzer(),
        AnonymizationConfig(
            excluded=("Иван Петров", "стороны"),
            included=("Иван Петров",),
        ),
    )

    masked, entities = mask_text(text, analyzer)

    assert masked.startswith("стороны ")
    assert "Иван Петров" not in masked
    assert masked.endswith(" остаются видимыми")
    assert len(entities) == 1


def test_included_literal_matches_across_whitespace_changes() -> None:
    """Verify a multiword include matches text split across lines.

    Protected risk: PDF OCR and electronic documents may insert line breaks
    inside one configured organization name.
    """
    text = "Учебная корпорация развития\nНижегородской области"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included=("Учебная корпорация развития Нижегородской области",),
        ),
    )

    masked, entities = mask_text(text, analyzer)

    assert "корпорация" not in masked
    assert "области" not in masked
    assert "\n" in masked
    assert len(entities) == 1


def test_empty_included_list_uses_default_analyzer_and_exclusions() -> None:
    """Verify exclusions still refine default detection outside included-only mode.

    Protected risk: an empty included list must retain the original automatic
    Presidio workflow and its false-positive exclusions.
    """
    text = "стороны Иван Петров"
    analyzer = ConfiguredTextAnalyzer(
        WholeTextAnalyzer(),
        AnonymizationConfig(excluded=("стороны",)),
    )

    masked, _entities = mask_text(text, analyzer)

    assert masked.startswith("стороны ")
    assert "Иван" not in masked


def test_included_paragraph_masks_everything_after_heading() -> None:
    """Verify configured section headings redact all following text.

    Protected risk: stamps and requisites below a known section heading may not
    be recognized as individual PII entities.
    """
    text = "Введение\n9. Реквизиты и подписи сторон\nПечать и подпись"
    heading = ("9. Реквизиты и подписи сторон",)

    span = find_heading_text_span(text, heading)
    masked, found = mask_after_heading(text, text, heading)

    assert span is not None
    assert found is True
    assert "9. Реквизиты и подписи сторон" in masked
    assert "Печать" not in masked
