"""Regression tests for the supported anonymization package API."""

from dataclasses import fields
from inspect import Parameter, signature
from pathlib import Path

from source_docs_processor.features import anonymization
from source_docs_processor.features.anonymization import api


_EXPECTED_PUBLIC_NAMES = (
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
)


def _field_names(model: type[object]) -> tuple[str, ...]:
    """Return dataclass field names in their public constructor order."""
    return tuple(field.name for field in fields(model))


def test_anonymization_package_exports_exact_supported_api() -> None:
    """Verify the package facade exposes only the documented API symbols.

    Protected risk: accidentally re-exporting an `_internal` helper would turn an
    implementation detail into a compatibility burden for future refactoring.
    """
    assert tuple(anonymization.__all__) == _EXPECTED_PUBLIC_NAMES
    assert tuple(api.__all__) == _EXPECTED_PUBLIC_NAMES

    for name in _EXPECTED_PUBLIC_NAMES:
        assert getattr(anonymization, name) is getattr(api, name)


def test_anonymization_public_constants_remain_stable() -> None:
    """Verify supported input types and the default config location stay stable.

    Protected risk: silent constant changes would alter CLI and embedded-call
    behavior without changing a function signature.
    """
    assert anonymization.DEFAULT_CONFIG_PATH == Path("config/anonymization.ini")
    assert anonymization.ENTITY_DETECTION_MODES == (
        "automatic",
        "configured",
        "combined",
        "disabled",
    )
    assert anonymization.SUPPORTED_EXTENSIONS == frozenset(
        {".bmp", ".docx", ".jpeg", ".jpg", ".pdf", ".png", ".tif", ".tiff", ".txt", ".xlsx"}
    )


def test_anonymize_folder_signature_is_stable() -> None:
    """Verify embedded callers retain the supported anonymization arguments.

    Protected risk: reordering, removing, or exposing implementation parameters
    would break scripts that call the feature programmatically.
    """
    parameters = signature(anonymization.anonymize_folder).parameters

    assert tuple(parameters) == (
        "source_dir",
        "output_dir",
        "analyzer",
        "lang",
        "config",
        "progress_callback",
        "output_document_type",
        "output_layout",
        "also_output_source_format",
        "clear_output",
    )
    assert parameters["source_dir"].default is Parameter.empty
    assert parameters["output_dir"].default is Parameter.empty
    assert parameters["analyzer"].default is Parameter.empty
    assert parameters["lang"].default == "rus+eng"
    assert parameters["config"].default == anonymization.AnonymizationConfig()
    assert parameters["progress_callback"].default is None
    assert parameters["output_document_type"].default is None
    assert parameters["output_layout"].default is None
    assert parameters["also_output_source_format"].default is False
    assert parameters["clear_output"].default is False


def test_anonymization_helper_signatures_are_stable() -> None:
    """Verify supported analyzer, config, and text helpers keep narrow contracts.

    Protected risk: adding internal workflow options to these helpers would blur
    the package API and couple simple callers to format-specific implementation.
    """
    assert tuple(signature(anonymization.create_presidio_analyzer).parameters) == (
        "model_name",
    )
    assert (
        signature(anonymization.create_presidio_analyzer)
        .parameters["model_name"]
        .default
        == "ru_core_news_sm"
    )
    assert tuple(signature(anonymization.load_anonymization_config).parameters) == (
        "path",
    )
    assert tuple(signature(anonymization.mask_text).parameters) == (
        "text",
        "analyzer",
    )


def test_anonymization_public_model_fields_are_stable() -> None:
    """Verify result and configuration models preserve their constructor fields.

    Protected risk: changing public dataclass fields implicitly changes keyword
    construction, serialization, and result inspection for embedded callers.
    """
    assert _field_names(anonymization.ReplacementRule) == ("source", "replacement")
    assert _field_names(anonymization.AnonymizationConfig) == (
        "entity_detection_mode",
        "excluded",
        "included",
        "included_and_replaced",
        "included_paragraphs",
        "included_fuzzy",
        "included_fuzzy_max_errors",
    )
    assert _field_names(anonymization.DetectedEntity) == (
        "start",
        "end",
        "entity_type",
        "score",
        "replacement",
    )
    assert _field_names(anonymization.AnonymizedFileResult) == (
        "source_path",
        "destination_path",
        "additional_destination_paths",
        "detected_entities",
        "error",
    )
    assert _field_names(anonymization.AnonymizationProgress) == (
        "event",
        "source_path",
        "file_index",
        "file_count",
        "unit_name",
        "unit_index",
        "unit_count",
        "detected_entities",
        "output_count",
        "error",
    )
    assert _field_names(anonymization.AnonymizationSummary) == (
        "source_root",
        "output_root",
        "results",
    )
