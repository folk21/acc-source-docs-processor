"""Framework contract for composing registered document implementations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .models import DocumentTypeMetadata
from .processor_base import Processor
from .registry_base import RegistryDefinition
from .workflow_base import ProcessingWorkflow


@dataclass(frozen=True)
class DocumentTypeDefinition:
    """Bundle recognition, folder workflow, and registry behavior for one type."""

    document_type: str
    metadata: DocumentTypeMetadata
    processor_factory: Callable[[], Processor]
    workflow_factory: Callable[[], ProcessingWorkflow]
    registry_definition_factory: Callable[[], RegistryDefinition]

    def __post_init__(self) -> None:
        """Validate that catalog metadata uses the registered identifier."""
        if self.metadata.identifier != self.document_type:
            raise ValueError(
                "Document type metadata identifier does not match its definition: "
                f"{self.metadata.identifier} != {self.document_type}"
            )

    def create_processor(self) -> Processor:
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


__all__ = ["DocumentTypeDefinition"]
