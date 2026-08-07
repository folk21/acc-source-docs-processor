"""Tests for anonymization configuration rules."""

from __future__ import annotations

from pathlib import Path

from source_docs_processor.features.anonymization._internal.config import (
    AnonymizationConfig,
    ConfiguredTextAnalyzer,
    ReplacementRule,
    find_heading_text_span,
    load_anonymization_config,
    mask_after_heading,
)
from source_docs_processor.features.anonymization._internal.models import DetectedEntity
from source_docs_processor.features.anonymization._internal.text import mask_text


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


class PreparedAnalyzer:
    """Return one prepared entity for detection-mode composition tests."""

    def __init__(self, entity: DetectedEntity) -> None:
        self._entity = entity

    def analyze(self, text: str) -> list[DetectedEntity]:
        """Return the prepared entity without external NLP dependencies."""
        return [self._entity]


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
        "includedAndReplaced =\n"
        "    Васильев -> Иванов\n"
        "    Учебная долина -> Учебная планета\n"
        "includedFuzzy = true\n"
        "includedFuzzyMaxErrors = 1\n"
        "includedParagraphs = 9. Реквизиты и подписи сторон\n",
        encoding="utf-8",
    )

    config = load_anonymization_config(path)

    assert config.excluded == ("стороны", "сторона")
    assert config.included == (
        "Иван Петров",
        "Учебная корпорация развития области",
    )
    assert config.included_and_replaced == (
        ReplacementRule("Васильев", "Иванов"),
        ReplacementRule("Учебная долина", "Учебная планета"),
    )
    assert config.included_paragraphs == ("9. Реквизиты и подписи сторон",)
    assert config.included_fuzzy is True
    assert config.included_fuzzy_max_errors == 1
    assert config.included_only is True
    assert config.resolved_entity_detection_mode == "configured"


def test_config_loader_reads_explicit_entity_detection_mode(tmp_path: Path) -> None:
    """Verify the INI file accepts all documented entity-detection modes.

    Protected risk: mode selection must remain configuration-driven so CLI and
    UI runs use the same anonymization behavior.
    """
    for mode in ("automatic", "configured", "combined", "disabled"):
        path = tmp_path / f"{mode}.ini"
        path.write_text(
            "[anonymization]\n"
            f"entityDetectionMode = {mode}\n"
            "included = Иван Петров\n",
            encoding="utf-8",
        )

        config = load_anonymization_config(path)

        assert config.entity_detection_mode == mode
        assert config.resolved_entity_detection_mode == mode


def test_config_rejects_unknown_entity_detection_mode(tmp_path: Path) -> None:
    """Verify unknown detection modes fail instead of silently changing privacy.

    Protected risk: a typo in a privacy-sensitive mode must not fall back to a
    weaker or unexpected analyzer selection.
    """
    path = tmp_path / "anonymization.ini"
    path.write_text(
        "[anonymization]\nentityDetectionMode = mappingOnly\n",
        encoding="utf-8",
    )

    try:
        load_anonymization_config(path)
    except ValueError as exc:
        assert "entityDetectionMode" in str(exc)
        assert "combined" in str(exc)
    else:
        raise AssertionError("Expected invalid entity detection mode to fail")


def test_automatic_mode_ignores_configured_rules() -> None:
    """Verify automatic mode uses only default detections and exclusions.

    Protected risk: selecting automatic mode must not unexpectedly apply stale
    literal mappings that remain in a shared configuration file.
    """
    text = "Иван Петров и Учебная компания"
    company_start = text.index("Учебная компания")
    analyzer = ConfiguredTextAnalyzer(
        PreparedAnalyzer(
            DetectedEntity(
                company_start,
                company_start + len("Учебная компания"),
                "ORGANIZATION",
            )
        ),
        AnonymizationConfig(
            entity_detection_mode="automatic",
            included=("Иван Петров",),
        ),
    )

    masked, entities = mask_text(text, analyzer)

    assert masked.startswith("Иван Петров и ")
    assert "Учебная компания" not in masked
    assert len(entities) == 1


def test_combined_mode_preserves_replacement_and_masks_remaining_entity() -> None:
    """Verify configured replacement wins inside a broader automatic entity.

    Protected risk: a PERSON span covering a configured surname plus an unknown
    name must preserve the pseudonym while masking the remaining detected PII.
    """
    text = "Петров Петр"
    analyzer = ConfiguredTextAnalyzer(
        PreparedAnalyzer(DetectedEntity(0, len(text), "PERSON")),
        AnonymizationConfig(
            entity_detection_mode="combined",
            included_and_replaced=(ReplacementRule("Петров", "Иванов"),),
        ),
    )

    transformed, entities = mask_text(text, analyzer)

    assert transformed == "Иванов ████"
    assert len(entities) == 2
    assert any(entity.replacement == "Иванов" for entity in entities)


