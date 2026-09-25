"""Global amount-matching regressions for expense reconciliation."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from source_docs_processor.features.expense_reconciliation._internal.matching import (
    match_expenses,
)
from source_docs_processor.features.expense_reconciliation._internal.models import (
    ExpenseDocument,
    StatementEntry,
)


def _entry(amount: str, day: int = 1) -> StatementEntry:
    """Build one synthetic statement position."""
    return StatementEntry(
        source_row=day + 10,
        transaction_date=date(2026, 7, day),
        person_name="Иванов Иван Иванович",
        amount=Decimal(amount),
    )


def _document(name: str, amount: str, day: int | None = None) -> ExpenseDocument:
    """Build one synthetic supporting document."""
    return ExpenseDocument(
        source_path=Path(name),
        amount=Decimal(amount),
        document_date=date(2026, 7, day) if day is not None else None,
    )


def test_global_match_prefers_1025_document_for_1000_plus_25_positions() -> None:
    """Verify a combined receipt can beat a conflicting smaller exact receipt.

    Protected risk: greedy one-to-one matching would consume the 1000 position
    first and leave 25 missing even though a 1025 document covers both rows.
    """
    entries = [_entry("1000.00"), _entry("25.00")]
    documents = [
        _document("small.pdf", "1000.00"),
        _document("combined.pdf", "1025.00"),
    ]

    matches = match_expenses(documents, entries)

    assert len(matches) == 1
    assert matches[0].document_index == 1
    assert matches[0].statement_indexes == (0, 1)


def test_global_match_prefers_two_documents_when_coverage_is_otherwise_equal() -> None:
    """Verify matched-document count breaks equal amount and row coverage ties.

    Protected risk: one combined receipt should not displace two independent
    exact receipts when both solutions cover the same statement amount and rows.
    """
    entries = [_entry("500.00"), _entry("500.00", day=2)]
    documents = [
        _document("combined.pdf", "1000.00"),
        _document("left.pdf", "500.00"),
        _document("right.pdf", "500.00"),
    ]

    matches = match_expenses(documents, entries)

    assert {match.document_index for match in matches} == {1, 2}
    assert {match.statement_indexes for match in matches} == {(0,), (1,)}


def test_date_is_only_a_tie_breaker_for_duplicate_amounts() -> None:
    """Verify recognized dates choose among equal amounts without becoming required.

    Protected risk: duplicate statement sums are expected, so optional dates
    should improve the selected row but never block exact amount matching.
    """
    entries = [_entry("750.00", day=3), _entry("750.00", day=9)]
    documents = [_document("dated.pdf", "750.00", day=9)]

    matches = match_expenses(documents, entries)

    assert matches[0].statement_indexes == (1,)
