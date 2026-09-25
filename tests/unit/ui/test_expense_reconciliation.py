"""Tests for the UI adapter around the public expense-reconciliation API."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from source_docs_processor.features.expense_reconciliation import (
    ExpenseReconciliationSummary,
)
from source_docs_processor.ui.expense_reconciliation import (
    ExpenseReconciliationRequest,
    execute_expense_reconciliation,
    workbook_display_path,
)


def _summary(source: Path, statement: Path, output: Path) -> ExpenseReconciliationSummary:
    """Build one compact public summary for adapter tests."""
    return ExpenseReconciliationSummary(
        source_dir=source,
        statement_path=statement,
        output_dir=output,
        workbook_path=output / "expense_reconciliation.xlsx",
        document_count=3,
        documents_with_amount_count=2,
        statement_position_count=4,
        matched_statement_position_count=3,
        unmatched_statement_position_count=1,
        unmatched_document_count=1,
        statement_total=Decimal("100.00"),
        document_total=Decimal("90.00"),
        difference=Decimal("10.00"),
        unmatched_statement_total=Decimal("10.00"),
    )


def test_execute_expense_reconciliation_forwards_ui_values_to_public_api(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify the UI calls only the public reconciliation API with form values.

    Protected risk: the Streamlit adapter must not duplicate reconciliation logic,
    invoke the CLI, or import private feature implementation modules.
    """
    from source_docs_processor.ui import expense_reconciliation as ui_reconciliation

    source = tmp_path / "source"
    statement = tmp_path / "payments.xlsx"
    output = tmp_path / "output"
    captured = {}

    def fake_reconcile_expenses(**kwargs):
        captured.update(kwargs)
        return _summary(source, statement, output)

    monkeypatch.setattr(
        ui_reconciliation,
        "reconcile_expenses",
        fake_reconcile_expenses,
    )
    request = ExpenseReconciliationRequest(
        source_dir=source,
        statement_path=statement,
        output_dir=output,
        lang="rus+eng",
    )

    summary = execute_expense_reconciliation(request)

    assert summary.unmatched_statement_position_count == 1
    assert captured == {
        "source_dir": source,
        "statement_path": statement,
        "output_dir": output,
        "lang": "rus+eng",
        "progress_callback": None,
    }


def test_workbook_display_path_does_not_expose_absolute_output_root(
    tmp_path: Path,
) -> None:
    """Verify the UI exposes only a portable generated workbook path.

    Protected risk: result screens can be copied into notes and must not leak the
    accountant's complete local directory structure.
    """
    source = tmp_path / "private-source"
    statement = tmp_path / "private-statement" / "payments.xlsx"
    output = tmp_path / "private-output"
    summary = _summary(source, statement, output)

    assert workbook_display_path(summary) == "expense_reconciliation.xlsx"
    assert str(tmp_path) not in workbook_display_path(summary)
