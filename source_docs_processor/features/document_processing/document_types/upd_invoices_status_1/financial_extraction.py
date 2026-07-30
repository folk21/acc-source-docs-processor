"""UPD-specific amount extraction using shared decimal normalization."""

from __future__ import annotations

import re

from ...normalization.money import normalize_decimal_value


def normalize_money(value: str | None) -> str | None:
    """Normalize one strict UPD money value while preserving its input scale."""
    return normalize_decimal_value(value, maximum_decimal_places=2)


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
