"""Formatted XLSX report writer for expense reconciliation."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import xlsxwriter

from .models import ExpenseDocument, ExpenseMatch, StatementEntry


OUTPUT_FILENAME = "expense_reconciliation.xlsx"


def _external_file_url(file_path: Path, workbook_path: Path) -> str | None:
    """Create a relative local-file hyperlink when both paths share a filesystem."""
    try:
        relative = os.path.relpath(file_path.resolve(), workbook_path.parent.resolve())
    except ValueError:
        return None
    return f"external:{Path(relative).as_posix()}"


def _write_money(worksheet, row: int, column: int, value: Decimal, cell_format) -> None:
    """Write one Decimal as a two-decimal Excel number."""
    worksheet.write_number(row, column, float(value), cell_format)


def write_reconciliation_workbook(
    path: Path,
    source_root: Path,
    documents: list[ExpenseDocument],
    entries: list[StatementEntry],
    matches: list[ExpenseMatch],
) -> None:
    """Write statement-centric reconciliation and supporting document sheets."""
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(path)
    header = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9EAF7",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    text = workbook.add_format({"valign": "top", "text_wrap": True})
    center = workbook.add_format({"align": "center", "valign": "top"})
    date_format = workbook.add_format({"num_format": "dd.mm.yyyy", "valign": "top"})
    money = workbook.add_format({"num_format": "#,##0.00", "valign": "top"})
    link = workbook.add_format({"font_color": "blue", "underline": 1, "valign": "top"})
    summary_label = workbook.add_format({"bold": True, "bg_color": "#F2F2F2"})
    summary_money = workbook.add_format(
        {"bold": True, "bg_color": "#F2F2F2", "num_format": "#,##0.00"}
    )

    reconciliation = workbook.add_worksheet("Reconciliation")
    columns = (
        ("ФИО", 32),
        ("Дата", 14),
        ("Сумма", 14),
        ("Чек", 14),
        ("Позиция", 10),
        ("Имя файла-чека", 46),
        ("Сумма из чека", 18),
    )
    for column_index, (label, width) in enumerate(columns):
        reconciliation.write(0, column_index, label, header)
        reconciliation.set_column(column_index, column_index, width)

    statement_match: dict[int, tuple[ExpenseMatch, int]] = {}
    matched_document_indexes = set()
    for match in matches:
        matched_document_indexes.add(match.document_index)
        for position, statement_index in enumerate(match.statement_indexes, start=1):
            statement_match[statement_index] = (match, position)

    for row_index, entry in enumerate(entries, start=1):
        reconciliation.write_string(row_index, 0, entry.person_name or "", text)
        reconciliation.write_datetime(row_index, 1, entry.transaction_date, date_format)
        _write_money(reconciliation, row_index, 2, entry.amount, money)
        matched = statement_match.get(row_index - 1)
        if matched is None:
            reconciliation.write_string(row_index, 3, "Не найден", center)
            continue
        match, position = matched
        document = documents[match.document_index]
        reconciliation.write_string(row_index, 3, "Найден", center)
        reconciliation.write_number(row_index, 4, position, center)
        url = _external_file_url(document.source_path, path)
        if url is None:
            reconciliation.write_string(row_index, 5, document.source_path.name, text)
        else:
            reconciliation.write_url(
                row_index,
                5,
                url,
                link,
                string=document.source_path.name,
            )
        if document.amount is not None:
            _write_money(reconciliation, row_index, 6, document.amount, money)

    last_data_row = len(entries)
    reconciliation.freeze_panes(1, 0)
    reconciliation.autofilter(0, 0, max(last_data_row, 1), len(columns) - 1)
    reconciliation.set_row(0, 34)
    if last_data_row:
        reconciliation.conditional_format(
            1,
            3,
            last_data_row,
            3,
            {
                "type": "formula",
                "criteria": '=$D2="Не найден"',
                "format": workbook.add_format({"bg_color": "#F4CCCC"}),
            },
        )
        reconciliation.conditional_format(
            1,
            3,
            last_data_row,
            3,
            {
                "type": "formula",
                "criteria": '=$D2="Найден"',
                "format": workbook.add_format({"bg_color": "#D9EAD3"}),
            },
        )

    statement_total = sum((entry.amount for entry in entries), Decimal("0"))
    document_total = sum(
        (document.amount for document in documents if document.amount is not None),
        Decimal("0"),
    )
    matched_statement_indexes = set(statement_match)
    unmatched_statement_indexes = [
        index for index in range(len(entries)) if index not in matched_statement_indexes
    ]
    unmatched_statement_total = sum(
        (entries[index].amount for index in unmatched_statement_indexes),
        Decimal("0"),
    )
    unmatched_document_indexes = [
        index for index in range(len(documents)) if index not in matched_document_indexes
    ]
    unmatched_document_total = sum(
        (
            documents[index].amount
            for index in unmatched_document_indexes
            if documents[index].amount is not None
        ),
        Decimal("0"),
    )
    documents_with_amount = sum(document.amount is not None for document in documents)

    summary_start = last_data_row + 3
    summary_rows = (
        ("Количество позиций выписки", len(entries), False),
        ("Количество входных документов", len(documents), False),
        ("Документы с распознанной суммой", documents_with_amount, False),
        ("Общая сумма выписки", statement_total, True),
        ("Общая сумма документов", document_total, True),
        ("Расхождение (выписка - документы)", statement_total - document_total, True),
        ("Найдено позиций выписки", len(matched_statement_indexes), False),
        ("Не найдено позиций выписки", len(unmatched_statement_indexes), False),
        ("Сумма ненайденных позиций", unmatched_statement_total, True),
        (
            "Суммы ненайденных позиций",
            ", ".join(f"{entries[index].amount:.2f}" for index in unmatched_statement_indexes),
            False,
        ),
        ("Несопоставленные документы", len(unmatched_document_indexes), False),
        ("Сумма несопоставленных документов", unmatched_document_total, True),
        (
            "Документы без распознанной суммы",
            len(documents) - documents_with_amount,
            False,
        ),
    )
    for offset, (label, value, is_money) in enumerate(summary_rows):
        row = summary_start + offset
        reconciliation.write_string(row, 0, label, summary_label)
        if is_money:
            _write_money(reconciliation, row, 1, value, summary_money)
        elif isinstance(value, int):
            reconciliation.write_number(row, 1, value, summary_label)
        else:
            reconciliation.write_string(row, 1, str(value), summary_label)
    reconciliation.set_column(0, 0, 38)

    documents_sheet = workbook.add_worksheet("Documents")
    document_columns = (
        ("Имя файла", 46),
        ("Тип", 14),
        ("Сумма", 16),
        ("Дата", 14),
        ("ФИО", 32),
        ("Сопоставлен", 14),
        ("Количество позиций", 20),
        ("Предупреждения", 34),
    )
    for column_index, (label, width) in enumerate(document_columns):
        documents_sheet.write(0, column_index, label, header)
        documents_sheet.set_column(column_index, column_index, width)

    matches_by_document = {match.document_index: match for match in matches}
    for row_index, document in enumerate(documents, start=1):
        url = _external_file_url(document.source_path, path)
        relative_label = document.source_path.relative_to(source_root).as_posix()
        if url is None:
            documents_sheet.write_string(row_index, 0, relative_label, text)
        else:
            documents_sheet.write_url(row_index, 0, url, link, string=relative_label)
        documents_sheet.write_string(row_index, 1, document.document_kind, text)
        if document.amount is not None:
            _write_money(documents_sheet, row_index, 2, document.amount, money)
        if document.document_date is not None:
            documents_sheet.write_datetime(row_index, 3, document.document_date, date_format)
        documents_sheet.write_string(row_index, 4, document.person_name or "", text)
        match = matches_by_document.get(row_index - 1)
        documents_sheet.write_string(
            row_index,
            5,
            "Да" if match is not None else "Нет",
            center,
        )
        documents_sheet.write_number(
            row_index,
            6,
            len(match.statement_indexes) if match is not None else 0,
            center,
        )
        documents_sheet.write_string(row_index, 7, ", ".join(document.warnings), text)

    last_document_row = max(len(documents), 1)
    documents_sheet.freeze_panes(1, 0)
    documents_sheet.autofilter(0, 0, last_document_row, len(document_columns) - 1)
    documents_sheet.set_row(0, 34)
    workbook.close()
