"""Money normalization and amount extraction for scanned UPD."""

from __future__ import annotations

import re


def normalize_money(value: str | None) -> str | None:
    """Convert Russian money notation into a machine-friendly decimal string."""
    if not value:
        return None
    cleaned = value.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    if re.fullmatch(r"\d+(?:\.\d{1,2})?", cleaned):
        return cleaned
    return None


def extract_amounts(
    text: str,
) -> tuple[str | None, str | None, str | None]:
    """Extract likely net, VAT, and gross amounts from the standard UPD table."""
    money_values = re.findall(r"\b\d{1,3}(?:\s\d{3})*,\d{2}\b", text)
    normalized = [normalize_money(value) for value in money_values]
    normalized = [value for value in normalized if value]
    if len(normalized) >= 3:
        return normalized[-3], normalized[-2], normalized[-1]
    return None, None, None
