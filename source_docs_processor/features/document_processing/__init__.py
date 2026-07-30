"""Public API for folder-based document processing."""

from .api import process_folder
from .document_types.catalog import DEFAULT_DOCUMENT_TYPE, SUPPORTED_DOCUMENT_TYPES
from .models import ExtractedDocument, ExtractedDocumentItem

__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "SUPPORTED_DOCUMENT_TYPES",
    "ExtractedDocument",
    "ExtractedDocumentItem",
    "process_folder",
]
