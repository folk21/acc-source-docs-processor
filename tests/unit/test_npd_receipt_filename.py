from pathlib import Path

from source_docs_processor.models import ExtractedDocument
from source_docs_processor.npd_receipts.workflow import NpdReceiptsWorkflow


def test_receipt_workflow_builds_date_amount_number_filename():
    """Verify receipt copies use the required Date_Amount_ReceiptNumber order."""
    document = ExtractedDocument(
        source_path=Path("scan.JPG"),
        document_type="npd_receipts",
        is_recognized=True,
        document_date="2026-04-02",
        total_amount="22578.00",
        document_number="204hy1b28u",
    )

    stem = NpdReceiptsWorkflow().build_output_filename_stem(document)

    assert stem == "2026-04-02_22578-00_204hy1b28u"
