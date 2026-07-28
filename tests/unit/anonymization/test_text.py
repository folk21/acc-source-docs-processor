"""Tests for format-preserving PII span masking."""

from __future__ import annotations

from source_docs_processor.anonymization.models import DetectedEntity
from source_docs_processor.anonymization.text import mask_text, merge_entities


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
