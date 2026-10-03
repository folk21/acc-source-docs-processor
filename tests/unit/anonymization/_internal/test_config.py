"""Tests for anonymization configuration rules."""

from __future__ import annotations

from pathlib import Path

import pytest

from source_docs_processor.features.anonymization._internal.config import (
    AnonymizationConfig,
    ConfiguredTextAnalyzer,
    LineRangeRedactionRule,
    LineRedactionRule,
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
        "includedParagraphs = 9. Реквизиты и подписи сторон\n"
        "redactLines =\n"
        "    page:1,direction:bottom,lines:3\n"
        "    page:2, direction:top, lines:2\n"
        "redactLineRanges =\n"
        '    page:2,start:"Section start",end:"Section end, signed"\n'
        '    page:3,start:"Footer start"\n',
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
    assert config.redact_lines == (
        LineRedactionRule(page=1, direction="bottom", lines=3),
        LineRedactionRule(page=2, direction="top", lines=2),
    )
    assert config.redact_line_ranges == (
        LineRangeRedactionRule(
            page=2,
            start="Section start",
            end="Section end, signed",
        ),
        LineRangeRedactionRule(page=3, start="Footer start"),
    )
    assert config.included_fuzzy is True
    assert config.included_fuzzy_max_errors == 1
    assert config.included_only is True
    assert config.resolved_entity_detection_mode == "configured"


@pytest.mark.parametrize(
    ("rule", "message"),
    (
        ("page:0,direction:bottom,lines:3", "page must be >= 1"),
        ("page:1,direction:middle,lines:3", "direction must be 'top' or 'bottom'"),
        ("page:1,direction:top,lines:0", "lines must be >= 1"),
        ("page:one,direction:top,lines:2", "page and lines values must be integers"),
        ("page:1,direction:top", "missing required key"),
        ("page:1,direction:top,lines:2,padding:4", "unknown key"),
    ),
)
def test_config_rejects_invalid_line_redaction_rules(
    tmp_path: Path,
    rule: str,
    message: str,
) -> None:
    """Verify malformed page-line rules fail instead of weakening redaction.

    Protected risk: a typo in a structural redaction rule must not be silently
    ignored because the user may rely on it to remove a known page footer.
    """
    path = tmp_path / "anonymization.ini"
    path.write_text(
        "[anonymization]\n"
        "redactLines =\n"
        f"    {rule}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_anonymization_config(path)




@pytest.mark.parametrize(
    ("rule", "message"),
    (
        ('page:0,start:"Begin"', "page must be >= 1"),
        ('page:1,end:"Finish"', "missing required key"),
        ('page:one,start:"Begin"', "page must be an integer"),
        ('page:1,start:"Begin",extra:value', "unknown key"),
        ('page:1,start:""', "keys and values must be non-empty"),
        ('page:1,start:"Begin",end:""', "keys and values must be non-empty"),
        ('page:1,start:"Begin', "invalid quoting"),
    ),
)
def test_config_rejects_invalid_line_range_redaction_rules(
    tmp_path: Path,
    rule: str,
    message: str,
) -> None:
    """Verify malformed anchored line ranges fail instead of weakening redaction.

    Protected risk: a typo in a structural range must not silently leave the
    configured page section visible.
    """
    path = tmp_path / "anonymization.ini"
    path.write_text(
        "[anonymization]\n"
        "redactLineRanges =\n"
        f"    {rule}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_anonymization_config(path)


def test_line_range_rule_normalizes_public_fragments() -> None:
    """Verify direct public construction trims anchored line-range fragments.

    Protected risk: embedded callers and INI users must receive equivalent
    matching semantics for leading and trailing whitespace.
    """
    rule = LineRangeRedactionRule(
        page=2,
        start="  Section start  ",
        end="  Section end  ",
    )

    assert rule.start == "Section start"
    assert rule.end == "Section end"


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


def test_line_redaction_rule_normalizes_direction_for_public_construction() -> None:
    """Verify direct public rule construction keeps the same validated contract.

    Protected risk: embedded callers must not bypass INI validation and create a
    direction that is later misinterpreted as a different page edge.
    """
    rule = LineRedactionRule(page=1, direction=" Bottom ", lines=2)

    assert rule.direction == "bottom"


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


def test_ocr_replacement_matches_email_split_by_punctuation_without_fuzzy() -> None:
    """Verify OCR punctuation segmentation does not break explicit email replacement.

    Protected risk: Tesseract may emit spaces around `@` or `.` even when the
    configured email is visually continuous, leaving a known private value visible.
    """
    source = "J.PETROVA@GM.SU"
    recognized = "J . PETROVA @ GM . SU"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included_and_replaced=(
                ReplacementRule(source, "J.IVANOVA@GM.SU"),
            ),
            included_fuzzy=False,
        ),
    )

    assert analyzer.analyze(recognized) == []
    entities = analyzer.analyze_ocr(recognized)

    assert len(entities) == 1
    assert entities[0].start == 0
    assert entities[0].end == len(recognized)
    assert entities[0].replacement == "J.IVANOVA@GM.SU"


def test_ocr_replacement_matches_uuid_with_spaced_unicode_dashes_without_fuzzy() -> None:
    """Verify OCR dash normalization preserves explicit identifier replacement.

    Protected risk: OCR can separate identifier groups with whitespace or Unicode
    dashes, so literal matching alone can miss a configured pseudonym mapping.
    """
    source = "9bfd1944-2a25-4864-bd33"
    recognized = "9bfd1944 – 2a25 – 4864 – bd33"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included_and_replaced=(
                ReplacementRule(source, "00000000-0000-0000-0000"),
            ),
            included_fuzzy=False,
        ),
    )

    entities = analyzer.analyze_ocr(recognized)

    assert len(entities) == 1
    assert entities[0].start == 0
    assert entities[0].end == len(recognized)
    assert entities[0].replacement == "00000000-0000-0000-0000"


