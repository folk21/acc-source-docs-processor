"""Strict numeric and Russian textual date normalization."""

from __future__ import annotations

import re


RUSSIAN_MONTHS_GENITIVE = {
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


def _validated_date(
    day: str,
    month: str,
    year: str,
    *,
    minimum_year: int,
    maximum_year: int,
) -> str | None:
    """Validate numeric date parts and return DD-MM-YYYY."""
    if len(year) == 2:
        year = f"20{year}"
    try:
        day_value = int(day)
        month_value = int(month)
        year_value = int(year)
    except ValueError:
        return None
    if not (
        1 <= day_value <= 31
        and 1 <= month_value <= 12
        and minimum_year <= year_value <= maximum_year
    ):
        return None
    return f"{day_value:02d}-{month_value:02d}-{year_value}"


def normalize_date(
    value: str | None,
    *,
    minimum_year: int = 2020,
    maximum_year: int = 2035,
) -> str | None:
    """Normalize a strict numeric or Russian textual date to DD-MM-YYYY."""
    if not value:
        return None

    normalized = value.strip().lower().replace("г.", "").replace("г", "")
    normalized = normalized.replace(",", " ").replace("—", " ").replace("–", " ")
    normalized = re.sub(r"\s+", " ", normalized)

    numeric = re.search(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})", normalized)
    if numeric:
        return _validated_date(
            *numeric.groups(),
            minimum_year=minimum_year,
            maximum_year=maximum_year,
        )

    textual = re.search(
        r"(\d{1,2})\s+([а-яё]{3,20})\s+(\d{4})",
        normalized,
        flags=re.IGNORECASE,
    )
    if not textual:
        return None
    day, month_name, year = textual.groups()
    month = RUSSIAN_MONTHS_GENITIVE.get(month_name)
    if month is None:
        return None
    return _validated_date(
        day,
        month,
        year,
        minimum_year=minimum_year,
        maximum_year=maximum_year,
    )
