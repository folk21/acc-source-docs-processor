"""Local Microsoft Presidio-based document anonymization."""

from .models import (
    AnonymizationSummary,
    AnonymizedFileResult,
    DetectedEntity,
    TextEntityAnalyzer,
)
from .text import PresidioTextAnalyzer, create_presidio_analyzer, mask_text
from .workflow import SUPPORTED_EXTENSIONS, anonymize_folder

__all__ = [
    "AnonymizationSummary",
    "AnonymizedFileResult",
    "DetectedEntity",
    "PresidioTextAnalyzer",
    "SUPPORTED_EXTENSIONS",
    "TextEntityAnalyzer",
    "anonymize_folder",
    "create_presidio_analyzer",
    "mask_text",
]
