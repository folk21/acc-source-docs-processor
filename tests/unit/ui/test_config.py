"""Tests for language-specific Streamlit UI configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from source_docs_processor.ui.config import (
    DEFAULT_UI_LANGUAGE,
    discover_ui_configs,
    load_ui_config,
    parse_launch_options,
    resolve_initial_language,
)


_REQUIRED_TEXTS = {
    "app": {
        "page_title",
        "language_label",
        "title",
        "description",
        "operation_label",
        "operation_help",
        "no_supported_operations",
        "unsupported_operations",
    },
    "defaults": {
        "source_path",
        "output_path",
        "anonymization_config_path",
        "ocr_language",
    },
    "anonymize": {
        "source_label",
        "source_help",
        "output_label",
        "output_help",
        "config_label",
        "config_help",
        "entity_detection_mode_label",
        "entity_detection_mode_help",
        "entity_detection_mode_automatic",
        "entity_detection_mode_configured",
        "entity_detection_mode_combined",
        "entity_detection_mode_disabled",
        "ocr_language_label",
        "ocr_language_help",
        "output_mode_label",
        "output_mode_help",
        "output_mode_source",
        "output_mode_docx",
        "output_mode_docx_and_source",
        "preserve_layout_label",
        "preserve_layout_help",
        "clear_output_label",
        "clear_output_help",
        "run_button",
        "running_status",
        "completed_status",
        "completed_with_errors",
        "failed_status",
        "unexpected_error",
        "progress_file_started",
        "progress_unit_started",
        "progress_file_finished",
        "progress_file_failed",
        "results_title",
        "metric_succeeded",
        "metric_failed",
        "metric_generated",
        "metric_detected",
        "column_source",
        "column_status",
        "column_outputs",
        "column_detected",
        "column_error",
        "status_success",
        "status_failed",
    },
    "process": {
        "source_label",
        "source_help",
        "output_label",
        "output_help",
        "target_dir_name_label",
        "target_dir_name_help",
        "ocr_language_label",
        "ocr_language_help",
        "deep_ocr_label",
        "deep_ocr_help",
        "auto_rotate_label",
        "auto_rotate_help",
        "debug_crops_label",
        "debug_crops_help",
        "dry_run_label",
        "dry_run_help",
        "supported_extensions",
        "run_button",
        "running_status",
        "completed_status",
        "completed_with_errors",
        "failed_status",
        "unexpected_error",
        "progress_scan_started",
        "progress_file_started",
        "progress_file_finished",
        "progress_file_failed",
        "progress_registry_written",
        "progress_run_finished",
        "results_title",
        "artifacts_title",
        "metric_processed",
        "metric_recognized",
        "metric_errors",
        "metric_generated",
        "column_source",
        "column_status",
        "column_output",
        "column_warnings",
        "column_error",
        "column_artifact_type",
        "column_artifact_path",
        "status_recognized",
        "status_unrecognized",
        "status_failed",
        "artifact_document",
        "artifact_registry",
        "artifact_report",
    },
    "validation": {
        "source_missing",
        "source_not_directory",
        "output_not_directory",
        "source_equals_output",
        "unsafe_clear_output",
        "config_missing",
        "config_not_file",
    },
}


def test_localized_configs_define_the_same_supported_ui_contract() -> None:
    """Verify Russian and English files provide the complete shared UI schema.

    Protected risk: a language switch must not fail because one locale omitted a
    widget label, progress message, validation message, or supported operation.
    """
    configs = discover_ui_configs()

    assert set(configs) == {"en", "ru"}
    expected_operations = (
        "anonymize",
        "process_npd_receipts",
        "process_incoming_purchase_documents",
        "process_upd_invoices_status_1",
    )
    assert configs["ru"].operation_ids == expected_operations
    assert configs["en"].operation_ids == expected_operations
    for config in configs.values():
        for operation_id in expected_operations:
            assert config.operation_title(operation_id)
            assert config.operation_description(operation_id)
        for operation_id in expected_operations[1:]:
            assert config.text(f"operation.{operation_id}", "source_path")
            assert config.text(f"operation.{operation_id}", "output_path")
        for section, keys in _REQUIRED_TEXTS.items():
            for key in keys:
                assert config.text(section, key)


def test_launch_language_defaults_to_russian_and_accepts_script_arguments() -> None:
    """Verify Streamlit launch arguments select a locale without CLI coupling.

    Protected risk: the UI must default to Russian while still supporting the
    documented ``-- --lang en`` script argument syntax.
    """
    assert parse_launch_options([]).language == DEFAULT_UI_LANGUAGE
    assert parse_launch_options(["--lang", "EN"]).language == "en"
    assert parse_launch_options(["--unknown", "value"]).language == "ru"


def test_unknown_launch_language_falls_back_to_russian() -> None:
    """Verify an unavailable launch locale cannot prevent the UI from starting.

    Protected risk: a typo in the optional launch argument should preserve a
    usable Russian interface instead of raising before Streamlit renders.
    """
    configs = discover_ui_configs()

    assert resolve_initial_language("de", configs) == "ru"
    assert resolve_initial_language("en", configs) == "en"


def test_config_file_suffix_must_match_its_locale_code(tmp_path: Path) -> None:
    """Verify locale identity is tied to the required language file suffix.

    Protected risk: silently loading Russian content from an English-named file
    would make language discovery and selection ambiguous.
    """
    path = tmp_path / "ui_en.ini"
    path.write_text(
        """
[locale]
code = ru
name = Russian
[operations]
ids = anonymize
[operation.anonymize]
title = Anonymize
description = Description
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must match"):
        load_ui_config(path)
