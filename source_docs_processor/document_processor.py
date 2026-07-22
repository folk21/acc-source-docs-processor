"""Document processor protocol and reusable default behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol

import numpy as np

from .models import ExtractedDocument, RegistryValue


class DocumentProcessor(Protocol):
    """Interface implemented by every document-specific processor."""

    document_type: str
    display_name: str
    default_target_dir_name: str
    supports_continuation_pages: bool
    registry_extra_columns: tuple[str, ...]

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        deep_ocr: bool,
        auto_rotate: bool,
        debug_root: Path | None = None,
    ) -> tuple[ExtractedDocument, np.ndarray]:
        """Analyze one scan as a standalone document and return its best orientation."""
        ...

    def analyze_continuation_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        auto_rotate: bool,
    ) -> tuple[ExtractedDocument, np.ndarray] | None:
        """Analyze one scan as a possible continuation page."""
        ...

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True when the result is a recognized primary document."""
        ...

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Return True when the result is a recognized continuation page."""
        ...

    def prepare_continuation_document(
        self,
        doc: ExtractedDocument,
        previous_doc: ExtractedDocument,
        page_number: int,
    ) -> None:
        """Attach inherited metadata and page numbering to a continuation page."""
        ...

    def build_output_filename_stem(self, doc: ExtractedDocument) -> str:
        """Build a document-type-specific output filename stem."""
        ...

    def registry_extra_values(self, doc: ExtractedDocument) -> Mapping[str, RegistryValue]:
        """Return values for the processor-specific registry columns."""
        ...


class BaseDocumentProcessor:
    """Provide simple defaults so new processors implement only real differences.

    A single-page document processor usually needs to implement only
    ``analyze_image_orientations()`` and configure its class attributes. It can
    override filename generation and registry columns when the document type has
    a business-specific output format.
    """

    document_type = "generic_document"
    display_name = "Generic document"
    default_target_dir_name = "processed_documents"
    supports_continuation_pages = False
    registry_extra_columns: tuple[str, ...] = ()

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        deep_ocr: bool,
        auto_rotate: bool,
        debug_root: Path | None = None,
    ) -> tuple[ExtractedDocument, np.ndarray]:
        """Analyze one scan as a standalone document."""
        raise NotImplementedError

    def analyze_continuation_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        auto_rotate: bool,
    ) -> tuple[ExtractedDocument, np.ndarray] | None:
        """Return no continuation result for single-page document types."""
        return None

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True for a recognized primary document of this processor type."""
        return (
            doc.is_primary_document
            and doc.document_type == self.document_type
        )

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Return True for a recognized continuation page of this processor type."""
        return (
            doc.is_recognized
            and doc.is_continuation_page
            and doc.document_type == self.document_type
        )

    def prepare_continuation_document(
        self,
        doc: ExtractedDocument,
        previous_doc: ExtractedDocument,
        page_number: int,
    ) -> None:
        """Inherit common metadata and set the continuation page number."""
        doc.inherit_common_metadata(previous_doc)
        doc.is_continuation_page = True
        doc.continuation_page_number = page_number
        doc.continued_from = (
            previous_doc.destination_path.name
            if previous_doc.destination_path
            else previous_doc.source_path.name
        )

    def build_primary_filename_stem(self, doc: ExtractedDocument) -> str:
        """Build a conservative generic filename for a primary document."""
        prefix = doc.document_type or self.document_type or "document"
        number = doc.document_number or "without_number"
        if doc.document_date:
            return f"{prefix}_{number}_{doc.document_date}"
        return f"{prefix}_{number}"

    def build_output_filename_stem(self, doc: ExtractedDocument) -> str:
        """Build a primary or continuation filename stem."""
        stem = self.build_primary_filename_stem(doc)
        if doc.is_continuation_page:
            page_number = doc.continuation_page_number or 2
            return f"{stem}_page_{page_number}"
        return stem

    def registry_extra_values(self, doc: ExtractedDocument) -> Mapping[str, RegistryValue]:
        """Read declared processor-specific values from ``extra_fields``."""
        return {
            column: doc.extra_fields.get(column)
            for column in self.registry_extra_columns
        }