def test_ocr_replacement_preserves_prefixed_number_mapping_without_masking() -> None:
    """Verify exact and normalized OCR matching do not duplicate one mapping.

    Protected risk: a configured value beginning with punctuation such as `№`
    previously produced one literal span and one shorter token-normalized span.
    The generic overlap merger then discarded the replacement and masked the
    value instead of writing the configured pseudonym.
    """
    from source_docs_processor.features.anonymization._internal.text import (
        merge_entities,
        transform_entities,
    )

    source = "№40817810355860000000"
    replacement = "№11111111111111111111"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            entity_detection_mode="configured",
            included_and_replaced=(ReplacementRule(source, replacement),),
            included_fuzzy=False,
        ),
    )

    entities = merge_entities(analyzer.analyze_ocr(source), len(source))

    assert len(entities) == 1
    assert entities[0].start == 0
    assert entities[0].end == len(source)
    assert entities[0].replacement == replacement
    assert transform_entities(source, entities) == replacement


def test_ocr_replacement_matches_number_split_inside_identifier_without_fuzzy() -> None:
    """Verify OCR-only token boundaries inside a long number do not expose it.

    Protected risk: Tesseract may split one visually continuous long identifier
    into several words, while configured-only anonymization must still apply the
    exact mapping without enabling character-error fuzzy matching.
    """
    source = "№40817810655190000001"
    recognized = "№ 4081781065519 0000001"
    replacement = "№22222222222222222222"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            entity_detection_mode="configured",
            included_and_replaced=(ReplacementRule(source, replacement),),
            included_fuzzy=False,
        ),
    )

    entities = analyzer.analyze_ocr(recognized)

    assert len(entities) == 1
    assert entities[0].start == 0
    assert entities[0].end == len(recognized)
    assert entities[0].replacement == replacement


def test_ocr_longest_overlapping_replacement_wins_without_masking() -> None:
    """Verify a full configured email mapping wins over an embedded mapping.

    Protected risk: overlapping configured replacements previously reached the
    generic overlap merger, which intentionally converts ambiguous overlaps to a
    mask. A specific full-value mapping must instead remain a replacement.
    """
    from source_docs_processor.features.anonymization._internal.text import (
        merge_entities,
        transform_entities,
    )

    text = "J.PETROVA@SSSASTER.SU PETROVA"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            entity_detection_mode="configured",
            included_and_replaced=(
                ReplacementRule("PETROVA", "IVANOVA"),
                ReplacementRule("J.PETROVA@SSSASTER.SU", "XXX@MMM.SU"),
            ),
            included_fuzzy=False,
        ),
    )

    entities = merge_entities(analyzer.analyze_ocr(text), len(text))

    assert len(entities) == 2
    assert all(entity.replacement is not None for entity in entities)
    assert transform_entities(text, entities) == "XXX@MMM.SU IVANOVA"


def test_ocr_replacement_takes_priority_over_overlapping_included_mask() -> None:
    """Verify an explicit replacement is not downgraded by an included substring.

    Protected risk: configured mode may contain both mask and replacement rules;
    a shorter included value inside a mapped identifier must not turn the mapped
    identifier into a black rectangle.
    """
    from source_docs_processor.features.anonymization._internal.text import (
        merge_entities,
        transform_entities,
    )

    text = "J.PETROVA@SSSASTER.SU"
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            entity_detection_mode="configured",
            included=("PETROVA",),
            included_and_replaced=(
                ReplacementRule("J.PETROVA@SSSASTER.SU", "XXX@MMM.SU"),
            ),
            included_fuzzy=False,
        ),
    )

    entities = merge_entities(analyzer.analyze_ocr(text), len(text))

    assert len(entities) == 1
    assert entities[0].replacement == "XXX@MMM.SU"
    assert transform_entities(text, entities) == "XXX@MMM.SU"


def test_ocr_normalized_replacement_does_not_accept_character_error_without_fuzzy() -> None:
    """Verify normalized OCR matching does not become implicit fuzzy matching.

    Protected risk: punctuation tolerance must not make unrelated identifiers match
    when the user intentionally keeps `includedFuzzy` disabled.
    """
    analyzer = ConfiguredTextAnalyzer(
        None,
        AnonymizationConfig(
            included_and_replaced=(
                ReplacementRule("J.PETROVA@GM.SU", "J.IVANOVA@GM.SU"),
            ),
            included_fuzzy=False,
        ),
    )

    assert analyzer.analyze_ocr("J . PETROWA @ GM . SU") == []


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
