"""OCR routines for NPD receipts."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytesseract

from ...image_processing import create_ocr_variants, crop_relative
from ...ocr import OcrResult, choose_best_text


_MARKERS = [r"\bчек\b", r"(?:ИНН|инн)"]


def _run_sparse_ocr(image: np.ndarray, lang: str) -> str:
    """Run sparse-text OCR, which often works better for mobile receipt screens."""
    try:
        return pytesseract.image_to_string(
            image,
            lang=lang,
            config="--psm 11",
            timeout=8,
        )
    except RuntimeError:
        return ""


def _write_debug_text(debug_dir: Path, name: str, text: str) -> None:
    """Write OCR diagnostics without storing sensitive images."""
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / name).write_text(text, encoding="utf-8")


def run_ocr(
    image: np.ndarray,
    lang: str,
    rotation_degrees: int,
    debug_dir: Path | None = None,
) -> OcrResult:
    """Read a complete NPD receipt and a targeted upper information region."""
    variants = create_ocr_variants(image)
    full_text, confidence, _ = choose_best_text(
        variants,
        lang=lang,
        marker_patterns=_MARKERS,
    )

    sparse_text = _run_sparse_ocr(variants[1], lang=lang)
    if len(sparse_text.strip()) > len(full_text.strip()) * 0.75:
        combined_text = "\n".join(part for part in (full_text, sparse_text) if part)
    else:
        combined_text = full_text

    # The issuer block is normally in the upper or middle part of a mobile receipt.
    # Reading it separately helps preserve blank-line block boundaries and full names.
    owner_crop = crop_relative(image, 0.03, 0.08, 0.97, 0.62)
    owner_gray = cv2.cvtColor(owner_crop, cv2.COLOR_BGR2GRAY)
    owner_gray = cv2.resize(owner_gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    owner_text = _run_sparse_ocr(owner_gray, lang=lang)

    if debug_dir:
        _write_debug_text(debug_dir, "full_ocr.txt", combined_text)
        _write_debug_text(debug_dir, "owner_block_ocr.txt", owner_text)

    return OcrResult(
        text=combined_text,
        header_text="",
        mean_confidence=confidence,
        rotation_degrees=rotation_degrees,
        targeted_text=owner_text,
        targeted_fields={"owner_block_text": owner_text},
    )
