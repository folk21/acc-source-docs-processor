"""Generic whitespace normalization helpers."""

from __future__ import annotations

import re


def normalize_inline_whitespace(value: str) -> str:
    """Collapse all whitespace into single spaces and trim the result."""
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def normalize_multiline_whitespace(value: str) -> str:
    """Normalize horizontal OCR whitespace while retaining line separation."""
    normalized = value.replace("\u00a0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\s*\n\s*", "\n", normalized)
    return normalized.strip()
