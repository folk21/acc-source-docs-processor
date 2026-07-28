"""Integration tests for recursive folder anonymization."""

from __future__ import annotations

from pathlib import Path

from source_docs_processor.anonymization.models import DetectedEntity
from source_docs_processor.anonymization.workflow import anonymize_folder


class FictionalNameAnalyzer:
    """Detect a fictional name in plain text fixtures."""

    def analyze(self, text: str) -> list[DetectedEntity]:
        """Return every fictional full-name occurrence."""
        value = "Иван Петров"
        entities: list[DetectedEntity] = []
        offset = 0
        while True:
            start = text.find(value, offset)
            if start < 0:
                return entities
            entities.append(
                DetectedEntity(start, start + len(value), "PERSON")
            )
            offset = start + len(value)


def test_folder_anonymization_preserves_relative_names_and_reports_unsupported_files(
    tmp_path: Path,
) -> None:
    """Verify directory-to-directory output mirrors source names and fails closed.

    Protected risk: unsupported files must not be copied unchanged into a folder
    which users may trust as fully anonymized.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    text_path = source / "nested" / "note.txt"
    text_path.parent.mkdir(parents=True)
    text_path.write_text("Контакт: Иван Петров", encoding="utf-8")
    (source / "raw.bin").write_bytes(b"Ivan Petrov")

    summary = anonymize_folder(source, output, FictionalNameAnalyzer())

    anonymized_text = output / "nested" / "note.txt"
    assert anonymized_text.exists()
    assert "Иван Петров" not in anonymized_text.read_text(encoding="utf-8")
    assert not (output / "raw.bin").exists()
    assert summary.succeeded_count == 1
    assert summary.failed_count == 1
