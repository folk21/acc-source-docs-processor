from pathlib import Path

from source_docs_processor.features.document_processing.models import ExtractedDocument
from source_docs_processor.features.document_processing.document_types.npd_receipts.workflow import (
    NpdReceiptRegistryWorkflow,
)


def test_receipt_workflow_builds_expected_filename():
    """Verify receipt copies use the date, amount, payee name, and number."""
    document = ExtractedDocument(
        source_path=Path("scan.JPG"),
        document_type="npd_receipts",
        is_recognized=True,
        document_date="02-04-2026",
        total_amount="22578.00",
        issuer_name="Иванов Иван Иванович",
        document_number="204hy1b28u",
    )

    stem = NpdReceiptRegistryWorkflow().build_output_filename_stem(document)

    assert (
        stem
        == "02-04-2026_22578.00_ИвановИванИванович_204hy1b28u"
    )
    