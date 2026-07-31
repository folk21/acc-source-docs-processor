"""Regression tests for the supported document-processing package API."""

from dataclasses import fields
from inspect import Parameter, signature

from source_docs_processor.features import document_processing
from source_docs_processor.features.document_processing import api, models
from source_docs_processor.features.document_processing import document_types


_EXPECTED_PUBLIC_NAMES = (
    "DEFAULT_DOCUMENT_TYPE",
    "SUPPORTED_DOCUMENT_TYPES",
    "ExtractedDocument",
    "ExtractedDocumentItem",
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
    assert tuple(models.__all__) == ("ExtractedDocument", "ExtractedDocumentItem")

    assert document_processing.process_folder is api.process_folder
    assert document_processing.ExtractedDocument is models.ExtractedDocument
    assert document_processing.ExtractedDocumentItem is models.ExtractedDocumentItem


def test_registered_document_type_identifiers_are_stable() -> None:
    """Verify programmatic and CLI document-type identifiers remain canonical.

    Protected risk: changing order, spelling, or the default would alter registry
    metadata and existing command invocations.
    """
    assert document_processing.DEFAULT_DOCUMENT_TYPE == "upd_invoices_status_1"
    assert document_processing.SUPPORTED_DOCUMENT_TYPES == (
        "upd_invoices_status_1",
        "npd_receipts",
        "incoming_purchase_documents",
    )
    assert tuple(document_types.__all__) == (
        "DEFAULT_DOCUMENT_TYPE",
        "DOCUMENT_TYPE_DEFINITIONS",
        "INCOMING_PURCHASE_DOCUMENTS_DOCUMENT_TYPE",
        "NPD_RECEIPT_DOCUMENT_TYPE",
        "SUPPORTED_DOCUMENT_TYPES",
        "get_document_type_definition",
    )


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


def test_public_document_model_fields_are_stable() -> None:
    """Verify extracted result models preserve their public schema and ordering.

    Protected risk: registry consumers and embedded callers may construct or read
    these dataclasses by field name, so silent schema drift must be explicit.
    """
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
