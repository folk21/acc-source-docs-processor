from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np
import pytest

from source_docs_processor.cli import process_folder
from source_docs_processor.features.document_processing.document_processor import BaseDocumentProcessor
from source_docs_processor.features.document_processing.models import ExtractedDocument
from source_docs_processor.features.document_processing.document_types.npd_receipts.registry import NpdReceiptRegistryDefinition
from source_docs_processor.features.document_processing.document_types.npd_receipts.workflow import NpdReceiptRegistryWorkflow


class FakeNpdReceiptProcessor(BaseDocumentProcessor):
    document_type = "npd_receipts"
    display_name = "Fake NPD receipt processor"

    def analyze_image_orientations(self, image_path: Path, image: np.ndarray, **_kwargs):
        if image_path.name == "receipt.jpg":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    document_type=self.document_type,
                    is_recognized=True,
                    document_number="R-10",
                    document_date="02-04-2026",
                    issuer_name="Иванов Иван Иванович",
                    issuer_inn="078123456789",
                    recipient_name="ООО Ромашка",
                    recipient_inn="7801234567",
                    description="Консультационные услуги",
                    total_amount="1250.50",
                    currency="RUB",
                    confidence=95,
                    warnings=["receipt number read from explicit prefix"],
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


def _write_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def _shared_strings(workbook_path: Path) -> str:
    with ZipFile(workbook_path) as archive:
        return archive.read("xl/sharedStrings.xml").decode("utf-8")


def _external_links(workbook_path: Path) -> str:
    with ZipFile(workbook_path) as archive:
        return archive.read("xl/worksheets/_rels/sheet1.xml.rels").decode("utf-8")


def test_workflow_uses_requested_filename_and_exact_registry_columns(tmp_path):
    pytest.importorskip("xlsxwriter")
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    _write_image(source_dir / "receipt.jpg")
    _write_image(source_dir / "other.jpg")

    found, all_documents = process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        target_dir_name="processed_receipts",
        lang="rus+eng",
        document_type="npd_receipts",
        document_processor=FakeNpdReceiptProcessor(),
        processing_workflow=NpdReceiptRegistryWorkflow(),
        registry_definition=NpdReceiptRegistryDefinition(),
    )

    target_dir = output_dir / "processed_receipts"
    registry_path = target_dir / "npd_receipts_registry.xlsx"
    target_name = "02-04-2026_1250.50_ИвановИванИванович_R-10.jpg"
    renamed_receipt = target_dir / target_name

    assert registry_path.exists()
    assert renamed_receipt.exists()
    assert (target_dir / "other.jpg").exists()
    assert not list(target_dir.glob("*_report.txt"))
    assert len(found) == 1
    assert len(all_documents) == 2
    assert found[0].destination_path == renamed_receipt

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
    assert target_name in shared_strings
    assert "receipt.jpg" in shared_strings
    assert "Иванов Иван Иванович" in shared_strings
    assert "078123456789" in shared_strings
    assert "receipt number read from explicit prefix" in shared_strings
    assert "Организация-заказчик" not in shared_strings
    assert "Наименование услуги" not in shared_strings

    links = _external_links(registry_path)
    assert target_name in links
    assert "receipt.jpg" not in links


def test_explicit_output_directory_is_used_without_default_nested_folder(tmp_path):
    """Write receipt artifacts directly into an explicit output directory.

    Protected risk: ``--output receipts_dir`` must not create an additional
    ``receipts_dir/чеки_нпд`` level when no target directory name is requested.
    """
    pytest.importorskip("xlsxwriter")
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "receipts_dir"
    _write_image(source_dir / "receipt.jpg")

    process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        document_type="npd_receipts",
        document_processor=FakeNpdReceiptProcessor(),
        processing_workflow=NpdReceiptRegistryWorkflow(),
        registry_definition=NpdReceiptRegistryDefinition(),
    )

    expected_receipt = (
        output_dir
        / "02-04-2026_1250.50_ИвановИванИванович_R-10.jpg"
    )
    assert expected_receipt.exists()
    assert (output_dir / "npd_receipts_registry.xlsx").exists()
    assert not list(output_dir.glob("*_report.txt"))
    assert not (output_dir / "чеки_нпд").exists()
