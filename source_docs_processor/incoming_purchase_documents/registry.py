"""Task workbook schema for electronic UPD status 1 documents."""

from __future__ import annotations

from pathlib import Path

from ..models import ExtractedDocument, RegistryValue
from ..registry.task_workbook import WorkbookColumn, WorkbookLink, WorkbookRow


class IncomingPurchaseDocumentsRegistryDefinition:
    """Define document, item, review, and metadata workbook sheets."""

    document_columns = (
        WorkbookColumn(
            "processed",
            "обработано",
            13,
            "dropdown",
            validation_options=("Нет", "Да"),
        ),
        WorkbookColumn(
            "task_id",
            "task_id",
            38,
            hidden=True,
            comment="Internal stable task identifier. Do not edit.",
        ),
        WorkbookColumn("source_file", "исходный файл", 34),
        WorkbookColumn("source_document", "открыть документ", 24),
        WorkbookColumn("is_recognized", "УПД распознан", 15),
        WorkbookColumn("status", "статус УПД", 12),
        WorkbookColumn("document_number", "номер", 16),
        WorkbookColumn("document_date", "дата", 14),
        WorkbookColumn("issuer_name", "продавец", 34),
        WorkbookColumn("issuer_inn", "ИНН продавца", 18, "inn"),
        WorkbookColumn("issuer_kpp", "КПП продавца", 16, "inn"),
        WorkbookColumn("recipient_name", "покупатель", 34),
        WorkbookColumn("recipient_inn", "ИНН покупателя", 18, "inn"),
        WorkbookColumn("recipient_kpp", "КПП покупателя", 16, "inn"),
        WorkbookColumn("amount_without_tax", "сумма без НДС", 18, "amount"),
        WorkbookColumn("tax_amount", "сумма НДС", 16, "amount"),
        WorkbookColumn("total_amount", "сумма с НДС", 18, "amount"),
        WorkbookColumn("currency", "валюта", 10),
        WorkbookColumn("item_count", "позиций", 10, "integer"),
        WorkbookColumn("requires_review", "требует проверки", 18),
        WorkbookColumn("confidence", "уверенность", 13, "integer"),
        WorkbookColumn("generation_comments", "комментарии", 48),
    )

    item_columns = (
        WorkbookColumn(
            "task_id",
            "task_id",
            38,
            hidden=True,
            comment="Internal stable task identifier. Do not edit.",
        ),
        WorkbookColumn("document_number", "номер УПД", 16),
        WorkbookColumn("document_date", "дата УПД", 14),
        WorkbookColumn("line_number", "№ строки", 10, "integer"),
        WorkbookColumn("name", "наименование товара/услуги", 56),
        WorkbookColumn("unit", "единица измерения", 18),
        WorkbookColumn("quantity", "количество", 14, "amount"),
        WorkbookColumn("unit_price", "цена за единицу", 18, "amount"),
        WorkbookColumn("amount_without_tax", "сумма без НДС", 18, "amount"),
        WorkbookColumn("tax_rate", "ставка НДС", 14),
        WorkbookColumn("tax_amount", "сумма НДС", 16, "amount"),
        WorkbookColumn("total_amount", "сумма с НДС", 18, "amount"),
        WorkbookColumn("requires_review", "требует проверки", 18),
        WorkbookColumn("generation_comments", "комментарии", 46),
    )

    review_columns = (
        WorkbookColumn(
            "task_id",
            "task_id",
            38,
            hidden=True,
            comment="Internal stable task identifier. Do not edit.",
        ),
        WorkbookColumn("source_file", "исходный файл", 34),
        WorkbookColumn("source_document", "открыть документ", 24),
        WorkbookColumn("document_number", "номер", 16),
        WorkbookColumn("issue_scope", "область", 16),
        WorkbookColumn("issue", "проблема", 62),
    )

    # The generic single-row contract remains available for callers that inspect
    # registry definitions without invoking the task workbook writer.
    columns = tuple(column.key for column in document_columns)

    def _task_id(self, document: ExtractedDocument) -> str:
        """Return the workflow-assigned stable task identifier."""
        return str(document.extra_fields.get("task_id") or "")

    def _source_link(self, document: ExtractedDocument) -> WorkbookLink | str:
        """Link directly to the original source document."""
        target = document.source_path
        return WorkbookLink(label=target.name, target=target)

    def build_document_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> WorkbookRow:
        """Build one accountant task row for a complete UPD document."""
        comments = list(document.warnings)
        if document.error:
            comments.append(document.error)
        return {
            "processed": "Нет",
            "task_id": self._task_id(document),
            "source_file": str(document.source_path.relative_to(source_root)),
            "source_document": self._source_link(document),
            "is_recognized": "да" if document.is_recognized else "нет",
            "status": document.status or "",
            "document_number": document.document_number or "",
            "document_date": document.document_date or "",
            "issuer_name": document.issuer_name or "",
            "issuer_inn": document.issuer_inn or "",
            "issuer_kpp": document.issuer_kpp or "",
            "recipient_name": document.recipient_name or "",
            "recipient_inn": document.recipient_inn or "",
            "recipient_kpp": document.recipient_kpp or "",
            "amount_without_tax": document.amount_without_tax or "",
            "tax_amount": document.tax_amount or "",
            "total_amount": document.total_amount or "",
            "currency": document.currency or "RUB",
            "item_count": len(document.items),
            "requires_review": (
                "да" if document.extra_fields.get("requires_review") else "нет"
            ),
            "confidence": document.confidence,
            "generation_comments": "; ".join(comments),
        }

    def build_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> dict[str, RegistryValue]:
        """Build a scalar compatibility row without workbook link objects."""
        row = dict(self.build_document_row(document, source_root))
        source_document = row.get("source_document")
        if isinstance(source_document, WorkbookLink):
            row["source_document"] = source_document.label
        return row  # type: ignore[return-value]

    def build_item_rows(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> list[WorkbookRow]:
        """Build one workbook row per extracted goods or service line."""
        rows: list[WorkbookRow] = []
        for item in document.items:
            rows.append(
                {
                    "task_id": self._task_id(document),
                    "document_number": document.document_number or "",
                    "document_date": document.document_date or "",
                    "line_number": item.line_number or "",
                    "name": item.name or "",
                    "unit": item.unit or "",
                    "quantity": item.quantity or "",
                    "unit_price": item.unit_price or "",
                    "amount_without_tax": item.amount_without_tax or "",
                    "tax_rate": item.tax_rate or "",
                    "tax_amount": item.tax_amount or "",
                    "total_amount": item.total_amount or "",
                    "requires_review": "да" if item.warnings else "нет",
                    "generation_comments": "; ".join(item.warnings),
                }
            )
        return rows

    def build_review_rows(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> list[WorkbookRow]:
        """Build explicit review issues for document and item warnings."""
        rows: list[WorkbookRow] = []
        document_issues = list(document.warnings)
        if document.error:
            document_issues.append(document.error)
        for issue in document_issues:
            rows.append(
                {
                    "task_id": self._task_id(document),
                    "source_file": str(document.source_path.relative_to(source_root)),
                    "source_document": self._source_link(document),
                    "document_number": document.document_number or "",
                    "issue_scope": "document",
                    "issue": issue,
                }
            )
        for item in document.items:
            for issue in item.warnings:
                rows.append(
                    {
                        "task_id": self._task_id(document),
                        "source_file": str(document.source_path.relative_to(source_root)),
                        "source_document": self._source_link(document),
                        "document_number": document.document_number or "",
                        "issue_scope": f"item {item.line_number or '-'}",
                        "issue": issue,
                    }
                )
        return rows

    def build_metadata(self) -> dict[str, RegistryValue]:
        """Describe the stable workbook contract for future task aggregation."""
        return {
            "registry_schema": "incoming_purchase_documents_tasks",
            "registry_schema_version": "2",
            "document_type": "incoming_purchase_documents",
        }
