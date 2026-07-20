"""Text normalization and metadata extraction from OCR output."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import ExtractedDocument
from .ocr import OcrResult


MONTHS_RU = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
}


def normalize_spaces(text: str) -> str:
    """Normalize OCR whitespace without destroying line boundaries."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip()


def normalize_number(value: str | None) -> Optional[str]:
    """Keep only digits from a possibly noisy document number."""
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)
    return digits or None

def choose_more_reliable_document_number(
    current_number: str | None,
    fallback_number: str | None,
) -> tuple[Optional[str], Optional[str]]:
    """Choose a document number after comparing header and fallback candidates.

    OCR may append one or two neighboring digits to the real UPD number. This
    happens when the number crop is slightly too wide or when the shipment row
    includes the row marker `№ п/п 1`. If one candidate is a clean 3-4 digit
    prefix of another candidate, the shorter prefix is considered more reliable.
    """
    current = normalize_number(current_number)
    fallback = normalize_number(fallback_number)

    if not current:
        return fallback, "document_number_from_fallback" if fallback else None
    if not fallback:
        if len(current) >= 5:
            trimmed = _trim_suspicious_trailing_digits(current)
            if trimmed != current:
                return trimmed, "trimmed_suspicious_trailing_digits"
        return current, None

    if current == fallback:
        return current, None

    if len(fallback) >= 3 and current.startswith(fallback) and len(current) > len(fallback):
        return fallback, "document_number_replaced_by_shorter_fallback_prefix"
    if len(current) >= 3 and fallback.startswith(current) and len(fallback) > len(current):
        return current, "document_number_kept_as_shorter_header_prefix"

    if len(current) <= 2 and len(fallback) >= 3:
        return fallback, "document_number_replaced_because_header_was_too_short"
    if len(fallback) <= 2 and len(current) >= 3:
        return current, None

    if len(current) >= 5:
        trimmed = _trim_suspicious_trailing_digits(current)
        if fallback == trimmed:
            return fallback, "document_number_replaced_by_trimmed_fallback"
        if trimmed != current:
            return trimmed, "trimmed_suspicious_trailing_digits"

    return current, None


def _trim_suspicious_trailing_digits(value: str) -> str:
    """Trim likely over-read form/date digits from a document number candidate."""
    if len(value) == 5 and value[-2:] in {"01", "07", "10", "20", "23"}:
        return value[:-2]
    return value


def normalize_money(value: str | None) -> Optional[str]:
    """Convert Russian money notation into a machine-friendly decimal string."""
    if not value:
        return None
    cleaned = value.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    if re.fullmatch(r"\d+(?:\.\d{1,2})?", cleaned):
        return cleaned
    return None


def _month_from_token(token: str) -> Optional[str]:
    """Map a Russian month token or noisy OCR fragment to a two-digit month."""
    cleaned = re.sub(r"[^а-яёa-z0-9]+", "", token.lower())
    if cleaned in MONTHS_RU:
        return MONTHS_RU[cleaned]
    # Common OCR fragments for Russian month names in these UPD scans.
    aliases = [
        ("01", ("янв",)),
        ("02", ("фев",)),
        ("03", ("мар",)),
        ("04", ("апр",)),
        ("05", ("мая",)),
        ("06", ("июн",)),
        ("07", ("июл",)),
        ("08", ("авг",)),
        ("09", ("сен",)),
        ("10", ("окт", "ктябр")),
        ("11", ("нояб",)),
        ("12", ("дек", "кабр", "хабр", "a6p")),
    ]
    for month, fragments in aliases:
        if any(fragment in cleaned for fragment in fragments):
            return month
    return None


