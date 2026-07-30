"""Processor protocols and reusable recognition defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np

from .models import ExtractedDocument


class Processor(Protocol):
    """Expose common identity shared by image and source-file processors."""

    document_type: str
    display_name: str


class DocumentProcessor(Processor, Protocol):
    """Recognize and extract one document type from a single image."""

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
        """Analyze one scan as a possible continuation page when supported."""
        ...

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True when the result is a recognized primary document."""
        ...

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Return True when the result is a recognized continuation page."""
        ...


class SourceFileProcessor(Processor, Protocol):
    """Recognize one structured or paged source file such as PDF or DOCX."""

    supported_extensions: frozenset[str]

    def analyze_source_file(
        self,
        source_path: Path,
        lang: str,
        deep_ocr: bool,
        debug_root: Path | None = None,
    ) -> ExtractedDocument:
        """Read and extract one source file without folder-level actions."""
        ...

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True when the source file is a recognized document."""
        ...


class BaseDocumentProcessor:
    """Provide recognition defaults for ordinary single-page image types."""

    document_type = "generic_document"
    display_name = "Generic document"

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
        """Return no continuation result for a single-page processor."""
        return None

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True for a recognized primary document of this processor type."""
        return doc.is_primary_document and doc.document_type == self.document_type

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Return True for a recognized continuation page of this processor type."""
        return (
            doc.is_recognized
            and doc.is_continuation_page
            and doc.document_type == self.document_type
        )


class BaseSourceFileProcessor:
    """Provide recognition defaults for structured source-file processors."""

    document_type = "generic_source_file"
    display_name = "Generic source file"
    supported_extensions: frozenset[str] = frozenset()

    def analyze_source_file(
        self,
        source_path: Path,
        lang: str,
        deep_ocr: bool,
        debug_root: Path | None = None,
    ) -> ExtractedDocument:
        """Analyze one source file."""
        raise NotImplementedError

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True for a recognized document of this processor type."""
        return doc.is_primary_document and doc.document_type == self.document_type


__all__ = [
    "BaseDocumentProcessor",
    "BaseSourceFileProcessor",
    "DocumentProcessor",
    "Processor",
    "SourceFileProcessor",
]
