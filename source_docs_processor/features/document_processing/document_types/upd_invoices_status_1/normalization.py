"""Shared OCR text normalization for scanned UPD extraction."""

from __future__ import annotations

import re


def normalize_spaces(text: str) -> str:
    """Normalize OCR whitespace without destroying line boundaries."""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip()
