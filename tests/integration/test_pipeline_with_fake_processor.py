import csv
from pathlib import Path

import cv2
import numpy as np

from source_docs_processor.features.document_processing._internal.service import (
    process_folder_with_components as process_folder,
)
from source_docs_processor.features.document_processing.processor_base import BaseDocumentProcessor
from source_docs_processor.features.document_processing.models import ExtractedDocument, RegistryValue
from source_docs_processor.features.document_processing.workflow_copy_and_register import CopyAndRegisterWorkflow


class FakeProcessor(BaseDocumentProcessor):
    """Recognize synthetic files without defining any folder-output behavior."""

    document_type = "fake_document"
    display_name = "Fake document processor"

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
                    document_number="D-511",
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


class FakeCopyWorkflow(CopyAndRegisterWorkflow):
    """Define synthetic copy, naming, and continuation behavior for tests."""

    default_target_dir_name = "fake_documents"
    supports_continuation_pages = True

    def build_primary_filename_stem(self, document: ExtractedDocument) -> str:
        """Use a non-UPD name to verify workflow-owned filename policy."""
        return f"DOC_{document.document_number}_{document.document_date}"


class FakeRegistryDefinition:
    """Define a small registry independent from processor and workflow classes."""

    columns = (
        "source_file",
        "destination_file",
        "document_type",
        "is_recognized",
        "is_continuation_page",
        "document_number",
        "issuer_name",
        "recipient_name",
        "total_amount",
        "payment_method",
    )

    def build_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> dict[str, RegistryValue]:
        """Build one portable row for the synthetic workflow."""
        return {
            "source_file": document.source_path.name,
            "destination_file": (
                document.destination_path.name if document.destination_path else ""
            ),
            "document_type": document.document_type or "",
            "is_recognized": int(document.is_recognized),
            "is_continuation_page": int(document.is_continuation_page),
            "document_number": document.document_number or "",
            "issuer_name": document.issuer_name or "",
            "recipient_name": document.recipient_name or "",
            "total_amount": document.total_amount or "",
            "payment_method": document.extra_fields.get("payment_method") or "",
        }


def _write_test_image(path: Path) -> None:
    """Create a tiny valid PNG image for file-system integration tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((12, 12, 3), 255, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def _read_registry(path: Path) -> list[dict[str, str]]:
    """Read the generated semicolon-separated registry file."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def _run_fake_workflow(source_dir: Path, output_dir: Path, target_name=None):
    """Run the internal composition service with independently injected components."""
    return process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang="rus+eng",
        target_dir_name=target_name,
        document_processor=FakeProcessor(),
        processing_workflow=FakeCopyWorkflow(),
        registry_definition=FakeRegistryDefinition(),
    )


def test_pipeline_separates_recognition_from_copying_and_naming(tmp_path):
    """Verify processor recognition and workflow file actions stay independent.

    Protected risk: a future registry-only receipt workflow must be selectable
    without adding copy, rename, or output-folder methods to its OCR processor.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    scans_dir = source_dir / "2023"
    _write_test_image(scans_dir / "scan_001.png")
    _write_test_image(scans_dir / "scan_002.png")
    _write_test_image(scans_dir / "scan_003.png")

    found_docs, all_docs = _run_fake_workflow(
        source_dir,
        output_dir,
        target_name="target_scans",
    )

    target_dir = output_dir / "target_scans" / "2023"
    assert len(found_docs) == 1
    assert len(all_docs) == 3
    assert (target_dir / "DOC_D-511_21-03-2023.png").exists()
    assert (target_dir / "DOC_D-511_21-03-2023_page_2.png").exists()
    assert (target_dir / "scan_003.png").exists()

    continuation = all_docs[1]
    assert continuation.document_number == "D-511"
    assert continuation.issuer_name == "Synthetic Supplier"
    assert continuation.extra_fields["payment_method"] == "card"


def test_registry_definition_controls_columns_and_rows(tmp_path):
    """Verify CSV shape is selected independently from processor and workflow.

    Protected risk: receipt registries need a short hyperlink-oriented schema,
    while the current UPD workflow needs a detailed audit registry.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    scans_dir = source_dir / "2023"
    _write_test_image(scans_dir / "scan_001.png")
    _write_test_image(scans_dir / "scan_002.png")
    _write_test_image(scans_dir / "scan_003.png")

    _run_fake_workflow(source_dir, output_dir, target_name="target_scans")

    rows = _read_registry(output_dir / "target_scans" / "target_scans.csv")
    assert tuple(rows[0]) == FakeRegistryDefinition.columns
    assert rows[0]["document_type"] == "fake_document"
    assert rows[0]["document_number"] == "D-511"
    assert rows[0]["issuer_name"] == "Synthetic Supplier"
    assert rows[0]["recipient_name"] == "Synthetic Buyer"
    assert rows[0]["total_amount"] == "1250.00"
    assert rows[0]["payment_method"] == "card"
    assert "invoice_number" not in rows[0]

    assert rows[1]["is_continuation_page"] == "1"
    assert rows[1]["destination_file"] == "DOC_D-511_21-03-2023_page_2.png"
    assert rows[2]["source_file"] == "scan_003.png"
    assert rows[2]["destination_file"] == "scan_003.png"


def test_workflow_default_target_directory_is_used(tmp_path):
    """Verify output-folder defaults belong to the selected workflow.

    Protected risk: a future registry-only workflow should write beside source
    files without inheriting the UPD target-directory convention.
    """
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    _write_test_image(source_dir / "scan_001.png")

    _run_fake_workflow(source_dir, output_dir)

    assert (output_dir / "fake_documents" / "fake_documents.csv").exists()
