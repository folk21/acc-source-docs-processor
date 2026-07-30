"""Practical recognition confidence scoring for scanned UPD."""

from __future__ import annotations

from .continuation import continuation_marker_score


def calculate_confidence(
    *,
    text: str,
    is_upd: bool,
    is_continuation: bool,
    document_number: str | None,
    document_date: str | None,
    seller_inn: str | None,
    buyer_inn: str | None,
    total_amount: str | None,
) -> int:
    """Calculate the existing field-presence confidence score."""
    confidence = 0
    if is_upd:
        confidence += 35
    if document_number:
        confidence += 25
    if document_date:
        confidence += 15
    if seller_inn:
        confidence += 10
    if buyer_inn:
        confidence += 10
    if total_amount:
        confidence += 5
    if is_continuation:
        confidence = max(confidence, min(90, continuation_marker_score(text)))
    return min(confidence, 100)
