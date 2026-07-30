"""Complete registration definition for incoming purchase documents."""

from __future__ import annotations

from ...contracts import DocumentTypeDefinition
from ...document_processor import Processor
from ...registry.base import RegistryDefinition
from ...workflows.base import ProcessingWorkflow


DOCUMENT_TYPE = "incoming_purchase_documents"


def _create_processor() -> Processor:
    """Create the PDF/DOCX incoming-document recognizer lazily."""
    from .processor import IncomingPurchaseDocumentsProcessor

    return IncomingPurchaseDocumentsProcessor()


def _create_workflow() -> ProcessingWorkflow:
    """Create the incoming-document folder workflow lazily."""
    from .workflow import IncomingPurchaseDocumentsWorkflow

    return IncomingPurchaseDocumentsWorkflow()


def _create_registry_definition() -> RegistryDefinition:
    """Create the accountant task workbook definition lazily."""
    from .registry import IncomingPurchaseDocumentsRegistryDefinition

    return IncomingPurchaseDocumentsRegistryDefinition()


DEFINITION = DocumentTypeDefinition(
    document_type=DOCUMENT_TYPE,
    processor_factory=_create_processor,
    workflow_factory=_create_workflow,
    registry_definition_factory=_create_registry_definition,
)

__all__ = ["DEFINITION", "DOCUMENT_TYPE"]
