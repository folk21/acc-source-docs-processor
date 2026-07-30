"""Local Microsoft Presidio-based document anonymization."""

from .config import (
    DEFAULT_CONFIG_PATH,
    AnonymizationConfig,
    ConfiguredTextAnalyzer,
    ReplacementRule,
    load_anonymization_config,
)
from .models import (
    AnonymizationProgress,
    AnonymizationSummary,
    AnonymizedFileResult,
    DetectedEntity,
    TextEntityAnalyzer,
)
from .text import PresidioTextAnalyzer, create_presidio_analyzer, mask_text
from .workflow import SUPPORTED_EXTENSIONS, anonymize_folder

__all__ = [
    "AnonymizationConfig",
    "AnonymizationProgress",
    "AnonymizationSummary",
    "AnonymizedFileResult",
    "ConfiguredTextAnalyzer",
    "DEFAULT_CONFIG_PATH",
    "DetectedEntity",
    "PresidioTextAnalyzer",
    "ReplacementRule",
    "SUPPORTED_EXTENSIONS",
    "TextEntityAnalyzer",
    "anonymize_folder",
    "create_presidio_analyzer",
    "load_anonymization_config",
    "mask_text",
]
