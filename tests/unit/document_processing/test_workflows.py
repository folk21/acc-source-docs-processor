"""Tests for shared document-processing workflow framework modules."""

from pathlib import Path

from source_docs_processor.features.document_processing.models import (
    ExtractedDocument,
)
from source_docs_processor.features.document_processing.workflow_base import ProcessingOptions
from source_docs_processor.features.document_processing.workflow_copy_and_register import (
    CopyAndRegisterWorkflow,
)


def test_continuation_workflow_inherits_common_and_extra_metadata():
    """Verify reusable continuation metadata inheritance in the copy workflow.

    Protected risk: continuation preparation is a folder workflow concern and
    must not force receipt or other single-page OCR processors to implement it.
    """
    primary = ExtractedDocument(
        source_path=Path("primary.png"),
        document_type="synthetic_type",
        is_recognized=True,
        document_number="D-42",
        document_date="05-06-2026",
        issuer_name="Synthetic Issuer",
        recipient_name="Synthetic Recipient",
        total_amount="900.00",
        extra_fields={"contract_id": "C-1", "page_note": "primary"},
    )
    continuation = ExtractedDocument(
        source_path=Path("continuation.png"),
        document_type="synthetic_type",
        is_recognized=True,
        is_continuation_page=True,
        extra_fields={"page_note": "continuation"},
    )

    CopyAndRegisterWorkflow().prepare_continuation_document(
        continuation,
        primary,
        page_number=2,
    )

    assert continuation.document_number == "D-42"
    assert continuation.issuer_name == "Synthetic Issuer"
    assert continuation.recipient_name == "Synthetic Recipient"
    assert continuation.total_amount == "900.00"
    assert continuation.extra_fields["contract_id"] == "C-1"
    assert continuation.extra_fields["page_note"] == "continuation"
    assert continuation.continuation_page_number == 2
    assert continuation.continued_from == "primary.png"


def test_processing_options_emits_privacy_conscious_progress_events(tmp_path):
    """Verify adapters receive counts and status without extracted field values.

    Protected risk: UI progress must not require private workflow inspection or
    expose OCR text and accounting fields before the final summary is returned.
    """
    events = []
    options = ProcessingOptions(
        source_dir=tmp_path,
        output_dir=None,
        target_dir_name=None,
        lang="rus+eng",
        progress_callback=events.append,
    )

    options.report_progress(
        "file_finished",
        file_index=2,
        file_count=5,
        source_path=tmp_path / "scan.png",
        recognized=True,
        error=None,
        output_path=tmp_path / "output.png",
    )

    assert len(events) == 1
    assert events[0].event == "file_finished"
    assert events[0].file_index == 2
    assert events[0].file_count == 5
    assert events[0].recognized is True
    assert events[0].error is None
    assert not hasattr(events[0], "document")


def test_processing_progress_callback_errors_propagate(tmp_path):
    """Verify a failing adapter callback stops the run instead of being hidden.

    Protected risk: swallowing UI adapter failures would leave callers showing
    stale progress while processing continues in an unknown state.
    """
    def fail(_progress):
        raise RuntimeError("synthetic callback failure")

    options = ProcessingOptions(
        source_dir=tmp_path,
        output_dir=None,
        target_dir_name=None,
        lang="rus+eng",
        progress_callback=fail,
    )

    import pytest

    with pytest.raises(RuntimeError, match="synthetic callback failure"):
        options.report_progress("scan_started", file_count=1)
