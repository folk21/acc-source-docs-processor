"""Public API for folder-based document processing."""

from .api import process_folder
from .document_types.catalog import (
    DEFAULT_DOCUMENT_TYPE,
    DOCUMENT_TYPE_METADATA,
    SUPPORTED_DOCUMENT_TYPES,
    get_document_type_metadata,
)
from .models import (
    DocumentTypeMetadata,
    ExtractedDocument,
    ExtractedDocumentItem,
    ProcessingProgress,
    ProcessingProgressCallback,
    ProcessingProgressEvent,
    ProcessingSummary,
)

__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "DOCUMENT_TYPE_METADATA",
    "SUPPORTED_DOCUMENT_TYPES",
    "DocumentTypeMetadata",
    "ExtractedDocument",
    "ExtractedDocumentItem",
    "ProcessingProgress",
    "ProcessingProgressCallback",
    "ProcessingProgressEvent",
    "ProcessingSummary",
    "get_document_type_metadata",
    "process_folder",
]
