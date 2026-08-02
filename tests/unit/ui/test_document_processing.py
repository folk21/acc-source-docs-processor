"""Tests for the UI adapter around the public document-processing API."""

from __future__ import annotations

from pathlib import Path

from source_docs_processor.features.document_processing import (
    ExtractedDocument,
    ProcessingSummary,
)
from source_docs_processor.ui.document_processing import (
    ProcessingRequest,
    build_generated_artifact_rows,
    build_processing_result_rows,
    execute_processing,
    get_processing_metadata,
)


def test_execute_processing_forwards_ui_values_to_the_public_api(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify the UI invokes the public API without CLI or internal imports.

    Protected risk: adding document-processing screens must not duplicate workflow
    behavior or silently drop capability-specific options selected by the user.
    """
    from source_docs_processor.ui import document_processing as ui_processing

    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    captured = {}

    def fake_process_folder(**kwargs):
        captured.update(kwargs)
        return ProcessingSummary(
            source_root=source,
            output_root=output,
            document_type="npd_receipts",
            found_documents=[],
            all_documents=[],
        )

    monkeypatch.setattr(ui_processing, "process_folder", fake_process_folder)
    request = ProcessingRequest(
        source_dir=source,
        output_dir=output,
        document_type="npd_receipts",
        lang="rus+eng",
        target_dir_name="batch-1",
        dry_run=True,
        deep_ocr=True,
        auto_rotate=False,
        debug_crops=True,
    )

    summary = execute_processing(request)

    assert summary.document_type == "npd_receipts"
    assert captured == {
        "source_dir": source,
        "output_dir": output,
        "lang": "rus+eng",
        "target_dir_name": "batch-1",
        "dry_run": True,
        "deep_ocr": True,
        "auto_rotate": False,
        "debug_crops": True,
        "document_type": "npd_receipts",
        "progress_callback": None,
    }


def test_processing_rows_and_artifacts_use_relative_paths(tmp_path: Path) -> None:
    """Verify processing tables avoid exposing machine-specific absolute paths.

    Protected risk: UI results may be copied into working notes and must not leak
    the accountant's complete local directory layout.
    """
    source = tmp_path / "private-source"
    output = tmp_path / "private-output"
    document = ExtractedDocument(
        source_path=source / "nested" / "receipt.png",
        is_recognized=True,
        destination_path=output / "nested" / "renamed.png",
        warnings=["manual_review"],
    )
    registry = output / "npd_receipts_registry.xlsx"
    report = output / "run_report.txt"
    summary = ProcessingSummary(
        source_root=source,
        output_root=output,
        document_type="npd_receipts",
        found_documents=[document],
        all_documents=[document],
        registry_paths=(registry,),
        report_paths=(report,),
    )

    rows = build_processing_result_rows(summary)
    artifacts = build_generated_artifact_rows(summary)

    assert rows[0].source_file == "nested/receipt.png"
    assert rows[0].output_file == "nested/renamed.png"
    assert rows[0].warning_count == 1
    assert {(row.artifact_type, row.path) for row in artifacts} == {
        ("document", "nested/renamed.png"),
        ("registry", "npd_receipts_registry.xlsx"),
        ("report", "run_report.txt"),
    }
    assert all(str(tmp_path) not in row.path for row in artifacts)


def test_all_ui_processing_types_resolve_through_public_metadata() -> None:
    """Verify every configured processing screen maps to a registered type.

    Protected risk: localized operation entries must not drift from the central
    document-type catalog or construct OCR processors merely to render controls.
    """
    expected = {
        "upd_invoices_status_1",
        "npd_receipts",
        "incoming_purchase_documents",
    }

    metadata = {identifier: get_processing_metadata(identifier) for identifier in expected}

    assert set(metadata) == expected
    assert metadata["incoming_purchase_documents"].supports_auto_rotate is False
    assert metadata["npd_receipts"].supports_auto_rotate is True