def normalize_date(raw: str | None) -> Optional[str]:
    """Normalize numeric or Russian textual dates to DD-MM-YYYY."""
    if not raw:
        return None
    value = raw.strip().lower().replace("г.", "").replace("г", "")
    value = value.replace(",", " ").replace("—", " ").replace("–", " ")
    value = re.sub(r"\s+", " ", value)

    # Numeric dates are common in transport details and are easier to validate
    # than textual dates, so handle them before Russian month names.
    numeric = re.search(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})", value)
    if numeric:
        day, month, year = numeric.groups()
        if len(year) == 2:
            year = "20" + year
        day_i = int(day)
        month_i = int(month)
        year_i = int(year)
        if not (1 <= day_i <= 31 and 1 <= month_i <= 12 and 2020 <= year_i <= 2035):
            return None
        return f"{day_i:02d}-{month_i:02d}-{year_i}"

    # Textual dates are used in the UPD header and shipment row, for example
    # `21 марта 2023 г.`. Month tokens may be distorted by OCR, so the month is
    # resolved through a tolerant alias table.
    textual = re.search(
        r"(\d{1,2})\s+([а-яёa-z0-9]{3,20})\s+(\d{4})",
        value,
        flags=re.IGNORECASE,
    )
    if textual:
        day, month_name, year = textual.groups()
        month = _month_from_token(month_name)
        if month:
            day_i = int(day)
            year_i = int(year)
            if not (1 <= day_i <= 31 and 2020 <= year_i <= 2035):
                return None
            return f"{day_i:02d}-{month}-{year_i}"
    return None

def extract_date_from_mixed_ocr_text(raw: str | None) -> Optional[str]:
    """Recover a date from noisy OCR snippets produced by targeted date crops."""
    if not raw:
        return None
    # First try normal date parsing. If the crop is too noisy, recover the date
    # from separate day/month/year fragments below.
    direct = normalize_date(raw)
    if direct:
        return direct
    year_match = re.search(r"20\d{2}", raw)
    if not year_match:
        return None
    year = year_match.group(0)
    if not (2020 <= int(year) <= 2035):
        return None

    month = None
    for token in re.findall(r"[А-Яа-яЁёA-Za-z0-9]{3,20}", raw):
        month = _month_from_token(token)
        if month:
            break
    if not month:
        month = _month_from_token(raw)
    if not month:
        return None

    day_candidates: list[int] = []
    for line in raw.splitlines():
        line_match = re.search(r"(?<!\d)(\d{1,2})(?!\d)", line)
        if line_match:
            value = int(line_match.group(1))
            if 1 <= value <= 31:
                day_candidates.append(value)
    if not day_candidates:
        return None
    two_digit = [value for value in day_candidates if value >= 10]
    day = max(two_digit or day_candidates)
    return f"{day:02d}-{month}-{year}"


def is_form_template_date(date_value: str | None, text: str) -> bool:
    """Return True when a date is likely from the UPD form template text.

    The standard UPD form has a service note in the top-right corner with
    `2 апреля 2021 г. № 534`. OCR may read that date when the real document
    date in the header is weak or partially covered. This date must not be
    used as the primary document date.
    """
    if date_value != "02-04-2021":
        return False
    compact = re.sub(r"\s+", " ", text.lower())
    template_markers = (
        "постановлен",
        "правительств",
        "российской федерации",
        "1137",
        "534",
    )
    return any(marker in compact for marker in template_markers)


def choose_more_reliable_document_date(
    current_date: str | None,
    shipment_date: str | None,
    crop_date_text: str | None,
    combined_text: str,
) -> tuple[Optional[str], Optional[str]]:
    """Choose a document date using source priority and template-date filtering.

    The shipment row (`Документ об отгрузке`) repeats the real document date
    and is usually more reliable than the top-right header area because the
    latter is close to the UPD form service text. Therefore, a valid shipment
    date is allowed to override an existing header/general OCR date.
    """
    crop_date = extract_date_from_mixed_ocr_text(crop_date_text) if crop_date_text else None

    # The shipment row is the safest source because it is located near the left
    # form fields and does not contain the `2 April 2021` form-template date.
    if shipment_date:
        if current_date and current_date != shipment_date:
            return shipment_date, "document_date_replaced_by_shipment_row"
        return shipment_date, "document_date_from_shipment_row" if not current_date else None

    # If OCR fell back to the service date from the standard UPD form, discard
    # it or replace it with a targeted date crop when available.
    if current_date and is_form_template_date(current_date, combined_text):
        if crop_date and not is_form_template_date(crop_date, combined_text):
            return crop_date, "ignored_form_template_date_used_crop_date"
        return None, "ignored_form_template_date"

    if current_date:
        return current_date, None

    if crop_date and not is_form_template_date(crop_date, combined_text):
        return crop_date, "document_date_from_target_crop"

    return None, None