def test_combined_mode_excluded_does_not_cancel_configured_replacement() -> None:
    """Verify exclusions affect automatic detections but not configured rules.

    Protected risk: reusing one literal in excluded and includedAndReplaced must
    not expose the original value or suppress its explicit pseudonym mapping.
    """
    text = "Петров Петр"
    analyzer = ConfiguredTextAnalyzer(
        PreparedAnalyzer(DetectedEntity(0, len(text), "PERSON")),
        AnonymizationConfig(
            entity_detection_mode="combined",
            excluded=("Петров",),
            included_and_replaced=(ReplacementRule("Петров", "Иванов"),),
        ),
    )

    transformed, entities = mask_text(text, analyzer)

    assert transformed == "Иванов ████"
    assert any(entity.replacement == "Иванов" for entity in entities)


def test_disabled_mode_ignores_automatic_and_configured_entity_rules() -> None:
    """Verify disabled mode leaves entity text untouched.

    Protected risk: the disabled mode must be explicit and deterministic while
    remaining independent from structural includedParagraphs redaction.
    """
    text = "Иван Петров"
    analyzer = ConfiguredTextAnalyzer(
        ExplodingAnalyzer(),
        AnonymizationConfig(
            entity_detection_mode="disabled",
            included=(text,),
        ),
    )

    transformed, entities = mask_text(text, analyzer)

    assert transformed == text
    assert entities == []


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


def test_ocr_fuzzy_included_matches_one_recognition_error_only_for_ocr() -> None:
    """Verify fuzzy included matching repairs one OCR error without changing text rules.

    Protected risk: a low-quality scan may recognize `Квантовая` as
    `Кванговая`, while native TXT and DOCX content must remain exact.
    """
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included=("Квантовая",),
            included_fuzzy=True,
            included_fuzzy_max_errors=1,
        ),
    )

    assert analyzer.analyze("Кванговая") == []
    ocr_entities = analyzer.analyze_ocr("Кванговая")

    assert len(ocr_entities) == 1
    assert ocr_entities[0].start == 0
    assert ocr_entities[0].end == len("Кванговая")


def test_ocr_fuzzy_included_normalizes_latin_cyrillic_lookalikes() -> None:
    """Verify OCR matching tolerates visually identical Latin characters.

    Protected risk: Tesseract may emit a Latin `K` inside an otherwise Russian
    word and exact matching would leave the configured value visible.
    """
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included=("Квантовая",),
            included_fuzzy=True,
            included_fuzzy_max_errors=1,
        ),
    )

    entities = analyzer.analyze_ocr("Kвантовая")

    assert len(entities) == 1


def test_config_rejects_excessive_fuzzy_error_limit(tmp_path: Path) -> None:
    """Verify unsafe broad fuzzy limits are rejected during configuration loading.

    Protected risk: a large edit-distance allowance could redact unrelated OCR
    words and make the output unusable.
    """
    path = tmp_path / "anonymization.ini"
    path.write_text(
        "[anonymization]\n"
        "included = Квантовая\n"
        "includedFuzzy = true\n"
        "includedFuzzyMaxErrors = 4\n",
        encoding="utf-8",
    )

    try:
        load_anonymization_config(path)
    except ValueError as exc:
        assert "between 0 and 3" in str(exc)
    else:
        raise AssertionError("Expected invalid fuzzy error limit to fail")


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



def test_replacement_rule_takes_priority_over_matching_included_literal() -> None:
    """Verify replacement wins when the same source is also listed in included.

    Protected risk: retaining the earlier included list must not turn a requested
    pseudonym replacement back into an opaque block mask.
    """
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included=("Учебная долина",),
            included_and_replaced=(
                ReplacementRule("Учебная долина", "Учебная планета"),
            ),
        ),
    )

    transformed, entities = mask_text("Проект Учебная долина", analyzer)

    assert transformed == "Проект Учебная планета"
    assert len(entities) == 1
    assert entities[0].replacement == "Учебная планета"


def test_fuzzy_ocr_replacement_uses_configured_target() -> None:
    """Verify OCR errors in replacement sources still produce the target value.

    Protected risk: a fuzzy match must not merely detect the source and then mask
    it; the configured pseudonym must be retained in editable and raster output.
    """
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included_and_replaced=(ReplacementRule("Квантовая", "цифровая"),),
            included_fuzzy=True,
            included_fuzzy_max_errors=1,
        ),
    )

    assert analyzer.analyze("Кванговая") == []
    entities = analyzer.analyze_ocr("Кванговая")

    assert len(entities) == 1
    assert entities[0].replacement == "цифровая"


def test_config_rejects_invalid_replacement_rule(tmp_path: Path) -> None:
    """Verify malformed replacement rules fail during configuration loading.

    Protected risk: silently treating a malformed line as an included literal
    could leave the intended private value unchanged.
    """
    path = tmp_path / "anonymization.ini"
    path.write_text(
        "[anonymization]\n"
        "includedAndReplaced = Васильев Иванов\n",
        encoding="utf-8",
    )

    try:
        load_anonymization_config(path)
    except ValueError as exc:
        assert "source -> replacement" in str(exc)
    else:
        raise AssertionError("Expected invalid replacement syntax to fail")
