"""Document processor for UPD invoice-transfer documents with status 1."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..document_processor import BaseDocumentProcessor
from ..file_ops import safe_filename
from ..image_processing import ROTATION_ANGLES, rotate_image
from ..models import ExtractedDocument
from ..ocr import OcrResult
from .extractor import extract_document
from .ocr import read_continuation_text_by_crop, run_ocr


class UpdInvoicesStatus1Processor(BaseDocumentProcessor):
    """Recognize and extract Russian UPD documents that have status ``1``."""

    document_type = "upd_invoices_status_1"
    display_name = "UPD invoice-transfer document, status 1"
    default_target_dir_name = "передаточные_документы"
    supports_continuation_pages = True
    registry_extra_columns = (
        "request_number",
        "request_date",
        "vehicle",
        "loading_datetime",
        "unloading_datetime",
    )

    def build_primary_filename_stem(self, doc: ExtractedDocument) -> str:
        """Preserve the established UPD filename convention."""
        number = doc.document_number or "без_номера"
        if doc.document_date:
            return f"УПД_{number}_от_{doc.document_date}"
        return f"УПД_{number}"

    def build_output_filename_stem(self, doc: ExtractedDocument) -> str:
        """Build the established primary or continuation UPD filename."""
        stem = self.build_primary_filename_stem(doc)
        if doc.is_continuation_page:
            page_number = doc.continuation_page_number or 2
            return f"{stem}_{page_number}_страница"
        return stem

    def _score_document(self, doc: ExtractedDocument) -> int:
        """Score one orientation using UPD-specific recognition signals."""
        score = doc.confidence
        if self.is_supported_document(doc):
            score += 1000
        if doc.status == "1":
            score += 100
        if doc.document_number:
            score += 50
        if doc.document_date:
            score += 30
        if self.is_continuation_page(doc):
            score += 450 + doc.confidence
        return score

    def _rotation_candidates(
        self,
        image: np.ndarray,
        auto_rotate: bool,
        *,
        continuation_mode: bool = False,
    ) -> tuple[int, ...]:
        """Return rotation order for this landscape-oriented UPD family."""
        if not auto_rotate:
            return (0,)
        if image.shape[0] > image.shape[1]:
            return (90, 270, 0, 180)
        return ROTATION_ANGLES

    def analyze_continuation_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        auto_rotate: bool,
    ) -> tuple[ExtractedDocument, np.ndarray] | None:
        """Quickly check whether the image is a continuation page."""
        best_doc: ExtractedDocument | None = None
        best_image: np.ndarray | None = None

        for angle in self._rotation_candidates(
            image,
            auto_rotate,
            continuation_mode=True,
        ):
            rotated = rotate_image(image, angle)
            continuation_text = read_continuation_text_by_crop(rotated, lang=lang)
            ocr_result = OcrResult(
                text="",
                header_text="",
                mean_confidence=0,
                rotation_degrees=angle,
                targeted_text=f"Continuation marker text:\n{continuation_text}",
                targeted_fields={"continuation_text": continuation_text},
            )
            doc = extract_document(image_path, ocr_result)
            doc.rotation_degrees = angle
            if (
                best_doc is None
                or self._score_document(doc) > self._score_document(best_doc)
            ):
                best_doc = doc
                best_image = rotated

        if (
            best_doc
            and self.is_continuation_page(best_doc)
            and best_image is not None
        ):
            return best_doc, best_image
        return None

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        deep_ocr: bool,
        auto_rotate: bool,
        debug_root: Path | None = None,
    ) -> tuple[ExtractedDocument, np.ndarray]:
        """Run OCR for candidate rotations and return the strongest result."""
        best_doc: ExtractedDocument | None = None
        best_image: np.ndarray | None = None

        for angle in self._rotation_candidates(image, auto_rotate):
            rotated = rotate_image(image, angle)
            debug_dir = None
            if debug_root:
                debug_dir = (
                    debug_root
                    / safe_filename(image_path.stem)
                    / f"rotation_{angle}"
                )
            ocr_result = run_ocr(
                rotated,
                lang=lang,
                deep=deep_ocr,
                rotation_degrees=angle,
                debug_dir=debug_dir,
            )
            doc = extract_document(image_path, ocr_result)
            doc.rotation_degrees = angle

            if (
                best_doc is None
                or self._score_document(doc) > self._score_document(best_doc)
            ):
                best_doc = doc
                best_image = rotated

            if (
                self.is_supported_document(doc)
                and doc.document_number
                and doc.document_date
            ):
                return doc, rotated

        assert best_doc is not None
        assert best_image is not None
        return best_doc, best_image
