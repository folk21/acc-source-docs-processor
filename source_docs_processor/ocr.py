"""Generic OCR primitives shared by document processors.

The functions in this module know how to call Tesseract and choose a useful OCR
variant, but they do not know anything about a concrete accounting document
layout. Document-type-specific OCR code should live inside a processor package.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pytesseract


@dataclass
class OcrResult:
    """Raw OCR output plus processor-defined targeted field values.

    Generic OCR code stores no invoice, receipt, or UPD-specific attributes.
    Concrete processors place anchored OCR results in ``targeted_fields`` and
    interpret those keys inside their own extractor package.
    """

    text: str
    header_text: str
    mean_confidence: float
    rotation_degrees: int = 0
    targeted_text: str = ""
    targeted_fields: dict[str, str | None] = field(default_factory=dict)


def _ocr_text(image: np.ndarray, lang: str, psm: int = 6, whitelist: str | None = None, timeout: int = 5) -> str:
    """Run Tesseract OCR with one page segmentation mode and optional whitelist."""
    config = f"--psm {psm}"
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"
    try:
        return pytesseract.image_to_string(image, lang=lang, config=config, timeout=timeout)
    except RuntimeError:
        # Wrongly oriented or noisy scans can make Tesseract spend too long on a crop.
        # Treat such orientation/preprocessing variant as unreadable and continue with other variants.
        return ""


def _mean_confidence(image: np.ndarray, lang: str) -> float:
    """Compute average Tesseract confidence for diagnostic use.

    The main pipeline usually uses cheaper proxy scores, but this helper is kept
    for debugging and future quality checks where raw OCR confidence is useful.
    """
    data = pytesseract.image_to_data(image, lang=lang, config="--psm 6", output_type=pytesseract.Output.DICT)
    values: list[float] = []
    for raw in data.get("conf", []):
        try:
            conf = float(raw)
        except (TypeError, ValueError):
            continue
        if conf >= 0:
            values.append(conf)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _text_has_all_markers(text: str, marker_patterns: list[str] | None) -> bool:
    """Return True when OCR text contains all configured marker patterns."""
    if not marker_patterns:
        return bool(text.strip())
    return all(re.search(pattern, text, re.IGNORECASE) for pattern in marker_patterns)


def choose_best_text(
    variants: list[np.ndarray],
    lang: str,
    marker_patterns: list[str] | None = None,
) -> tuple[str, float, np.ndarray]:
    """Choose the OCR variant with the strongest textual signal.

    `marker_patterns` allows a concrete document processor to add domain markers
    such as invoice/header keywords while keeping the OCR selection loop generic.
    """
    best_text = ""
    best_score = -1.0
    best_image = variants[0]

    # Each variant is a different preprocessing attempt over the same crop. The
    # first variant is usually cheap grayscale text; later variants can recover
    # weak scans but may also slow down the run.
    for variant in variants:
        text = _ocr_text(variant, lang=lang, psm=6, timeout=4)
        marker_bonus = 0
        for pattern in marker_patterns or []:
            if re.search(pattern, text, re.IGNORECASE):
                marker_bonus += 75
        score = len(text.strip()) + marker_bonus
        if score > best_score:
            best_score = score
            best_text = text
            best_image = variant
        if _text_has_all_markers(text, marker_patterns):
            confidence_proxy = min(100.0, max(0.0, score / 20.0))
            return text, confidence_proxy, variant
    confidence_proxy = min(100.0, max(0.0, best_score / 20.0))
    return best_text, confidence_proxy, best_image


# Backward-compatible private alias for older internal imports.
_choose_best_text = choose_best_text
