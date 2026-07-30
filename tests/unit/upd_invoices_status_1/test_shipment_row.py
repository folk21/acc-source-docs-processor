from source_docs_processor.features.document_types.upd_invoices_status_1.extractor import _extract_number_date_from_shipment_document


def test_extracts_number_and_date_from_explicit_shipment_row():
    """Verify the main fallback parser for `Документ об отгрузке`.

    Fixed problem verified: dates and numbers may be weak in the header, but the
    form repeats them in a row like `№ п/п 1 № 511 от 21 марта 2023 г.`.
    """
    number, date = _extract_number_date_from_shipment_document(
        "Документ об отгрузке № п/п 1 № 511 от 21 марта 2023 г."
    )

    assert number == "511"
    assert date == "21-03-2023"


def test_ignores_row_number_before_real_document_number():
    """Verify that the row marker `1` is not mistaken for the document number.

    Fixed problem verified: the fallback row contains `№ п/п 1`; the first `1`
    is only the row number and must be ignored.
    """
    number, date = _extract_number_date_from_shipment_document(
        "Документ об отгрузке № п/п 1 № 426 от 09 марта 2023 г."
    )

    assert number == "426"
    assert date == "09-03-2023"


def test_extracts_shipment_row_with_numeric_date():
    """Verify fallback-row parsing when OCR returns a numeric date.

    Fixed problem verified: some OCR runs may normalize or read the printed date
    as `20.03.2023`; the shipment-row parser should still return the date.
    """
    number, date = _extract_number_date_from_shipment_document(
        "Документ об отгрузке № п/п 1 № 504 от 20.03.2023"
    )

    assert number == "504"
    assert date == "20-03-2023"


def test_returns_empty_result_for_unrelated_text():
    """Verify that unrelated OCR text is not treated as a shipment row.

    Fixed problem verified: generic dates elsewhere in the page should not be
    parsed as document dates unless the text looks like the shipment row.
    """
    number, date = _extract_number_date_from_shipment_document(
        "Постановление Правительства Российской Федерации от 2 апреля 2021 г. № 534"
    )

    assert number is None
    assert date is None
