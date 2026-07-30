"""Field extraction for Russian NPD receipts issued by self-employed persons."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ....models import ExtractedDocument
from ...._internal.ocr import OcrResult


DOCUMENT_TYPE = "npd_receipts"

_INN_PATTERN = re.compile(r"(?<!\d)(\d(?:[\s\-]?\d){9,11})(?!\d)")
_DATE_PATTERN = re.compile(r"(?<!\d)(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})(?!\d)")
_MONEY_PATTERN = re.compile(
    r"(?<!\d)(\d{1,3}(?:[\s\u00a0]\d{3})*(?:[.,]\d{2})|\d+(?:[.,]\d{2}))(?!\d)"
)
_NAME_TOKEN_PATTERN = re.compile(r"^[А-ЯЁA-Z][А-ЯЁа-яёA-Za-z'’\-]{1,39}$")

_FORBIDDEN_NAME_WORDS = {
    "федеральная",
    "налоговая",
    "служба",
    "российская",
    "федерации",
    "налог",
    "профессиональный",
    "доход",
    "чек",
    "покупатель",
    "заказчик",
    "организация",
    "исполнитель",
    "самозанятый",
    "налогоплательщик",
    "продавец",
    "поставщик",
    "услуга",
    "услуги",
    "итого",
    "сумма",
    "инн",
    "дата",
    "номер",
    "мой",
}

_ORGANIZATION_MARKERS = (
    "ооо",
    "ао ",
    "пао",
    "зао",
    "общество",
    "компания",
    "организация",
    "заказчик",
    "покупатель",
)


@dataclass(frozen=True)
class InnCandidate:
    """Normalized INN value and its position in OCR text."""

    value: str
    start: int
    end: int


@dataclass(frozen=True)
class NameCandidate:
    """Normalized person name, source position, and layout quality."""

    value: str
    position: int
    layout_score: int


def _normalize_spaces(value: str) -> str:
    """Collapse OCR whitespace while preserving line boundaries."""
    lines = [re.sub(r"[\t \u00a0]+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(lines)


def _normalize_inn(raw: str) -> str | None:
    """Normalize a possible Russian INN and reject unsupported lengths."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) in {10, 12}:
        return digits
    return None


def extract_inn_candidates(text: str) -> list[InnCandidate]:
    """Return distinct INNs in the same order as they appear in the receipt."""
    candidates: list[InnCandidate] = []
    seen: set[str] = set()
    for match in _INN_PATTERN.finditer(text):
        normalized = _normalize_inn(match.group(1))
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(
            InnCandidate(value=normalized, start=match.start(), end=match.end())
        )
    return candidates


def _split_information_blocks(text: str) -> list[tuple[int, int, str]]:
    """Split OCR text into non-empty information blocks with source offsets."""
    blocks: list[tuple[int, int, str]] = []
    for match in re.finditer(r"(?:^|\n)(.*?)(?=\n\s*\n|\Z)", text, flags=re.DOTALL):
        value = match.group(1).strip()
        if value:
            blocks.append((match.start(1), match.end(1), value))
    if not blocks and text.strip():
        blocks.append((0, len(text), text.strip()))
    return blocks


