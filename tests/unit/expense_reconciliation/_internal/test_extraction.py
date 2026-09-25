"""Deterministic field-extraction tests without real OCR calls."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from source_docs_processor.features.expense_reconciliation._internal.extraction import (
    classify_document_kind,
    extract_document_date,
    extract_fields_from_text,
    extract_max_amount,
    extract_person_name,
)


def test_max_amount_requires_two_decimals_and_ignores_full_dates() -> None:
    """Verify the primary heuristic chooses the largest valid money token.

    Protected risk: a date such as 02.07.2026 or an integer subtotal must not
    replace the requested maximum two-decimal receipt amount.
    """
    text = "Дата 02.07.2026\nSubtotal 980\nTax 45.00\nTOTAL 1 025,00 RUB"

    assert extract_max_amount(text) == Decimal("1025.00")


def test_max_amount_supports_english_thousands_separator() -> None:
    """Verify ticket totals such as 19,845.50 normalize exactly with Decimal.

    Protected risk: treating the thousands comma as a decimal separator would
    corrupt higher-value airline ticket amounts.
    """
    assert extract_max_amount("TOTAL USD 19,845.50") == Decimal("19845.50")


def test_document_date_prefers_issue_date_over_departure_date() -> None:
    """Verify payment-like labeled dates outrank travel dates.

    Protected risk: airline departure dates are useful context but can differ
    from the accounting purchase/issue date used for statement tie-breaking.
    """
    text = "Departure date 20.07.2026\nIssue date 14.07.2026\n"

    assert extract_document_date(text) == date(2026, 7, 14)


def test_passenger_name_supports_stacked_label_value_layout() -> None:
    """Verify a labeled passenger value can be read from the following line.

    Protected risk: many ticket PDFs and boarding passes place the passenger name
    below its field label rather than on the same line.
    """
    text = "Passenger name\nSMITH/JOHN MR\nFlight AB123"

    assert extract_person_name(text) == "SMITH/JOHN MR"


def test_fields_keep_amount_mandatory_and_other_values_optional() -> None:
    """Verify missing optional fields do not prevent amount-based reconciliation.

    Protected risk: requiring a recognized date or person would reject otherwise
    valid receipts that can be matched safely by exact amount.
    """
    document = extract_fields_from_text(Path("receipt.pdf"), "Receipt\nTOTAL 125.50")

    assert document.amount == Decimal("125.50")
    assert document.document_date is None
    assert document.person_name is None
    assert document.document_kind == "receipt"
    assert document.warnings == ()


def test_ticket_classifier_stays_narrow() -> None:
    """Verify explicit passenger/ticket markers classify airline documents.

    Protected risk: generic financial text must not become a ticket merely because
    it contains dates, totals, or English words.
    """
    assert classify_document_kind("E-TICKET\nPassenger name SMITH/JOHN") == "ticket"
    assert classify_document_kind("Invoice\nTotal 10.00") == "unknown"
