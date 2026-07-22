from pathlib import Path

from source_docs_processor.document_processor import BaseDocumentProcessor
from source_docs_processor.models import ExtractedDocument


def test_continuation_inherits_common_and_extra_metadata():
    """Verify reusable continuation metadata inheritance.

    Protected risk: continuation logic must not depend on seller/buyer or invoice
    field names and must preserve page-specific values over inherited values.
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

    BaseDocumentProcessor().prepare_continuation_document(
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


def test_base_processor_rejects_other_document_types():
    """Verify document-type isolation in shared recognition checks.

    Protected risk: a recognized result produced by one processor must not be
    accepted accidentally by another processor in an embedded workflow.
    """
    doc = ExtractedDocument(
        source_path=Path("document.png"),
        document_type="another_type",
        is_recognized=True,
    )

    assert BaseDocumentProcessor().is_supported_document(doc) is False
