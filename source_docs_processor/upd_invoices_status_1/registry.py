"""CSV registry schema for UPD status 1 processing."""

from __future__ import annotations

from pathlib import Path

from ..models import ExtractedDocument, RegistryValue


class UpdInvoicesStatus1RegistryDefinition:
    """Build the detailed UPD registry while keeping shared writers generic."""

    columns = (
        "source_file",
        "destination_file",
        "document_type",
        "is_recognized",
        "is_continuation_page",
        "continued_from",
        "status",
        "document_number",
        "document_date",
        "document_datetime",
        "rotation_degrees",
        "issuer_name",
        "issuer_inn",
        "issuer_kpp",
        "recipient_name",
        "recipient_inn",
        "recipient_kpp",
        "amount_without_tax",
        "tax_amount",
        "total_amount",
        "currency",
        "description",
        "confidence",
        "warnings",
        "error",
        "text_preview",
        "request_number",
        "request_date",
        "vehicle",
        "loading_datetime",
        "unloading_datetime",
    )

    def build_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> dict[str, RegistryValue]:
        """Build one recognized or unrecognized UPD workflow row."""
        if not document.is_recognized:
            return {
                "source_file": document.source_path.name,
                "document_type": document.document_type or "upd_invoices_status_1",
                "is_recognized": 0,
                "warnings": " | ".join(document.warnings),
                "error": document.error or "",
            }

        return {
            "source_file": document.source_path.name,
            "destination_file": (
                document.destination_path.name if document.destination_path else ""
            ),
            "document_type": document.document_type or "upd_invoices_status_1",
            "is_recognized": int(document.is_recognized),
            "is_continuation_page": int(document.is_continuation_page),
            "continued_from": document.continued_from or "",
            "status": document.status or "",
            "document_number": document.document_number or "",
            "document_date": document.document_date or "",
            "document_datetime": document.document_datetime or "",
            "rotation_degrees": document.rotation_degrees,
            "issuer_name": document.issuer_name or "",
            "issuer_inn": document.issuer_inn or "",
            "issuer_kpp": document.issuer_kpp or "",
            "recipient_name": document.recipient_name or "",
            "recipient_inn": document.recipient_inn or "",
            "recipient_kpp": document.recipient_kpp or "",
            "amount_without_tax": document.amount_without_tax or "",
            "tax_amount": document.tax_amount or "",
            "total_amount": document.total_amount or "",
            "currency": document.currency or "",
            "description": document.description or "",
            "confidence": document.confidence,
            "warnings": " | ".join(document.warnings),
            "error": document.error or "",
            "text_preview": document.text_preview,
            "request_number": document.extra_fields.get("request_number") or "",
            "request_date": document.extra_fields.get("request_date") or "",
            "vehicle": document.extra_fields.get("vehicle") or "",
            "loading_datetime": (
                document.extra_fields.get("loading_datetime") or ""
            ),
            "unloading_datetime": (
                document.extra_fields.get("unloading_datetime") or ""
            ),
        }
