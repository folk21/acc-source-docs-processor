"""Excel registry schema for NPD receipts."""

from __future__ import annotations

from pathlib import Path

from ..models import ExtractedDocument, RegistryValue


class NpdReceiptRegistryDefinition:
    """Define the requested compact column order for recognized NPD receipts."""

    columns = (
        "target_file_name",
        "source_file_name",
        "receipt_date",
        "amount",
        "payee_name",
        "receipt_number",
        "payee_inn",
        "generation_comments",
    )

    headers = {
        "target_file_name": "target_file_name",
        "source_file_name": "source_file_name",
        "receipt_date": "дата",
        "amount": "сумма",
        "payee_name": "фио получателя суммы",
        "receipt_number": "номер_чека",
        "payee_inn": "ИНН получателя",
        "generation_comments": "комментарии о генерации",
    }

    def build_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> dict[str, RegistryValue]:
        """Build one row with the copied target and original source file names."""
        target_file_name = (
            document.destination_path.name
            if document.destination_path is not None
            else ""
        )
        comments = list(document.warnings)
        if document.error:
            comments.append(document.error)

        return {
            "target_file_name": target_file_name,
            "source_file_name": document.source_path.name,
            "receipt_date": document.document_date or document.document_datetime or "",
            "amount": document.total_amount or "",
            "payee_name": document.issuer_name or "",
            "receipt_number": document.document_number or "",
            "payee_inn": document.issuer_inn or "",
            "generation_comments": "; ".join(comments),
        }
