"""Document processor for NPD receipts issued by self-employed persons."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ...document_processor import BaseDocumentProcessor
from ...file_ops import safe_filename
from ...image_processing import ROTATION_ANGLES, rotate_image
from ...models import ExtractedDocument
from .extractor import DOCUMENT_TYPE, extract_document
from .ocr import run_ocr


class NpdReceiptProcessor(BaseDocumentProcessor):
    """Recognize single-page NPD receipts and extract issuer details."""

    document_type = DOCUMENT_TYPE
    display_name = "NPD receipt issued by a self-employed person"

    def _score_document(self, document: ExtractedDocument) -> int:
        """Score one orientation using receipt recognition and extracted fields."""
        score = document.confidence
        if document.is_recognized:
            score += 1000
        if document.issuer_inn:
            score += 120
        if document.issuer_name:
            score += 100
        if document.total_amount:
            score += 40
        if document.document_date:
            score += 30
        return score

    def _rotation_candidates(
        self,
        image: np.ndarray,
        auto_rotate: bool,
    ) -> tuple[int, ...]:
        """Return a portrait-first rotation order for receipt images."""
        if not auto_rotate:
            return (0,)
        if image.shape[0] >= image.shape[1]:
            return (0, 90, 270, 180)
        return ROTATION_ANGLES

    def analyze_image_orientations(
        self,
        image_path: Path,
        image: np.ndarray,
        lang: str,
        deep_ocr: bool,
        auto_rotate: bool,
        debug_root: Path | None = None,
    ) -> tuple[ExtractedDocument, np.ndarray]:
        """Run receipt OCR for candidate rotations and return the strongest result."""
        best_document: ExtractedDocument | None = None
        best_image: np.ndarray | None = None

        for angle in self._rotation_candidates(image, auto_rotate):
            rotated = rotate_image(image, angle)
            debug_dir = None
            if debug_root:
                debug_dir = debug_root / safe_filename(image_path.stem) / f"rotation_{angle}"
            ocr_result = run_ocr(
                rotated,
                lang=lang,
                rotation_degrees=angle,
                debug_dir=debug_dir,
            )
            document = extract_document(image_path, ocr_result)
            document.rotation_degrees = angle

            if (
                best_document is None
                or self._score_document(document) > self._score_document(best_document)
            ):
                best_document = document
                best_image = rotated

            if (
                document.is_recognized
                and document.issuer_inn
                and document.issuer_name
                and document.total_amount
            ):
                return document, rotated

        assert best_document is not None
        assert best_image is not None
        return best_document, best_image
