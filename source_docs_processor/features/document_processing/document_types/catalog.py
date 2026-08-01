"""Explicit catalog of complete document-processing definitions."""

from __future__ import annotations

from ..document_type_definition import DocumentTypeDefinition
from ..models import DocumentTypeMetadata
from .incoming_purchase_documents.definition import (
    DEFINITION as INCOMING_PURCHASE_DOCUMENTS_DEFINITION,
)
from .incoming_purchase_documents.definition import (
    DOCUMENT_TYPE as INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE,
)
from .npd_receipts.definition import DEFINITION as NPD_RECEIPTS_DEFINITION
from .npd_receipts.definition import DOCUMENT_TYPE as NPD_RECEIPT_DOCUMENT_TYPE
from .upd_invoices_status_1.definition import (
    DEFINITION as UPD_INVOICES_STATUS_1_DEFINITION,
)
from .upd_invoices_status_1.definition import (
    DOCUMENT_TYPE as DEFAULT_DOCUMENT_TYPE,
)


DOCUMENT_TYPE_DEFINITIONS: dict[str, DocumentTypeDefinition] = {
    definition.document_type: definition
    for definition in (
        UPD_INVOICES_STATUS_1_DEFINITION,
        NPD_RECEIPTS_DEFINITION,
        INCOMING_PURCHASE_DOCUMENTS_DEFINITION,
    )
}
SUPPORTED_DOCUMENT_TYPES = tuple(DOCUMENT_TYPE_DEFINITIONS)
DOCUMENT_TYPE_METADATA = tuple(
    definition.metadata for definition in DOCUMENT_TYPE_DEFINITIONS.values()
)


def get_document_type_definition(document_type: str) -> DocumentTypeDefinition:
    """Return the complete processing definition selected by an adapter."""
    normalized = document_type.strip().lower()
    definition = DOCUMENT_TYPE_DEFINITIONS.get(normalized)
    if definition is not None:
        return definition
    supported = ", ".join(SUPPORTED_DOCUMENT_TYPES)
    raise ValueError(
        f"Unsupported document type: {document_type}. Supported values: {supported}"
    )


def get_document_type_metadata(document_type: str) -> DocumentTypeMetadata:
    """Return UI-facing metadata for one registered document type."""
    return get_document_type_definition(document_type).metadata


__all__ = [
    "DEFAULT_DOCUMENT_TYPE",
    "DOCUMENT_TYPE_DEFINITIONS",
    "DOCUMENT_TYPE_METADATA",
    "INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE",
    "NPD_RECEIPT_DOCUMENT_TYPE",
    "SUPPORTED_DOCUMENT_TYPES",
    "get_document_type_definition",
    "get_document_type_metadata",
]
