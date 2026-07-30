"""Tests for feature-neutral whitespace normalization."""

from source_docs_processor.core.text import (
    normalize_inline_whitespace,
    normalize_multiline_whitespace,
)


def test_inline_whitespace_collapses_lines_and_nonbreaking_spaces() -> None:
    """Verify inline normalization produces one stable compact text value.

    Protected risk: structured document matching relies on equivalent spaces,
    tabs, line breaks, and non-breaking spaces producing the same text.
    """
    assert normalize_inline_whitespace(' A\u00a0 B\n\tC ') == 'A B C'


def test_multiline_whitespace_preserves_line_separation() -> None:
    """Verify OCR line boundaries survive horizontal-space normalization.

    Protected risk: UPD extraction uses line-aware text while still requiring
    tabs and non-breaking spaces to normalize deterministically.
    """
    assert normalize_multiline_whitespace(' A\t B \n C\u00a0 D ') == 'A B\nC D'
