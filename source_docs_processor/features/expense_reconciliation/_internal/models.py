"""Private data contracts for expense reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ExpenseDocument:
    """Represent one supporting receipt or ticket extracted from a local file."""

    source_path: Path
    amount: Decimal | None
    document_date: date | None = None
    person_name: str | None = None
    document_kind: str = "unknown"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class StatementEntry:
    """Represent one expense position parsed from a bank statement workbook."""

    source_row: int
    transaction_date: date
    person_name: str | None
    amount: Decimal
    description: str | None = None


@dataclass(frozen=True)
class ExpenseMatch:
    """Bind one supporting document to one or two bank statement positions."""

    document_index: int
    statement_indexes: tuple[int, ...]


@dataclass(frozen=True)
class ExpenseReconciliationProgress:
    """Describe one privacy-safe synchronous reconciliation progress event."""

    event: str
    file_index: int = 0
    file_count: int = 0
    source_path: Path | None = None
    output_path: Path | None = None
    error: str | None = None


ExpenseReconciliationProgressCallback = Callable[[ExpenseReconciliationProgress], None]


@dataclass(frozen=True)
class ExpenseReconciliationSummary:
    """Summarize one completed expense reconciliation run."""

    source_dir: Path
    statement_path: Path
    output_dir: Path
    workbook_path: Path
    document_count: int
    documents_with_amount_count: int
    statement_position_count: int
    matched_statement_position_count: int
    unmatched_statement_position_count: int
    unmatched_document_count: int
    statement_total: Decimal
    document_total: Decimal
    difference: Decimal
    unmatched_statement_total: Decimal
