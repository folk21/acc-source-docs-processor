"""OCR pipeline, targeted UPD field recognition, and debug crop output."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from .image_processing import (
    create_ocr_variants,
    crop_header,
    crop_invoice_date_candidates,
    crop_invoice_number_candidates,
    crop_shipment_document_row_candidates,
    crop_continuation_marker_candidates,
    crop_status_area,
    crop_status_digit_candidates,
    crop_transfer_date_candidates,
)


@dataclass
class OcrResult:
    """Raw OCR output plus targeted field-recognition results."""

    text: str
    header_text: str
    status_digit: str | None
    mean_confidence: float
    rotation_degrees: int = 0
    targeted_text: str = ""
    invoice_number_from_crop: str | None = None
    invoice_date_text_from_crop: str | None = None
    shipment_document_text_from_crop: str | None = None
    continuation_text: str = ""


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


def _text_has_invoice_and_transfer_markers(text: str) -> bool:
    """Check whether OCR text looks like a UPD invoice-transfer header."""
    has_invoice = bool(re.search(r"сч[её]т\s*[-–]?\s*фактур", text, re.IGNORECASE))
    has_transfer = bool(re.search(r"универсальн|передаточ", text, re.IGNORECASE))
    has_date = bool(
        re.search(r"\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}", text)
        or re.search(r"\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}", text)
    )
    return has_invoice and has_transfer and has_date


def _choose_best_text(variants: list[np.ndarray], lang: str) -> tuple[str, float, np.ndarray]:
    """Choose the OCR variant with the strongest textual signal."""
    best_text = ""
    best_score = -1.0
    best_image = variants[0]
    for variant in variants:
        text = _ocr_text(variant, lang=lang, psm=6, timeout=4)
        # Use a lightweight score. Full confidence extraction is too slow for large archives.
        keyword_bonus = 100 if re.search(r"сч[её]т\s*[-–]?\s*фактур", text, re.IGNORECASE) else 0
        status_bonus = 50 if re.search(r"универсальн|передаточ", text, re.IGNORECASE) else 0
        score = len(text.strip()) + keyword_bonus + status_bonus
        if score > best_score:
            best_score = score
            best_text = text
            best_image = variant
        # The first grayscale variant is usually enough for good UPD headers.
        # Stop early to avoid slow or stuck OCR attempts on unnecessary preprocessing variants.
        if _text_has_invoice_and_transfer_markers(text):
            confidence_proxy = min(100.0, max(0.0, score / 20.0))
            return text, confidence_proxy, variant
    confidence_proxy = min(100.0, max(0.0, best_score / 20.0))
    return best_text, confidence_proxy, best_image


def _score_digits(raw: str) -> tuple[int, str]:
    """Score a digit-only OCR candidate for the document number.

    Small UPD number crops sometimes include the nearby form marker `(1)` or
    a digit from the date field. The score is therefore intentionally cautious
    with long candidates and later post-processing prefers a reliable shorter
    prefix over an over-read longer value.
    """
    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return 0, ""
    if len(digits) == 1:
        return 10, digits
    if 2 <= len(digits) <= 4:
        return 100 + len(digits), digits
    if len(digits) == 5:
        # Five-digit values are possible, but in the current UPD archive they
        # are often caused by a 3-4 digit number plus an extra neighboring digit.
        return 95, digits
    # Very long strings usually mean that the crop included neighboring labels or dates.
    return 20, digits[:6]


def _prefer_shorter_prefix_candidate(candidates: list[str]) -> str | None:
    """Prefer a stable shorter number when OCR over-reads trailing digits.

    Examples observed in real scans: `430` may also be read as `43007`, and
    `497` may also be read as `4977`. When a 3-4 digit candidate is a prefix of
    a longer candidate, the shorter value is usually the actual document number.
    """
    unique = []
    for value in candidates:
        if value and value not in unique:
            unique.append(value)
    if not unique:
        return None

    for shorter in sorted(unique, key=lambda item: (len(item), item)):
        if len(shorter) < 3 or len(shorter) > 4:
            continue
        for longer in unique:
            if longer != shorter and longer.startswith(shorter) and len(longer) > len(shorter):
                return shorter

    plausible = [value for value in unique if 3 <= len(value) <= 5]
    if plausible:
        # Prefer common 3-4 digit numbers over suspicious 5-digit over-reads.
        plausible.sort(key=lambda item: (0 if 3 <= len(item) <= 4 else 1, len(item)))
        return plausible[0]
    return unique[0]


def _fast_target_variants(crop: np.ndarray, scale: int = 4) -> list[np.ndarray]:
    """Create high-contrast variants for small targeted OCR crops."""
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    upscaled = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    normalized = cv2.normalize(upscaled, None, 0, 255, cv2.NORM_MINMAX)
    thresholded = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return [normalized, thresholded]


def read_invoice_number_by_crop(image: np.ndarray) -> str | None:
    """Read the document number from fixed UPD header crop candidates.

    The first narrow crop is trusted when it returns a 3-5 digit value. Wider
    crops are used only as fallbacks because they can accidentally capture
    nearby date/form digits and append them to the document number.
    """
    all_candidates: list[str] = []

    for crop_index, crop in enumerate(crop_invoice_number_candidates(image)):
        crop_candidates: list[str] = []
        for variant in _fast_target_variants(crop, scale=4):
            text = _ocr_text(variant, lang="eng", psm=7, whitelist="0123456789 ", timeout=2)
            _score, digits = _score_digits(text)
            if digits:
                crop_candidates.append(digits)
                all_candidates.append(digits)

        crop_choice = _prefer_shorter_prefix_candidate(crop_candidates)
        if crop_index == 0 and crop_choice and 3 <= len(crop_choice) <= 5:
            return crop_choice

    return _prefer_shorter_prefix_candidate(all_candidates)

def read_invoice_date_text_by_crop(image: np.ndarray, lang: str) -> str | None:
    """Read document date text from top and fallback transfer-date crops."""
    candidates: list[str] = []
    date_crops = crop_invoice_date_candidates(image) + crop_transfer_date_candidates(image)
    for crop in date_crops:
        for variant in _fast_target_variants(crop, scale=4):
            text = _ocr_text(variant, lang=lang, psm=7, timeout=2).strip()
            if text and re.search(r"\d{4}|\d{1,2}|янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек|ябр|кабр|хабр", text, re.IGNORECASE):
                candidates.append(text)
    if not candidates:
        return None

    unique: list[str] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return "\n".join(unique[:8])



def read_shipment_document_text_by_crop(image: np.ndarray, lang: str) -> str | None:
    """Read the shipment row that repeats the document number and date.

    Keep this fallback fast: it is executed for every candidate page orientation.
    The crop is highly specific, so one OCR mode per crop is usually enough.
    """
    candidates: list[str] = []
    for crop in crop_shipment_document_row_candidates(image):
        variant = _fast_target_variants(crop, scale=3)[0]
        text = _ocr_text(variant, lang=lang, psm=6, timeout=3).strip()
        if text and re.search(r"от|20\d{2}|№|N|п/п", text, re.IGNORECASE):
            candidates.append(text)
    unique: list[str] = []
    for candidate in candidates:
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if candidate and candidate not in unique:
            unique.append(candidate)
    return "\n".join(unique[:4]) if unique else None


def read_continuation_text_by_crop(image: np.ndarray, lang: str) -> str:
    """Read marker areas used to detect continuation pages.

    Continuation pages in the current archive usually expose their signature
    blocks near the top after the correct rotation, so the first crop is enough
    for reliable detection and avoids expensive full-page OCR.
    """
    chunks: list[str] = []
    for crop in crop_continuation_marker_candidates(image)[:2]:
        variant = _fast_target_variants(crop, scale=2)[0]
        text = _ocr_text(variant, lang=lang, psm=6, timeout=3).strip()
        if text:
            chunks.append(text)
    return "\n".join(chunks[:2])

def read_status_digit(image: np.ndarray, lang: str = "eng+rus") -> str | None:
    """Read the UPD status digit from its framed left-side field.

    Tesseract occasionally reads the explanatory text below the framed status
    box and returns `2` even when the boxed value is `1`. To reduce false
    negatives, collect all tight-crop candidates first and prefer `1` when it is
    present anywhere in the dedicated status area.
    """
    tight_candidates: list[str] = []
    for crop in crop_status_digit_candidates(image):
        gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        for variant in _fast_target_variants(gray_crop, scale=6):
            for psm in (6, 10):
                text = _ocr_text(variant, lang="eng", psm=psm, whitelist="0123456789", timeout=2)
                tight_candidates.extend(re.findall(r"[12]", text))

    if "1" in tight_candidates:
        return "1"
    # Do not return `2` from tight crops yet: in this archive false `2` values
    # often come from the explanatory text below the framed status field. First
    # try the wider status area, which can recover the boxed `1`.

    status_area = crop_status_area(image)
    gray_area = cv2.cvtColor(status_area, cv2.COLOR_BGR2GRAY) if len(status_area.shape) == 3 else status_area
    for variant in _fast_target_variants(gray_area, scale=4):
        text = _ocr_text(variant, lang="eng", psm=6, whitelist="0123456789", timeout=2)
        unique_digits = sorted(set(re.findall(r"[12]", text)))
        if len(unique_digits) == 1:
            return unique_digits[0]

    status_area = crop_status_area(image)
    gray = cv2.cvtColor(status_area, cv2.COLOR_BGR2GRAY) if len(status_area.shape) == 3 else status_area
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[tuple[int, int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect = w / max(h, 1)
        if area > 800 and 0.5 <= aspect <= 1.5:
            candidates.append((x, y, w, h, area))

    for x, y, w, h, _area in sorted(candidates, key=lambda item: item[4], reverse=True)[:3]:
        margin_x = max(3, int(w * 0.12))
        margin_y = max(3, int(h * 0.12))
        inner = gray[y + margin_y : y + h - margin_y, x + margin_x : x + w - margin_x]
        if inner.size == 0:
            continue
        inner = cv2.resize(inner, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
        text = _ocr_text(inner, lang="eng", psm=10, whitelist="0123456789", timeout=2)
        match = re.search(r"[12]", text)
        if match:
            return match.group(0)

    # Fallback for cases where contour detection fails.
    enlarged = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    text = _ocr_text(enlarged, lang=lang, psm=6, timeout=3)
    match = re.search(r"статус\D{0,10}([12])", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    if "2" in tight_candidates:
        return "2"
    return None

def _write_debug_crops(debug_dir: Path, image: np.ndarray, header_text: str, targeted_text: str) -> None:
    """Save crops and OCR text to help tune recognition on difficult scans."""
    debug_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(debug_dir / "header.png"), crop_header(image))
    cv2.imwrite(str(debug_dir / "status_area.png"), crop_status_area(image))
    for index, crop in enumerate(crop_status_digit_candidates(image), start=1):
        cv2.imwrite(str(debug_dir / f"status_digit_crop_{index}.png"), crop)
    for index, crop in enumerate(crop_invoice_number_candidates(image), start=1):
        cv2.imwrite(str(debug_dir / f"invoice_number_crop_{index}.png"), crop)
    for index, crop in enumerate(crop_invoice_date_candidates(image), start=1):
        cv2.imwrite(str(debug_dir / f"invoice_date_crop_{index}.png"), crop)
    for index, crop in enumerate(crop_transfer_date_candidates(image), start=1):
        cv2.imwrite(str(debug_dir / f"transfer_date_crop_{index}.png"), crop)
    for index, crop in enumerate(crop_shipment_document_row_candidates(image), start=1):
        cv2.imwrite(str(debug_dir / f"shipment_document_row_crop_{index}.png"), crop)
    for index, crop in enumerate(crop_continuation_marker_candidates(image), start=1):
        cv2.imwrite(str(debug_dir / f"continuation_marker_crop_{index}.png"), crop)
    (debug_dir / "ocr_text.txt").write_text(header_text + "\n\n" + targeted_text, encoding="utf-8")


def run_ocr(
    image: np.ndarray,
    lang: str = "rus+eng",
    deep: bool = False,
    rotation_degrees: int = 0,
    debug_dir: Path | None = None,
) -> OcrResult:
    """Run header OCR and targeted UPD field OCR for one oriented image."""
    header = crop_header(image)
    header_variants = create_ocr_variants(header)
    header_text, header_conf, _ = _choose_best_text(header_variants, lang=lang)

    text = ""
    conf = header_conf
    if deep:
        variants = create_ocr_variants(image)
        text, full_conf, _ = _choose_best_text(variants, lang=lang)
        conf = max(header_conf, full_conf)

    status_digit = read_status_digit(image)
    invoice_number_from_crop = read_invoice_number_by_crop(image)
    invoice_date_text_from_crop = read_invoice_date_text_by_crop(image, lang=lang)
    shipment_document_text_from_crop = read_shipment_document_text_by_crop(image, lang=lang)

    # Continuation-page OCR is needed mainly for pages without the normal UPD header.
    # Skip it for confident first pages to keep large archive processing faster.
    continuation_text = ""
    if not _text_has_invoice_and_transfer_markers(header_text) and not invoice_number_from_crop:
        continuation_text = read_continuation_text_by_crop(image, lang=lang)

    targeted_lines: list[str] = []
    if invoice_number_from_crop:
        targeted_lines.append(f"Счет-фактура № {invoice_number_from_crop}")
    if invoice_date_text_from_crop:
        targeted_lines.append(f"Дата счета-фактуры от {invoice_date_text_from_crop}")
    if shipment_document_text_from_crop:
        targeted_lines.append(f"Документ об отгрузке {shipment_document_text_from_crop}")
    if continuation_text:
        targeted_lines.append(f"Continuation marker text:\n{continuation_text}")
    targeted_text = "\n".join(targeted_lines)

    if debug_dir:
        _write_debug_crops(debug_dir, image, header_text, targeted_text)

    return OcrResult(
        text=text,
        header_text=header_text,
        status_digit=status_digit,
        mean_confidence=conf,
        rotation_degrees=rotation_degrees,
        targeted_text=targeted_text,
        invoice_number_from_crop=invoice_number_from_crop,
        invoice_date_text_from_crop=invoice_date_text_from_crop,
        shipment_document_text_from_crop=shipment_document_text_from_crop,
        continuation_text=continuation_text,
    )
