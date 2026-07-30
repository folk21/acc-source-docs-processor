"""Complete registration definition for scanned NPD receipts."""

from __future__ import annotations

from ...document_type_definition import DocumentTypeDefinition
from ...processor_base import Processor
from ...registry_base import RegistryDefinition
from ...workflow_base import ProcessingWorkflow


DOCUMENT_TYPE = "npd_receipts"


def _create_processor() -> Processor:
    """Create the NPD receipt recognizer lazily."""
    from .processor import NpdReceiptProcessor

    return NpdReceiptProcessor()


def _create_workflow() -> ProcessingWorkflow:
    """Create the NPD receipt folder workflow lazily."""
    from .workflow import NpdReceiptRegistryWorkflow

    return NpdReceiptRegistryWorkflow()


def _create_registry_definition() -> RegistryDefinition:
    """Create the compact NPD workbook definition lazily."""
    from .registry import NpdReceiptRegistryDefinition

    return NpdReceiptRegistryDefinition()


DEFINITION = DocumentTypeDefinition(
    document_type=DOCUMENT_TYPE,
    processor_factory=_create_processor,
    workflow_factory=_create_workflow,
    registry_definition_factory=_create_registry_definition,
)

__all__ = ["DEFINITION", "DOCUMENT_TYPE"]
