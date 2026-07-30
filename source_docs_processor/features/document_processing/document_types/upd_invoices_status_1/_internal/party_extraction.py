"""Seller and buyer field extraction for scanned UPD."""

from __future__ import annotations

import re


def extract_inn_kpp_after_label(
    text: str,
    label: str,
) -> tuple[str | None, str | None]:
    """Extract an INN/KPP pair after a tolerant OCR-aware label pattern."""
    label_pattern = label.replace(" ", r"\s+")
    regex = rf"{label_pattern}[^0-9]{{0,40}}(\d{{10}})\s*/\s*(\d{{9}})"
    match = re.search(regex, text, flags=re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None, None


def extract_party_name(text: str, label: str) -> str | None:
    """Extract a seller or buyer legal name following the given field label."""
    compact = re.sub(r"\s+", " ", text)
    match = re.search(
        rf"{label}\s*[:：]?\s*(ООО\s*[\"“”']?[^\n\r;()]+)",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        name = match.group(1).strip()
        name = re.sub(r"\s{2,}", " ", name)
        return name[:80]
    return None
