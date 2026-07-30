"""Service description and transport detail extraction for scanned UPD."""

from __future__ import annotations

import re
from .date_extraction import normalize_date
from .number_extraction import normalize_number


def extract_service_text(text: str) -> str | None:
    """Extract the service description from the UPD table row."""
    compact = re.sub(r"\s+", " ", text)
    match = re.search(
        r"(Транспортно[-\s]экспедиционные услуги.{0,600}?)"
        r"(?:Всего к оплате|Руководитель|Главный бухгалтер)",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    match = re.search(
        r"(Транспортно[-\s]экспедиционные услуги.{0,400})",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return None


def extract_transport_details(
    service_text: str | None,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Extract request, vehicle, loading, and unloading details."""
    if not service_text:
        return None, None, None, None, None
    compact = re.sub(r"\s+", " ", service_text)

    request_number = None
    request_date = None
    request_match = re.search(
        r"заявк[аеи]\s*(?:№|N|No)?\s*([0-9\s\-/]+)\s*от\s*"
        r"(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}"
        r"|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
        compact,
        flags=re.IGNORECASE,
    )
    if request_match:
        request_number = normalize_number(request_match.group(1))
        request_date = normalize_date(request_match.group(2))

    vehicle = None
    vehicle_match = re.search(
        r"(?:а/м|автомобиль|машина)\s*"
        r"([A-Za-zА-Яа-я0-9\-\s]{3,40})\s+Погрузка",
        compact,
        flags=re.IGNORECASE,
    )
    if vehicle_match:
        vehicle = vehicle_match.group(1).strip()

    loading_datetime = None
    unloading_datetime = None
    loading_match = re.search(
        r"Погрузка\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\s*"
        r"(\d{1,2}:\d{2})",
        compact,
        flags=re.IGNORECASE,
    )
    if loading_match:
        loading_datetime = (
            f"{normalize_date(loading_match.group(1))} {loading_match.group(2)}"
        )
    unloading_match = re.search(
        r"разгрузка\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\s*"
        r"(\d{1,2}:\d{2})",
        compact,
        flags=re.IGNORECASE,
    )
    if unloading_match:
        unloading_datetime = (
            f"{normalize_date(unloading_match.group(1))} {unloading_match.group(2)}"
        )

    return (
        request_number,
        request_date,
        vehicle,
        loading_datetime,
        unloading_datetime,
    )
