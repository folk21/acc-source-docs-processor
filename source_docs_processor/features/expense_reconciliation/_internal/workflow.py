"""End-to-end local expense reconciliation workflow."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

from .extraction import extract_expense_document, iter_expense_document_files
from .matching import match_expenses
from .models import (
    ExpenseDocument,
    ExpenseReconciliationProgress,
    ExpenseReconciliationProgressCallback,
    ExpenseReconciliationSummary,
)
from .statement import parse_statement
from .workbook import OUTPUT_FILENAME, write_reconciliation_workbook


def _emit(
    callback: ExpenseReconciliationProgressCallback | None,
    progress: ExpenseReconciliationProgress,
) -> None:
    """Emit one synchronous progress event when a callback is configured."""
    if callback is not None:
        callback(progress)


def reconcile_expenses(
    source_dir: Path,
    statement_path: Path,
    output_dir: Path,
    lang: str = "rus+eng",
    progress_callback: ExpenseReconciliationProgressCallback | None = None,
) -> ExpenseReconciliationSummary:
    """Reconcile local receipt/ticket files with one XLSX bank statement."""
    source_dir = source_dir.expanduser().resolve()
    statement_path = statement_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    if not source_dir.is_dir():
        raise ValueError(f"Source directory does not exist: {source_dir}")
    if not statement_path.is_file() or statement_path.suffix.lower() != ".xlsx":
        raise ValueError(f"Statement must be an existing XLSX file: {statement_path}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"Output path exists but is not a directory: {output_dir}")

    _emit(progress_callback, ExpenseReconciliationProgress(event="statement_started"))
    entries = parse_statement(statement_path)
    _emit(progress_callback, ExpenseReconciliationProgress(event="statement_finished"))

    files = iter_expense_document_files(source_dir)
    _emit(
        progress_callback,
        ExpenseReconciliationProgress(event="scan_finished", file_count=len(files)),
    )
    documents: list[ExpenseDocument] = []
    for file_index, path in enumerate(files, start=1):
        _emit(
            progress_callback,
            ExpenseReconciliationProgress(
                event="file_started",
                file_index=file_index,
                file_count=len(files),
                source_path=path,
            ),
        )
        try:
            document = extract_expense_document(path, lang)
        except Exception as exc:
            document = ExpenseDocument(
                source_path=path,
                amount=None,
                warnings=(f"extraction_failed:{type(exc).__name__}",),
            )
            _emit(
                progress_callback,
                ExpenseReconciliationProgress(
                    event="file_failed",
                    file_index=file_index,
                    file_count=len(files),
                    source_path=path,
                    error=type(exc).__name__,
                ),
            )
        else:
            _emit(
                progress_callback,
                ExpenseReconciliationProgress(
                    event="file_finished",
                    file_index=file_index,
                    file_count=len(files),
                    source_path=path,
                ),
            )
        documents.append(document)

    matches = match_expenses(documents, entries)
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook_path = output_dir / OUTPUT_FILENAME
    temporary_path = output_dir / f".{OUTPUT_FILENAME}.tmp.xlsx"
    try:
        write_reconciliation_workbook(
            temporary_path,
            source_dir,
            documents,
            entries,
            matches,
        )
        os.replace(temporary_path, workbook_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    matched_statement_indexes = {
        statement_index
        for match in matches
        for statement_index in match.statement_indexes
    }
    matched_document_indexes = {match.document_index for match in matches}
    statement_total = sum((entry.amount for entry in entries), Decimal("0"))
    document_total = sum(
        (document.amount for document in documents if document.amount is not None),
        Decimal("0"),
    )
    unmatched_statement_total = sum(
        (
            entry.amount
            for index, entry in enumerate(entries)
            if index not in matched_statement_indexes
        ),
        Decimal("0"),
    )
    summary = ExpenseReconciliationSummary(
        source_dir=source_dir,
        statement_path=statement_path,
        output_dir=output_dir,
        workbook_path=workbook_path,
        document_count=len(documents),
        documents_with_amount_count=sum(document.amount is not None for document in documents),
        statement_position_count=len(entries),
        matched_statement_position_count=len(matched_statement_indexes),
        unmatched_statement_position_count=len(entries) - len(matched_statement_indexes),
        unmatched_document_count=len(documents) - len(matched_document_indexes),
        statement_total=statement_total,
        document_total=document_total,
        difference=statement_total - document_total,
        unmatched_statement_total=unmatched_statement_total,
    )
    _emit(
        progress_callback,
        ExpenseReconciliationProgress(
            event="workbook_written",
            output_path=workbook_path,
        ),
    )
    return summary
