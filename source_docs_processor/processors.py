"""Document processor factory and shared processor protocol.

A document processor encapsulates all document-type-specific OCR and extraction
rules. The CLI and folder pipeline call only this factory-level abstraction, so
new document types can be added without mixing their recognition logic into the
main workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .models import ExtractedDocument


DEFAULT_DOCUMENT_TYPE = "upd_invoices_status_1"
SUPPORTED_DOCUMENT_TYPES = (DEFAULT_DOCUMENT_TYPE,)


class DocumentProcessor(Protocol):
    """Protocol implemented by every document-specific processor."""

    document_type: str
    display_name: str

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        deep_ocr: bool,
        auto_rotate: bool,
        debug_root: Path | None = None,
    ) -> tuple[ExtractedDocument, np.ndarray]:
        """Analyze one scan as a standalone document and return the best orientation."""
        ...

    def analyze_continuation_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        auto_rotate: bool,
    ) -> tuple[ExtractedDocument, np.ndarray] | None:
        """Analyze one scan as a possible continuation page of the previous document."""
        ...

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True when the extracted document matches this processor's primary type."""
        ...

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Return True when the extracted document is a continuation page."""
        ...


def create_document_processor(document_type: str) -> DocumentProcessor:
    """Create a document processor selected by the CLI document type parameter.

    The switch is intentionally explicit for now. Once multiple processors are
    added, this can evolve into plugin discovery or a registry populated by entry
    points, but a simple switch keeps the first generalization step transparent.
    """
    normalized = document_type.strip().lower()
    if normalized == DEFAULT_DOCUMENT_TYPE:
        from .upd_invoices_status_1.processor import UpdInvoicesStatus1Processor

        return UpdInvoicesStatus1Processor()
    supported = ", ".join(SUPPORTED_DOCUMENT_TYPES)
    raise ValueError(f"Unsupported document type: {document_type}. Supported values: {supported}")
