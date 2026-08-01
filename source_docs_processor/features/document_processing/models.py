"""Public result, progress, and document-type metadata models."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypeAlias


RegistryValue: TypeAlias = str | int | float | bool | None


@dataclass
class ExtractedDocumentItem:
    """One extracted goods or service line from an accounting document."""

    line_number: int | None = None
    name: str | None = None
    unit: str | None = None
    quantity: str | None = None
    unit_price: str | None = None
    amount_without_tax: str | None = None
    tax_rate: str | None = None
    tax_amount: str | None = None
    total_amount: str | None = None
    confidence: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExtractedDocument:
    """Generic metadata and processing state for one input document.

    Common accounting fields live directly on the model so processors for UPD,
    receipts, acts, invoices, and other documents can share the same pipeline.
    Repeating goods or service lines live in ``items``. Template-specific scalar
    values belong in ``extra_fields`` and are exposed by the selected registry.
    """

    source_path: Path
    document_type: str | None = None
    is_recognized: bool = False
    status: str | None = None
    document_number: str | None = None
    document_date: str | None = None
    document_datetime: str | None = None
    issuer_name: str | None = None
    issuer_inn: str | None = None
    issuer_kpp: str | None = None
    recipient_name: str | None = None
    recipient_inn: str | None = None
    recipient_kpp: str | None = None
    amount_without_tax: str | None = None
    tax_amount: str | None = None
    total_amount: str | None = None
    currency: str | None = None
    description: str | None = None
    confidence: int = 0
    rotation_degrees: int = 0
    is_continuation_page: bool = False
    continuation_page_number: int | None = None
    continued_from: str | None = None
    destination_path: Path | None = None
    error: str | None = None
    text_preview: str = ""
    warnings: list[str] = field(default_factory=list)
    items: list[ExtractedDocumentItem] = field(default_factory=list)
    extra_fields: dict[str, RegistryValue] = field(default_factory=dict)

    @property
    def is_primary_document(self) -> bool:
        """Return True for a recognized standalone document page."""
        return self.is_recognized and not self.is_continuation_page

    def inherit_common_metadata(self, previous: "ExtractedDocument") -> None:
        """Fill missing continuation metadata from the previous primary page.

        A continuation page normally has no independent number, date, or party
        fields. Existing values on the continuation page win, which allows a
        document-specific processor to preserve page-level data when available.
        """
        common_fields = (
            "document_type",
            "status",
            "document_number",
            "document_date",
            "document_datetime",
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
        )
        for field_name in common_fields:
            if getattr(self, field_name) is None:
                setattr(self, field_name, getattr(previous, field_name))

        inherited_extra = dict(previous.extra_fields)
        inherited_extra.update(self.extra_fields)
        self.extra_fields = inherited_extra
        self.is_recognized = True


ProcessingProgressEvent: TypeAlias = Literal[
    "scan_started",
    "file_started",
    "file_finished",
    "registry_written",
    "run_finished",
]


@dataclass(frozen=True)
class ProcessingProgress:
    """One synchronous progress event emitted during folder processing."""

    event: ProcessingProgressEvent
    file_index: int = 0
    file_count: int = 0
    source_path: Path | None = None
    recognized: bool | None = None
    error: str | None = None
    output_path: Path | None = None


ProcessingProgressCallback: TypeAlias = Callable[[ProcessingProgress], None]


@dataclass(frozen=True)
class DocumentTypeMetadata:
    """UI-facing description and capabilities of one registered document type."""

    identifier: str
    display_name: str
    description: str
    supported_extensions: tuple[str, ...]
    supports_deep_ocr: bool
    supports_auto_rotate: bool
    supports_debug_crops: bool


@dataclass
class ProcessingSummary:
    """Structured outcome and generated artifacts from one processing run."""

    source_root: Path
    output_root: Path | None
    document_type: str
    found_documents: list[ExtractedDocument]
    all_documents: list[ExtractedDocument]
    registry_paths: tuple[Path, ...] = ()
    report_paths: tuple[Path, ...] = ()

    @property
    def recognized_count(self) -> int:
        """Return the number of recognized primary documents."""
        return len(self.found_documents)

    @property
    def processed_count(self) -> int:
        """Return the number of input files represented in the result."""
        return len(self.all_documents)

    @property
    def error_count(self) -> int:
        """Return the number of documents with processing errors."""
        return sum(document.error is not None for document in self.all_documents)

    @property
    def generated_files(self) -> tuple[Path, ...]:
        """Return copied documents, registries, and reports without duplicates."""
        paths = [
            document.destination_path
            for document in self.all_documents
            if document.destination_path is not None
        ]
        paths.extend(self.registry_paths)
        paths.extend(self.report_paths)
        return tuple(dict.fromkeys(paths))

    def __iter__(self) -> Iterator[list[ExtractedDocument]]:
        """Preserve legacy ``found, all_documents = process_folder(...)`` usage."""
        yield self.found_documents
        yield self.all_documents


__all__ = [
    "DocumentTypeMetadata",
    "ExtractedDocument",
    "ExtractedDocumentItem",
    "ProcessingProgress",
    "ProcessingProgressCallback",
    "ProcessingProgressEvent",
    "ProcessingSummary",
]
