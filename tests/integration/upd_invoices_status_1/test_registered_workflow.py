import csv
from pathlib import Path

import cv2
import numpy as np

from source_docs_processor.cli import process_folder
from source_docs_processor.features.document_processing.document_processor import BaseDocumentProcessor
from source_docs_processor.features.document_processing.models import ExtractedDocument


class FakeUpdProcessor(BaseDocumentProcessor):
    """Return deterministic UPD-like results while bypassing real Tesseract."""

    document_type = "upd_invoices_status_1"
    display_name = "Fake UPD processor"

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        **_kwargs,
    ):
        """Recognize only the first synthetic image as a UPD document."""
        if image_path.name == "scan_001.png":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    document_type=self.document_type,
                    is_recognized=True,
                    status="1",
                    document_number="511",
                    document_date="21-03-2023",
                    issuer_name="ООО Учебный Перевозчик",
                    recipient_name="ООО Учебный Производитель",
                    total_amount="1500.00",
                    confidence=95,
                    extra_fields={"request_number": "R-42"},
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


def _write_test_image(path: Path) -> None:
    """Create a tiny valid image for workflow integration testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((12, 12, 3), 255, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def test_registered_upd_definition_preserves_current_public_output(tmp_path):
    """Verify the new component registry keeps existing UPD workflow behavior.

    Protected risk: separating workflow and registry classes must not change the
    current output folder, filename format, detailed CSV, or unrecognized-file
    handling used by accountants.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    _write_test_image(source_dir / "scan_001.png")
    _write_test_image(source_dir / "scan_002.png")

    found, all_documents = process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        document_processor=FakeUpdProcessor(),
    )

    target_dir = output_dir / "передаточные_документы"
    assert len(found) == 1
    assert len(all_documents) == 2
    assert (target_dir / "УПД_511_от_21-03-2023.png").exists()
    assert (target_dir / "scan_002.png").exists()
    assert (target_dir / "передаточные_документы_report.txt").exists()

    registry_path = target_dir / "передаточные_документы.csv"
    with registry_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file, delimiter=";"))

    assert rows[0]["document_number"] == "511"
    assert rows[0]["issuer_name"] == "ООО Учебный Перевозчик"
    assert rows[0]["request_number"] == "R-42"
    assert rows[1]["source_file"] == "scan_002.png"
    assert rows[1]["destination_file"] == ""
