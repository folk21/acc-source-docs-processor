from pathlib import Path

from source_docs_processor.ocr import OcrResult
from source_docs_processor.upd_invoices_status_1.extractor import (
    _is_probable_continuation_page,
    extract_document,
)


def test_sparse_signature_page_is_detected_as_continuation():
    """Verify detection of sparse page-2 scans with no invoice header.

    Fixed problem verified: some important scans are second pages with stamp and
    signature fields only. They must be copied as continuation pages rather than
    treated as unrecognized noise.
    """
    text = """
    Наименование экономического субъекта составителя документа
    Ответственный за правильность оформления факта хозяйственной жизни
    Должность Подпись М.П. ООО Учебный Перевозчик ООО Учебный Производитель
    """

    assert _is_probable_continuation_page(text) is True


def test_normal_upd_first_page_is_not_detected_as_continuation():
    """Verify that a normal first page is never downgraded to continuation.

    Fixed problem verified: a valid UPD first page was once falsely named as
    `<previous>_2_страница.png` because it also had signature markers near the
    bottom. The first-page markers must win.
    """
    ocr = OcrResult(
        text="Наименование экономического субъекта составителя документа Подпись М.П.",
        header_text="Универсальный передаточный документ Счет-фактура № 434 от 10 марта 2023 г.",
        status_digit="1",
        mean_confidence=80,
        targeted_text="Документ об отгрузке № п/п 1 № 434 от 10 марта 2023 г.",
        shipment_document_text_from_crop="Документ об отгрузке № п/п 1 № 434 от 10 марта 2023 г.",
    )

    doc = extract_document(Path("scan_434.png"), ocr)

    assert doc.is_upd_invoice_transfer is True
    assert doc.is_continuation_page is False
    assert doc.invoice_number == "434"
    assert doc.invoice_date == "10-03-2023"


def test_header_marker_reduces_continuation_score():
    """Verify the conservative continuation scoring guard.

    Fixed problem verified: first pages contain enough signature text to look like
    continuations, so invoice/UPD header markers must penalize continuation score.
    """
    text = """
    Универсальный передаточный документ Счет-фактура № 434 от 10 марта 2023 г.
    Наименование экономического субъекта составителя документа Ответственный за правильность
    Подпись М.П. ООО Учебный Перевозчик ООО Учебный Производитель
    """

    assert _is_probable_continuation_page(text) is False
