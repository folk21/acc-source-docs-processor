"""Strict localized decimal parsing and formatting."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def _clean_decimal_text(value: str, *, strip_non_numeric: bool) -> str:
    """Normalize separators and optionally discard surrounding currency text."""
    cleaned = value.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    if not strip_non_numeric:
        return cleaned
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    return match.group(0) if match else ""


def parse_decimal_value(
    value: str | None,
    *,
    strip_non_numeric: bool = False,
) -> Decimal | None:
    """Parse one localized decimal value without applying field semantics."""
    if not value:
        return None
    cleaned = _clean_decimal_text(value, strip_non_numeric=strip_non_numeric)
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def format_decimal_value(value: Decimal, *, decimal_places: int = 2) -> str:
    """Format a decimal value with a fixed number of fractional digits."""
    if decimal_places < 0:
        raise ValueError("decimal_places must not be negative")
    return f"{value:.{decimal_places}f}"


def normalize_decimal_value(
    value: str | None,
    *,
    maximum_decimal_places: int = 2,
) -> str | None:
    """Normalize a strict decimal string while preserving its input scale."""
    if not value:
        return None
    cleaned = _clean_decimal_text(value, strip_non_numeric=False)
    pattern = rf"\d+(?:\.\d{{1,{maximum_decimal_places}}})?"
    if not re.fullmatch(pattern, cleaned):
        return None
    return cleaned
