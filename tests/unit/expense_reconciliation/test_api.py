"""Public API regression tests for expense reconciliation."""

from inspect import signature

from source_docs_processor.features import expense_reconciliation


def test_expense_reconciliation_exports_exact_supported_api() -> None:
    """Verify callers get one small explicit reconciliation package surface.

    Protected risk: accidental private helper exports would couple adapters to
    extraction, statement, matching, or workbook implementation details.
    """
    assert tuple(expense_reconciliation.__all__) == (
        "ExpenseDocument",
        "ExpenseMatch",
        "ExpenseReconciliationProgress",
        "ExpenseReconciliationProgressCallback",
        "ExpenseReconciliationSummary",
        "SUPPORTED_DOCUMENT_EXTENSIONS",
        "StatementEntry",
        "reconcile_expenses",
    )


def test_reconcile_expenses_signature_is_stable() -> None:
    """Verify the public operation keeps explicit source, statement, and output inputs.

    Protected risk: hiding the second input inside document processing would make
    reconciliation look like a single-source document type again.
    """
    parameters = signature(expense_reconciliation.reconcile_expenses).parameters
    assert tuple(parameters) == (
        "source_dir",
        "statement_path",
        "output_dir",
        "lang",
        "progress_callback",
    )
    assert parameters["lang"].default == "rus+eng"
    assert parameters["progress_callback"].default is None
