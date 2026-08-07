"""Tests for the UI adapter around the public anonymization API."""

from __future__ import annotations

from pathlib import Path

import pytest

from source_docs_processor.features.anonymization import (
    AnonymizationSummary,
    AnonymizedFileResult,
)
from source_docs_processor.ui.anonymization import (
    build_result_rows,
    resolve_output_options,
)


def test_output_modes_map_to_public_api_options() -> None:
    """Verify UI choices preserve all supported anonymization output variants.

    Protected risk: a label-only UI change must not accidentally enable dual
    output, layout reconstruction, or format conversion with the wrong options.
    """
    assert resolve_output_options("source", True) == (None, None, False)
    assert resolve_output_options("docx", False) == ("docx", None, False)
    assert resolve_output_options("docx", True) == ("docx", "preserve", False)
    assert resolve_output_options("docx_and_source", True) == (
        "docx",
        "preserve",
        True,
    )

    with pytest.raises(ValueError, match="Unsupported"):
        resolve_output_options("unknown", False)  # type: ignore[arg-type]


def test_result_rows_use_relative_paths_and_privacy_safe_counts(tmp_path: Path) -> None:
    """Verify result tables avoid exposing machine-specific absolute paths.

    Protected risk: a local UI table copied into a report must not reveal the
    accountant's full filesystem layout.
    """
    source_root = tmp_path / "private-source"
    output_root = tmp_path / "private-output"
    source_path = source_root / "nested" / "document.pdf"
    output_path = output_root / "nested" / "document.pdf"
    summary = AnonymizationSummary(
        source_root=source_root,
        output_root=output_root,
        results=[
            AnonymizedFileResult(
                source_path=source_path,
                destination_path=output_path,
                detected_entities=3,
            )
        ],
    )

    rows = build_result_rows(summary)

    assert len(rows) == 1
    assert rows[0].source_file == "nested/document.pdf"
    assert rows[0].output_files == "nested/document.pdf"
    assert rows[0].succeeded is True
    assert rows[0].detected_entities == 3
    assert str(tmp_path) not in rows[0].source_file
    assert str(tmp_path) not in rows[0].output_files


def test_execute_anonymization_uses_public_api_and_skips_presidio_for_configured_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify configured-only UI runs do not load the heavy Presidio model.

    Protected risk: the Streamlit adapter must preserve the feature's fast
    configured-only behavior and pass output options through the public API.
    """
    from source_docs_processor.ui import anonymization as ui_anonymization

    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    config_path = tmp_path / "anonymization.ini"
    config_path.write_text(
        "[anonymization]\nincluded = Учебная организация\n",
        encoding="utf-8",
    )
    captured = {}

    def fake_anonymize_folder(**kwargs):
        captured.update(kwargs)
        return AnonymizationSummary(source_root=source, output_root=output)

    def forbidden_analyzer_provider():
        raise AssertionError("Presidio must not load in configured-only mode")

    monkeypatch.setattr(
        ui_anonymization,
        "anonymize_folder",
        fake_anonymize_folder,
    )
    request = ui_anonymization.AnonymizationRequest(
        source_dir=source,
        output_dir=output,
        config_path=config_path,
        output_mode="docx_and_source",
        preserve_layout=True,
        clear_output=True,
    )

    summary = ui_anonymization.execute_anonymization(
        request,
        analyzer_provider=forbidden_analyzer_provider,
    )

    assert summary.source_root == source
    assert captured["source_dir"] == source
    assert captured["output_dir"] == output
    assert captured["output_document_type"] == "docx"
    assert captured["output_layout"] == "preserve"
    assert captured["also_output_source_format"] is True
    assert captured["clear_output"] is True


def test_execute_anonymization_loads_presidio_for_combined_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify the UI uses automatic detection when combined mode requests it.

    Protected risk: CLI and Streamlit must derive analyzer loading from the same
    configuration mode instead of diverging between adapters.
    """
    from source_docs_processor.ui import anonymization as ui_anonymization

    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    config_path = tmp_path / "anonymization.ini"
    config_path.write_text(
        "[anonymization]\n"
        "entityDetectionMode = combined\n"
        "included = Учебная организация\n",
        encoding="utf-8",
    )
    captured = {}
    analyzer_calls = 0

    class EmptyAnalyzer:
        """Return no automatic entities for deterministic UI wiring coverage."""

        def analyze(self, text: str):
            """Return no entities."""
            return []

    def analyzer_provider():
        nonlocal analyzer_calls
        analyzer_calls += 1
        return EmptyAnalyzer()

    def fake_anonymize_folder(**kwargs):
        captured.update(kwargs)
        return AnonymizationSummary(source_root=source, output_root=output)

    monkeypatch.setattr(ui_anonymization, "anonymize_folder", fake_anonymize_folder)
    request = ui_anonymization.AnonymizationRequest(
        source_dir=source,
        output_dir=output,
        config_path=config_path,
    )

    ui_anonymization.execute_anonymization(
        request,
        analyzer_provider=analyzer_provider,
    )

    assert analyzer_calls == 1
    assert captured["analyzer"].analyze("Учебная организация")
