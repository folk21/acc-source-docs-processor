"""Document-processing feature public API."""

from .api import process_folder
from .contracts import DocumentTypeDefinition
from .document_types.catalog import (
    DEFAULT_DOCUMENT_TYPE,
    DOCUMENT_TYPE_DEFINITIONS,
    INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE,
    NPD_RECEIPT_DOCUMENT_TYPE,
    SUPPORTED_DOCUMENT_TYPES,
    get_document_type_definition,
)

__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "DOCUMENT_TYPE_DEFINITIONS",
    "DocumentTypeDefinition",
    "INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE",
    "NPD_RECEIPT_DOCUMENT_TYPE",
    "SUPPORTED_DOCUMENT_TYPES",
    "get_document_type_definition",
    "process_folder",
]
