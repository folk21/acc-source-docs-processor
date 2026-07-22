"""Explicit document processor registry and factory."""

from __future__ import annotations

from collections.abc import Callable

from .document_processor import DocumentProcessor


DEFAULT_DOCUMENT_TYPE = "upd_invoices_status_1"


def _create_upd_invoices_status_1_processor() -> DocumentProcessor:
    """Import and create the UPD processor lazily."""
    from .upd_invoices_status_1.processor import UpdInvoicesStatus1Processor

    return UpdInvoicesStatus1Processor()


PROCESSOR_FACTORIES: dict[str, Callable[[], DocumentProcessor]] = {
    DEFAULT_DOCUMENT_TYPE: _create_upd_invoices_status_1_processor,
}
SUPPORTED_DOCUMENT_TYPES = tuple(PROCESSOR_FACTORIES)


def create_document_processor(document_type: str) -> DocumentProcessor:
    """Create a document processor selected by the CLI document type value.

    Adding a processor requires a new package plus one explicit entry in
    ``PROCESSOR_FACTORIES``. The registry remains intentionally small and local;
    plugin discovery can be added later if multiple external processors exist.
    """
    normalized = document_type.strip().lower()
    factory = PROCESSOR_FACTORIES.get(normalized)
    if factory is not None:
        return factory()
    supported = ", ".join(SUPPORTED_DOCUMENT_TYPES)
    raise ValueError(
        f"Unsupported document type: {document_type}. Supported values: {supported}"
    )
