"""Tests for fail-closed XLSX package anonymization."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
import xlsxwriter

from source_docs_processor.features.anonymization._internal.models import DetectedEntity
from source_docs_processor.features.anonymization._internal.xlsx import anonymize_xlsx_file


class NamesAnalyzer:
    """Detect fictional Russian and English names in deterministic fixtures."""

    def analyze(self, text: str) -> list[DetectedEntity]:
        """Return every configured fictional full-name occurrence."""
        entities: list[DetectedEntity] = []
        for value in ("Иван Петров", "John Smith"):
            offset = 0
            while True:
                start = text.find(value, offset)
                if start < 0:
                    break
                entities.append(DetectedEntity(start, start + len(value), "PERSON"))
                offset = start + len(value)
        return entities


def _write_workbook(path: Path) -> None:
    """Create one synthetic workbook with visible, hidden, and metadata PII."""
    workbook = xlsxwriter.Workbook(path)
    workbook.set_properties({"author": "John Smith", "title": "Synthetic workbook"})
    sheet = workbook.add_worksheet("Receipt")
    sheet.write("A1", "Получатель: Иван Петров")
    sheet.write_comment("A1", "Contact John Smith", {"author": "John Smith"})
    sheet.write("A2", "ИТОГО")
    sheet.write_number("B2", 1234.56)
    sheet.write_formula("B3", "=SUM(B2:B2)")
    hidden = workbook.add_worksheet("Hidden")
    hidden.hide()
    hidden.write("A1", "Passenger: John Smith")
    workbook.close()


def test_xlsx_anonymization_masks_cells_comments_and_metadata(tmp_path: Path) -> None:
    """Verify XLSX text is sanitized while receipt amounts and formulas survive.

    Protected risk: hidden sheets, shared strings, comments, and document
    properties must not retain PII inside an apparently anonymized workbook.
    """
    source = tmp_path / "source.xlsx"
    output = tmp_path / "output.xlsx"
    _write_workbook(source)

    detected = anonymize_xlsx_file(source, output, NamesAnalyzer())

    assert detected >= 3
    with zipfile.ZipFile(output) as archive:
        package_text = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.endswith(".xml") or name.endswith(".rels")
        )
    assert "Иван Петров" not in package_text
    assert "John Smith" not in package_text
    assert "ИТОГО" in package_text
    assert "1234.56" in package_text
    assert "SUM(B2:B2)" in package_text


def test_xlsx_anonymization_rejects_external_relationships(tmp_path: Path) -> None:
    """Verify external workbook links fail closed instead of leaking targets.

    Protected risk: URLs and external-file relationships can contain private
    identifiers even when the visible cell text has been anonymized.
    """
    source = tmp_path / "external.xlsx"
    output = tmp_path / "output.xlsx"
    workbook = xlsxwriter.Workbook(source)
    sheet = workbook.add_worksheet()
    sheet.write_url("A1", "https://example.invalid/private/John-Smith")
    workbook.close()

    with pytest.raises(ValueError, match="external relationships"):
        anonymize_xlsx_file(source, output, NamesAnalyzer())


def test_xlsx_anonymization_rejects_pii_inside_formula(tmp_path: Path) -> None:
    """Verify formulas containing PII are rejected instead of rewritten unsafely.

    Protected risk: changing formula text can corrupt workbook semantics, while
    preserving a detected private literal would violate fail-closed behavior.
    """
    source = tmp_path / "formula.xlsx"
    output = tmp_path / "output.xlsx"
    workbook = xlsxwriter.Workbook(source)
    sheet = workbook.add_worksheet()
    sheet.write_formula("A1", '="John Smith"')
    workbook.close()

    with pytest.raises(ValueError, match="formula"):
        anonymize_xlsx_file(source, output, NamesAnalyzer())
