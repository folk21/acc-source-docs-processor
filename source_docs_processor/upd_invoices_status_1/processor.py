"""Document processor for UPD invoice-transfer documents with status 1."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..file_ops import safe_filename
from ..image_processing import ROTATION_ANGLES, rotate_image
from ..models import ExtractedDocument
from ..ocr import OcrResult
from .extractor import extract_document
from .ocr import read_continuation_text_by_crop, run_ocr


class UpdInvoicesStatus1Processor:
    """Recognize and extract Russian UPD documents that have status `1`.

    This class is the boundary between the generic folder-processing pipeline and
    the UPD-specific OCR/extraction implementation. The CLI should not call the
    UPD extractor or targeted OCR functions directly; it should work through this
    processor interface instead.
    """

    document_type = "upd_invoices_status_1"
    display_name = "UPD invoice-transfer document, status 1"

    def is_supported_document(self, doc: ExtractedDocument) -> bool:
        """Return True when the scan is recognized as a UPD status 1 first page."""
        return doc.is_upd_invoice_transfer

    def is_continuation_page(self, doc: ExtractedDocument) -> bool:
        """Return True when the scan is recognized as a continuation page."""
        return doc.is_continuation_page

    def _score_document(self, doc: ExtractedDocument) -> int:
        """Score a recognition candidate so the best page orientation can be selected.

        The score is not meant to be a statistical OCR confidence value. It is a
        practical ranking heuristic that lets the processor choose between rotations:
        a real first page must outrank noisy text, while a continuation page can
        still win when no standalone document markers are found.
        """
        score = doc.confidence
        if doc.is_upd_invoice_transfer:
            score += 1000
        if doc.status == "1":
            score += 100
        if doc.invoice_number:
            score += 50
        if doc.invoice_date:
            score += 30
        if doc.is_continuation_page:
            score += 450 + doc.confidence
        return score

    def _rotation_candidates(self, image: np.ndarray, auto_rotate: bool, *, continuation_mode: bool = False) -> tuple[int, ...]:
        """Return rotation order for this UPD document family.

        Most first pages are landscape. When the raw scan is portrait-shaped, the
        sideways rotations are tried first because that usually means a landscape
        page was scanned on its side. Continuation pages in the current archive are
        also commonly sideways, so the same optimization applies there.
        """
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
        """Quickly check whether the image is a continuation page.

        When a recognized document was just processed, the next scan is often page 2.
        A continuation page does not need the full UPD header OCR path: signature and
        company-name marker areas are enough to attach it to the previous document.
        """
        best_doc: ExtractedDocument | None = None
        best_image: np.ndarray | None = None

        for angle in self._rotation_candidates(image, auto_rotate, continuation_mode=True):
            rotated = rotate_image(image, angle)

            # Continuation recognition deliberately reads only small marker regions.
            # A full-page OCR pass is unnecessary here because page 2 has no document
            # number/date header and is used only to inherit metadata from page 1.
            continuation_text = read_continuation_text_by_crop(rotated, lang=lang)
            ocr_result = OcrResult(
                text="",
                header_text="",
                status_digit=None,
                mean_confidence=0,
                rotation_degrees=angle,
                targeted_text=f"Continuation marker text:\n{continuation_text}",
                continuation_text=continuation_text,
            )
            doc = extract_document(image_path, ocr_result)
            doc.rotation_degrees = angle
            if best_doc is None or self._score_document(doc) > self._score_document(best_doc):
                best_doc = doc
                best_image = rotated

        if best_doc and best_doc.is_continuation_page and best_image is not None:
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
        """Run OCR for candidate rotations and return the strongest recognition result.

        This method is the first-page recognizer. It may detect a continuation-like
        signal, but the main workflow accepts that signal only after standalone UPD
        recognition has failed, preventing normal first pages from being attached to
        the previous document by mistake.
        """
        best_doc: ExtractedDocument | None = None
        best_image: np.ndarray | None = None

        for angle in self._rotation_candidates(image, auto_rotate):
            rotated = rotate_image(image, angle)

            # Save debug crops per rotation. This makes it possible to compare why a
            # particular angle was selected or why a field was missed.
            debug_dir = None
            if debug_root:
                debug_dir = debug_root / safe_filename(image_path.stem) / f"rotation_{angle}"
            ocr_result = run_ocr(rotated, lang=lang, deep=deep_ocr, rotation_degrees=angle, debug_dir=debug_dir)
            doc = extract_document(image_path, ocr_result)
            doc.rotation_degrees = angle

            # Keep the oriented image together with its extracted metadata. If this
            # rotation wins, the copied output image will be saved in this orientation.
            if best_doc is None or self._score_document(doc) > self._score_document(best_doc):
                best_doc = doc
                best_image = rotated

            # Fast path: when status, number, and date are recognized, further
            # rotations are very unlikely to improve the answer.
            if doc.is_upd_invoice_transfer and doc.invoice_number and doc.invoice_date:
                return doc, rotated

        assert best_doc is not None
        assert best_image is not None
        return best_doc, best_image
