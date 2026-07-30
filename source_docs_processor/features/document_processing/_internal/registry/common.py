"""Shared validation and row construction for registry writers."""

from __future__ import annotations

from pathlib import Path

from ...models import ExtractedDocument, RegistryValue
from ...registry_base import RegistryDefinition


def validate_registry_columns(columns: tuple[str, ...]) -> None:
    """Validate registry column names before serializing rows."""
    if not columns:
        raise ValueError("Registry definition must declare at least one column")
    if len(columns) != len(set(columns)):
        raise ValueError("Registry columns must be unique")
    if any(not column.strip() for column in columns):
        raise ValueError("Registry column names must not be empty")


def build_registry_row(
    document: ExtractedDocument,
    definition: RegistryDefinition,
    source_root: Path,
) -> dict[str, RegistryValue]:
    """Build and validate one registry row against the declared columns."""
    columns = tuple(definition.columns)
    raw_row = dict(definition.build_row(document, source_root))
    unexpected = set(raw_row).difference(columns)
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise ValueError(f"Registry row contains undeclared columns: {names}")
    return {column: raw_row.get(column, "") for column in columns}
