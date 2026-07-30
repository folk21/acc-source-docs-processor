"""Backward-compatible processor factory built on document type definitions."""

from __future__ import annotations

from .document_processor import Processor
from .document_types.catalog import (
    DEFAULT_DOCUMENT_TYPE,
    SUPPORTED_DOCUMENT_TYPES,
    get_document_type_definition,
)


def create_document_processor(document_type: str) -> Processor:
    """Create only the recognizer from a complete document type definition."""
    return get_document_type_definition(document_type).create_processor()


__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "SUPPORTED_DOCUMENT_TYPES",
    "create_document_processor",
]
