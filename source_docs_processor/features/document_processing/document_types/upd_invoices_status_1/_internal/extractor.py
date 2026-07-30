"""Orchestrate scanned UPD field extraction from prepared OCR output."""

from __future__ import annotations

from pathlib import Path

from source_docs_processor.core.text import (
    normalize_multiline_whitespace as normalize_spaces,
)

from ....models import ExtractedDocument
from ...._internal.ocr import OcrResult
from .classification import (
    classify_page,
    is_upd_invoice_transfer as _is_upd_invoice_transfer,
)
from .confidence import calculate_confidence
from .continuation import (
    continuation_marker_score as _continuation_marker_score,
    is_probable_continuation_page as _is_probable_continuation_page,
)
from .date_extraction import (
    MONTHS_RU,
    choose_more_reliable_document_date,
    extract_date_from_mixed_ocr_text,
    is_form_template_date,
    normalize_date,
)
from .financial_extraction import (
    extract_amounts as _extract_amounts,
    normalize_money,
)
from .identity_extraction import (
    extract_document_identity,
    extract_invoice_number_and_date as _extract_invoice_number_and_date,
)
from .number_extraction import (
    choose_more_reliable_document_number,
    normalize_number,
)
from .party_extraction import (
    extract_inn_kpp_after_label as _extract_inn_kpp_after_label,
    extract_party_name as _extract_party_name,
)
from .shipment_row import (
    extract_number_date_from_shipment_document
    as _extract_number_date_from_shipment_document,
)
from .transport_extraction import (
    extract_service_text as _extract_service_text,
    extract_transport_details as _extract_transport_details,
)


__all__ = [
    "MONTHS_RU",
    "choose_more_reliable_document_date",
    "choose_more_reliable_document_number",
    "extract_date_from_mixed_ocr_text",
    "extract_document",
    "is_form_template_date",
    "normalize_date",
    "normalize_money",
    "normalize_number",
    "normalize_spaces",
]


def extract_document(source_path: Path, ocr: OcrResult) -> ExtractedDocument:
    """Convert prepared OCR output into structured UPD document metadata."""
    combined = normalize_spaces(
        ocr.header_text + "\n" + ocr.text + "\n" + ocr.targeted_text
    )
    identity = extract_document_identity(combined, ocr)

    seller_inn, seller_kpp = _extract_inn_kpp_after_label(
        combined,
        r"(?:ИНН|VHH|ИHH)\s*/\s*(?:КПП|KNN|КNN)\s+продавца",
    )
    buyer_inn, buyer_kpp = _extract_inn_kpp_after_label(
        combined,
        r"(?:ИНН|VHH|ИHH)\s*/\s*(?:КПП|KNN|КNN)\s+покупателя",
    )
    seller_name = _extract_party_name(combined, "Продавец")
    buyer_name = _extract_party_name(combined, "Покупатель")
    amount_without_vat, vat_amount, amount_with_vat = _extract_amounts(combined)
    service_text = _extract_service_text(combined)
    (
        request_number,
        request_date,
        vehicle,
        loading_datetime,
        unloading_datetime,
    ) = _extract_transport_details(service_text)

    status = ocr.targeted_fields.get("status")
    classification = classify_page(
        text=combined,
        status=status,
        document_number=identity.document_number,
        document_date=identity.document_date,
        has_shipment_row=bool(
            ocr.targeted_fields.get("shipment_document_text_from_crop")
        ),
    )
    confidence = calculate_confidence(
        text=combined,
        is_upd=classification.is_upd,
        is_continuation=classification.is_continuation,
        document_number=identity.document_number,
        document_date=identity.document_date,
        seller_inn=seller_inn,
        buyer_inn=buyer_inn,
        total_amount=amount_with_vat,
    )

    document = ExtractedDocument(
        source_path=source_path,
        document_type="upd_invoices_status_1",
        is_recognized=classification.is_upd or classification.is_continuation,
        status=status,
        document_number=identity.document_number,
        document_date=identity.document_date,
        issuer_name=seller_name,
        issuer_inn=seller_inn,
        issuer_kpp=seller_kpp,
        recipient_name=buyer_name,
        recipient_inn=buyer_inn,
        recipient_kpp=buyer_kpp,
        amount_without_tax=amount_without_vat,
        tax_amount=vat_amount,
        total_amount=amount_with_vat,
        description=service_text,
        confidence=confidence,
        rotation_degrees=getattr(ocr, "rotation_degrees", 0),
        is_continuation_page=classification.is_continuation,
        text_preview=combined[:500].replace("\n", " "),
        extra_fields={
            "request_number": request_number,
            "request_date": request_date,
            "vehicle": vehicle,
            "loading_datetime": loading_datetime,
            "unloading_datetime": unloading_datetime,
        },
    )

    if classification.is_upd and identity.number_warning:
        document.warnings.append(identity.number_warning)
    if classification.is_upd and identity.date_warning:
        document.warnings.append(identity.date_warning)
    if (
        classification.is_upd
        and identity.shipment_number
        and identity.document_number == identity.shipment_number
    ):
        document.warnings.append(
            "Document number was recognized from the shipment row"
        )
    if (
        classification.is_upd
        and identity.shipment_date
        and identity.document_date == identity.shipment_date
    ):
        document.warnings.append("Document date was recognized from the shipment row")
    if classification.is_continuation:
        document.warnings.append(
            "Page was detected as a continuation of the previous recognized document"
        )
    if classification.is_upd and classification.status_warning:
        document.warnings.append(
            "Status digit was unreliable; document was accepted by UPD invoice "
            "markers, number, and date"
        )
    if classification.is_upd and not identity.document_number:
        document.warnings.append("Invoice number was not recognized")
    if classification.is_upd and not identity.document_date:
        document.warnings.append("Invoice date was not recognized")
    if (
        classification.is_upd
        and ocr.targeted_fields.get("invoice_number_from_crop")
        and identity.document_number
        == ocr.targeted_fields.get("invoice_number_from_crop")
    ):
        document.warnings.append("Invoice number was recognized from target crop")
    if (
        classification.is_upd
        and ocr.targeted_fields.get("invoice_date_text_from_crop")
        and identity.document_date
    ):
        document.warnings.append("Invoice date crop was used or checked")
    return document
