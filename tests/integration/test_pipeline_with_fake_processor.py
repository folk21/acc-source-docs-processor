import csv
from pathlib import Path

import cv2
import numpy as np

from source_docs_processor.cli import process_folder
from source_docs_processor.models import ExtractedDocument


class FakeProcessor:
    """Small test processor that bypasses Tesseract and returns fixed results.

    The production processor performs OCR and extraction. Integration tests use
    this fake to verify the generic folder pipeline, output naming, continuation
    handling, and registry generation without depending on the local Tesseract
    installation or customer scanned accounting documents.
    """

    document_type = "fake_processor"
    display_name = "Fake processor for pipeline tests"

    def analyze_image_orientations(self, image_path: Path, image: np.ndarray, **_kwargs):
        """Return deterministic first-pass results based on the file name."""
        if image_path.name == "scan_001.png":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    is_upd_invoice_transfer=True,
                    status="1",
                    invoice_number="511",
                    invoice_date="21-03-2023",
                    confidence=95,
                ),
                image,
            )
        # Page 2 is intentionally not recognized as a standalone first page in
        # this first-pass method. The pipeline should then call the continuation
        # analyzer because a previous first page is active.
        return ExtractedDocument(source_path=image_path, confidence=0), image

    def analyze_continuation_orientations(self, image_path: Path, image: np.ndarray, **_kwargs):
        """Return a continuation result only for the known second-page fixture."""
        if image_path.name == "scan_002.png":
            return (
                ExtractedDocument(
                    source_path=image_path,
                    is_continuation_page=True,
                    rotation_degrees=90,
                    confidence=80,
                ),
                image,
            )
        return None

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Mirror the production processor first-page check."""
        return doc.is_upd_invoice_transfer

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Mirror the production processor continuation-page check."""
        return doc.is_continuation_page


def _write_test_image(path: Path) -> None:
    """Create a tiny valid PNG image for file-system integration tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = np.full((12, 12, 3), 255, dtype=np.uint8)
    assert cv2.imwrite(str(path), image)


def _read_registry(path: Path) -> list[dict[str, str]]:
    """Read the generated semicolon-separated registry file."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def test_pipeline_copies_recognized_continuation_and_unrecognized_files(tmp_path):
    """Verify the generic pipeline with an injected fake document processor.

    Fixed problem verified: the high-level folder workflow should be testable
    without real OCR. It must copy page 1 with generated naming, attach page 2
    as a continuation, preserve the source subfolder, and keep unrecognized files.
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
    assert (target_dir / "УПД_511_от_21-03-2023.png").exists()
    assert (target_dir / "УПД_511_от_21-03-2023_2_страница.png").exists()
    assert (target_dir / "scan_003.png").exists()


def test_registry_contains_portable_file_names_not_absolute_paths(tmp_path):
    """Verify registry rows stay portable and do not expose absolute paths.

    Fixed problem verified: earlier CSV output used full paths. The current
    accounting workflow needs only source/destination file names so the registry
    can be moved together with the result folder.
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
    assert rows[0]["source_file"] == "scan_001.png"
    assert rows[0]["destination_file"] == "УПД_511_от_21-03-2023.png"
    assert rows[1]["is_continuation_page"] == "1"
    assert rows[1]["destination_file"] == "УПД_511_от_21-03-2023_2_страница.png"
    assert rows[2]["source_file"] == "scan_003.png"
    assert rows[2]["destination_file"] == ""

    for row in rows:
        assert "/" not in row["source_file"]
        assert "\\" not in row["source_file"]
        assert not row["source_file"].startswith(str(tmp_path))
