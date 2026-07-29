"""Configuration and literal matching rules for document anonymization."""

from __future__ import annotations

import configparser
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Sequence

from .models import DetectedEntity, TextEntityAnalyzer


DEFAULT_CONFIG_PATH = Path("config/anonymization.ini")
_SECTION_NAME = "anonymization"
_TOKEN_PATTERN = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")
_HEADING_FUZZY_THRESHOLD = 0.84
_MAX_INCLUDED_FUZZY_ERRORS = 3
_MIN_FUZZY_LITERAL_LENGTH = 5
_OCR_CONFUSABLES = str.maketrans(
    {
        "a": "а",
        "b": "в",
        "c": "с",
        "e": "е",
        "h": "н",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "t": "т",
        "x": "х",
        "y": "у",
    }
)


@dataclass(frozen=True)
class AnonymizationConfig:
    """User-defined literal and section rules for anonymization."""

    excluded: tuple[str, ...] = ()
    included: tuple[str, ...] = ()
    included_paragraphs: tuple[str, ...] = ()
    included_fuzzy: bool = False
    included_fuzzy_max_errors: int = 1

    @property
    def included_only(self) -> bool:
        """Return True when literal-only anonymization mode is enabled."""
        return bool(self.included)


EMPTY_ANONYMIZATION_CONFIG = AnonymizationConfig()


def _split_values(raw_value: str) -> tuple[str, ...]:
    """Split comma-separated or multiline configuration values."""
    values: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[,\n]", raw_value):
        value = part.strip()
        normalized = value.casefold()
        if not value or normalized in seen:
            continue
        values.append(value)
        seen.add(normalized)
    return tuple(values)


def load_anonymization_config(path: Path) -> AnonymizationConfig:
    """Load anonymization rules from one INI file."""
    config_path = path.expanduser().resolve()
    if not config_path.exists() or not config_path.is_file():
        raise ValueError(f"Anonymization config file does not exist: {config_path}")

    parser = configparser.ConfigParser(interpolation=None)
    try:
        with config_path.open("r", encoding="utf-8-sig") as stream:
            parser.read_file(stream)
    except (OSError, configparser.Error) as exc:
        raise ValueError(f"Cannot read anonymization config: {config_path}: {exc}") from exc

    if not parser.has_section(_SECTION_NAME):
        raise ValueError(
            f"Anonymization config must contain [{_SECTION_NAME}] section: {config_path}"
        )

    section = parser[_SECTION_NAME]
    excluded = _split_values(section.get("excluded", ""))
    included = _split_values(section.get("included", ""))
    included_paragraphs = _split_values(section.get("includedparagraphs", ""))
    try:
        included_fuzzy = section.getboolean("includedfuzzy", fallback=False)
    except ValueError as exc:
        raise ValueError("includedFuzzy must be true or false") from exc
    try:
        included_fuzzy_max_errors = section.getint(
            "includedfuzzymaxerrors",
            fallback=1,
        )
    except ValueError as exc:
        raise ValueError("includedFuzzyMaxErrors must be an integer") from exc
    if not 0 <= included_fuzzy_max_errors <= _MAX_INCLUDED_FUZZY_ERRORS:
        raise ValueError(
            "includedFuzzyMaxErrors must be between 0 and "
            f"{_MAX_INCLUDED_FUZZY_ERRORS}"
        )

    return AnonymizationConfig(
        excluded=excluded,
        included=included,
        included_paragraphs=included_paragraphs,
        included_fuzzy=included_fuzzy,
        included_fuzzy_max_errors=included_fuzzy_max_errors,
    )


def _literal_pattern(value: str) -> re.Pattern[str] | None:
    """Build a case-insensitive pattern tolerant of whitespace differences."""
    parts = value.split()
    if not parts:
        return None
    return re.compile(r"\s+".join(re.escape(part) for part in parts), re.IGNORECASE)


def _literal_spans(text: str, values: Sequence[str]) -> list[tuple[int, int]]:
    """Return case-insensitive spans for configured literal fragments."""
    spans: list[tuple[int, int]] = []
    for value in values:
        pattern = _literal_pattern(value)
        if pattern is None:
            continue
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end()))
    return sorted(set(spans))


def _normalize_ocr_token(value: str) -> str:
    """Normalize OCR text and common Latin/Cyrillic lookalikes."""
    return _normalize_token(value).translate(_OCR_CONFUSABLES)


def _bounded_edit_distance(left: str, right: str, maximum: int) -> int | None:
    """Return Levenshtein distance when it does not exceed the bound."""
    if abs(len(left) - len(right)) > maximum:
        return None
    if left == right:
        return 0
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        row_minimum = left_index
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1]
                    + (left_character != right_character),
                )
            )
            row_minimum = min(row_minimum, current[-1])
        if row_minimum > maximum:
            return None
        previous = current
    distance = previous[-1]
    return distance if distance <= maximum else None


def _fuzzy_literal_spans(
    text: str,
    values: Sequence[str],
    maximum_errors: int,
) -> list[tuple[int, int]]:
    """Return OCR-tolerant literal spans with a bounded total edit distance."""
    tokens = [
        (match, normalized)
        for match in _TOKEN_PATTERN.finditer(text)
        if (normalized := _normalize_ocr_token(match.group(0)))
    ]
    spans = set(_literal_spans(text, values))
    if maximum_errors <= 0 or not tokens:
        return sorted(spans)

    for value in values:
        target_tokens = tuple(
            normalized
            for token in _TOKEN_PATTERN.findall(value)
            if (normalized := _normalize_ocr_token(token))
        )
        if not target_tokens:
            continue
        target = "".join(target_tokens)
        if len(target) < _MIN_FUZZY_LITERAL_LENGTH:
            continue
        window_size = len(target_tokens)
        for start in range(0, len(tokens) - window_size + 1):
            window = tokens[start : start + window_size]
            candidate = "".join(normalized for _match, normalized in window)
            if _bounded_edit_distance(candidate, target, maximum_errors) is None:
                continue
            spans.add((window[0][0].start(), window[-1][0].end()))
    return sorted(spans)


