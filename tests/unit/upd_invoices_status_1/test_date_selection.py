from source_docs_processor.features.document_types.upd_invoices_status_1.extractor import (
    choose_more_reliable_document_date,
    is_form_template_date,
    normalize_date,
)


TEMPLATE_TEXT = """
Приложение № 1 к постановлению Правительства Российской Федерации от 26 декабря 2011 г. № 1137
в редакции постановления Правительства Российской Федерации от 2 апреля 2021 г. № 534
"""


def test_normalize_russian_textual_date():
    """Verify Russian textual date normalization used for UPD headers.

    Fixed problem verified: document dates are usually printed as `21 марта 2023 г.`
    and must become stable filename-safe values such as `21-03-2023`.
    """
    assert normalize_date("21 марта 2023 г.") == "21-03-2023"


def test_normalize_numeric_date_with_dots():
    """Verify numeric date normalization used in transport details.

    Fixed problem verified: some fields use numeric dates such as `20.03.2023`,
    and the registry/filename layer should get the same `DD-MM-YYYY` format.
    """
    assert normalize_date("20.03.2023") == "20-03-2023"


def test_detects_form_template_regulation_date():
    """Verify that the static UPD form date is recognized as non-document data.

    Fixed problem verified: OCR repeatedly picked `02-04-2021` from the legal
    service note in the top-right corner and used it as the document date.
    """
    assert is_form_template_date("02-04-2021", TEMPLATE_TEXT) is True


def test_shipment_row_date_overrides_form_template_date():
    """Verify that `Документ об отгрузке` wins over the template service date.

    Fixed problem verified: scans with a weak header date were incorrectly named
    with `02-04-2021`. The shipment row repeats the correct accounting date and must
    override the template date.
    """
    value, warning = choose_more_reliable_document_date(
        current_date="02-04-2021",
        shipment_date="09-03-2023",
        crop_date_text=None,
        combined_text=TEMPLATE_TEXT,
    )

    assert value == "09-03-2023"
    assert warning == "document_date_replaced_by_shipment_row"


def test_template_date_is_rejected_when_no_better_date_exists():
    """Verify that the form-template date is not used as a fallback document date.

    Fixed problem verified: if no reliable document date is found, the program
    should produce `УПД_<number>.png` instead of falsely naming the file with
    `02-04-2021`.
    """
    value, warning = choose_more_reliable_document_date(
        current_date="02-04-2021",
        shipment_date=None,
        crop_date_text=None,
        combined_text=TEMPLATE_TEXT,
    )

    assert value is None
    assert warning == "ignored_form_template_date"


def test_crop_date_is_used_when_header_date_is_missing():
    """Verify targeted date-crop recovery when the header parser returns no date.

    Fixed problem verified: some scans have a date visible in the targeted crop
    even when the generic header regex fails; the crop should then supply the date.
    """
    value, warning = choose_more_reliable_document_date(
        current_date=None,
        shipment_date=None,
        crop_date_text="06 марта 2023 г.",
        combined_text="Счет-фактура",
    )

    assert value == "06-03-2023"
    assert warning == "document_date_from_target_crop"
