"""Tests for shared document-processing workflow framework modules."""

from pathlib import Path

from source_docs_processor.features.document_processing.models import (
    ExtractedDocument,
)
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
