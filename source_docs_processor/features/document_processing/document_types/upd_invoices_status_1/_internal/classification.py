"""Primary-document and continuation classification for scanned UPD."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .continuation import is_probable_continuation_page


@dataclass(frozen=True)
class PageClassification:
    """Recognition classification and status-diagnostic state for one page."""

    is_upd: bool
    is_continuation: bool
    status_warning: bool


def is_upd_invoice_transfer(text: str, status: str | None) -> bool:
    """Detect a UPD status 1 document using status and header markers."""
    compact = re.sub(r"\s+", " ", text.lower())
    has_invoice = bool(re.search(r"сч[её]т\s*[-–]?\s*фактур", compact))
    has_transfer_doc = "передаточ" in compact or "универсальн" in compact
    if status == "1":
        return has_invoice and has_transfer_doc
    status_one_text = bool(
        re.search(
            r"1\s*[-–]\s*сч[её]т\s*[-–]?\s*фактура\s*и\s*передаточ",
            compact,
        )
    )
    return has_invoice and has_transfer_doc and status_one_text


def classify_page(
    text: str,
    status: str | None,
    document_number: str | None,
    document_date: str | None,
    has_shipment_row: bool,
) -> PageClassification:
    """Classify one OCR page while preserving conservative fallback behavior."""
    is_upd = is_upd_invoice_transfer(text, status)
    is_continuation = False if is_upd else is_probable_continuation_page(text)
    status_warning = False
    compact = re.sub(r"\s+", " ", text.lower())

    if not is_upd and document_number and document_date:
        has_invoice_marker = bool(
            re.search(r"сч[её]т\s*[-–]?\s*фактур", compact)
        )
        has_transfer_marker = "универсальн" in compact or "передаточ" in compact
        if has_invoice_marker and (
            has_transfer_marker or (status == "1" and has_shipment_row)
        ):
            is_upd = True
            status_warning = True

    return PageClassification(
        is_upd=is_upd,
        is_continuation=is_continuation,
        status_warning=status_warning,
    )
