"""Local text and field extraction for expense receipts and tickets."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import fitz
import numpy as np
import pytesseract
from PIL import Image, ImageSequence

from .models import ExpenseDocument


SUPPORTED_DOCUMENT_EXTENSIONS = frozenset(
    {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
)

_DATE_PATTERNS = (
    re.compile(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{4})(?!\d)"),
    re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)"),
)
_DATE_MASK_PATTERN = re.compile(
    r"(?<!\d)(?:\d{1,2}[./-]\d{1,2}[./-](?:\d{2}|\d{4})|\d{4}-\d{1,2}-\d{1,2})(?!\d)"
)
_MONEY_PATTERN = re.compile(
    r"(?<![\d.,])(?:\d{1,3}(?:[ \u00a0.,]\d{3})+|\d+)[.,]\d{2}(?![\d.,])"
)
_DATE_LABELS = (
    "дата чека",
    "дата оплаты",
    "дата оформления",
    "дата покупки",
    "issue date",
    "purchase date",
    "payment date",
    "date",
    "дата",
)
_TRAVEL_DATE_LABELS = (
    "departure",
    "arrival",
    "flight date",
    "date of flight",
    "вылет",
    "прилет",
    "прибыт",
)
_PASSENGER_LABELS = (
    "passenger name",
    "name of passenger",
    "фамилия пассажира",
    "фио пассажира",
)
_NAME_COMPONENT = re.compile(r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё'’.-]*$")


def iter_expense_document_files(source_dir: Path) -> list[Path]:
    """Return supported receipt and ticket files in deterministic path order."""
    return sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    )


def _normalize_money_token(value: str) -> Decimal | None:
    """Normalize one two-decimal OCR money token into an exact Decimal."""
    compact = value.replace("\u00a0", "").replace(" ", "")
    separator_index = max(compact.rfind("."), compact.rfind(","))
    if separator_index <= 0 or len(compact) - separator_index - 1 != 2:
        return None
    integer_part = re.sub(r"[.,]", "", compact[:separator_index])
    decimal_part = compact[separator_index + 1 :]
    if not integer_part.isdigit() or not decimal_part.isdigit():
        return None
    try:
        return Decimal(f"{integer_part}.{decimal_part}")
    except InvalidOperation:
        return None


def extract_max_amount(text: str) -> Decimal | None:
    """Return the maximum two-decimal amount while excluding full date tokens."""
    normalized = text.replace("\u00a0", " ")
    masked = _DATE_MASK_PATTERN.sub(lambda match: " " * len(match.group(0)), normalized)
    amounts = [
        amount
        for match in _MONEY_PATTERN.finditer(masked)
        if (amount := _normalize_money_token(match.group(0))) is not None
    ]
    return max(amounts, default=None)


def _parse_date_match(match: re.Match[str]) -> date | None:
    """Convert one supported date regex match to a date."""
    groups = match.groups()
    try:
        if len(groups[0]) == 4:
            year, month, day = (int(value) for value in groups)
        else:
            day, month, year = (int(value) for value in groups)
        return date(year, month, day)
    except ValueError:
        return None


def extract_document_date(text: str) -> date | None:
    """Prefer labeled purchase or issue dates over generic and travel dates."""
    candidates: list[tuple[int, int, date]] = []
    folded = text.casefold().replace("ё", "е")
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            parsed = _parse_date_match(match)
            if parsed is None:
                continue
            line_start = text.rfind("\n", 0, match.start()) + 1
            context = folded[line_start : match.start()]
            score = 0
            if any(label in context[-60:] for label in _DATE_LABELS):
                score += 10
            if any(label in context[-60:] for label in _TRAVEL_DATE_LABELS):
                score -= 8
            candidates.append((score, -match.start(), parsed))
    if not candidates:
        return None
    return max(candidates)[2]


def _clean_name_candidate(value: str) -> str | None:
    """Return a compact passenger name when a label-adjacent value is plausible."""
    cleaned = value.strip().strip(":;-|,")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return None
    parts = [part for token in cleaned.split() for part in token.split("/") if part]
    meaningful = [part for part in parts if part.casefold().rstrip(".") not in {"mr", "mrs", "ms", "miss", "dr"}]
    if not 2 <= len(meaningful) <= 5:
        return None
    if not all(_NAME_COMPONENT.fullmatch(part) for part in meaningful):
        return None
    return cleaned


def extract_person_name(text: str) -> str | None:
    """Extract a passenger name only when anchored to an explicit field label."""
    lines = [line.strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        folded = line.casefold().replace("ё", "е")
        for label in _PASSENGER_LABELS:
            position = folded.find(label)
            if position < 0:
                continue
            same_line = line[position + len(label) :]
            if candidate := _clean_name_candidate(same_line):
                return candidate
            for next_line in lines[index + 1 : index + 3]:
                if candidate := _clean_name_candidate(next_line):
                    return candidate
    return None


def classify_document_kind(text: str) -> str:
    """Classify extracted text as a receipt, ticket, or unknown expense document."""
    folded = text.casefold().replace("ё", "е")
    if any(
        marker in folded
        for marker in (
            "boarding pass",
            "e-ticket",
            "electronic ticket",
            "passenger name",
            "name of passenger",
            "фамилия пассажира",
            "посадочный талон",
            "авиабилет",
        )
    ):
        return "ticket"
    if any(
        marker in folded
        for marker in ("кассовый чек", "фискальный", "receipt", "чек №", "чек n")
    ):
        return "receipt"
    return "unknown"


def extract_fields_from_text(path: Path, text: str) -> ExpenseDocument:
    """Extract reconciliation fields from already available document text."""
    amount = extract_max_amount(text)
    warnings: list[str] = []
    if amount is None:
        warnings.append("amount_not_found")
    return ExpenseDocument(
        source_path=path,
        amount=amount,
        document_date=extract_document_date(text),
        person_name=extract_person_name(text),
        document_kind=classify_document_kind(text),
        warnings=tuple(warnings),
    )


def _ocr_image(image: Image.Image, lang: str) -> str:
    """OCR one image, trying additional orientations only when amount is absent."""
    candidates: list[str] = []
    for angle in (0, 90, 270, 180):
        candidate = image if angle == 0 else image.rotate(-angle, expand=True)
        text = pytesseract.image_to_string(
            np.asarray(candidate.convert("RGB")),
            lang=lang,
            config="--psm 6",
            timeout=30,
        )
        candidates.append(text)
        if extract_max_amount(text) is not None:
            return text
    return max(candidates, key=len, default="")


def _read_raster_text(path: Path, lang: str) -> str:
    """OCR all raster frames and return combined text."""
    texts: list[str] = []
    with Image.open(path) as image:
        for frame in ImageSequence.Iterator(image):
            texts.append(_ocr_image(frame.copy().convert("RGB"), lang))
    return "\n".join(texts)


def _read_pdf_text(path: Path, lang: str) -> str:
    """Prefer native PDF text and use local OCR only when no amount is available."""
    with fitz.open(path) as document:
        if document.needs_pass:
            raise ValueError("Password-protected PDF files are not supported")
        native_text = "\n".join(page.get_text("text") for page in document)
        if extract_max_amount(native_text) is not None:
            return native_text

        texts: list[str] = []
        matrix = fitz.Matrix(200 / 72.0, 200 / 72.0)
        for page in document:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes(
                "RGBA" if pixmap.alpha else "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            ).convert("RGB")
            texts.append(_ocr_image(image, lang))
        return "\n".join(texts) if texts else native_text


def extract_expense_document(path: Path, lang: str) -> ExpenseDocument:
    """Extract reconciliation fields from one supported local receipt or ticket."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = _read_pdf_text(path, lang)
    elif suffix in SUPPORTED_DOCUMENT_EXTENSIONS:
        text = _read_raster_text(path, lang)
    else:
        raise ValueError(f"Unsupported expense document format: {suffix}")
    return extract_fields_from_text(path, text)
