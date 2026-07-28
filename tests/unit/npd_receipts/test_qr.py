from source_docs_processor.npd_receipts.qr import parse_npd_receipt_qr_url


def test_parses_official_npd_receipt_qr_url():
    """Verify the official QR path supplies the seller INN and receipt number."""
    result = parse_npd_receipt_qr_url(
        "https://lknpd.nalog.ru/api/v1/receipt/000000000000/abc123/print"
    )

    assert result is not None
    assert result.issuer_inn == "000000000000"
    assert result.receipt_number == "abc123"


def test_rejects_non_npd_qr_url():
    """Verify unrelated QR URLs cannot classify an image as an NPD receipt."""
    assert parse_npd_receipt_qr_url("https://example.invalid/receipt/abc") is None
