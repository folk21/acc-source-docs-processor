"""UI-facing adapter helpers for the public expense-reconciliation API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from source_docs_processor.features.expense_reconciliation import (
    ExpenseReconciliationProgress,
    ExpenseReconciliationSummary,
    reconcile_expenses,
)


ProgressCallback = Callable[[ExpenseReconciliationProgress], None]


@dataclass(frozen=True)
class ExpenseReconciliationRequest:
    """Validated UI values required for one expense-reconciliation run."""

    source_dir: Path
    statement_path: Path
    output_dir: Path
    lang: str = "rus+eng"


def execute_expense_reconciliation(
    request: ExpenseReconciliationRequest,
    *,
    progress_callback: ProgressCallback | None = None,
) -> ExpenseReconciliationSummary:
    """Execute one local reconciliation request through the public feature API."""
    return reconcile_expenses(
        source_dir=request.source_dir,
        statement_path=request.statement_path,
        output_dir=request.output_dir,
        lang=request.lang,
        progress_callback=progress_callback,
    )


def workbook_display_path(summary: ExpenseReconciliationSummary) -> str:
    """Return a portable workbook path suitable for the local UI."""
    try:
        return summary.workbook_path.relative_to(summary.output_dir).as_posix()
    except ValueError:
        return summary.workbook_path.name
