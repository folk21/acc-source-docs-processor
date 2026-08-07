"""Presidio-backed multilingual PII detection and configurable text transformation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .models import DetectedEntity, TextEntityAnalyzer


MASK_CHARACTER = "█"
_INTERNATIONAL_PHONE_PATTERN = r"(?<![\w+])\+\d(?:[\s().-]*\d){7,14}(?!\d)"


def merge_entities(
    entities: Iterable[DetectedEntity],
    text_length: int,
) -> list[DetectedEntity]:
    """Normalize, sort, and merge overlapping sensitive text spans."""
    normalized = sorted(
        (
            DetectedEntity(
                start=max(0, min(text_length, entity.start)),
                end=max(0, min(text_length, entity.end)),
                entity_type=entity.entity_type,
                score=entity.score,
                replacement=entity.replacement,
            )
            for entity in entities
            if entity.end > entity.start
        ),
        key=lambda entity: (entity.start, entity.end),
    )
    merged: list[DetectedEntity] = []
    for entity in normalized:
        if entity.end <= entity.start:
            continue
        if not merged or entity.start >= merged[-1].end:
            merged.append(entity)
            continue
        previous = merged[-1]
        same_span = previous.start == entity.start and previous.end == entity.end
        if same_span:
            preferred = entity if entity.replacement is not None else previous
            replacement = preferred.replacement
        else:
            replacement = None
        merged[-1] = DetectedEntity(
            start=previous.start,
            end=max(previous.end, entity.end),
            entity_type=(
                previous.entity_type
                if previous.score >= entity.score
                else entity.entity_type
            ),
            score=max(previous.score, entity.score),
            replacement=replacement,
        )
    return merged


def _masked_fragment(value: str) -> str:
    """Mask one source fragment while preserving its whitespace."""
    return "".join(
        character if character.isspace() else MASK_CHARACTER
        for character in value
    )


def transform_entities(
    text: str,
    entities: Sequence[DetectedEntity],
) -> str:
    """Apply masking or configured replacement to explicit entity spans."""
    transformed = text
    for entity in reversed(merge_entities(entities, len(text))):
        replacement = (
            entity.replacement
            if entity.replacement is not None
            else _masked_fragment(text[entity.start : entity.end])
        )
        transformed = (
            transformed[: entity.start]
            + replacement
            + transformed[entity.end :]
        )
    return transformed


def transform_text(
    text: str,
    analyzer: TextEntityAnalyzer,
) -> tuple[str, list[DetectedEntity]]:
    """Apply configured masking or replacement to detected text spans."""
    if not text:
        return text, []
    entities = merge_entities(analyzer.analyze(text), len(text))
    if not entities:
        return text, []
    return transform_entities(text, entities), entities


def transform_text_parts(
    parts: Sequence[str],
    analyzer: TextEntityAnalyzer,
) -> tuple[list[str], list[DetectedEntity]]:
    """Transform concatenated text while retaining its original run boundaries."""
    text = "".join(parts)
    entities = merge_entities(analyzer.analyze(text), len(text))
    if not entities:
        return list(parts), []

    boundaries: list[tuple[int, int]] = []
    offset = 0
    for part in parts:
        boundaries.append((offset, offset + len(part)))
        offset += len(part)
    output = ["" for _part in parts]

    def append_range(start: int, end: int, mask: bool = False) -> None:
        for index, (part_start, part_end) in enumerate(boundaries):
            overlap_start = max(start, part_start)
            overlap_end = min(end, part_end)
            if overlap_start >= overlap_end:
                continue
            fragment = text[overlap_start:overlap_end]
            output[index] += _masked_fragment(fragment) if mask else fragment

    cursor = 0
    for entity in entities:
        append_range(cursor, entity.start)
        if entity.replacement is None:
            append_range(entity.start, entity.end, mask=True)
        else:
            owner_index = next(
                (
                    index
                    for index, (part_start, part_end) in enumerate(boundaries)
                    if entity.start < part_end and entity.end > part_start
                ),
                len(parts) - 1,
            )
            if owner_index >= 0:
                output[owner_index] += entity.replacement
        cursor = entity.end
    append_range(cursor, len(text))
    return output, entities


def mask_text(
    text: str,
    analyzer: TextEntityAnalyzer,
) -> tuple[str, list[DetectedEntity]]:
    """Backward-compatible alias for configurable text transformation."""
    return transform_text(text, analyzer)


class PresidioTextAnalyzer:
    """Adapt multilingual Microsoft Presidio results to the project protocol."""

    def __init__(
        self,
        analyzer_engine,
        languages: tuple[str, ...] = ("ru", "en"),
    ) -> None:
        self._engine = analyzer_engine
        self._languages = languages

    def analyze(self, text: str) -> Sequence[DetectedEntity]:
        """Detect PII by combining results from every configured NLP language."""
        if not text.strip():
            return []

        entities: list[DetectedEntity] = []
        for language in self._languages:
            results = self._engine.analyze(
                text=text,
                language=language,
                score_threshold=0.30,
            )
            entities.extend(
                DetectedEntity(
                    start=result.start,
                    end=result.end,
                    entity_type=result.entity_type,
                    score=float(result.score),
                )
                for result in results
            )
        return merge_entities(entities, len(text))


def _add_pattern_recognizers(engine) -> None:
    """Register accounting, identity, and contact patterns in Presidio."""
    from presidio_analyzer import Pattern, PatternRecognizer

    specifications = (
        (
            "ORGANIZATION",
            (
                Pattern(
                    "Quoted Russian organization",
                    r"(?i)(?<![A-ZА-Я])(?:ООО|ПАО|АО|ЗАО)\s*"
                    r"[«\"][^»\"\n]{2,120}[»\"]",
                    0.75,
                ),
            ),
            ("организация", "продавец", "покупатель", "поставщик"),
        ),
        (
            "PERSON",
            (
                Pattern(
                    "Labeled Russian person",
                    r"(?i)(?:ФИО|водитель|директор|руководитель|"
                    r"представитель|исполнитель)\s*[:.-]?\s*"
                    r"[А-ЯЁ][а-яё-]{1,30}\s+[А-ЯЁ][а-яё-]{1,30}"
                    r"(?:\s+[А-ЯЁ][а-яё-]{1,30})?",
                    0.70,
                ),
            ),
            ("фио", "водитель", "директор", "руководитель"),
        ),
        (
            "RU_INN",
            (
                Pattern(
                    "Russian INN",
                    r"(?<!\d)(?:\d[\s-]?){9}\d(?!\d)|"
                    r"(?<!\d)(?:\d[\s-]?){11}\d(?!\d)",
                    0.55,
                ),
            ),
            ("инн", "налогоплательщик"),
        ),
        (
            "RU_KPP",
            (Pattern("Russian KPP", r"(?<!\d)\d{4}[0-9A-ZА-Я]{2}\d{3}(?!\d)", 0.45),),
            ("кпп",),
        ),
        (
            "RU_OGRN",
            (Pattern("Russian OGRN", r"(?<!\d)\d{13}(?!\d)|(?<!\d)\d{15}(?!\d)", 0.45),),
            ("огрн", "огрнип"),
        ),
        (
            "RU_SNILS",
            (Pattern("Russian SNILS", r"(?<!\d)\d{3}[ -]?\d{3}[ -]?\d{3}[ -]?\d{2}(?!\d)", 0.60),),
            ("снилс",),
        ),
        (
            "RU_PASSPORT",
            (Pattern("Russian passport", r"(?<!\d)\d{2}[ ]?\d{2}[ ]?\d{6}(?!\d)", 0.45),),
            ("паспорт", "серия", "выдан"),
        ),
        (
            "RU_BANK_ACCOUNT",
            (Pattern("Russian bank account", r"(?<!\d)\d{20}(?!\d)", 0.55),),
            ("счет", "счёт", "р/с", "к/с", "расчетный", "корреспондентский"),
        ),
        (
            "RU_BIK",
            (Pattern("Russian BIK", r"(?<!\d)\d{9}(?!\d)", 0.35),),
            ("бик",),
        ),
        (
            "PHONE_NUMBER",
            (
                Pattern(
                    "Russian phone",
                    r"(?<!\d)(?:\+7|8)[\s(.-]*\d{3}[\s).-]*"
                    r"\d{3}[\s.-]*\d{2}[\s.-]*\d{2}(?!\d)",
                    0.70,
                ),
            ),
            ("телефон", "тел", "моб"),
        ),
        (
            "EMAIL_ADDRESS",
            (
                Pattern(
                    "Email address",
                    r"(?i)(?<![\w.+-])[\w.+-]+@[\w-]+"
                    r"(?:\.[\w-]+)+(?![\w.-])",
                    0.85,
                ),
            ),
            ("email", "e-mail", "почта"),
        ),
        (
            "IP_ADDRESS",
            (Pattern("IPv4 address", r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)", 0.55),),
            ("ip", "адрес"),
        ),
        (
            "VEHICLE_REGISTRATION",
            (
                Pattern(
                    "Russian vehicle plate",
                    r"(?i)(?<![A-ZА-Я0-9])"
                    r"[ABEKMHOPCTYXАВЕКМНОРСТУХ]\d{3}"
                    r"[ABEKMHOPCTYXАВЕКМНОРСТУХ]{2}\s?\d{2,3}"
                    r"(?![A-ZА-Я0-9])",
                    0.65,
                ),
            ),
            ("госномер", "автомобиль", "транспортное средство"),
        ),
        (
            "VIN",
            (Pattern("Vehicle VIN", r"(?i)(?<![A-Z0-9])[A-HJ-NPR-Z0-9]{17}(?![A-Z0-9])", 0.65),),
            ("vin", "вин"),
        ),
        (
            "DOCUMENT_NUMBER",
            (
                Pattern(
                    "Labeled document number",
                    r"(?i)(?:договор|сч[её]т(?:-фактура)?|упд|акт|"
                    r"накладная|чек|документ|паспорт)\s*"
                    r"(?:№|N|No\.?)[\s:.-]*"
                    r"[A-ZА-Я0-9][A-ZА-Я0-9/_-]{2,}",
                    0.60,
                ),
            ),
            ("номер", "№"),
        ),
    )

    for entity_type, patterns, context in specifications:
        engine.registry.add_recognizer(
            PatternRecognizer(
                supported_entity=entity_type,
                patterns=list(patterns),
                context=list(context),
                supported_language="ru",
            )
        )

    international_phone_pattern = Pattern(
        "International phone with country prefix",
        _INTERNATIONAL_PHONE_PATTERN,
        0.78,
    )
    phone_context = (
        "phone",
        "mobile",
        "tel",
        "telephone",
        "телефон",
        "тел",
        "моб",
    )
    for language in ("ru", "en"):
        engine.registry.add_recognizer(
            PatternRecognizer(
                supported_entity="PHONE_NUMBER",
                patterns=[international_phone_pattern],
                context=list(phone_context),
                supported_language=language,
            )
        )


def create_presidio_analyzer(
    model_name: str = "ru_core_news_sm",
) -> PresidioTextAnalyzer:
    """Create a local Presidio analyzer with Russian and English spaCy NER."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NerModelConfiguration, SpacyNlpEngine
    except ImportError as exc:
        raise RuntimeError(
            "Microsoft Presidio is not installed. Run: pip install -r requirements.txt"
        ) from exc

    try:
        ner_configuration = NerModelConfiguration(
            default_score=0.65,
            model_to_presidio_entity_mapping={
                "PER": "PERSON",
                "PERSON": "PERSON",
                "LOC": "LOCATION",
                "GPE": "LOCATION",
                "ORG": "ORGANIZATION",
            },
        )
        nlp_engine = SpacyNlpEngine(
            models=[
                {"lang_code": "ru", "model_name": model_name},
                {"lang_code": "en", "model_name": "en_core_web_sm"},
            ],
            ner_model_configuration=ner_configuration,
        )
        engine = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["ru", "en"],
        )
    except OSError as exc:
        raise RuntimeError(
            "The required spaCy models are not installed. Run: "
            "python -m spacy download ru_core_news_sm && "
            "python -m spacy download en_core_web_sm"
        ) from exc

    _add_pattern_recognizers(engine)
    return PresidioTextAnalyzer(engine)
