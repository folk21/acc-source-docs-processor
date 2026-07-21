from pathlib import Path

from source_docs_processor.models import ExtractedDocument


def test_output_filename_uses_upd_prefix_number_and_date():
    """Verify the agreed output filename format for recognized first pages.

    Fixed problem verified: the project uses the `УПД_` prefix and must preserve
    the document number/date naming convention used by the accountant workflow.
    """
    doc = ExtractedDocument(
        source_path=Path("scan.png"),
        invoice_number="511",
        invoice_date="21-03-2023",
    )

    assert doc.filename_stem() == "УПД_511_от_21-03-2023"


def test_continuation_filename_appends_page_suffix():
    """Verify output naming for second pages attached to a previous document.

    Fixed problem verified: page-2 scans must keep the previous document number
    and date while adding `_2_страница` to remain visually grouped with page 1.
    """
    doc = ExtractedDocument(
        source_path=Path("scan_page_2.png"),
        invoice_number="356",
        invoice_date="27-02-2023",
        continuation_page_number=2,
    )

    assert doc.continuation_filename_stem() == "УПД_356_от_27-02-2023_2_страница"
