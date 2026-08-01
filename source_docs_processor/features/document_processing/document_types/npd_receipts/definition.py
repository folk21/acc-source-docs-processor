"""Complete registration definition for scanned NPD receipts."""

from __future__ import annotations

from ...document_type_definition import DocumentTypeDefinition
from ...models import DocumentTypeMetadata
from ...processor_base import Processor
from ...registry_base import RegistryDefinition
from ...workflow_base import ProcessingWorkflow


DOCUMENT_TYPE = "npd_receipts"


METADATA = DocumentTypeMetadata(
    identifier=DOCUMENT_TYPE,
    display_name="Self-employed tax receipts",
    description="Recognize scanned NPD receipts issued by self-employed persons.",
    supported_extensions=(".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"),
    supports_deep_ocr=True,
    supports_auto_rotate=True,
    supports_debug_crops=True,
)


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
    metadata=METADATA,
    processor_factory=_create_processor,
    workflow_factory=_create_workflow,
    registry_definition_factory=_create_registry_definition,
)

__all__ = ["DEFINITION", "DOCUMENT_TYPE", "METADATA"]
