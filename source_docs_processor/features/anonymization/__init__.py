"""Public API for local document anonymization."""

from .api import (
    DEFAULT_CONFIG_PATH,
    SUPPORTED_EXTENSIONS,
    AnonymizationConfig,
    AnonymizationProgress,
    AnonymizationSummary,
    AnonymizedFileResult,
    ConfiguredTextAnalyzer,
    DetectedEntity,
    PresidioTextAnalyzer,
    ReplacementRule,
    TextEntityAnalyzer,
    anonymize_folder,
    create_presidio_analyzer,
    load_anonymization_config,
    mask_text,
)

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
