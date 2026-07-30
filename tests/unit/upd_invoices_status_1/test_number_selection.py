from source_docs_processor.features.document_types.upd_invoices_status_1.extractor import (
    choose_more_reliable_document_number,
    normalize_number,
)


def test_normalize_document_number_removes_spaces_and_noise():
    """Verify the basic cleanup used before every document-number comparison.

    Fixed problem verified: Tesseract may read document numbers with spaces or
    punctuation, for example `2 548`, while output filenames must use a compact
    document number.
    """
    assert normalize_number("  № 2 548 ") == "2548"


def test_replaces_too_short_header_number_with_shipment_row_number():
    """Verify fallback when the header OCR reads only the first digit.

    Fixed problem verified: one observed OCR failure had document number `405`, but the
    header crop returned only `4`. The shipment row repeats the correct number
    and should override the suspiciously short header candidate.
    """
    value, warning = choose_more_reliable_document_number("4", "405")

    assert value == "405"
    assert warning == "document_number_replaced_because_header_was_too_short"


def test_prefers_shorter_shipment_row_prefix_when_header_overreads_suffix():
    """Verify correction of OCR over-read at the end of the document number.

    Fixed problem verified: observed OCR output produced values such as `43007`, where
    `07` was accidentally attached from a neighbouring date/crop area. The
    cleaner shipment-row value `430` should win.
    """
    value, warning = choose_more_reliable_document_number("43007", "430")

    assert value == "430"
    assert warning == "document_number_replaced_by_shorter_fallback_prefix"


def test_keeps_shorter_header_prefix_when_fallback_overreads_suffix():
    """Verify the symmetric over-read correction for fallback candidates.

    Fixed problem verified: a crop or shipment-row OCR candidate can also read
    `4977` while the correct document number is `497`. A reliable 3-digit prefix
    should not be replaced by the longer noisy value.
    """
    value, warning = choose_more_reliable_document_number("497", "4977")

    assert value == "497"
    assert warning == "document_number_kept_as_shorter_header_prefix"


def test_trims_known_suspicious_trailing_digits_when_no_fallback_exists():
    """Verify last-resort trimming when only one over-read candidate exists.

    Fixed problem verified: some OCR candidates contain a 3-digit document number
    followed by a common date fragment such as `07`. When no fallback exists, the
    algorithm still trims known suspicious suffixes.
    """
    value, warning = choose_more_reliable_document_number("43007", None)

    assert value == "430"
    assert warning == "trimmed_suspicious_trailing_digits"
