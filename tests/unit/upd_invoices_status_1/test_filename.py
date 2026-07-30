from pathlib import Path

from source_docs_processor.features.document_types.models import ExtractedDocument
from source_docs_processor.features.document_types.upd_invoices_status_1.workflow import (
    UpdInvoicesStatus1Workflow,
)


def test_upd_workflow_builds_established_primary_filename():
    """Verify that workflow separation preserves the existing UPD output name.

    Protected risk: moving naming out of the OCR processor must not alter the
    accountant-facing ``УПД_<number>_от_<date>`` convention.
    """
    document = ExtractedDocument(
        source_path=Path("scan.png"),
        document_type="upd_invoices_status_1",
        is_recognized=True,
        document_number="511",
        document_date="21-03-2023",
    )

    stem = UpdInvoicesStatus1Workflow().build_output_filename_stem(document)

    assert stem == "УПД_511_от_21-03-2023"


def test_upd_workflow_builds_established_continuation_filename():
    """Verify that the existing Russian continuation suffix remains unchanged.

    Protected risk: the reusable copy workflow uses a neutral suffix, while UPD
    output must continue producing ``_2_страница`` names.
    """
    document = ExtractedDocument(
        source_path=Path("scan_page_2.png"),
        document_type="upd_invoices_status_1",
        is_recognized=True,
        document_number="356",
        document_date="27-02-2023",
        is_continuation_page=True,
        continuation_page_number=2,
    )

    stem = UpdInvoicesStatus1Workflow().build_output_filename_stem(document)

    assert stem == "УПД_356_от_27-02-2023_2_страница"
