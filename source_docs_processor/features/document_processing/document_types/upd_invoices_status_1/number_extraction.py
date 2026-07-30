"""Document-number normalization and candidate selection for scanned UPD."""

from __future__ import annotations

import re


def normalize_number(value: str | None) -> str | None:
    """Keep only digits from a possibly noisy document number."""
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)
    return digits or None


def choose_more_reliable_document_number(
    current_number: str | None,
    fallback_number: str | None,
) -> tuple[str | None, str | None]:
    """Choose a document number after comparing header and fallback candidates.

    OCR may append one or two neighboring digits to the real UPD number. This
    happens when the number crop is slightly too wide or when the shipment row
    includes the row marker `№ п/п 1`. If one candidate is a clean 3-4 digit
    prefix of another candidate, the shorter prefix is considered more reliable.
    """
    current = normalize_number(current_number)
    fallback = normalize_number(fallback_number)

    if not current:
        return fallback, "document_number_from_fallback" if fallback else None
    if not fallback:
        if len(current) >= 5:
            trimmed = _trim_suspicious_trailing_digits(current)
            if trimmed != current:
                return trimmed, "trimmed_suspicious_trailing_digits"
        return current, None

    if current == fallback:
        return current, None

    if (
        len(fallback) >= 3
        and current.startswith(fallback)
        and len(current) > len(fallback)
    ):
        return fallback, "document_number_replaced_by_shorter_fallback_prefix"
    if (
        len(current) >= 3
        and fallback.startswith(current)
        and len(fallback) > len(current)
    ):
        return current, "document_number_kept_as_shorter_header_prefix"

    if len(current) <= 2 and len(fallback) >= 3:
        return fallback, "document_number_replaced_because_header_was_too_short"
    if len(fallback) <= 2 and len(current) >= 3:
        return current, None

    if len(current) >= 5:
        trimmed = _trim_suspicious_trailing_digits(current)
        if fallback == trimmed:
            return fallback, "document_number_replaced_by_trimmed_fallback"
        if trimmed != current:
            return trimmed, "trimmed_suspicious_trailing_digits"

    return current, None


def _trim_suspicious_trailing_digits(value: str) -> str:
    """Trim likely over-read form/date digits from a document number candidate."""
    if len(value) == 5 and value[-2:] in {"01", "07", "10", "20", "23"}:
        return value[:-2]
    return value
