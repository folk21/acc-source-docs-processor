"""Generic XLSX registry writer for document-specific row definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import xlsxwriter

from ..models import ExtractedDocument, RegistryValue
from .base import RegistryDefinition


def _validate_columns(columns: tuple[str, ...]) -> None:
    """Validate registry column names before creating an XLSX file."""
    if not columns:
        raise ValueError("Registry definition must declare at least one column")
    if len(columns) != len(set(columns)):
        raise ValueError("Registry columns must be unique")
    if any(not column.strip() for column in columns):
        raise ValueError("Registry column names must not be empty")


def _external_file_url(file_path: Path, workbook_path: Path) -> str:
    """Create a portable local-file hyperlink relative to the workbook."""
    try:
        relative = file_path.resolve().relative_to(workbook_path.parent.resolve())
        target = relative.as_posix()
    except ValueError:
        target = file_path.resolve().as_posix()
    return f"external:{target}"


def write_xlsx_registry(
    documents: list[ExtractedDocument],
    path: Path,
    definition: RegistryDefinition,
    source_root: Path,
    headers: Mapping[str, str] | None = None,
) -> None:
    """Write a formatted XLSX registry with links to copied receipt files."""
    columns = tuple(definition.columns)
    _validate_columns(columns)
    header_labels = headers or {column: column for column in columns}
    path.parent.mkdir(parents=True, exist_ok=True)

    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet("Чеки НПД")
    header_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#D9EAF7",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    text_format = workbook.add_format({"valign": "top", "text_wrap": True})
    link_format = workbook.add_format(
        {
            "font_color": "blue",
            "underline": 1,
            "valign": "top",
        }
    )
    inn_format = workbook.add_format({"num_format": "@", "valign": "top"})
    amount_format = workbook.add_format({"num_format": "0.00", "valign": "top"})
    confidence_format = workbook.add_format({"num_format": "0", "valign": "top"})

    for column_index, column in enumerate(columns):
        worksheet.write(0, column_index, header_labels.get(column, column), header_format)

    for row_index, document in enumerate(documents, start=1):
        raw_row = dict(definition.build_row(document, source_root))
        unexpected = set(raw_row).difference(columns)
        if unexpected:
            names = ", ".join(sorted(unexpected))
            workbook.close()
            raise ValueError(f"Registry row contains undeclared columns: {names}")

        for column_index, column in enumerate(columns):
            value: RegistryValue = raw_row.get(column, "")
            if column == "target_file_name" and document.destination_path is not None:
                worksheet.write_url(
                    row_index,
                    column_index,
                    _external_file_url(document.destination_path, path),
                    link_format,
                    string=str(value),
                )
            elif column in {"issuer_inn", "recipient_inn", "payee_inn"}:
                worksheet.write_string(
                    row_index,
                    column_index,
                    str(value or ""),
                    inn_format,
                )
            elif column == "amount" and value not in {None, ""}:
                try:
                    worksheet.write_number(
                        row_index,
                        column_index,
                        float(str(value)),
                        amount_format,
                    )
                except ValueError:
                    worksheet.write(row_index, column_index, value, text_format)
            elif column == "confidence" and value not in {None, ""}:
                worksheet.write_number(
                    row_index,
                    column_index,
                    float(value),
                    confidence_format,
                )
            else:
                worksheet.write(row_index, column_index, value, text_format)

    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, max(len(documents), 1), len(columns) - 1)
    widths = {
        "target_file_name": 52,
        "source_file_name": 34,
        "receipt_date": 14,
        "amount": 14,
        "payee_name": 32,
        "receipt_number": 26,
        "payee_inn": 18,
        "generation_comments": 46,
    }
    for column_index, column in enumerate(columns):
        worksheet.set_column(column_index, column_index, widths.get(column, 18))
    worksheet.set_row(0, 34)
    workbook.close()
