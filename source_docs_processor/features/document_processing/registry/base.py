"""Registry definition contract for document-type-specific tabular output."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol

from ..models import ExtractedDocument, RegistryValue


class RegistryDefinition(Protocol):
    """Define registry columns and convert one extracted document into a row."""

    columns: tuple[str, ...]

    def build_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> Mapping[str, RegistryValue]:
        """Build one row using paths relative to the registry source root."""
        ...
