"""Tests for shared strict document-value normalization."""

from decimal import Decimal

from source_docs_processor.features.document_processing.normalization.dates import (
    normalize_date,
)
from source_docs_processor.features.document_processing.normalization.money import (
    format_decimal_value,
    normalize_decimal_value,
    parse_decimal_value,
)


def test_strict_date_normalization_accepts_numeric_and_russian_text() -> None:
    """Verify reusable date parsing avoids document-specific OCR aliases.

    Protected risk: common date normalization must support normal source formats
    without acquiring noisy UPD crop heuristics or form-template rules.
    """
    assert normalize_date('21 марта 2023 г.') == '21-03-2023'
    assert normalize_date('20.03.23') == '20-03-2023'
    assert normalize_date('21 хабр 2023') is None


def test_decimal_helpers_separate_parsing_and_output_format() -> None:
    """Verify localized parsing can serve different document output contracts.

    Protected risk: UPD preserves input scale while task workbooks require fixed
    two-decimal formatting; one hidden policy must not be imposed on both.
    """
    parsed = parse_decimal_value('1 234,5 руб.', strip_non_numeric=True)

    assert parsed == Decimal('1234.5')
    assert format_decimal_value(parsed) == '1234.50'
    assert normalize_decimal_value('1 234,5') == '1234.5'
    assert normalize_decimal_value('1 234,567') is None
