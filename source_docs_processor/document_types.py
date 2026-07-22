"""Explicit registry of complete document-processing definitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .document_processor import DocumentProcessor
from .registry.base import RegistryDefinition
from .workflows.base import ProcessingWorkflow


DEFAULT_DOCUMENT_TYPE = "upd_invoices_status_1"


@dataclass(frozen=True)
class DocumentTypeDefinition:
    """Bundle recognition, folder workflow, and registry behavior for one type."""

    document_type: str
    processor_factory: Callable[[], DocumentProcessor]
    workflow_factory: Callable[[], ProcessingWorkflow]
    registry_definition_factory: Callable[[], RegistryDefinition]

    def create_processor(self) -> DocumentProcessor:
        """Create the file-level recognizer configured for this document type."""
        processor = self.processor_factory()
        if processor.document_type != self.document_type:
            raise ValueError(
                "Processor document type does not match its registered definition: "
                f"{processor.document_type} != {self.document_type}"
            )
        return processor

    def create_workflow(self) -> ProcessingWorkflow:
        """Create the folder-level workflow configured for this document type."""
        return self.workflow_factory()

    def create_registry_definition(self) -> RegistryDefinition:
        """Create the registry schema configured for this document type."""
        return self.registry_definition_factory()


def _create_upd_processor() -> DocumentProcessor:
    """Import and create the UPD processor lazily."""
    from .upd_invoices_status_1.processor import UpdInvoicesStatus1Processor

    return UpdInvoicesStatus1Processor()


def _create_upd_workflow() -> ProcessingWorkflow:
    """Import and create the UPD folder workflow lazily."""
    from .upd_invoices_status_1.workflow import UpdInvoicesStatus1Workflow

    return UpdInvoicesStatus1Workflow()


def _create_upd_registry_definition() -> RegistryDefinition:
    """Import and create the UPD registry definition lazily."""
    from .upd_invoices_status_1.registry import (
        UpdInvoicesStatus1RegistryDefinition,
    )

    return UpdInvoicesStatus1RegistryDefinition()


DOCUMENT_TYPE_DEFINITIONS: dict[str, DocumentTypeDefinition] = {
    DEFAULT_DOCUMENT_TYPE: DocumentTypeDefinition(
        document_type=DEFAULT_DOCUMENT_TYPE,
        processor_factory=_create_upd_processor,
        workflow_factory=_create_upd_workflow,
        registry_definition_factory=_create_upd_registry_definition,
    ),
}
SUPPORTED_DOCUMENT_TYPES = tuple(DOCUMENT_TYPE_DEFINITIONS)


def get_document_type_definition(document_type: str) -> DocumentTypeDefinition:
    """Return the complete processing definition selected by the CLI value."""
    normalized = document_type.strip().lower()
    definition = DOCUMENT_TYPE_DEFINITIONS.get(normalized)
    if definition is not None:
        return definition
    supported = ", ".join(SUPPORTED_DOCUMENT_TYPES)
    raise ValueError(
        f"Unsupported document type: {document_type}. Supported values: {supported}"
    )
