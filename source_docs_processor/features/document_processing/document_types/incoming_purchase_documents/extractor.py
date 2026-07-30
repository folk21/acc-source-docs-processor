"""Field and item extraction for electronic UPD status 1 documents."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ...models import ExtractedDocument, ExtractedDocumentItem
from .readers import StructuredSourceContent


DOCUMENT_TYPE = "incoming_purchase_documents"

_MONTHS = {
    "января": "01",
    "февраля": "02",
    "марта": "03",
    "апреля": "04",
    "мая": "05",
    "июня": "06",
    "июля": "07",
    "августа": "08",
    "сентября": "09",
    "октября": "10",
    "ноября": "11",
    "декабря": "12",
}


def _compact(value: str) -> str:
    """Collapse whitespace while preserving useful punctuation."""
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def _normalize_date(value: str | None) -> str | None:
    """Normalize numeric or Russian textual dates to DD-MM-YYYY."""
    if not value:
        return None
    numeric = re.search(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})", value)
    if numeric:
        day, month, year = numeric.groups()
        if len(year) == 2:
            year = f"20{year}"
        try:
            day_value = int(day)
            month_value = int(month)
            year_value = int(year)
        except ValueError:
            return None
        if 1 <= day_value <= 31 and 1 <= month_value <= 12 and 2020 <= year_value <= 2035:
            return f"{day_value:02d}-{month_value:02d}-{year_value}"
        return None

    textual = re.search(
        r"(\d{1,2})\s+([А-Яа-яЁё]+)\s+(\d{4})",
        value,
        flags=re.IGNORECASE,
    )
    if not textual:
        return None
    day, month_name, year = textual.groups()
    month = _MONTHS.get(month_name.lower())
    if month is None:
        return None
    return f"{int(day):02d}-{month}-{year}"


def _normalize_money(value: str | None) -> str | None:
    """Normalize a monetary value to a dot-decimal string."""
    if not value:
        return None
    cleaned = value.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if not cleaned or cleaned in {"-", "."}:
        return None
    try:
        return f"{Decimal(cleaned):.2f}"
    except InvalidOperation:
        return None


def _decimal(value: str | None) -> Decimal | None:
    """Convert a normalized money or quantity value to Decimal."""
    normalized = _normalize_money(value)
    if normalized is None:
        return None
    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def _extract_status(text: str) -> str | None:
    """Extract UPD status and avoid accepting an explicit status 2 document."""
    compact = _compact(text).lower()
    explicit = re.search(r"статус\s*[:№]?\s*([12])\b", compact)
    if explicit:
        return explicit.group(1)
    if re.search(
        r"1\s*[-–—]\s*сч[её]т\s*[-–—]?\s*фактура\s+и\s+передаточ",
        compact,
    ):
        return "1"
    if "счет-фактура и передаточный документ" in compact:
        return "1"
    if "счёт-фактура и передаточный документ" in compact:
        return "1"
    return None


def _extract_number_and_date(text: str) -> tuple[str | None, str | None]:
    """Extract the primary UPD or invoice number and date."""
    compact = _compact(text)
    date_pattern = (
        r"\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}"
        r"|\d{1,2}\s+[А-Яа-яЁё]+\s+\d{4}"
    )
    patterns = (
        rf"(?:сч[её]т\s*[-–—]?\s*фактура|универсальн\w*\s+передаточ\w*\s+документ)\s*"
        rf"(?:№|N|No)?\s*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-/]*)\s*от\s*({date_pattern})",
        rf"документ\s+об\s+отгрузке[^№N0-9]{{0,40}}(?:№|N|No)?\s*"
        rf"([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-/]*)\s*от\s*({date_pattern})",
    )
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(), _normalize_date(match.group(2))
    return None, None


def _extract_party(text: str, label: str) -> tuple[str | None, str | None, str | None]:
    """Extract a party name and nearby INN/KPP values."""
    compact = _compact(text)
    next_labels = (
        r"Адрес|ИНН\s*/\s*КПП|Грузоотправитель|Грузополучатель|Покупатель|"
        r"Продавец|Валюта|Идентификатор"
    )
    name_match = re.search(
        rf"{label}\s*[:：]?\s*(.+?)(?=\s+(?:{next_labels})\b|$)",
        compact,
        flags=re.IGNORECASE,
    )
    name = name_match.group(1).strip(" :;|")[:200] if name_match else None

    tax_party_pattern = r"продав\w*" if label.lower().startswith("продав") else r"покупател\w*"
    tax_match = re.search(
        rf"ИНН\s*/\s*КПП\s+{tax_party_pattern}\s*[:：]?\s*"
        r"(\d{10,12})(?:\s*/\s*(\d{9}))?",
        compact,
        flags=re.IGNORECASE,
    )
    inn = tax_match.group(1) if tax_match else None
    kpp = tax_match.group(2) if tax_match and tax_match.group(2) else None
    return name, inn, kpp


def _normalize_header(value: str) -> str:
    """Normalize one table header for tolerant column matching."""
    value = _compact(value).lower().replace("ё", "е")
    value = re.sub(r"\(.*?\)", " ", value)
    return re.sub(r"[^а-яa-z0-9]+", " ", value).strip()


def _column_key(header: str) -> str | None:
    """Map a UPD table header to one normalized item field."""
    normalized = _normalize_header(header)
    if not normalized:
        return None
    if "наименование" in normalized and any(
        marker in normalized for marker in ("товар", "работ", "услуг", "имуществен")
    ):
        return "name"
    if "количество" in normalized or "объем" in normalized:
        return "quantity"
    if "цена" in normalized and "единиц" in normalized:
        return "unit_price"
    if "налоговая ставка" in normalized:
        return "tax_rate"
    if "сумма налога" in normalized:
        return "tax_amount"
    if "стоимость" in normalized and "без налога" in normalized:
        return "amount_without_tax"
    if "стоимость" in normalized and (
        "с налогом" in normalized or "всего" in normalized
    ):
        return "total_amount"
    if (
        "единица измерения" in normalized and "код" in normalized
    ) or "океи" in normalized:
        return "unit_code"
    if "условное обозначение" in normalized or (
        "единица измерения" in normalized and "код" not in normalized
    ):
        return "unit"
    return None


def _find_header_map(table: list[list[str]]) -> tuple[int, dict[str, int]] | None:
    """Locate a one-row or vertically split UPD goods table header."""
    best: tuple[int, dict[str, int]] | None = None
    maximum_columns = max((len(row) for row in table[:12]), default=0)
    for start_index in range(min(len(table), 12)):
        for span in range(1, 5):
            end_index = start_index + span
            if end_index > len(table):
                break
            mapping: dict[str, int] = {}
            for column_index in range(maximum_columns):
                combined = " ".join(
                    row[column_index]
                    for row in table[start_index:end_index]
                    if column_index < len(row) and row[column_index]
                )
                key = _column_key(combined)
                if key and key not in mapping:
                    mapping[key] = column_index
            if "name" in mapping and len(mapping) >= 4:
                candidate = (end_index - 1, mapping)
                if best is None or len(mapping) > len(best[1]):
                    best = candidate
    return best


def _cell(row: list[str], mapping: dict[str, int], key: str) -> str | None:
    """Read one mapped table cell."""
    index = mapping.get(key)
    if index is None or index >= len(row):
        return None
    value = _compact(row[index])
    return value or None


_COLUMN_NUMBER_PATTERN = re.compile(r"\d{1,2}[а-яa-z]?", re.IGNORECASE)


def _is_column_number_row(row: list[str]) -> bool:
    """Return True for the official row containing UPD column designators."""
    values = [_compact(value).lower() for value in row if _compact(value)]
    if len(values) < 3:
        return False
    normalized = [re.sub(r"[\s№().:-]+", "", value) for value in values]
    marker_count = sum(
        bool(_COLUMN_NUMBER_PATTERN.fullmatch(value)) for value in normalized
    )
    return marker_count >= 3 and marker_count * 10 >= len(values) * 7


def _normalize_unit(value: str | None) -> str | None:
    """Keep a textual unit name and reject numeric OKEI codes or column labels."""
    if not value:
        return None
    compact = _compact(value)
    marker = re.sub(r"[\s№().:-]+", "", compact.lower())
    if _COLUMN_NUMBER_PATTERN.fullmatch(marker):
        return None
    if re.fullmatch(r"[0-9.,-]+", compact):
        return None

    without_codes = re.sub(r"(?<![A-Za-zА-Яа-яЁё])\d+(?![A-Za-zА-Яа-яЁё])", " ", compact)
    without_codes = re.sub(r"\(\s*\)", " ", without_codes)
    normalized = _compact(without_codes).strip(" -;,/")
    if not re.search(r"[A-Za-zА-Яа-яЁё]", normalized):
        return None
    return normalized


def _looks_like_item_name(value: str) -> bool:
    """Return True when a possible item name contains meaningful text."""
    marker = re.sub(r"[\s№().:-]+", "", value.lower())
    if _COLUMN_NUMBER_PATTERN.fullmatch(marker):
        return False
    return bool(re.search(r"[A-Za-zА-Яа-яЁё]", value))


def _is_summary_row(name: str) -> bool:
    """Return True when a table row represents totals instead of an item."""
    lowered = name.lower()
    return any(
        marker in lowered
        for marker in (
            "всего к оплате",
            "всего по документу",
            "итого",
            "всего",
        )
    )


def _extract_items_and_totals(
    tables: list[list[list[str]]],
) -> tuple[list[ExtractedDocumentItem], tuple[str | None, str | None, str | None]]:
    """Extract item rows and explicit totals from structured tables."""
    items: list[ExtractedDocumentItem] = []
    explicit_net: str | None = None
    explicit_tax: str | None = None
    explicit_total: str | None = None

    for table in tables:
        header = _find_header_map(table)
        if header is None:
            continue
        header_index, mapping = header
        for raw_row in table[header_index + 1 :]:
            if _is_column_number_row(raw_row):
                continue

            name = _cell(raw_row, mapping, "name")
            if not name:
                continue
            if _is_summary_row(name):
                explicit_net = _normalize_money(
                    _cell(raw_row, mapping, "amount_without_tax")
                ) or explicit_net
                explicit_tax = _normalize_money(
                    _cell(raw_row, mapping, "tax_amount")
                ) or explicit_tax
                explicit_total = _normalize_money(
                    _cell(raw_row, mapping, "total_amount")
                ) or explicit_total
                continue
            if _column_key(name) == "name" or not _looks_like_item_name(name):
                continue

            raw_unit = _cell(raw_row, mapping, "unit")
            unit_code = _cell(raw_row, mapping, "unit_code")
            quantity = _normalize_money(_cell(raw_row, mapping, "quantity"))
            unit_price = _normalize_money(_cell(raw_row, mapping, "unit_price"))
            amount_without_tax = _normalize_money(
                _cell(raw_row, mapping, "amount_without_tax")
            )
            tax_rate = _cell(raw_row, mapping, "tax_rate")
            tax_amount = _normalize_money(_cell(raw_row, mapping, "tax_amount"))
            total_amount = _normalize_money(_cell(raw_row, mapping, "total_amount"))
            if not any(
                value
                for value in (
                    quantity,
                    unit_price,
                    amount_without_tax,
                    tax_rate,
                    tax_amount,
                    total_amount,
                )
            ):
                continue

            unit = _normalize_unit(raw_unit)
            item = ExtractedDocumentItem(
                line_number=len(items) + 1,
                name=name,
                unit=unit,
                quantity=quantity,
                unit_price=unit_price,
                amount_without_tax=amount_without_tax,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                total_amount=total_amount,
                confidence=min(100, 45 + len(mapping) * 7),
            )
            if unit is None and (raw_unit or unit_code):
                item.warnings.append(
                    "Text unit name was not extracted; numeric OKEI code was ignored"
                )
            _validate_item(item)
            items.append(item)

    return items, (explicit_net, explicit_tax, explicit_total)


def _validate_item(item: ExtractedDocumentItem) -> None:
    """Add line-level arithmetic warnings without rejecting extracted values."""
    quantity = _decimal(item.quantity)
    price = _decimal(item.unit_price)
    net = _decimal(item.amount_without_tax)
    tax = _decimal(item.tax_amount)
    total = _decimal(item.total_amount)

    if quantity is not None and price is not None and net is not None:
        if abs(quantity * price - net) > Decimal("0.02"):
            item.warnings.append("Quantity multiplied by price does not match line amount")
    if net is not None and tax is not None and total is not None:
        if abs(net + tax - total) > Decimal("0.02"):
            item.warnings.append("Line amount plus VAT does not match line total")


def _sum_item_field(
    items: list[ExtractedDocumentItem],
    field_name: str,
) -> str | None:
    """Sum one monetary item field when at least one value is available."""
    values = [
        _decimal(getattr(item, field_name))
        for item in items
        if getattr(item, field_name) not in {None, ""}
    ]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return f"{sum(values, Decimal('0')):.2f}"


def _extract_text_totals(text: str) -> tuple[str | None, str | None, str | None]:
    """Extract a totals triplet from the textual `Всего к оплате` row."""
    compact = _compact(text)
    match = re.search(
        r"всего\s+к\s+оплате[^0-9]{0,80}"
        r"([0-9][0-9\s.,]*)\s+([0-9][0-9\s.,]*)\s+([0-9][0-9\s.,]*)",
        compact,
        flags=re.IGNORECASE,
    )
    if not match:
        return None, None, None
    return tuple(_normalize_money(value) for value in match.groups())  # type: ignore[return-value]


def _validate_document(document: ExtractedDocument) -> None:
    """Add document-level completeness and arithmetic warnings."""
    required = {
        "document number": document.document_number,
        "document date": document.document_date,
        "seller INN": document.issuer_inn,
        "total amount": document.total_amount,
    }
    for label, value in required.items():
        if not value:
            document.warnings.append(f"Missing required {label}")
    if not document.items:
        document.warnings.append("No goods or service rows were extracted")

    item_net = _sum_item_field(document.items, "amount_without_tax")
    item_tax = _sum_item_field(document.items, "tax_amount")
    item_total = _sum_item_field(document.items, "total_amount")
    comparisons = (
        ("amount without VAT", item_net, document.amount_without_tax),
        ("VAT amount", item_tax, document.tax_amount),
        ("total amount", item_total, document.total_amount),
    )
    for label, item_value, document_value in comparisons:
        if item_value is None or document_value is None:
            continue
        if abs(Decimal(item_value) - Decimal(document_value)) > Decimal("0.02"):
            document.warnings.append(f"Item {label} does not match document total")


def extract_document(
    source_path: Path,
    content: StructuredSourceContent,
) -> ExtractedDocument:
    """Build one structured electronic UPD result from local file content."""
    text = content.text
    compact_lower = _compact(text).lower()
    status = _extract_status(text)
    number, date = _extract_number_and_date(text)
    issuer_name, issuer_inn, issuer_kpp = _extract_party(text, "Продавец")
    recipient_name, recipient_inn, recipient_kpp = _extract_party(text, "Покупатель")
    items, table_totals = _extract_items_and_totals(content.tables)
    text_totals = _extract_text_totals(text)

    amount_without_tax = table_totals[0] or text_totals[0] or _sum_item_field(
        items, "amount_without_tax"
    )
    tax_amount = table_totals[1] or text_totals[1] or _sum_item_field(
        items, "tax_amount"
    )
    total_amount = table_totals[2] or text_totals[2] or _sum_item_field(
        items, "total_amount"
    )

    has_invoice = bool(re.search(r"сч[её]т\s*[-–—]?\s*фактур", compact_lower))
    has_upd = "универсальн" in compact_lower and "передаточ" in compact_lower
    explicit_status_two = status == "2"
    recognized = has_invoice and has_upd and not explicit_status_two and (
        status == "1" or (number is not None and date is not None)
    )

    confidence = 0
    if has_invoice:
        confidence += 20
    if has_upd:
        confidence += 20
    if status == "1":
        confidence += 20
    if number:
        confidence += 10
    if date:
        confidence += 10
    if issuer_inn:
        confidence += 8
    if items:
        confidence += 7
    if total_amount:
        confidence += 5

    document = ExtractedDocument(
        source_path=source_path,
        document_type=DOCUMENT_TYPE,
        is_recognized=recognized,
        status=status,
        document_number=number,
        document_date=date,
        issuer_name=issuer_name,
        issuer_inn=issuer_inn,
        issuer_kpp=issuer_kpp,
        recipient_name=recipient_name,
        recipient_inn=recipient_inn,
        recipient_kpp=recipient_kpp,
        amount_without_tax=amount_without_tax,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency="RUB",
        description="; ".join(item.name for item in items[:5] if item.name),
        confidence=min(100, confidence),
        text_preview=_compact(text)[:500],
        items=items,
        extra_fields={
            "page_count": content.page_count,
            "used_ocr": content.used_ocr,
        },
    )
    document.warnings.extend(content.warnings)
    if explicit_status_two:
        document.warnings.append("The file contains explicit UPD status 2")
    if recognized and status is None:
        document.warnings.append(
            "UPD status was not explicit; status 1 was inferred from invoice-transfer markers"
        )
    if not recognized and not explicit_status_two:
        document.warnings.append("The file was not recognized as an UPD status 1 document")
    _validate_document(document)
    document.extra_fields["requires_review"] = bool(
        document.warnings
        or document.error
        or not document.is_recognized
        or any(item.warnings for item in document.items)
    )
    return document
