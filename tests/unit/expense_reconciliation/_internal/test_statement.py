"""Synthetic XLSX statement parser tests."""

from datetime import date
from decimal import Decimal

from openpyxl import Workbook

from source_docs_processor.features.expense_reconciliation._internal.statement import (
    parse_statement,
)


def _write_statement(path) -> None:
    """Write a minimal 1C-style account-card workbook with a redacted person header."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Лист_1"
    worksheet.append(["Карточка счета 51"])
    worksheet.append([])
    worksheet.append(
        [
            "Период",
            "Документ",
            "████████",
            "Доп. аналитика",
            "Дебет",
            None,
            None,
            "Кредит",
            None,
            None,
            "Текущее сальдо",
        ]
    )
    worksheet.append([None, None, None, None, "Счет", None, None, "Счет"])
    worksheet.append(
        [date(2026, 7, 2), "Payment 1", "Иванов Иван Иванович", "Bank", "71.01", None, None, "51", 1000]
    )
    worksheet.append(
        [date(2026, 7, 2), "Payment 2", "Иванов Иван Иванович", "Bank", "71.01", None, None, "51", 25]
    )
    worksheet.append(
        [date(2026, 7, 3), "Payment 3", "Иванов Иван Иванович", "Bank", "71.01", None, None, "51", 500]
    )
    worksheet.append(["Обороты", None, None, None, None, None, None, None, 1525])
    workbook.save(path)


def test_statement_parser_infers_credit_amount_and_person_columns(tmp_path) -> None:
    """Verify the parser handles grouped credit columns and anonymized headers.

    Protected risk: the supplied 1C export keeps the credit account in the group
    header column and the monetary amount in the next column, while the employee
    analytics header itself may be anonymized.
    """
    path = tmp_path / "statement.xlsx"
    _write_statement(path)

    entries = parse_statement(path)

    assert [entry.amount for entry in entries] == [
        Decimal("1000.00"),
        Decimal("25.00"),
        Decimal("500.00"),
    ]
    assert [entry.transaction_date for entry in entries] == [
        date(2026, 7, 2),
        date(2026, 7, 2),
        date(2026, 7, 3),
    ]
    assert {entry.person_name for entry in entries} == {"Иванов Иван Иванович"}
