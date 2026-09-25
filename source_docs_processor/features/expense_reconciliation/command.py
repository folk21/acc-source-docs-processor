"""CLI adapter for expense reconciliation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .api import ExpenseReconciliationProgress, reconcile_expenses


def _print_progress(progress: ExpenseReconciliationProgress, source_root: Path) -> None:
    """Print one privacy-safe reconciliation progress line."""
    if progress.event == "statement_started":
        print("Reading bank statement...", flush=True)
    elif progress.event == "statement_finished":
        print("Bank statement parsed.", flush=True)
    elif progress.event == "scan_finished":
        print(f"Expense documents selected: {progress.file_count}", flush=True)
    elif progress.event in {"file_started", "file_finished", "file_failed"}:
        if progress.source_path is None:
            return
        relative = progress.source_path.relative_to(source_root)
        prefix = f"[{progress.file_index}/{progress.file_count}]"
        status = {
            "file_started": "START",
            "file_finished": "DONE",
            "file_failed": "FAILED",
        }[progress.event]
        print(f"{prefix} {status}: {relative}", flush=True)
    elif progress.event == "workbook_written" and progress.output_path is not None:
        print(f"Workbook written: {progress.output_path}", flush=True)


def _run_reconcile_expenses_command(args: argparse.Namespace) -> int:
    """Run expense reconciliation from parsed CLI arguments."""
    source_dir = Path(args.source).expanduser().resolve()
    statement_path = Path(args.statement).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    summary = reconcile_expenses(
        source_dir=source_dir,
        statement_path=statement_path,
        output_dir=output_dir,
        lang=args.lang,
        progress_callback=lambda progress: _print_progress(progress, source_dir),
    )
    print(
        "Expense reconciliation finished: "
        f"documents={summary.document_count}, "
        f"statement_positions={summary.statement_position_count}, "
        f"matched_positions={summary.matched_statement_position_count}, "
        f"unmatched_positions={summary.unmatched_statement_position_count}",
        flush=True,
    )
    return 0


def register_reconcile_expenses_command(subparsers: Any) -> None:
    """Register the expense-reconciliation subcommand."""
    parser = subparsers.add_parser(
        "reconcile-expenses",
        help="Match receipt and ticket files to bank-statement expense positions.",
        description=(
            "Extract amounts and optional dates/passenger names from local receipt "
            "and ticket files, match them to one XLSX bank statement, and create "
            "expense_reconciliation.xlsx."
        ),
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source folder with receipt and ticket files. Subfolders are recursive.",
    )
    parser.add_argument(
        "--statement",
        required=True,
        help="XLSX bank statement exported in the supported 1C account-card layout.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output folder for expense_reconciliation.xlsx.",
    )
    parser.add_argument(
        "--lang",
        default="rus+eng",
        help="Tesseract language combination for scanned files. Default: rus+eng",
    )
    parser.set_defaults(command_handler=_run_reconcile_expenses_command)


__all__ = ["register_reconcile_expenses_command"]
