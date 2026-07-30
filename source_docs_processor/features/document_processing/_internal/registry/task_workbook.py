"""Generic multi-sheet XLSX writer for accountant task workbooks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Protocol, Sequence

import xlsxwriter

from ...models import ExtractedDocument, RegistryValue


@dataclass(frozen=True)
class WorkbookColumn:
    """Describe one workbook column and its serialization behavior."""

    key: str
    header: str
    width: float = 18
    value_type: str = "text"
    hidden: bool = False
    comment: str | None = None
    validation_options: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkbookLink:
    """Represent one portable external file hyperlink."""

    label: str
    target: Path


WorkbookCellValue = RegistryValue | WorkbookLink
WorkbookRow = Mapping[str, WorkbookCellValue]


class TaskWorkbookDefinition(Protocol):
    """Define Documents, Items, Review, and metadata workbook content."""

    document_columns: tuple[WorkbookColumn, ...]
    item_columns: tuple[WorkbookColumn, ...]
    review_columns: tuple[WorkbookColumn, ...]

    def build_document_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> WorkbookRow:
        """Build one row for the Documents sheet."""
        ...

    def build_item_rows(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> Sequence[WorkbookRow]:
        """Build zero or more rows for the Items sheet."""
        ...

    def build_review_rows(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> Sequence[WorkbookRow]:
        """Build zero or more rows for the Review sheet."""
        ...

    def build_metadata(self) -> Mapping[str, RegistryValue]:
        """Build hidden workbook metadata."""
        ...


def _validate_columns(columns: tuple[WorkbookColumn, ...]) -> None:
    """Validate one sheet definition before creating the workbook."""
    if not columns:
        raise ValueError("Workbook sheet must declare at least one column")
    keys = [column.key for column in columns]
    if len(keys) != len(set(keys)):
        raise ValueError("Workbook column keys must be unique")
    if any(not key.strip() for key in keys):
        raise ValueError("Workbook column keys must not be empty")


def _external_file_url(file_path: Path, workbook_path: Path) -> str:
    """Create a portable local-file hyperlink relative to the workbook."""
    try:
        relative = file_path.resolve().relative_to(workbook_path.parent.resolve())
        target = relative.as_posix()
    except ValueError:
        target = file_path.resolve().as_posix()
    return f"external:{target}"


def _write_cell(
    worksheet,
    row_index: int,
    column_index: int,
    value: WorkbookCellValue,
    column: WorkbookColumn,
    workbook_path: Path,
    formats: Mapping[str, object],
) -> None:
    """Write one typed workbook cell."""
    if isinstance(value, WorkbookLink):
        worksheet.write_url(
            row_index,
            column_index,
            _external_file_url(value.target, workbook_path),
            formats["link"],
            string=value.label,
        )
        return

    if column.value_type == "checkbox":
        boolean_value = bool(value)
        if hasattr(worksheet, "insert_checkbox"):
            worksheet.insert_checkbox(
                row_index,
                column_index,
                boolean_value,
                formats["checkbox"],
            )
        else:
            worksheet.write_boolean(
                row_index,
                column_index,
                boolean_value,
                formats["checkbox"],
            )
        return

    if column.value_type == "dropdown":
        worksheet.write_string(
            row_index,
            column_index,
            "" if value is None else str(value),
            formats["text"],
        )
        return

    if column.value_type == "amount" and value not in {None, ""}:
        try:
            worksheet.write_number(
                row_index,
                column_index,
                float(str(value).replace(",", ".")),
                formats["amount"],
            )
        except ValueError:
            worksheet.write(row_index, column_index, value, formats["text"])
        return

    if column.value_type == "integer" and value not in {None, ""}:
        try:
            worksheet.write_number(
                row_index,
                column_index,
                int(value),
                formats["integer"],
            )
        except (TypeError, ValueError):
            worksheet.write(row_index, column_index, value, formats["text"])
        return

    if column.value_type in {"inn", "text"}:
        worksheet.write_string(
            row_index,
            column_index,
            "" if value is None else str(value),
            formats["text"],
        )
        return

    worksheet.write(row_index, column_index, value, formats["text"])


def _write_sheet(
    workbook,
    workbook_path: Path,
    name: str,
    columns: tuple[WorkbookColumn, ...],
    rows: Sequence[WorkbookRow],
    formats: Mapping[str, object],
) -> None:
    """Write one filtered and frozen worksheet."""
    _validate_columns(columns)
    worksheet = workbook.add_worksheet(name)

    for column_index, column in enumerate(columns):
        worksheet.write(0, column_index, column.header, formats["header"])
        if column.comment:
            worksheet.write_comment(0, column_index, column.comment)
        worksheet.set_column(
            column_index,
            column_index,
            column.width,
            None,
            {"hidden": column.hidden},
        )

    declared = {column.key for column in columns}
    for row_index, raw_row in enumerate(rows, start=1):
        unexpected = set(raw_row).difference(declared)
        if unexpected:
            names = ", ".join(sorted(unexpected))
            raise ValueError(f"Workbook row contains undeclared columns: {names}")
        for column_index, column in enumerate(columns):
            _write_cell(
                worksheet,
                row_index,
                column_index,
                raw_row.get(column.key, ""),
                column,
                workbook_path,
                formats,
            )

    last_data_row = max(len(rows), 1)
    for column_index, column in enumerate(columns):
        if column.validation_options:
            worksheet.data_validation(
                1,
                column_index,
                last_data_row,
                column_index,
                {
                    "validate": "list",
                    "source": list(column.validation_options),
                    "error_title": "Invalid value",
                    "error_message": "Select a value from the list.",
                },
            )

    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, last_data_row, len(columns) - 1)
    worksheet.set_row(0, 34)


def write_task_workbook(
    documents: list[ExtractedDocument],
    path: Path,
    definition: TaskWorkbookDefinition,
    source_root: Path,
) -> None:
    """Write a task-oriented workbook for documents, items, and review issues."""
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(path)
    formats = {
        "header": workbook.add_format(
            {
                "bold": True,
                "bg_color": "#D9EAF7",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "text": workbook.add_format({"valign": "top", "text_wrap": True}),
        "link": workbook.add_format(
            {
                "font_color": "blue",
                "underline": 1,
                "valign": "top",
            }
        ),
        "amount": workbook.add_format(
            {"num_format": "#,##0.00", "valign": "top"}
        ),
        "integer": workbook.add_format(
            {"num_format": "0", "valign": "top"}
        ),
        "checkbox": workbook.add_format(
            {"align": "center", "valign": "vcenter"}
        ),
    }

    document_rows = [
        definition.build_document_row(document, source_root)
        for document in documents
    ]
    item_rows = [
        row
        for document in documents
        for row in definition.build_item_rows(document, source_root)
    ]
    review_rows = [
        row
        for document in documents
        for row in definition.build_review_rows(document, source_root)
    ]

    try:
        _write_sheet(
            workbook,
            path,
            "Documents",
            definition.document_columns,
            document_rows,
            formats,
        )
        _write_sheet(
            workbook,
            path,
            "Items",
            definition.item_columns,
            item_rows,
            formats,
        )
        _write_sheet(
            workbook,
            path,
            "Review",
            definition.review_columns,
            review_rows,
            formats,
        )

        metadata = dict(definition.build_metadata())
        metadata.setdefault("generated_at", datetime.now().isoformat(timespec="seconds"))
        metadata_sheet = workbook.add_worksheet("_metadata")
        metadata_sheet.hide()
        for row_index, (key, value) in enumerate(metadata.items()):
            metadata_sheet.write_string(row_index, 0, str(key))
            metadata_sheet.write_string(row_index, 1, "" if value is None else str(value))
    finally:
        workbook.close()
