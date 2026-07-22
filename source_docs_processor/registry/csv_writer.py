"""Generic CSV writer driven by a document-type-specific registry definition."""

from __future__ import annotations

import csv
from pathlib import Path

from ..models import ExtractedDocument
from .base import RegistryDefinition


def _validate_columns(columns: tuple[str, ...]) -> None:
    """Validate registry column names before creating a CSV file."""
    if not columns:
        raise ValueError("Registry definition must declare at least one column")
    if len(columns) != len(set(columns)):
        raise ValueError("Registry columns must be unique")
    if any(not column.strip() for column in columns):
        raise ValueError("Registry column names must not be empty")


def write_csv_registry(
    documents: list[ExtractedDocument],
    path: Path,
    definition: RegistryDefinition,
    source_root: Path,
) -> None:
    """Write an Excel-friendly semicolon-separated registry file."""
    columns = tuple(definition.columns)
    _validate_columns(columns)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=";")
        writer.writeheader()
        for document in documents:
            raw_row = dict(definition.build_row(document, source_root))
            unexpected = set(raw_row).difference(columns)
            if unexpected:
                names = ", ".join(sorted(unexpected))
                raise ValueError(f"Registry row contains undeclared columns: {names}")
            writer.writerow({column: raw_row.get(column, "") for column in columns})
