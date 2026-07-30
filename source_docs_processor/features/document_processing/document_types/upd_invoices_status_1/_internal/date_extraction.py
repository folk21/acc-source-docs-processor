"""Date normalization and source-aware selection for scanned UPD."""

from __future__ import annotations

import re

from ...._internal.date_normalization import (
    RUSSIAN_MONTHS_GENITIVE,
    normalize_date as normalize_strict_date,
)


MONTHS_RU = RUSSIAN_MONTHS_GENITIVE


def _month_from_ocr_token(token: str) -> str | None:
    """Map a Russian month token or noisy OCR fragment to a two-digit month."""
    cleaned = re.sub(r"[^а-яёa-z0-9]+", "", token.lower())
    if cleaned in MONTHS_RU:
        return MONTHS_RU[cleaned]
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


def normalize_date(raw: str | None) -> str | None:
    """Normalize a UPD date, including conservative noisy OCR month aliases."""
    strict = normalize_strict_date(raw)
    if strict or not raw:
        return strict

    value = raw.strip().lower().replace("г.", "").replace("г", "")
    value = value.replace(",", " ").replace("—", " ").replace("–", " ")
    value = re.sub(r"\s+", " ", value)
    textual = re.search(
        r"(\d{1,2})\s+([а-яёa-z0-9]{3,20})\s+(\d{4})",
        value,
        flags=re.IGNORECASE,
    )
    if not textual:
        return None
    day, month_token, year = textual.groups()
    month = _month_from_ocr_token(month_token)
    if month is None:
        return None
    day_value = int(day)
    year_value = int(year)
    if not (1 <= day_value <= 31 and 2020 <= year_value <= 2035):
        return None
    return f"{day_value:02d}-{month}-{year_value}"


def extract_date_from_mixed_ocr_text(raw: str | None) -> str | None:
    """Recover a date from noisy OCR snippets produced by targeted date crops."""
    if not raw:
        return None
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
        month = _month_from_ocr_token(token)
        if month:
            break
    if not month:
        month = _month_from_ocr_token(raw)
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
    `2 апреля 2021 г. № 534`. OCR may read that date when the actual document
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
) -> tuple[str | None, str | None]:
    """Choose a document date using source priority and template-date filtering.

    The shipment row (`Документ об отгрузке`) repeats the actual document date
    and is usually more reliable than the top-right header area because the
    latter is close to the UPD form service text. Therefore, a valid shipment
    date is allowed to override an existing header/general OCR date.
    """
    crop_date = (
        extract_date_from_mixed_ocr_text(crop_date_text)
        if crop_date_text
        else None
    )

    if shipment_date:
        if current_date and current_date != shipment_date:
            return shipment_date, "document_date_replaced_by_shipment_row"
        return (
            shipment_date,
            "document_date_from_shipment_row" if not current_date else None,
        )

    if current_date and is_form_template_date(current_date, combined_text):
        if crop_date and not is_form_template_date(crop_date, combined_text):
            return crop_date, "ignored_form_template_date_used_crop_date"
        return None, "ignored_form_template_date"

    if current_date:
        return current_date, None

    if crop_date and not is_form_template_date(crop_date, combined_text):
        return crop_date, "document_date_from_target_crop"

    return None, None
