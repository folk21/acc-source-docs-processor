"""Processor package for electronic UPD status 1 PDF and DOCX files."""

from .processor import IncomingPurchaseDocumentsProcessor
from .registry import IncomingPurchaseDocumentsRegistryDefinition
from .workflow import IncomingPurchaseDocumentsWorkflow

__all__ = [
    "IncomingPurchaseDocumentsProcessor",
    "IncomingPurchaseDocumentsRegistryDefinition",
    "IncomingPurchaseDocumentsWorkflow",
]
