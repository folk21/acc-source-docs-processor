from pathlib import Path

from source_docs_processor.models import ExtractedDocument
from source_docs_processor.upd_invoices_status_1.processor import (
    UpdInvoicesStatus1Processor,
)


def test_upd_processor_builds_established_primary_filename():
    """Verify that generalization preserves the existing UPD output convention.

    Protected risk: moving filename policy out of the shared model must not alter
    the accountant-facing ``УПД_<number>_от_<date>`` naming format.
    """
    doc = ExtractedDocument(
        source_path=Path("scan.png"),
        document_type="upd_invoices_status_1",
        is_recognized=True,
        document_number="511",
        document_date="21-03-2023",
    )

    stem = UpdInvoicesStatus1Processor().build_output_filename_stem(doc)

    assert stem == "УПД_511_от_21-03-2023"


def test_upd_processor_builds_established_continuation_filename():
    """Verify that the existing Russian page suffix remains unchanged.

    Protected risk: the generic base processor uses a neutral page suffix, while
    the UPD workflow must continue producing ``_2_страница`` names.
    """
    doc = ExtractedDocument(
        source_path=Path("scan_page_2.png"),
        document_type="upd_invoices_status_1",
        is_recognized=True,
        document_number="356",
        document_date="27-02-2023",
        is_continuation_page=True,
        continuation_page_number=2,
    )

    stem = UpdInvoicesStatus1Processor().build_output_filename_stem(doc)

    assert stem == "УПД_356_от_27-02-2023_2_страница"
