from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np

from source_docs_processor.cli import process_folder
from source_docs_processor.features.document_processing.document_processor import BaseDocumentProcessor
from source_docs_processor.features.document_processing.models import ExtractedDocument


class FakeNpdReceiptProcessor(BaseDocumentProcessor):
    """Return deterministic receipt results without calling Tesseract."""

    document_type = "npd_receipts"
    display_name = "Fake NPD receipt processor"

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        **_kwargs,
    ):
        """Recognize one synthetic file and reject all other images."""
        if image_path.name == "incoming.JPG":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    document_type=self.document_type,
                    is_recognized=True,
                    document_date="2026-07-15",
                    document_number="receipt-42",
                    total_amount="1250.00",
                    issuer_name="Иванов Иван Иванович",
                    issuer_inn="000000000000",
                    confidence=98,
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
    """Create a tiny valid image for receipt workflow integration testing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((12, 12, 3), 255, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def _shared_strings(workbook_path: Path) -> str:
    """Read shared strings from the generated XLSX workbook."""
    with ZipFile(workbook_path) as archive:
        return archive.read("xl/sharedStrings.xml").decode("utf-8")


def _external_links(workbook_path: Path) -> str:
    """Read external file links from the generated XLSX workbook."""
    with ZipFile(workbook_path) as archive:
        return archive.read(
            "xl/worksheets/_rels/sheet1.xml.rels"
        ).decode("utf-8")


def test_registered_receipt_workflow_uses_current_output_contract(tmp_path):
    """Verify the registered NPD workflow copies images and writes its XLSX registry.

    Protected risk: the registered workflow must preserve source subfolders,
    rename recognized receipts using the current filename convention, copy
    unrecognized images unchanged, and use the compact linked XLSX registry.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_subdir = source_dir / "nested"

    _write_test_image(source_subdir / "incoming.JPG")
    _write_test_image(source_subdir / "other.png")

    found, all_documents = process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        document_type="npd_receipts",
        document_processor=FakeNpdReceiptProcessor(),
    )

    target_root = output_dir
    target_subdir = target_root / "nested"
    copied_name = (
        "2026-07-15_1250.00_"
        "ИвановИванИванович_receipt-42.jpg"
    )
    copied_receipt = target_subdir / copied_name
    copied_unrecognized = target_subdir / "other.png"
    registry_path = target_root / "npd_receipts_registry.xlsx"

    assert len(found) == 1
    assert len(all_documents) == 2
    assert copied_receipt.exists()
    assert copied_unrecognized.exists()
    assert registry_path.exists()
    assert not list(target_root.glob("*_report.txt"))
    assert found[0].destination_path == copied_receipt

    shared_strings = _shared_strings(registry_path)
    expected_headers = [
        "target_file_name",
        "source_file_name",
        "дата",
        "сумма",
        "фио получателя суммы",
        "номер_чека",
        "ИНН получателя",
        "комментарии о генерации",
    ]
    positions = [shared_strings.index(header) for header in expected_headers]

    assert positions == sorted(positions)
    assert copied_name in shared_strings
    assert "incoming.JPG" in shared_strings
    assert "Иванов Иван Иванович" in shared_strings
    assert "000000000000" in shared_strings
    assert "other.png" not in shared_strings

    external_links = _external_links(registry_path)
    assert copied_name in external_links
    assert "incoming.JPG" not in external_links
    