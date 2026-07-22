import csv
from pathlib import Path

import cv2
import numpy as np

from source_docs_processor.cli import process_folder
from source_docs_processor.document_processor import BaseDocumentProcessor
from source_docs_processor.models import ExtractedDocument


class FakeProcessor(BaseDocumentProcessor):
    """Test processor that proves the shared pipeline has no UPD assumptions."""

    document_type = "fake_receipt"
    display_name = "Fake receipt processor"
    default_target_dir_name = "fake_receipts"
    supports_continuation_pages = True
    registry_extra_columns = ("payment_method",)

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        **_kwargs,
    ):
        """Return deterministic standalone results based on the file name."""
        if image_path.name == "scan_001.png":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    document_type=self.document_type,
                    is_recognized=True,
                    document_number="R-511",
                    document_date="21-03-2023",
                    issuer_name="Synthetic Supplier",
                    recipient_name="Synthetic Buyer",
                    total_amount="1250.00",
                    currency="RUB",
                    confidence=95,
                    extra_fields={"payment_method": "card"},
                ),
                image,
            )
        return (
            ExtractedDocument(
                source_path=image_path,
                document_type=self.document_type,
            ),
            image,
        )

    def analyze_continuation_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        **_kwargs,
    ):
        """Return a continuation result only for the known second page."""
        if image_path.name == "scan_002.png":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    document_type=self.document_type,
                    is_recognized=True,
                    is_continuation_page=True,
                    rotation_degrees=90,
                    confidence=80,
                ),
                image,
            )
        return None

    def build_primary_filename_stem(self, doc: ExtractedDocument) -> str:
        """Use a non-UPD filename to guard the generic output boundary."""
        return f"RECEIPT_{doc.document_number}_{doc.document_date}"


def _write_test_image(path: Path) -> None:
    """Create a tiny valid PNG image for file-system integration tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((12, 12, 3), 255, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def _read_registry(path: Path) -> list[dict[str, str]]:
    """Read the generated semicolon-separated registry file."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def test_pipeline_uses_processor_naming_and_generic_metadata(tmp_path):
    """Verify processor-controlled names, continuation handling, and copying.

    Protected risk: adding a second document type must not require UPD-specific
    flags, invoice field names, or filename logic in the shared folder pipeline.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    scans_dir = source_dir / "2023"
    _write_test_image(scans_dir / "scan_001.png")
    _write_test_image(scans_dir / "scan_002.png")
    _write_test_image(scans_dir / "scan_003.png")

    found_docs, all_docs = process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        target_dir_name="target_scans",
        document_processor=FakeProcessor(),
    )

    target_dir = output_dir / "target_scans" / "2023"
    assert len(found_docs) == 1
    assert len(all_docs) == 3
    assert (target_dir / "RECEIPT_R-511_21-03-2023.png").exists()
    assert (target_dir / "RECEIPT_R-511_21-03-2023_page_2.png").exists()
    assert (target_dir / "scan_003.png").exists()

    continuation = all_docs[1]
    assert continuation.document_number == "R-511"
    assert continuation.issuer_name == "Synthetic Supplier"
    assert continuation.extra_fields["payment_method"] == "card"


def test_registry_uses_common_and_processor_specific_columns(tmp_path):
    """Verify generic CSV columns plus declared document-specific fields.

    Protected risk: a new processor should extend the registry without editing
    the shared CSV writer or reusing invoice-oriented column names.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    scans_dir = source_dir / "2023"
    _write_test_image(scans_dir / "scan_001.png")
    _write_test_image(scans_dir / "scan_002.png")
    _write_test_image(scans_dir / "scan_003.png")

    process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        target_dir_name="target_scans",
        document_processor=FakeProcessor(),
    )

    rows = _read_registry(output_dir / "target_scans" / "target_scans.csv")
    assert rows[0]["document_type"] == "fake_receipt"
    assert rows[0]["document_number"] == "R-511"
    assert rows[0]["issuer_name"] == "Synthetic Supplier"
    assert rows[0]["recipient_name"] == "Synthetic Buyer"
    assert rows[0]["total_amount"] == "1250.00"
    assert rows[0]["payment_method"] == "card"
    assert "invoice_number" not in rows[0]
    assert "is_upd_invoice_transfer" not in rows[0]

    assert rows[1]["is_continuation_page"] == "1"
    assert rows[1]["destination_file"] == "RECEIPT_R-511_21-03-2023_page_2.png"
    assert rows[2]["source_file"] == "scan_003.png"
    assert rows[2]["destination_file"] == ""

    for row in rows:
        assert "/" not in row["source_file"]
        assert "\\" not in row["source_file"]
        assert not row["source_file"].startswith(str(tmp_path))


def test_processor_default_target_directory_is_used(tmp_path):
    """Verify that each processor can provide its own default output folder.

    Protected risk: future receipt and act processors should not inherit the
    current UPD-specific default directory name from generic CLI code.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    _write_test_image(source_dir / "scan_001.png")

    process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        document_processor=FakeProcessor(),
    )

    assert (output_dir / "fake_receipts" / "fake_receipts.csv").exists()
