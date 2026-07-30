"""Document processing feature and its registered document types."""

from .catalog import (
    DEFAULT_DOCUMENT_TYPE,
    DOCUMENT_TYPE_DEFINITIONS,
    INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE,
    NPD_RECEIPT_DOCUMENT_TYPE,
    SUPPORTED_DOCUMENT_TYPES,
    DocumentTypeDefinition,
    get_document_type_definition,
)

__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "DOCUMENT_TYPE_DEFINITIONS",
    "INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE",
    "NPD_RECEIPT_DOCUMENT_TYPE",
    "SUPPORTED_DOCUMENT_TYPES",
    "DocumentTypeDefinition",
    "get_document_type_definition",
]
