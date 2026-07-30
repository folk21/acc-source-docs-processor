from pathlib import Path

from source_docs_processor.features.document_types.incoming_purchase_documents.extractor import (
    extract_document,
)
from source_docs_processor.features.document_types.incoming_purchase_documents.readers import (
    StructuredSourceContent,
)


def _upd_table() -> list[list[str]]:
    """Build a synthetic structured UPD goods table."""
    return [
        [
            "Наименование товара (описание выполненных работ, оказанных услуг), имущественного права",
            "Единица измерения",
            "Количество (объем)",
            "Цена (тариф) за единицу измерения",
            "Стоимость товаров (работ, услуг), имущественных прав без налога - всего",
            "Налоговая ставка",
            "Сумма налога, предъявляемая покупателю",
            "Стоимость товаров (работ, услуг), имущественных прав с налогом - всего",
        ],
        [
            "Учебный товар",
            "шт",
            "2",
            "1000,00",
            "2000,00",
            "20%",
            "400,00",
            "2400,00",
        ],
        [
            "Всего к оплате",
            "",
            "",
            "",
            "2000,00",
            "",
            "400,00",
            "2400,00",
        ],
    ]


def test_extracts_upd_identity_parties_items_and_totals():
    """Verify native structured content produces a complete UPD task.

    Protected risk: electronic UPD processing must preserve table rows instead
    of reducing a document to only its number, date, and total.
    """
    text = """
    Универсальный передаточный документ
    Счет-фактура № 511 от 21.03.2026
    Статус: 1
    Продавец: ООО Учебный Поставщик
    ИНН/КПП продавца: 7801234567 / 780101001
    Покупатель: ООО Учебный Покупатель
    ИНН/КПП покупателя: 7701234567 / 770101001
    """
    content = StructuredSourceContent(text=text, tables=[_upd_table()])

    document = extract_document(Path("upd.docx"), content)

    assert document.is_recognized
    assert document.status == "1"
    assert document.document_number == "511"
    assert document.document_date == "21-03-2026"
    assert document.issuer_inn == "7801234567"
    assert document.recipient_inn == "7701234567"
    assert document.amount_without_tax == "2000.00"
    assert document.tax_amount == "400.00"
    assert document.total_amount == "2400.00"
    assert len(document.items) == 1
    assert document.items[0].name == "Учебный товар"
    assert document.items[0].quantity == "2.00"
    assert document.items[0].unit_price == "1000.00"
    assert document.extra_fields["requires_review"] is False


def test_explicit_status_two_is_not_accepted():
    """Verify the electronic processor rejects an explicit UPD status 2 file.

    Protected risk: the new type is limited to status 1 and must not silently
    convert a status 2 primary document into an accountant task.
    """
    text = """
    Универсальный передаточный документ
    Счет-фактура № 512 от 22.03.2026
    Статус: 2
    """

    document = extract_document(
        Path("status_2.pdf"),
        StructuredSourceContent(text=text),
    )

    assert not document.is_recognized
    assert document.status == "2"
    assert document.extra_fields["requires_review"] is True
    assert "The file contains explicit UPD status 2" in document.warnings


def test_extracts_items_when_headers_are_split_across_rows():
    """Verify vertically split UPD headers still map item columns.

    Protected risk: official supplier templates often split long column labels
    across several header rows, so a single-row-only parser would lose items.
    """
    table = [
        [
            "Наименование товара",
            "Единица",
            "Количество",
            "Цена за",
            "Стоимость без",
            "Налоговая",
            "Сумма",
            "Стоимость с",
        ],
        [
            "описание выполненных работ и услуг",
            "измерения",
            "объем",
            "единицу измерения",
            "налога всего",
            "ставка",
            "налога",
            "налогом всего",
        ],
        [
            "Учебная услуга",
            "усл",
            "1",
            "5000,00",
            "5000,00",
            "20%",
            "1000,00",
            "6000,00",
        ],
    ]
    text = """
    Универсальный передаточный документ
    Счет-фактура № 700 от 24.03.2026
    Статус: 1
    Продавец: ООО Учебный Поставщик
    ИНН/КПП продавца: 7801234567 / 780101001
    """

    document = extract_document(
        Path("split_headers.docx"),
        StructuredSourceContent(text=text, tables=[table]),
    )

    assert len(document.items) == 1
    assert document.items[0].name == "Учебная услуга"
    assert document.items[0].total_amount == "6000.00"


def test_skips_official_column_number_row_and_uses_textual_unit():
    """Verify UPD column labels such as 1a are not emitted as goods rows.

    Protected risk: the official two-level table header includes a separate row
    of column designators and both a numeric OKEI code and a textual unit name.
    """
    table = [
        [
            "№ п/п",
            "Наименование товара (описание выполненных работ, оказанных услуг)",
            "Код вида товара",
            "Единица измерения",
            "Единица измерения",
            "Количество (объем)",
            "Цена за единицу измерения",
            "Стоимость без налога всего",
            "Налоговая ставка",
            "Сумма налога",
            "Стоимость с налогом всего",
        ],
        ["", "", "", "код", "условное обозначение", "", "", "", "", "", ""],
        ["1", "1а", "1б", "2", "2а", "3", "4", "5", "6", "7", "8"],
        [
            "1",
            "Учебный товар",
            "",
            "796",
            "шт",
            "2",
            "1000,00",
            "2000,00",
            "20%",
            "400,00",
            "2400,00",
        ],
    ]
    text = """
    Универсальный передаточный документ
    Счет-фактура № 801 от 25.03.2026
    Статус: 1
    Продавец: ООО Учебный Поставщик
    ИНН/КПП продавца: 7801234567 / 780101001
    """

    document = extract_document(
        Path("official_headers.docx"),
        StructuredSourceContent(text=text, tables=[table]),
    )

    assert len(document.items) == 1
    assert document.items[0].name == "Учебный товар"
    assert document.items[0].unit == "шт"
    assert document.items[0].quantity == "2.00"


def test_numeric_okei_code_is_not_exported_as_unit_name():
    """Verify a numeric OKEI code cannot become the displayed unit value.

    Protected risk: supplier tables may expose only the code column, but a
    numeric value such as 796 is not a human-readable unit for 1C entry.
    """
    table = [
        [
            "Наименование товара (описание выполненных работ, оказанных услуг)",
            "Единица измерения код ОКЕИ",
            "Количество (объем)",
            "Цена за единицу измерения",
            "Стоимость без налога всего",
            "Налоговая ставка",
            "Сумма налога",
            "Стоимость с налогом всего",
        ],
        [
            "Учебный товар",
            "796",
            "1",
            "1000,00",
            "1000,00",
            "20%",
            "200,00",
            "1200,00",
        ],
    ]
    text = """
    Универсальный передаточный документ
    Счет-фактура № 802 от 25.03.2026
    Статус: 1
    Продавец: ООО Учебный Поставщик
    ИНН/КПП продавца: 7801234567 / 780101001
    """

    document = extract_document(
        Path("numeric_unit.docx"),
        StructuredSourceContent(text=text, tables=[table]),
    )

    assert len(document.items) == 1
    assert document.items[0].unit is None
    assert (
        "Text unit name was not extracted; numeric OKEI code was ignored"
        in document.items[0].warnings
    )
