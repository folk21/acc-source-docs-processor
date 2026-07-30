from pathlib import Path

from source_docs_processor.features.document_processing.document_types.npd_receipts.extractor import (
    extract_document,
    extract_inn_candidates,
    extract_issuer_name,
)
from source_docs_processor.features.document_processing.ocr import OcrResult


def _extract(text: str):
    return extract_document(
        Path("receipt.jpg"),
        OcrResult(text=text, header_text="", mean_confidence=80),
    )


def test_first_inn_is_the_self_employed_receipt_issuer():
    text = """
ЧЕК
Налог на профессиональный доход

Иванов Иван Иванович
ИНН 781234567890

Покупатель
ООО Ромашка
ИНН 7801234567

ИТОГО 12 500,00 руб.
"""

    document = _extract(text)

    assert document.is_recognized is True
    assert document.issuer_name == "Иванов Иван Иванович"
    assert document.issuer_inn == "781234567890"
    assert document.recipient_inn == "7801234567"
    assert document.total_amount == "12500.00"


def test_name_is_preferred_from_second_information_block_near_first_inn():
    text = """
Федеральная Налоговая Служба
ЧЕК НПД

Петрова Анна Сергеевна
ИНН: 500123456789

ООО Альфа Сервис
ИНН: 7701234567
"""
    candidates = extract_inn_candidates(text)

    issuer_name = extract_issuer_name(text, candidates[0])

    assert issuer_name == "Петрова Анна Сергеевна"


def test_split_surname_and_first_name_patronymic_are_joined():
    text = """
ЧЕК НПД

Кузнецов
Алексей Николаевич
ИНН 500123456789

Покупатель ООО Альфа
ИНН 7701234567
ИТОГО 1000,00 руб.
"""

    document = _extract(text)

    assert document.issuer_name == "Кузнецов Алексей Николаевич"


def test_split_two_words_and_one_word_are_supported_as_fallback():
    text = """
ЧЕК НПД

Кузнецова Мария
Петровна
ИНН 500123456789

Покупатель ООО Альфа
ИНН 7701234567
ИТОГО 1000,00 руб.
"""

    document = _extract(text)

    assert document.issuer_name == "Кузнецова Мария Петровна"


def test_second_inn_must_not_replace_owner_inn():
    text = """
ЧЕК
Мой налог

Сидоров Петр Алексеевич
ИНН 590123456789

Заказчик ООО Бета
ИНН 5901234567
Сумма чека 9000,00
Дата 02.04.2026
"""

    document = _extract(text)

    assert document.issuer_inn == "590123456789"
    assert document.recipient_inn == "5901234567"
    assert document.issuer_name == "Сидоров Петр Алексеевич"


def test_fio_label_on_same_line_is_supported():
    text = """
ЧЕК НПД

ФИО: Смирнова Елена Викторовна
ИНН: 770123456789

Покупатель ООО Гамма
ИНН: 7701234567
ИТОГО: 1 250,50 RUB
"""

    document = _extract(text)

    assert document.issuer_name == "Смирнова Елена Викторовна"
    assert document.issuer_inn == "770123456789"


def test_plain_receipt_heading_is_not_used_as_receipt_number():
    text = """
Чек
Налог на профессиональный доход

Иванов Иван Иванович
ИНН 781234567890

ИТОГО 1000,00 руб.
Дата 02.04.2026
"""

    document = _extract(text)

    assert document.document_number is None


def test_receipt_number_is_read_only_after_explicit_prefix():
    text = """
Чек № 2000-ABC-778899
Дата 02.04.2026
Налог на профессиональный доход

Иванов Иван Иванович
ИНН 781234567890

ИТОГО 1000,00 руб.
"""

    document = _extract(text)

    assert document.document_number == "2000-ABC-778899"


def test_receipt_number_stops_before_date_label():
    text = """
Чек № 123456789 Дата 02.04.2026
Налог на профессиональный доход

Иванов Иван Иванович
ИНН 781234567890

ИТОГО 1000,00 руб.
"""

    document = _extract(text)

    assert document.document_number == "123456789"


def test_service_description_is_preserved():
    text = """
Чек № 123456789
Дата 02.04.2026
Налог на профессиональный доход

Иванов Иван Иванович
ИНН 781234567890

Покупатель ООО Ромашка
ИНН 7801234567
Наименование услуги: Консультационные услуги по договору
ИТОГО 12 500,00 руб.
"""

    document = _extract(text)

    assert document.description == "Консультационные услуги по договору"
