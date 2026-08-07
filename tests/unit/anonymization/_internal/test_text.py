"""Tests for format-preserving PII span masking."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from types import ModuleType

import pytest

from source_docs_processor.features.anonymization._internal.models import DetectedEntity
from source_docs_processor.features.anonymization._internal.text import (
    _INTERNATIONAL_PHONE_PATTERN,
    PresidioTextAnalyzer,
    create_presidio_analyzer,
    mask_text,
    merge_entities,
)


class FakeAnalyzer:
    """Return prepared entities for deterministic masking tests."""

    def __init__(self, entities: list[DetectedEntity]) -> None:
        self.entities = entities

    def analyze(self, text: str) -> list[DetectedEntity]:
        """Return prepared spans without external NLP dependencies."""
        return self.entities


def test_mask_text_preserves_length_and_whitespace() -> None:
    """Verify masked text keeps document layout and character offsets stable.

    Protected risk: replacing entities with variable-length labels would break
    DOCX run boundaries and OCR coordinate mappings.
    """
    text = "Получатель: Иван Петров\nИНН 123456789012"
    start = text.index("Иван Петров")
    analyzer = FakeAnalyzer(
        [DetectedEntity(start, start + len("Иван Петров"), "PERSON")]
    )

    masked, entities = mask_text(text, analyzer)

    assert len(masked) == len(text)
    assert masked.count("\n") == 1
    assert "Иван" not in masked
    assert masked[start + 4] == " "
    assert entities[0].entity_type == "PERSON"


def test_merge_entities_combines_overlapping_spans() -> None:
    """Verify overlapping recognizers produce one stable redaction range.

    Protected risk: duplicate regex and NER results must not create fragmented
    or order-dependent masking.
    """
    merged = merge_entities(
        [
            DetectedEntity(2, 8, "PERSON", 0.6),
            DetectedEntity(5, 12, "ORGANIZATION", 0.8),
        ],
        text_length=20,
    )

    assert merged == [DetectedEntity(2, 12, "ORGANIZATION", 0.8)]


def test_merge_entities_keeps_adjacent_spans_separate() -> None:
    """Verify touching entities remain independent transformation ranges.

    Protected risk: combined mode may split an automatic entity directly next
    to a configured replacement, and merging those spans would discard the
    replacement value.
    """
    merged = merge_entities(
        [
            DetectedEntity(0, 6, "CONFIG_REPLACED", 1.1, replacement="Иванов"),
            DetectedEntity(6, 11, "PERSON", 0.8),
        ],
        text_length=11,
    )

    assert len(merged) == 2
    assert merged[0].replacement == "Иванов"
    assert merged[1].entity_type == "PERSON"


@dataclass(frozen=True)
class _FakePresidioResult:
    """Minimal Presidio-compatible result used by multilingual analyzer tests."""

    start: int
    end: int
    entity_type: str
    score: float


class _FakePresidioEngine:
    """Return language-specific entities without loading real NLP models."""

    def __init__(self, results_by_language: dict[str, list[_FakePresidioResult]]) -> None:
        self.results_by_language = results_by_language
        self.calls: list[str] = []
        self.requested_entities: list[tuple[str, ...]] = []

    def analyze(
        self,
        *,
        text: str,
        language: str,
        entities: list[str],
        score_threshold: float,
    ):
        """Record the requested language/entity scope and return prepared results."""
        self.calls.append(language)
        self.requested_entities.append(tuple(entities))
        return [
            result
            for result in self.results_by_language.get(language, [])
            if result.entity_type in entities
        ]


def test_presidio_analyzer_combines_russian_and_english_ner_results() -> None:
    """Verify automatic detection queries both local NER languages.

    Protected risk: English personal names in mixed accounting documents must
    not remain visible merely because the primary document language is Russian.
    """
    text = "Иван Петров / John Smith"
    russian_start = text.index("Иван Петров")
    english_start = text.index("John Smith")
    engine = _FakePresidioEngine(
        {
            "ru": [
                _FakePresidioResult(
                    russian_start,
                    russian_start + len("Иван Петров"),
                    "PERSON",
                    0.83,
                )
            ],
            "en": [
                _FakePresidioResult(
                    english_start,
                    english_start + len("John Smith"),
                    "PERSON",
                    0.91,
                )
            ],
        }
    )

    entities = PresidioTextAnalyzer(engine).analyze(text)

    assert engine.calls == ["ru", "en"]
    assert [(entity.start, entity.end, entity.entity_type) for entity in entities] == [
        (russian_start, russian_start + len("Иван Петров"), "PERSON"),
        (english_start, english_start + len("John Smith"), "PERSON"),
    ]


def test_presidio_analyzer_requests_only_targeted_privacy_entities() -> None:
    """Verify automatic mode does not ask Presidio for broad numeric entities.

    Protected risk: receipt amounts and ordinary financial text must remain
    available for downstream recognition instead of being hidden by unrelated
    generic Presidio recognizers.
    """
    engine = _FakePresidioEngine({"ru": [], "en": []})

    PresidioTextAnalyzer(engine).analyze("ИТОГО 1 234,56")

    assert len(engine.requested_entities) == 2
    for requested in engine.requested_entities:
        assert "PERSON" in requested
        assert "RU_INN" in requested
        assert "INTERNATIONAL_PHONE_NUMBER" in requested
        assert "CREDIT_CARD" in requested
        assert "IBAN_CODE" in requested
        assert "PHONE_NUMBER" not in requested
        assert "DATE_TIME" not in requested


def test_presidio_analyzer_preserves_receipt_amounts_from_broad_phone_detection() -> None:
    """Verify receipt amounts survive broad default recognizer false positives.

    Protected risk: generic phone/date recognizers may interpret grouped numeric
    receipt values as PII and hide the amounts needed for downstream analysis.
    """
    text = "ИТОГО 1 234,56"
    amount_start = text.index("1 234,56")
    broad_results = [
        _FakePresidioResult(
            amount_start,
            amount_start + len("1 234,56"),
            "PHONE_NUMBER",
            0.75,
        )
    ]
    engine = _FakePresidioEngine({"ru": broad_results, "en": broad_results})
    analyzer = PresidioTextAnalyzer(engine)

    masked, entities = mask_text(text, analyzer)

    assert masked == text
    assert entities == []


def test_presidio_analyzer_rejects_single_token_ner_false_positives() -> None:
    """Verify isolated receipt words are not masked as names or organizations.

    Protected risk: NER can misclassify ordinary words such as receipt headings
    as PERSON, ORGANIZATION, or LOCATION, destroying content needed for LLM
    recognition experiments.
    """
    text = "Внимание билете кассовый Иван Петров John Smith"
    fragments = (
        ("Внимание", "PERSON"),
        ("билете", "LOCATION"),
        ("кассовый", "ORGANIZATION"),
        ("Иван Петров", "PERSON"),
        ("John Smith", "PERSON"),
    )
    results = []
    for fragment, entity_type in fragments:
        start = text.index(fragment)
        results.append(
            _FakePresidioResult(start, start + len(fragment), entity_type, 0.80)
        )
    engine = _FakePresidioEngine({"ru": results, "en": []})

    entities = PresidioTextAnalyzer(engine).analyze(text)

    detected_text = [text[entity.start : entity.end] for entity in entities]
    assert detected_text == ["Иван Петров", "John Smith"]


def test_international_phone_pattern_accepts_common_plus_prefixed_formats() -> None:
    """Verify automatic patterns cover common international phone formatting.

    Protected risk: phone numbers with a country-code plus sign, spaces,
    parentheses, or hyphens must be redacted in automatic and combined modes.
    """
    samples = (
        "+1 (415) 555-2671",
        "+44 20 7946 0958",
        "+31 6 12345678",
        "+49.30.12345678",
        "+7 (999) 123-45-67",
    )

    for value in samples:
        match = re.search(_INTERNATIONAL_PHONE_PATTERN, f"Phone: {value}")
        assert match is not None
        assert match.group(0) == value


def test_international_phone_pattern_rejects_short_plus_prefixed_numbers() -> None:
    """Verify short signed numbers are not mistaken for phone numbers.

    Protected risk: a broad plus-prefix pattern must not redact ordinary signed
    numeric values which are too short to be plausible international phones.
    """
    assert re.search(_INTERNATIONAL_PHONE_PATTERN, "Adjustment: +1234567") is None


def test_create_presidio_analyzer_configures_russian_and_english_models(monkeypatch) -> None:
    """Verify automatic mode initializes both local spaCy NER pipelines.

    Protected risk: querying English in the adapter is insufficient if the
    underlying Presidio NLP engine was initialized with Russian only.
    """
    captured: dict[str, object] = {}

    class FakeNerModelConfiguration:
        """Capture NER mapping without loading Presidio."""

        def __init__(self, **kwargs) -> None:
            captured["ner_configuration"] = kwargs

    class FakeSpacyNlpEngine:
        """Capture configured spaCy models without loading spaCy."""

        def __init__(self, *, models, ner_model_configuration) -> None:
            captured["models"] = models

    class FakeRegistry:
        """Accept custom pattern recognizers added by project code."""

        def __init__(self) -> None:
            self.recognizers: list[object] = []

        def add_recognizer(self, recognizer) -> None:
            self.recognizers.append(recognizer)

    class FakeAnalyzerEngine:
        """Capture supported languages while exposing a fake registry."""

        def __init__(self, *, nlp_engine, supported_languages) -> None:
            captured["supported_languages"] = supported_languages
            self.registry = FakeRegistry()

    class FakePattern:
        """Store pattern construction arguments for registration."""

        def __init__(self, name, regex, score) -> None:
            self.name = name
            self.regex = regex
            self.score = score

    class FakePatternRecognizer:
        """Store recognizer construction arguments for registration."""

        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    presidio_module = ModuleType("presidio_analyzer")
    presidio_module.AnalyzerEngine = FakeAnalyzerEngine
    presidio_module.Pattern = FakePattern
    presidio_module.PatternRecognizer = FakePatternRecognizer
    nlp_module = ModuleType("presidio_analyzer.nlp_engine")
    nlp_module.NerModelConfiguration = FakeNerModelConfiguration
    nlp_module.SpacyNlpEngine = FakeSpacyNlpEngine
    monkeypatch.setitem(sys.modules, "presidio_analyzer", presidio_module)
    monkeypatch.setitem(sys.modules, "presidio_analyzer.nlp_engine", nlp_module)

    analyzer = create_presidio_analyzer()

    assert isinstance(analyzer, PresidioTextAnalyzer)
    assert captured["models"] == [
        {"lang_code": "ru", "model_name": "ru_core_news_sm"},
        {"lang_code": "en", "model_name": "en_core_web_sm"},
    ]
    assert captured["supported_languages"] == ["ru", "en"]


def test_create_presidio_analyzer_fails_closed_when_a_required_model_is_missing(
    monkeypatch,
) -> None:
    """Verify multilingual automatic detection never degrades silently.

    Protected risk: missing English NER must fail the run instead of leaving
    English personal names visible while reporting successful anonymization.
    """

    class FakeNerModelConfiguration:
        """Accept configuration without loading Presidio."""

        def __init__(self, **kwargs) -> None:
            pass

    class MissingModelSpacyNlpEngine:
        """Simulate spaCy failing while loading one required model."""

        def __init__(self, *, models, ner_model_configuration) -> None:
            raise OSError("missing model")

    class FakeAnalyzerEngine:
        """Unused analyzer placeholder required by the import surface."""

    presidio_module = ModuleType("presidio_analyzer")
    presidio_module.AnalyzerEngine = FakeAnalyzerEngine
    nlp_module = ModuleType("presidio_analyzer.nlp_engine")
    nlp_module.NerModelConfiguration = FakeNerModelConfiguration
    nlp_module.SpacyNlpEngine = MissingModelSpacyNlpEngine
    monkeypatch.setitem(sys.modules, "presidio_analyzer", presidio_module)
    monkeypatch.setitem(sys.modules, "presidio_analyzer.nlp_engine", nlp_module)

    with pytest.raises(RuntimeError) as error:
        create_presidio_analyzer()

    message = str(error.value)
    assert "ru_core_news_sm" in message
    assert "en_core_web_sm" in message
