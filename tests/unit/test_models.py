from pathlib import Path

from source_docs_processor.features.document_processing.document_processor import BaseDocumentProcessor
from source_docs_processor.features.document_processing.models import ExtractedDocument
from source_docs_processor.features.document_processing.workflows.copy_and_register import CopyAndRegisterWorkflow


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


def test_base_processor_rejects_other_document_types():
    """Verify document-type isolation remains a recognition responsibility.

    Protected risk: a result produced by one processor must not be accepted by
    another processor even though folder actions are now selected separately.
    """
    document = ExtractedDocument(
        source_path=Path("document.png"),
        document_type="another_type",
        is_recognized=True,
    )

    assert BaseDocumentProcessor().is_supported_document(document) is False


def test_base_processor_does_not_define_output_policy():
    """Verify OCR processors do not own copying, naming, or registry concerns.

    Protected risk: putting workflow methods back on processors would make a
    registry-only document type inherit irrelevant file-output behavior.
    """
    processor = BaseDocumentProcessor()

    assert not hasattr(processor, "default_target_dir_name")
    assert not hasattr(processor, "build_output_filename_stem")
    assert not hasattr(processor, "registry_extra_columns")
