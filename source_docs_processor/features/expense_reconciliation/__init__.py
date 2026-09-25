"""Public API for matching expense documents to a bank statement."""

from .api import (
    ExpenseDocument,
    ExpenseMatch,
    ExpenseReconciliationProgress,
    ExpenseReconciliationProgressCallback,
    ExpenseReconciliationSummary,
    SUPPORTED_DOCUMENT_EXTENSIONS,
    StatementEntry,
    reconcile_expenses,
)

__all__ = [
    "ExpenseDocument",
    "ExpenseMatch",
    "ExpenseReconciliationProgress",
    "ExpenseReconciliationProgressCallback",
    "ExpenseReconciliationSummary",
    "SUPPORTED_DOCUMENT_EXTENSIONS",
    "StatementEntry",
    "reconcile_expenses",
]