def _strip_name_label(line: str) -> str:
    """Remove common field labels before evaluating a line as a person's name."""
    value = line.strip(" \t:;|—–-.,")
    value = re.sub(
        r"^(?:фио|ф\.\s*и\.\s*о\.|налогоплательщик|самозанятый|исполнитель|продавец|поставщик)\s*[:：-]?\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return value.strip(" \t:;|—–-.,")


def _clean_name_tokens(line: str) -> list[str]:
    """Return clean name-like tokens from one OCR line."""
    cleaned = _strip_name_label(line)
    cleaned = re.sub(r"[()\[\]{}<>]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned or any(char.isdigit() for char in cleaned):
        return []
    tokens = cleaned.split(" ")
    if not all(_NAME_TOKEN_PATTERN.match(token) for token in tokens):
        return []
    lowered = {token.lower().strip(".'’-") for token in tokens}
    if lowered.intersection(_FORBIDDEN_NAME_WORDS):
        return []
    compact_lower = cleaned.lower()
    if any(marker in compact_lower for marker in _ORGANIZATION_MARKERS):
        return []
    return tokens


def _candidate_name_lines(text: str, base_offset: int = 0) -> list[NameCandidate]:
    """Return one-line and split-line full-name candidates with source positions."""
    indexed_lines: list[tuple[str, int]] = []
    position = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.strip()
        if line:
            indexed_lines.append((line, base_offset + position))
        position += len(raw_line)

    result: list[NameCandidate] = []
    seen: set[tuple[str, int]] = set()

    for line, line_position in indexed_lines:
        tokens = _clean_name_tokens(line)
        if len(tokens) == 3:
            candidate = NameCandidate(" ".join(tokens), line_position, 140)
        elif len(tokens) == 2:
            candidate = NameCandidate(" ".join(tokens), line_position, 45)
        else:
            continue
        key = (candidate.value, candidate.position)
        if key not in seen:
            seen.add(key)
            result.append(candidate)

    for index in range(len(indexed_lines) - 1):
        first_line, first_position = indexed_lines[index]
        second_line, _ = indexed_lines[index + 1]
        first_tokens = _clean_name_tokens(first_line)
        second_tokens = _clean_name_tokens(second_line)

        combined_tokens: list[str] = []
        layout_score = 0
        if len(first_tokens) == 1 and len(second_tokens) == 2:
            combined_tokens = first_tokens + second_tokens
            layout_score = 150
        elif len(first_tokens) == 2 and len(second_tokens) == 1:
            combined_tokens = first_tokens + second_tokens
            layout_score = 120

        if combined_tokens:
            candidate = NameCandidate(
                " ".join(combined_tokens),
                first_position,
                layout_score,
            )
            key = (candidate.value, candidate.position)
            if key not in seen:
                seen.add(key)
                result.append(candidate)

    return result


def extract_issuer_name(text: str, first_inn: InnCandidate | None) -> str | None:
    """Extract the self-employed issuer's full name near the first INN."""
    normalized = _normalize_spaces(text)
    blocks = _split_information_blocks(normalized)
    candidates: list[tuple[int, int, str]] = []

    for block_index, (start, end, block_text) in enumerate(blocks):
        for candidate in _candidate_name_lines(block_text, start):
            score = candidate.layout_score

            if block_index == 1:
                score += 35

            if first_inn is not None:
                if start <= first_inn.start <= end:
                    score += 140
                distance = abs(candidate.position - first_inn.start)
                score += max(0, 100 - min(distance, 100))
                if candidate.position <= first_inn.start:
                    score += 20

            local_start = max(start, candidate.position - 80)
            local_end = min(end, candidate.position + len(candidate.value) + 80)
            local_text = normalized[local_start:local_end]
            if re.search(
                r"\b(?:ФИО|самозанятый|исполнитель|налогоплательщик)\b",
                local_text,
                re.IGNORECASE,
            ):
                score += 45

            candidates.append((score, -candidate.position, candidate.value))

    if not candidates and first_inn is not None:
        window_start = max(0, first_inn.start - 320)
        window_end = min(len(normalized), first_inn.end + 180)
        for candidate in _candidate_name_lines(
            normalized[window_start:window_end],
            window_start,
        ):
            distance = abs(candidate.position - first_inn.start)
            candidates.append(
                (
                    candidate.layout_score + max(0, 90 - distance),
                    -candidate.position,
                    candidate.value,
                )
            )

    if not candidates:
        return None
    return max(candidates)[2]


def _extract_organization_name(text: str, second_inn: InnCandidate | None) -> str | None:
    """Extract a nearby organization name for the receipt recipient."""
    if second_inn is None:
        return None
    normalized = _normalize_spaces(text)
    lines = normalized.splitlines()
    offset = 0
    indexed_lines: list[tuple[int, str]] = []
    for line in lines:
        indexed_lines.append((offset, line.strip()))
        offset += len(line) + 1

    nearby = sorted(indexed_lines, key=lambda item: abs(item[0] - second_inn.start))[:8]
    for _, line in nearby:
        compact = re.sub(r"\s+", " ", line).strip(" :;|—–-")
        lowered = compact.lower()
        if any(marker in lowered for marker in _ORGANIZATION_MARKERS):
            compact = re.sub(
                r"^(?:покупатель|заказчик|организация)\s*[:：-]?\s*",
                "",
                compact,
                flags=re.IGNORECASE,
            )
            if compact and not re.fullmatch(
                r"(?:ИНН)?\s*\d[\d\s-]+",
                compact,
                re.IGNORECASE,
            ):
                return compact[:160]
    return None


def _normalize_date(raw: str) -> str:
    """Normalize a numeric date to DD-MM-YYYY."""
    parts = re.split(r"[.\-/]", raw)
    if len(parts) != 3:
        return raw
    day, month, year = parts
    if len(year) == 2:
        year = f"20{year}"
    return f"{int(day):02d}-{int(month):02d}-{year}"


def _normalize_receipt_number(raw: str) -> str | None:
    """Normalize a receipt number and reject words mistaken for an identifier."""
    value = re.sub(r"\s+", "", raw).strip(" .,:;")
    if len(value) < 3 or not re.search(r"\d", value):
        return None
    if value.lower() in {"нпд", "налог", "доход"}:
        return None
    return value


def _extract_receipt_number(text: str) -> str | None:
    """Extract a receipt number only from an explicit number label."""
    compact = re.sub(r"\s+", " ", text)
    patterns = (
        r"\bчек\s*(?:№|N(?:o)?\.?)[\s:：-]*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-/ ]{2,80})",
        r"\b(?:номер\s+чека|№\s*чека)\s*[:：-]?\s*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-/ ]{2,80})",
        r"\bквитанц(?:ия|ии)\s*(?:№|N(?:o)?\.?)[\s:：-]*([A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-/ ]{2,80})",
    )
    stop_words = re.compile(
        r"\s+(?:от|дата|инн|покупатель|заказчик|сумма|итого|наименование)\b",
        re.IGNORECASE,
    )
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if not match:
            continue
        raw = stop_words.split(match.group(1), maxsplit=1)[0]
        normalized = _normalize_receipt_number(raw)
        if normalized:
            return normalized
    return None


def _extract_receipt_date(text: str) -> str | None:
    """Extract the first receipt date near a date/time or receipt label."""
    compact = re.sub(r"\s+", " ", text)
    labeled_patterns = (
        rf"(?:дата|дата\s+чека|чек[^\n]{{0,80}}?от)\s*[:：-]?\s*({_DATE_PATTERN.pattern})",
        rf"({_DATE_PATTERN.pattern})\s*(?:г\.?|в\s+\d{{1,2}}[:.]\d{{2}})",
    )
    for pattern in labeled_patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            raw = next(group for group in match.groups() if group)
            return _normalize_date(raw)
    match = _DATE_PATTERN.search(compact)
    return _normalize_date(match.group(1)) if match else None


def _normalize_money(raw: str) -> str:
    """Normalize a money value to a dot-decimal string."""
    value = raw.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return f"{float(value):.2f}"
    except ValueError:
        return value


def _extract_total_amount(text: str) -> str | None:
    """Extract total receipt amount, preferring explicitly labeled values."""
    compact = re.sub(r"\s+", " ", text)
    patterns = (
        rf"(?:итого|всего|сумма\s+чека|к\s+оплате)\s*[:：-]?\s*({_MONEY_PATTERN.pattern})",
        rf"({_MONEY_PATTERN.pattern})\s*(?:₽|руб\.?|RUB)\b",
    )
    for pattern in patterns:
        matches = list(re.finditer(pattern, compact, flags=re.IGNORECASE))
        if matches:
            raw = next(group for group in matches[-1].groups() if group)
            return _normalize_money(raw)
    all_values = _MONEY_PATTERN.findall(compact)
    return _normalize_money(all_values[-1]) if all_values else None


def _extract_service_description(text: str) -> str | None:
    """Extract the service description from common NPD receipt labels."""
    normalized = _normalize_spaces(text)
    patterns = (
        r"(?:наименование\s+(?:предмета\s+расч[её]та|услуги)|описание\s+услуги|услуга)\s*[:：-]?\s*(.+)",
        r"(?:предмет\s+расч[её]та)\s*[:：-]?\s*(.+)",
    )
    stop_pattern = re.compile(
        r"^(?:количество|цена|стоимость|сумма|итого|всего|инн|покупатель|заказчик|дата|чек)\b",
        re.IGNORECASE,
    )
    for line_index, line in enumerate(normalized.splitlines()):
        compact = re.sub(r"\s+", " ", line).strip()
        for pattern in patterns:
            match = re.search(pattern, compact, flags=re.IGNORECASE)
            if not match:
                continue
            value = match.group(1).strip(" :;|—–-")
            if value and not stop_pattern.match(value):
                return value[:300]
            following = normalized.splitlines()[line_index + 1 : line_index + 4]
            collected: list[str] = []
            for following_line in following:
                following_compact = re.sub(r"\s+", " ", following_line).strip()
                if not following_compact or stop_pattern.match(following_compact):
                    break
                collected.append(following_compact)
            if collected:
                return " ".join(collected)[:300]
    return None


def _recognition_score(text: str, inns: list[InnCandidate]) -> int:
    """Score OCR text as a probable NPD receipt."""
    compact = re.sub(r"\s+", " ", text).lower()
    score = 0
    if re.search(r"\bчек\b", compact):
        score += 35
    if "налог на профессиональный доход" in compact:
        score += 45
    if re.search(r"\bнпд\b", compact):
        score += 35
    if "мой налог" in compact:
        score += 30
    if "самозан" in compact or "налогоплательщик" in compact:
        score += 25
    if inns:
        score += 35
    if inns and len(inns[0].value) == 12:
        score += 20
    if _extract_total_amount(text):
        score += 10
    if _extract_receipt_date(text):
        score += 10
    return score


def extract_document(image_path: Path, ocr_result: OcrResult) -> ExtractedDocument:
    """Build a generic extracted document from NPD receipt OCR output."""
    combined = "\n".join(
        part
        for part in (
            ocr_result.header_text,
            ocr_result.targeted_text,
            ocr_result.text,
        )
        if part
    )
    combined = _normalize_spaces(combined)
    inn_candidates = extract_inn_candidates(combined)
    issuer_inn_candidate = inn_candidates[0] if inn_candidates else None
    recipient_inn_candidate = inn_candidates[1] if len(inn_candidates) > 1 else None
    issuer_name = extract_issuer_name(combined, issuer_inn_candidate)
    score = _recognition_score(combined, inn_candidates)

    document = ExtractedDocument(
        source_path=image_path,
        document_type=DOCUMENT_TYPE,
        is_recognized=score >= 80,
        document_number=_extract_receipt_number(combined),
        document_date=_extract_receipt_date(combined),
        issuer_name=issuer_name,
        issuer_inn=issuer_inn_candidate.value if issuer_inn_candidate else None,
        recipient_name=_extract_organization_name(combined, recipient_inn_candidate),
        recipient_inn=(
            recipient_inn_candidate.value if recipient_inn_candidate else None
        ),
        total_amount=_extract_total_amount(combined),
        currency="RUB",
        description=_extract_service_description(combined),
        confidence=min(100, score),
        rotation_degrees=ocr_result.rotation_degrees,
        text_preview=re.sub(r"\s+", " ", combined)[:500],
    )

    if issuer_inn_candidate and len(issuer_inn_candidate.value) != 12:
        document.warnings.append(
            "The first INN was selected as the receipt issuer, but it is not 12 digits"
        )
    if document.is_recognized and not document.issuer_name:
        document.warnings.append(
            "The receipt was recognized, but the self-employed issuer name was not extracted"
        )
    if document.is_recognized and not document.issuer_inn:
        document.warnings.append(
            "The receipt was recognized, but the self-employed issuer INN was not extracted"
        )
    if document.is_recognized and not document.document_number:
        document.warnings.append(
            "The receipt was recognized, but no value following an explicit receipt-number label was found"
        )
    return document