def _extract_invoice_number_and_date(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract document number and date from full OCR text or shipment row text."""
    compact = re.sub(r"\s+", " ", text)

    # Try explicit number+date patterns first. They provide the cleanest result
    # because the number and date come from the same OCR context.
    patterns = [
        r"сч[её]т\s*[-–]?\s*фактура\s*(?:№|N|No)?\s*([0-9\s\-/]+)\s*от\s*(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}\s*г?\.?)",
        r"сч[её]т\s*[-–]?\s*фактура\s*(?:№|N|No)?\s*([0-9\s\-/]+)\s*от\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
        r"документ\s+об\s+отгрузке\s*(?:№|N|No)?[^0-9]{0,20}([0-9\s\-/]+)\s*от\s*(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}\s*г?\.?)",
        r"документ\s+об\s+отгрузке\s*(?:№|N|No)?[^0-9]{0,20}([0-9\s\-/]+)\s*от\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            return normalize_number(match.group(1)), normalize_date(match.group(2))

    # If the full pair is not recognized, still return partial candidates.
    # Later adjustment logic can combine them with targeted crops or shipment-row OCR.
    number_match = re.search(r"сч[её]т\s*[-–]?\s*фактура\s*(?:№|N|No)?\s*([0-9\s\-/]{1,20})", compact, flags=re.IGNORECASE)
    date_match = re.search(r"от\s*(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}\s*г?\.?)", compact, flags=re.IGNORECASE)
    if not date_match:
        date_match = re.search(r"от\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})", compact, flags=re.IGNORECASE)
    return (
        normalize_number(number_match.group(1)) if number_match else None,
        normalize_date(date_match.group(1)) if date_match else None,
    )



def _extract_number_date_from_shipment_document(text: str | None) -> tuple[Optional[str], Optional[str]]:
    """Extract number/date from the `Документ об отгрузке` fallback row.

    In these UPD forms the row often looks like `№ п/п 1 № 511 от 21 марта 2023 г.`.
    The first `1` is only the row number, so the algorithm intentionally takes the
    last numeric group before the `от <date>` part.
    """
    if not text:
        return None, None
    compact = re.sub(r"\s+", " ", text)
    compact_lower = compact.lower()
    if not (("документ" in compact_lower and "отгруз" in compact_lower) or re.search(r"№\s*п\s*/?\s*п", compact_lower)):
        return None, None
    date_pattern = r"(\d{1,2}\s+[А-Яа-яёЁA-Za-z0-9]{3,20}\s+\d{4}\s*г?\.?|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})"

    # The most stable case is an explicit row-number marker followed by the real
    # document number and `от <date>`. Ignore the first `1`, which is just the row.
    explicit = re.search(
        rf"№\s*п\s*/?\s*п\s*1\s*(?:№|N|No)?\s*([0-9\s\-/]{{1,15}})\s*от\s*{date_pattern}",
        compact,
        flags=re.IGNORECASE,
    )
    if explicit:
        return normalize_number(explicit.group(1)), normalize_date(explicit.group(2))

    date_match = re.search(rf"\bот\s*{date_pattern}", compact, flags=re.IGNORECASE)
    if not date_match:
        return None, None

    before_date = compact[: date_match.start()]
    if "документ" in before_date.lower() and "отгруз" in before_date.lower():
        # Prefer the document number after the last № sign before the date.
        after_last_number_sign = re.split(r"(?:№|N|No)", before_date, flags=re.IGNORECASE)[-1]
        number_candidates = [normalize_number(value) for value in re.findall(r"[0-9][0-9\s\-/]{0,12}", after_last_number_sign)]
    else:
        number_candidates = [normalize_number(value) for value in re.findall(r"[0-9][0-9\s\-/]{0,12}", before_date)]

    number_candidates = [value for value in number_candidates if value and value != "1" and 2 <= len(value) <= 6]
    number = number_candidates[-1] if number_candidates else None
    date = normalize_date(date_match.group(1))
    return number, date


def _continuation_marker_score(text: str) -> int:
    """Score OCR text as a probable continuation page of a UPD document."""
    compact = re.sub(r"\s+", " ", text.lower())
    score = 0
    markers = [
        ("наименование экономического субъекта", 35),
        ("составителя документа", 35),
        ("ответственный за правильность", 30),
        ("оформления факта хозяйственной жизни", 25),
        ("м.п", 15),
        ("подпись", 10),
        ("должность", 10),
        ("траст", 15),
        ("эталон", 15),
    ]
    for marker, weight in markers:
        if marker in compact:
            score += weight

    # Do not classify a normal first page as a continuation merely because it also
    # contains signature blocks at the bottom.
    if re.search(r"сч[её]т\s*[-–]?\s*фактур", compact) or "универсальн" in compact:
        score -= 80
    return max(score, 0)


def _is_probable_continuation_page(text: str) -> bool:
    """Return True when OCR markers point to a page 2 without the invoice header."""
    return _continuation_marker_score(text) >= 60

def _extract_inn_kpp_after_label(text: str, label: str) -> tuple[Optional[str], Optional[str]]:
    """Extract INN/KPP pair located after a tolerant OCR-aware label pattern."""
    # OCR often turns ИНН/КПП into VHH/KNN, so use a tolerant label pattern.
    label_pattern = label.replace(" ", r"\s+")
    regex = rf"{label_pattern}[^0-9]{{0,40}}(\d{{10}})\s*/\s*(\d{{9}})"
    match = re.search(regex, text, flags=re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None, None


def _extract_party_name(text: str, label: str) -> Optional[str]:
    """Extract a seller or buyer legal name following the given field label."""
    compact = re.sub(r"\s+", " ", text)
    match = re.search(rf"{label}\s*[:：]?\s*(ООО\s*[\"“”']?[^\n\r;()]+)", compact, flags=re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        name = re.sub(r"\s{2,}", " ", name)
        return name[:80]
    return None


def _extract_amounts(text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract likely net, VAT, and gross amounts from the standard UPD table."""
    money_values = re.findall(r"\b\d{1,3}(?:\s\d{3})*,\d{2}\b", text)
    normalized = [normalize_money(v) for v in money_values]
    normalized = [v for v in normalized if v]
    # In the standard UPD table the last three visible amounts are often net, VAT, gross.
    if len(normalized) >= 3:
        return normalized[-3], normalized[-2], normalized[-1]
    return None, None, None


def _extract_service_text(text: str) -> Optional[str]:
    """Extract the service description from the UPD table row.

    The service row contains useful transport details, but it is densely printed
    and often split across OCR lines. The regex therefore captures a bounded
    window after the service marker instead of relying on exact table columns.
    """
    compact = re.sub(r"\s+", " ", text)
    match = re.search(r"(Транспортно[-\s]экспедиционные услуги.{0,600}?)(?:Всего к оплате|Руководитель|Главный бухгалтер)", compact, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"(Транспортно[-\s]экспедиционные услуги.{0,400})", compact, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _extract_transport_details(service_text: str | None) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Extract request, vehicle, loading, and unloading details from service text."""
    if not service_text:
        return None, None, None, None, None
    compact = re.sub(r"\s+", " ", service_text)

    # Request number/date is useful for the transport registry but should not be
    # confused with the primary document number/date used in output filenames.
    request_number = None
    request_date = None
    request_match = re.search(r"заявк[аеи]\s*(?:№|N|No)?\s*([0-9\s\-/]+)\s*от\s*(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})", compact, flags=re.IGNORECASE)
    if request_match:
        request_number = normalize_number(request_match.group(1))
        request_date = normalize_date(request_match.group(2))

    # Vehicle details are taken from the free-form service cell. Stop the match
    # at `Погрузка` to avoid swallowing loading dates into the vehicle field.
    vehicle = None
    vehicle_match = re.search(r"(?:а/м|автомобиль|машина)\s*([A-Za-zА-Яа-я0-9\-\s]{3,40})\s+Погрузка", compact, flags=re.IGNORECASE)
    if vehicle_match:
        vehicle = vehicle_match.group(1).strip()

    loading_datetime = None
    unloading_datetime = None
    loading_match = re.search(r"Погрузка\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\s*(\d{1,2}:\d{2})", compact, flags=re.IGNORECASE)
    if loading_match:
        loading_datetime = f"{normalize_date(loading_match.group(1))} {loading_match.group(2)}"
    unloading_match = re.search(r"разгрузка\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\s*(\d{1,2}:\d{2})", compact, flags=re.IGNORECASE)
    if unloading_match:
        unloading_datetime = f"{normalize_date(unloading_match.group(1))} {unloading_match.group(2)}"

    return request_number, request_date, vehicle, loading_datetime, unloading_datetime


def _is_upd_invoice_transfer(text: str, status: str | None) -> bool:
    """Detect a UPD status 1 document using status and header markers."""
    compact = re.sub(r"\s+", " ", text.lower())
    has_invoice = bool(re.search(r"сч[её]т\s*[-–]?\s*фактур", compact))
    has_transfer_doc = "передаточ" in compact or "универсальн" in compact
    if status == "1":
        return has_invoice and has_transfer_doc
    # Fallback is intentionally conservative: it requires a direct status explanation.
    status_one_text = bool(re.search(r"1\s*[-–]\s*сч[её]т\s*[-–]?\s*фактура\s*и\s*передаточ", compact))
    return has_invoice and has_transfer_doc and status_one_text


def extract_document(source_path: Path, ocr: OcrResult) -> ExtractedDocument:
    """Convert OCR output into structured document metadata."""
    combined = normalize_spaces(ocr.header_text + "\n" + ocr.text + "\n" + getattr(ocr, "targeted_text", ""))
    invoice_number, invoice_date = _extract_invoice_number_and_date(combined)

    # The shipment row is handled as a first-class fallback source because it
    # repeats the real document number and date in a cleaner area of the form.
    shipment_source = getattr(ocr, "shipment_document_text_from_crop", None)
    if not shipment_source and "документ" in combined.lower() and "отгруз" in combined.lower():
        shipment_source = combined
    shipment_number, shipment_date = _extract_number_date_from_shipment_document(shipment_source)
    crop_number = getattr(ocr, "invoice_number_from_crop", None)

    # Prefer the most document-like number candidate before using it for output
    # filenames. The shipment row is especially useful for rejecting numbers
    # where OCR appended a stray trailing digit.
    if not invoice_number and crop_number:
        invoice_number = crop_number
    invoice_number, number_adjustment_warning = choose_more_reliable_document_number(invoice_number, shipment_number)

    # Date selection is intentionally source-aware. It must avoid the static form
    # template date from the top-right government-resolution note.
    invoice_date, date_adjustment_warning = choose_more_reliable_document_date(
        current_date=invoice_date,
        shipment_date=shipment_date,
        crop_date_text=getattr(ocr, "invoice_date_text_from_crop", None),
        combined_text=combined,
    )

    # Secondary fields are best-effort metadata for the registry. They do not
    # decide whether a file is copied, but they help manual verification.
    seller_inn, seller_kpp = _extract_inn_kpp_after_label(combined, r"(?:ИНН|VHH|ИHH)\s*/\s*(?:КПП|KNN|КNN)\s+продавца")
    buyer_inn, buyer_kpp = _extract_inn_kpp_after_label(combined, r"(?:ИНН|VHH|ИHH)\s*/\s*(?:КПП|KNN|КNN)\s+покупателя")

    seller_name = _extract_party_name(combined, "Продавец")
    buyer_name = _extract_party_name(combined, "Покупатель")
    amount_without_vat, vat_amount, amount_with_vat = _extract_amounts(combined)
    service_text = _extract_service_text(combined)
    request_number, request_date, vehicle, loading_datetime, unloading_datetime = _extract_transport_details(service_text)

    # Classify the page after extracting key fields. Continuation pages are never
    # allowed to override a successful first-page UPD classification.
    is_upd = _is_upd_invoice_transfer(combined, ocr.status_digit)
    is_continuation = False if is_upd else _is_probable_continuation_page(combined)
    status_warning = False
    compact_combined = re.sub(r"\s+", " ", combined.lower())
    if not is_upd and invoice_number and invoice_date:
        # Some scans have an unreliable status crop but still expose strong UPD
        # markers plus a valid number/date. Accept them with a warning instead
        # of losing the document entirely.
        has_invoice_marker = bool(re.search(r"сч[её]т\s*[-–]?\s*фактур", compact_combined))
        has_transfer_marker = "универсальн" in compact_combined or "передаточ" in compact_combined
        has_shipment_row = bool(getattr(ocr, "shipment_document_text_from_crop", None))
        if has_invoice_marker and (has_transfer_marker or (ocr.status_digit == "1" and has_shipment_row)):
            is_upd = True
            status_warning = True
    # Confidence is a practical score for sorting/diagnostics. It intentionally
    # combines field presence rather than Tesseract's raw confidence values.
    confidence = 0
    if is_upd:
        confidence += 35
    if invoice_number:
        confidence += 25
    if invoice_date:
        confidence += 15
    if seller_inn:
        confidence += 10
    if buyer_inn:
        confidence += 10
    if amount_with_vat:
        confidence += 5
    if is_continuation:
        confidence = max(confidence, min(90, _continuation_marker_score(combined)))

    doc = ExtractedDocument(
        source_path=source_path,
        is_upd_invoice_transfer=is_upd,
        status=ocr.status_digit,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        seller_name=seller_name,
        seller_inn=seller_inn,
        seller_kpp=seller_kpp,
        buyer_name=buyer_name,
        buyer_inn=buyer_inn,
        buyer_kpp=buyer_kpp,
        amount_without_vat=amount_without_vat,
        vat_amount=vat_amount,
        amount_with_vat=amount_with_vat,
        service_text=service_text,
        request_number=request_number,
        request_date=request_date,
        vehicle=vehicle,
        loading_datetime=loading_datetime,
        unloading_datetime=unloading_datetime,
        confidence=min(confidence, 100),
        rotation_degrees=getattr(ocr, "rotation_degrees", 0),
        is_continuation_page=is_continuation,
        text_preview=combined[:500].replace("\n", " "),
    )

    if is_upd and number_adjustment_warning:
        doc.warnings.append(number_adjustment_warning)
    if is_upd and date_adjustment_warning:
        doc.warnings.append(date_adjustment_warning)
    if is_upd and shipment_number and invoice_number == shipment_number:
        doc.warnings.append("Document number was recognized from the shipment row")
    if is_upd and shipment_date and invoice_date == shipment_date:
        doc.warnings.append("Document date was recognized from the shipment row")
    if is_continuation:
        doc.warnings.append("Page was detected as a continuation of the previous recognized document")
    if is_upd and status_warning:
        doc.warnings.append("Status digit was unreliable; document was accepted by UPD invoice markers, number, and date")
    if is_upd and not invoice_number:
        doc.warnings.append("Invoice number was not recognized")
    if is_upd and not invoice_date:
        doc.warnings.append("Invoice date was not recognized")
    if is_upd and getattr(ocr, "invoice_number_from_crop", None) and invoice_number == ocr.invoice_number_from_crop:
        doc.warnings.append("Invoice number was recognized from target crop")
    if is_upd and getattr(ocr, "invoice_date_text_from_crop", None) and invoice_date:
        doc.warnings.append("Invoice date crop was used or checked")
    return doc
