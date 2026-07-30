"""Parsing of the repeated `Документ об отгрузке` identity row."""

from __future__ import annotations

import re

from .date_extraction import normalize_date
from .number_extraction import normalize_number


def extract_number_date_from_shipment_document(
    text: str | None,
) -> tuple[str | None, str | None]:
    """Extract number/date from the `Документ об отгрузке` fallback row.

    In these UPD forms the row often looks like `№ п/п 1 № 511 от 21 марта 2023 г.`.
    The first `1` is only the row number, so the algorithm intentionally takes the
    last numeric group before the `от <date>` part.
    """
    if not text:
        return None, None
    compact = re.sub(r"\s+", " ", text)
    compact_lower = compact.lower()
    has_row_marker = re.search(r"№\s*п\s*/?\s*п", compact_lower)
    if not (
        ("документ" in compact_lower and "отгруз" in compact_lower)
        or has_row_marker
    ):
        return None, None
    date_pattern = (
        r"(\d{1,2}\s+[А-Яа-яёЁA-Za-z0-9]{3,20}\s+\d{4}\s*г?\.?"
        r"|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})"
    )

    explicit = re.search(
        rf"№\s*п\s*/?\s*п\s*1\s*(?:№|N|No)?\s*"
        rf"([0-9\s\-/]{{1,15}})\s*от\s*{date_pattern}",
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
        after_last_number_sign = re.split(
            r"(?:№|N|No)",
            before_date,
            flags=re.IGNORECASE,
        )[-1]
        raw_candidates = re.findall(
            r"[0-9][0-9\s\-/]{0,12}",
            after_last_number_sign,
        )
    else:
        raw_candidates = re.findall(r"[0-9][0-9\s\-/]{0,12}", before_date)

    number_candidates = [normalize_number(value) for value in raw_candidates]
    number_candidates = [
        value
        for value in number_candidates
        if value and value != "1" and 2 <= len(value) <= 6
    ]
    number = number_candidates[-1] if number_candidates else None
    date = normalize_date(date_match.group(1))
    return number, date