def _subtract_spans(
    entity: DetectedEntity,
    excluded_spans: Sequence[tuple[int, int]],
) -> list[DetectedEntity]:
    """Remove excluded literal ranges from one detected entity."""
    segments = [(entity.start, entity.end)]
    for excluded_start, excluded_end in excluded_spans:
        updated: list[tuple[int, int]] = []
        for start, end in segments:
            if excluded_end <= start or excluded_start >= end:
                updated.append((start, end))
                continue
            if excluded_start > start:
                updated.append((start, excluded_start))
            if excluded_end < end:
                updated.append((excluded_end, end))
        segments = updated
    return [
        DetectedEntity(
            start=start,
            end=end,
            entity_type=entity.entity_type,
            score=entity.score,
        )
        for start, end in segments
        if end > start
    ]


class ConfiguredTextAnalyzer:
    """Select literal-only or default-analyzer anonymization behavior."""

    def __init__(
        self,
        base_analyzer: TextEntityAnalyzer | None,
        config: AnonymizationConfig,
    ) -> None:
        self._base_analyzer = base_analyzer
        self._config = config

    def analyze(self, text: str) -> Sequence[DetectedEntity]:
        """Return configured literals only, or filtered default detections."""
        if self._config.included_only:
            return [
                DetectedEntity(start, end, "CONFIG_INCLUDED", 1.0)
                for start, end in _literal_spans(text, self._config.included)
            ]

        if self._base_analyzer is None:
            raise RuntimeError(
                "A base analyzer is required when the included list is empty"
            )

        entities = list(self._base_analyzer.analyze(text))
        excluded_spans = _literal_spans(text, self._config.excluded)
        if not excluded_spans:
            return entities

        filtered: list[DetectedEntity] = []
        for entity in entities:
            filtered.extend(_subtract_spans(entity, excluded_spans))
        return filtered

    def analyze_ocr(self, text: str) -> Sequence[DetectedEntity]:
        """Analyze OCR text with optional included-only fuzzy matching."""
        if not self._config.included_only or not self._config.included_fuzzy:
            return self.analyze(text)
        return [
            DetectedEntity(start, end, "CONFIG_INCLUDED_FUZZY", 1.0)
            for start, end in _fuzzy_literal_spans(
                text,
                self._config.included,
                self._config.included_fuzzy_max_errors,
            )
        ]


def _normalize_token(value: str) -> str:
    """Normalize one OCR or heading token for tolerant comparisons."""
    return "".join(
        character
        for character in value.casefold().replace("ё", "е")
        if character.isalnum()
    )


def _heading_tokens(value: str) -> tuple[str, ...]:
    """Return normalized tokens from one configured heading."""
    return tuple(
        normalized
        for token in _TOKEN_PATTERN.findall(value)
        if (normalized := _normalize_token(token))
    )


def find_heading_token_range(
    values: Sequence[str],
    headings: Sequence[str],
) -> tuple[int, int] | None:
    """Find a configured heading in OCR tokens using exact or safe fuzzy matching."""
    normalized_values: list[tuple[int, str]] = [
        (index, normalized)
        for index, value in enumerate(values)
        if (normalized := _normalize_token(value))
    ]
    if not normalized_values:
        return None

    best_match: tuple[float, int, int] | None = None
    source_tokens = [value for _index, value in normalized_values]
    for heading in headings:
        target_tokens = _heading_tokens(heading)
        if not target_tokens:
            continue
        target_text = " ".join(target_tokens)
        minimum_size = max(1, len(target_tokens) - 1)
        maximum_size = len(target_tokens) + 1
        for start in range(len(source_tokens)):
            for size in range(minimum_size, maximum_size + 1):
                end = start + size
                if end > len(source_tokens):
                    continue
                candidate_tokens = source_tokens[start:end]
                if tuple(candidate_tokens) == target_tokens:
                    score = 1.0
                elif len(target_tokens) < 3:
                    continue
                else:
                    score = SequenceMatcher(
                        None,
                        " ".join(candidate_tokens),
                        target_text,
                    ).ratio()
                    if score < _HEADING_FUZZY_THRESHOLD:
                        continue
                original_start = normalized_values[start][0]
                original_end = normalized_values[end - 1][0] + 1
                candidate = (score, -original_start, original_end)
                if best_match is None or candidate > best_match:
                    best_match = candidate

    if best_match is None:
        return None
    _score, negative_start, end = best_match
    return -negative_start, end


def find_heading_text_span(
    text: str,
    headings: Sequence[str],
) -> tuple[int, int] | None:
    """Find one configured heading and return its character span."""
    tokens = list(_TOKEN_PATTERN.finditer(text))
    token_range = find_heading_token_range(
        [match.group(0) for match in tokens],
        headings,
    )
    if token_range is None:
        return None
    start, end = token_range
    return tokens[start].start(), tokens[end - 1].end()


def mask_after_heading(
    original_text: str,
    masked_text: str,
    headings: Sequence[str],
) -> tuple[str, bool]:
    """Mask all non-whitespace text after the first configured heading."""
    span = find_heading_text_span(original_text, headings)
    if span is None:
        return masked_text, False
    characters = list(masked_text)
    for index in range(span[1], len(characters)):
        if not characters[index].isspace():
            characters[index] = "█"
    return "".join(characters), True
