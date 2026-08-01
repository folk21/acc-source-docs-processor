"""Regression tests for the supported document-processing package API."""

from dataclasses import fields
from inspect import Parameter, signature
from pathlib import Path
from typing import get_args

from source_docs_processor.features import document_processing
from source_docs_processor.features.document_processing import api, models
from source_docs_processor.features.document_processing import document_types


_EXPECTED_PUBLIC_NAMES = (
    "DEFAULT_DOCUMENT_TYPE",
    "DOCUMENT_TYPE_METADATA",
    "SUPPORTED_DOCUMENT_TYPES",
    "DocumentTypeMetadata",
    "ExtractedDocument",
    "ExtractedDocumentItem",
    "ProcessingProgress",
    "ProcessingProgressCallback",
    "ProcessingProgressEvent",
    "ProcessingSummary",
    "get_document_type_metadata",
    "process_folder",
)


def _field_names(model: type[object]) -> tuple[str, ...]:
    """Return dataclass field names in their public constructor order."""
    return tuple(field.name for field in fields(model))


def test_document_processing_package_exports_exact_supported_api() -> None:
    """Verify the package facade exposes only supported embedded-call symbols.

    Protected risk: internal services, serializers, or dependency-injection
    contracts must not become accidental package-level compatibility promises.
    """
    assert tuple(document_processing.__all__) == _EXPECTED_PUBLIC_NAMES
    assert tuple(api.__all__) == ("process_folder",)
    assert tuple(models.__all__) == (
        "DocumentTypeMetadata",
        "ExtractedDocument",
        "ExtractedDocumentItem",
        "ProcessingProgress",
        "ProcessingProgressCallback",
        "ProcessingProgressEvent",
        "ProcessingSummary",
    )

    assert document_processing.process_folder is api.process_folder
    assert document_processing.ExtractedDocument is models.ExtractedDocument
    assert document_processing.ExtractedDocumentItem is models.ExtractedDocumentItem
    assert document_processing.ProcessingSummary is models.ProcessingSummary
    assert document_processing.ProcessingProgress is models.ProcessingProgress
    assert document_processing.DocumentTypeMetadata is models.DocumentTypeMetadata


def test_registered_document_type_identifiers_and_metadata_are_stable() -> None:
    """Verify programmatic identifiers and UI-facing metadata remain canonical.

    Protected risk: changing order, spelling, or capability flags would alter CLI
    selection and adapter behavior.
    """
    assert document_processing.DEFAULT_DOCUMENT_TYPE == "upd_invoices_status_1"
    assert document_processing.SUPPORTED_DOCUMENT_TYPES == (
        "upd_invoices_status_1",
        "npd_receipts",
        "incoming_purchase_documents",
    )
    assert tuple(metadata.identifier for metadata in document_processing.DOCUMENT_TYPE_METADATA) == (
        "upd_invoices_status_1",
        "npd_receipts",
        "incoming_purchase_documents",
    )
    assert tuple(document_types.__all__) == (
        "DEFAULT_DOCUMENT_TYPE",
        "DOCUMENT_TYPE_DEFINITIONS",
        "DOCUMENT_TYPE_METADATA",
        "INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE",
        "NPD_RECEIPT_DOCUMENT_TYPE",
        "SUPPORTED_DOCUMENT_TYPES",
        "get_document_type_definition",
        "get_document_type_metadata",
    )

    upd = document_processing.get_document_type_metadata("UPD_INVOICES_STATUS_1")
    assert upd.display_name == "Scanned UPD status 1"
    assert upd.supported_extensions == (
        ".bmp",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
    )
    assert upd.supports_auto_rotate is True

    incoming = document_processing.get_document_type_metadata(
        "incoming_purchase_documents"
    )
    assert incoming.supported_extensions == (".docx", ".pdf")
    assert incoming.supports_auto_rotate is False


def test_public_process_folder_signature_is_stable() -> None:
    """Verify callers select registered behavior without internal DI contracts.

    Protected risk: exposing processors, workflows, or registry definitions in
    the public signature would make internal architecture a compatibility burden.
    """
    parameters = signature(document_processing.process_folder).parameters

    assert tuple(parameters) == (
        "source_dir",
        "output_dir",
        "lang",
        "target_dir_name",
        "dry_run",
        "deep_ocr",
        "auto_rotate",
        "debug_crops",
        "document_type",
        "progress_callback",
    )
    assert parameters["source_dir"].default is Parameter.empty
    assert parameters["output_dir"].default is Parameter.empty
    assert parameters["lang"].default is Parameter.empty
    assert parameters["target_dir_name"].default is None
    assert parameters["dry_run"].default is False
    assert parameters["deep_ocr"].default is False
    assert parameters["auto_rotate"].default is True
    assert parameters["debug_crops"].default is False
    assert parameters["document_type"].default == "upd_invoices_status_1"
    assert parameters["progress_callback"].default is None
    assert get_args(document_processing.ProcessingProgressEvent) == (
        "scan_started",
        "file_started",
        "file_finished",
        "registry_written",
        "run_finished",
    )


def test_public_processing_model_fields_are_stable() -> None:
    """Verify extracted, progress, metadata, and summary model schemas remain stable."""
    assert _field_names(document_processing.ExtractedDocumentItem) == (
        "line_number",
        "name",
        "unit",
        "quantity",
        "unit_price",
        "amount_without_tax",
        "tax_rate",
        "tax_amount",
        "total_amount",
        "confidence",
        "warnings",
    )
    assert _field_names(document_processing.ExtractedDocument) == (
        "source_path",
        "document_type",
        "is_recognized",
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
        "confidence",
        "rotation_degrees",
        "is_continuation_page",
        "continuation_page_number",
        "continued_from",
        "destination_path",
        "error",
        "text_preview",
        "warnings",
        "items",
        "extra_fields",
    )
    assert _field_names(document_processing.ProcessingProgress) == (
        "event",
        "file_index",
        "file_count",
        "source_path",
        "recognized",
        "error",
        "output_path",
    )
    assert _field_names(document_processing.DocumentTypeMetadata) == (
        "identifier",
        "display_name",
        "description",
        "supported_extensions",
        "supports_deep_ocr",
        "supports_auto_rotate",
        "supports_debug_crops",
    )
    assert _field_names(document_processing.ProcessingSummary) == (
        "source_root",
        "output_root",
        "document_type",
        "found_documents",
        "all_documents",
        "registry_paths",
        "report_paths",
    )


def test_processing_summary_exposes_counts_files_and_legacy_unpacking() -> None:
    """Verify UI summaries remain useful without breaking legacy tuple unpacking."""
    copied = Path("output/copied.png")
    registry = Path("output/registry.xlsx")
    report = Path("output/report.txt")
    found = document_processing.ExtractedDocument(
        source_path=Path("source/found.png"),
        is_recognized=True,
        destination_path=copied,
    )
    failed = document_processing.ExtractedDocument(
        source_path=Path("source/failed.png"),
        error="synthetic error",
    )
    summary = document_processing.ProcessingSummary(
        source_root=Path("source"),
        output_root=Path("output"),
        document_type="synthetic",
        found_documents=[found],
        all_documents=[found, failed],
        registry_paths=(registry,),
        report_paths=(report,),
    )

    legacy_found, legacy_all = summary

    assert legacy_found is summary.found_documents
    assert legacy_all is summary.all_documents
    assert summary.recognized_count == 1
    assert summary.processed_count == 2
    assert summary.error_count == 1
    assert summary.generated_files == (copied, registry, report)
