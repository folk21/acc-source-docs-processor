"""Shared data models used by the document processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExtractedDocument:
    """Recognized metadata and processing state for a single input scan.

    The internal field names keep the current UPD/invoice terminology because
    UPD status 1 acts both as an invoice and as a transfer document. User-facing
    documentation can still describe this as a primary document number.
    """

    source_path: Path
    is_upd_invoice_transfer: bool = False
    status: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    seller_name: Optional[str] = None
    seller_inn: Optional[str] = None
    seller_kpp: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_inn: Optional[str] = None
    buyer_kpp: Optional[str] = None
    amount_without_vat: Optional[str] = None
    vat_amount: Optional[str] = None
    amount_with_vat: Optional[str] = None
    service_text: Optional[str] = None
    request_number: Optional[str] = None
    request_date: Optional[str] = None
    vehicle: Optional[str] = None
    loading_datetime: Optional[str] = None
    unloading_datetime: Optional[str] = None
    confidence: int = 0
    rotation_degrees: int = 0
    is_continuation_page: bool = False
    continuation_page_number: Optional[int] = None
    continued_from: Optional[str] = None
    destination_path: Optional[Path] = None
    error: Optional[str] = None
    text_preview: str = ""
    warnings: list[str] = field(default_factory=list)

    def filename_stem(self) -> str:
        """Build the output filename stem for a recognized primary document."""
        number = self.invoice_number or "без_номера"
        if self.invoice_date:
            return f"УПД_{number}_от_{self.invoice_date}"
        return f"УПД_{number}"

    def continuation_filename_stem(self) -> str:
        """Build the output filename stem for a continuation page."""
        page_number = self.continuation_page_number or 2
        return f"{self.filename_stem()}_{page_number}_страница"
