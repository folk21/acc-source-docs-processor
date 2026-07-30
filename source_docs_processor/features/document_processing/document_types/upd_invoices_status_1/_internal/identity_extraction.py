"""Document identity extraction and source reconciliation for scanned UPD."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ...._internal.ocr import OcrResult
from .date_extraction import choose_more_reliable_document_date, normalize_date
from .number_extraction import (
    choose_more_reliable_document_number,
    normalize_number,
)
from .shipment_row import extract_number_date_from_shipment_document


@dataclass(frozen=True)
class DocumentIdentity:
    """Selected document identity plus source-specific diagnostics."""

    document_number: str | None
    document_date: str | None
    shipment_number: str | None
    shipment_date: str | None
    number_warning: str | None
    date_warning: str | None


def extract_invoice_number_and_date(
    text: str,
) -> tuple[str | None, str | None]:
    """Extract document number and date from full OCR or shipment-row text."""
    compact = re.sub(r"\s+", " ", text)
    patterns = [
        r"сч[её]т\s*[-–]?\s*фактура\s*(?:№|N|No)?\s*"
        r"([0-9\s\-/]+)\s*от\s*"
        r"(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}\s*г?\.?)",
        r"сч[её]т\s*[-–]?\s*фактура\s*(?:№|N|No)?\s*"
        r"([0-9\s\-/]+)\s*от\s*"
        r"(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
        r"документ\s+об\s+отгрузке\s*(?:№|N|No)?[^0-9]{0,20}"
        r"([0-9\s\-/]+)\s*от\s*"
        r"(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}\s*г?\.?)",
        r"документ\s+об\s+отгрузке\s*(?:№|N|No)?[^0-9]{0,20}"
        r"([0-9\s\-/]+)\s*от\s*"
        r"(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            return normalize_number(match.group(1)), normalize_date(match.group(2))

    number_match = re.search(
        r"сч[её]т\s*[-–]?\s*фактура\s*(?:№|N|No)?\s*"
        r"([0-9\s\-/]{1,20})",
        compact,
        flags=re.IGNORECASE,
    )
    date_match = re.search(
        r"от\s*(\d{1,2}\s+[А-Яа-яёЁ]+\s+\d{4}\s*г?\.?)",
        compact,
        flags=re.IGNORECASE,
    )
    if not date_match:
        date_match = re.search(
            r"от\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})",
            compact,
            flags=re.IGNORECASE,
        )
    return (
        normalize_number(number_match.group(1)) if number_match else None,
        normalize_date(date_match.group(1)) if date_match else None,
    )


def extract_document_identity(combined_text: str, ocr: OcrResult) -> DocumentIdentity:
    """Select number and date from header, crop, and shipment-row sources."""
    document_number, document_date = extract_invoice_number_and_date(combined_text)

    shipment_source = ocr.targeted_fields.get("shipment_document_text_from_crop")
    if (
        not shipment_source
        and "документ" in combined_text.lower()
        and "отгруз" in combined_text.lower()
    ):
        shipment_source = combined_text
    shipment_number, shipment_date = extract_number_date_from_shipment_document(
        shipment_source
    )

    crop_number = ocr.targeted_fields.get("invoice_number_from_crop")
    if not document_number and crop_number:
        document_number = crop_number
    document_number, number_warning = choose_more_reliable_document_number(
        document_number,
        shipment_number,
    )
    document_date, date_warning = choose_more_reliable_document_date(
        current_date=document_date,
        shipment_date=shipment_date,
        crop_date_text=ocr.targeted_fields.get("invoice_date_text_from_crop"),
        combined_text=combined_text,
    )

    return DocumentIdentity(
        document_number=document_number,
        document_date=document_date,
        shipment_number=shipment_number,
        shipment_date=shipment_date,
        number_warning=number_warning,
        date_warning=date_warning,
    )
