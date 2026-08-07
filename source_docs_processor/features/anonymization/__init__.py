"""Public API for local document anonymization."""

from .api import (
    DEFAULT_CONFIG_PATH,
    ENTITY_DETECTION_MODES,
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
    "ENTITY_DETECTION_MODES",
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
