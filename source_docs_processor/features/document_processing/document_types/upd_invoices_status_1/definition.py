"""Complete registration definition for scanned UPD status 1 documents."""

from __future__ import annotations

from ...document_type_definition import DocumentTypeDefinition
from ...processor_base import Processor
from ...registry_base import RegistryDefinition
from ...workflow_base import ProcessingWorkflow


DOCUMENT_TYPE = "upd_invoices_status_1"


def _create_processor() -> Processor:
    """Create the scan-oriented UPD recognizer lazily."""
    from .processor import UpdInvoicesStatus1Processor

    return UpdInvoicesStatus1Processor()


def _create_workflow() -> ProcessingWorkflow:
    """Create the UPD scan folder workflow lazily."""
    from .workflow import UpdInvoicesStatus1Workflow

    return UpdInvoicesStatus1Workflow()


def _create_registry_definition() -> RegistryDefinition:
    """Create the detailed UPD CSV definition lazily."""
    from .registry import UpdInvoicesStatus1RegistryDefinition

    return UpdInvoicesStatus1RegistryDefinition()


DEFINITION = DocumentTypeDefinition(
    document_type=DOCUMENT_TYPE,
    processor_factory=_create_processor,
    workflow_factory=_create_workflow,
    registry_definition_factory=_create_registry_definition,
)

__all__ = ["DEFINITION", "DOCUMENT_TYPE"]
