from source_docs_processor.features.document_processing._internal.ocr import OcrResult


def test_ocr_result_accepts_processor_defined_targeted_fields():
    """Verify that shared OCR output accepts arbitrary processor field keys.

    Protected risk: receipt, act, and UPD processors must store anchored OCR
    results without adding document-specific attributes to the generic OCR model.
    """
    result = OcrResult(
        text="",
        header_text="Receipt",
        mean_confidence=88.0,
        targeted_fields={
            "receipt_number": "R-100",
            "qr_url": "https://example.invalid/receipt/R-100",
        },
    )

    assert result.targeted_fields["receipt_number"] == "R-100"
    assert result.targeted_fields["qr_url"].endswith("R-100")
