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
_ENTITY_DETECTION_MODES = frozenset(
    {"automatic", "configured", "combined", "disabled"}
)
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


def _normalize_entity_detection_mode(value: str) -> str:
    """Normalize and validate one configured entity-detection mode."""
    normalized = value.strip().casefold()
    if normalized not in _ENTITY_DETECTION_MODES:
        supported = ", ".join(sorted(_ENTITY_DETECTION_MODES))
        raise ValueError(f"entityDetectionMode must be one of: {supported}")
    return normalized


@dataclass(frozen=True)
class ReplacementRule:
    """Replace one configured literal with a privacy-safe user value."""

    source: str
    replacement: str


@dataclass(frozen=True)
class AnonymizationConfig:
    """User-defined literal, replacement, and section anonymization rules."""

    entity_detection_mode: str | None = None
    excluded: tuple[str, ...] = ()
    included: tuple[str, ...] = ()
    included_and_replaced: tuple[ReplacementRule, ...] = ()
    included_paragraphs: tuple[str, ...] = ()
    included_fuzzy: bool = False
    included_fuzzy_max_errors: int = 1

    @property
    def resolved_entity_detection_mode(self) -> str:
        """Return the explicit mode or the backward-compatible inferred mode."""
        if self.entity_detection_mode is None:
            if self.included or self.included_and_replaced:
                return "configured"
            return "automatic"

        return _normalize_entity_detection_mode(self.entity_detection_mode)

    @property
    def uses_automatic_detection(self) -> bool:
        """Return True when Presidio-based detections participate in masking."""
        return self.resolved_entity_detection_mode in {"automatic", "combined"}

    @property
    def uses_configured_detection(self) -> bool:
        """Return True when configured literal rules participate in masking."""
        return self.resolved_entity_detection_mode in {"configured", "combined"}

    @property
    def configured_only(self) -> bool:
        """Return True when only configured literal rules are active."""
        return self.resolved_entity_detection_mode == "configured"

    @property
    def included_only(self) -> bool:
        """Return the backward-compatible name for configured-only mode."""
        return self.configured_only


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


def _split_replacement_rules(raw_value: str) -> tuple[ReplacementRule, ...]:
    """Parse multiline ``source -> replacement`` configuration rules."""
    rules: list[ReplacementRule] = []
    seen: dict[str, str] = {}
    for line_number, raw_line in enumerate(raw_value.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if "->" not in line:
            raise ValueError(
                "includedAndReplaced entries must use 'source -> replacement': "
                f"line {line_number}: {line}"
            )
        source, replacement = (part.strip() for part in line.split("->", 1))
        if not source or not replacement:
            raise ValueError(
                "includedAndReplaced source and replacement must be non-empty: "
                f"line {line_number}: {line}"
            )
        normalized = source.casefold()
        previous = seen.get(normalized)
        if previous is not None:
            if previous != replacement:
                raise ValueError(
                    "includedAndReplaced contains conflicting replacements for: "
                    f"{source}"
                )
            continue
        seen[normalized] = replacement
        rules.append(ReplacementRule(source=source, replacement=replacement))
    return tuple(rules)


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
    entity_detection_mode: str | None = None
    if "entitydetectionmode" in section:
        entity_detection_mode = _normalize_entity_detection_mode(
            section.get("entitydetectionmode", "")
        )
    excluded = _split_values(section.get("excluded", ""))
    included = _split_values(section.get("included", ""))
    included_and_replaced = _split_replacement_rules(
        section.get("includedandreplaced", "")
    )
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
        entity_detection_mode=entity_detection_mode,
        excluded=excluded,
        included=included,
        included_and_replaced=included_and_replaced,
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


def _literal_matches(
    text: str,
    values: Sequence[str],
) -> list[tuple[int, int, str]]:
    """Return case-insensitive spans and their configured source literals."""
    matches: list[tuple[int, int, str]] = []
    for value in values:
        pattern = _literal_pattern(value)
        if pattern is None:
            continue
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end(), value))
    return sorted(set(matches), key=lambda item: (item[0], item[1], item[2].casefold()))


def _literal_spans(text: str, values: Sequence[str]) -> list[tuple[int, int]]:
    """Return case-insensitive spans for configured literal fragments."""
    return sorted({(start, end) for start, end, _value in _literal_matches(text, values)})


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


def _fuzzy_literal_matches(
    text: str,
    values: Sequence[str],
    maximum_errors: int,
) -> list[tuple[int, int, str]]:
    """Return OCR-tolerant matches with a bounded total edit distance."""
    tokens = [
        (match, normalized)
        for match in _TOKEN_PATTERN.finditer(text)
        if (normalized := _normalize_ocr_token(match.group(0)))
    ]
    matches = set(_literal_matches(text, values))
    if maximum_errors <= 0 or not tokens:
        return sorted(matches, key=lambda item: (item[0], item[1], item[2].casefold()))

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
            matches.add((window[0][0].start(), window[-1][0].end(), value))
    return sorted(matches, key=lambda item: (item[0], item[1], item[2].casefold()))


def _fuzzy_literal_spans(
    text: str,
    values: Sequence[str],
    maximum_errors: int,
) -> list[tuple[int, int]]:
    """Return OCR-tolerant literal spans with a bounded total edit distance."""
    return sorted(
        {
            (start, end)
            for start, end, _value in _fuzzy_literal_matches(
                text,
                values,
                maximum_errors,
            )
        }
    )


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
            replacement=entity.replacement,
        )
        for start, end in segments
        if end > start
    ]


def _configured_entities(
    text: str,
    config: AnonymizationConfig,
    fuzzy: bool,
) -> list[DetectedEntity]:
    """Build explicit mask and replacement entities from configured rules."""
    match_function = _fuzzy_literal_matches if fuzzy else _literal_matches
    match_args = (
        (config.included_fuzzy_max_errors,)
        if fuzzy
        else ()
    )

    replacements_by_source = {
        rule.source.casefold(): rule.replacement
        for rule in config.included_and_replaced
    }
    replacement_sources = tuple(rule.source for rule in config.included_and_replaced)
    replacement_matches = match_function(
        text,
        replacement_sources,
        *match_args,
    )
    replacement_entities = [
        DetectedEntity(
            start=start,
            end=end,
            entity_type=(
                "CONFIG_REPLACED_FUZZY" if fuzzy else "CONFIG_REPLACED"
            ),
            score=1.1,
            replacement=replacements_by_source[source.casefold()],
        )
        for start, end, source in replacement_matches
    ]

    included_matches = match_function(
        text,
        config.included,
        *match_args,
    )
    mask_entities: list[DetectedEntity] = []
    for start, end, _source in included_matches:
        exact_replacement = next(
            (
                entity
                for entity in replacement_entities
                if entity.start == start and entity.end == end
            ),
            None,
        )
        if exact_replacement is not None:
            continue
        mask_entities.append(
            DetectedEntity(
                start=start,
                end=end,
                entity_type=(
                    "CONFIG_INCLUDED_FUZZY" if fuzzy else "CONFIG_INCLUDED"
                ),
                score=1.0,
            )
        )
    return [*replacement_entities, *mask_entities]


class ConfiguredTextAnalyzer:
    """Apply the configured entity-detection mode to one base analyzer."""

    def __init__(
        self,
        base_analyzer: TextEntityAnalyzer | None,
        config: AnonymizationConfig,
    ) -> None:
        self._base_analyzer = base_analyzer
        self._config = config

    def analyze(self, text: str) -> Sequence[DetectedEntity]:
        """Return exact configured and/or automatic detections for native text."""
        return self._analyze(text, fuzzy_configured=False)

    def analyze_ocr(self, text: str) -> Sequence[DetectedEntity]:
        """Analyze OCR text with optional fuzzy mask and replacement matching."""
        return self._analyze(
            text,
            fuzzy_configured=self._config.included_fuzzy,
        )

    def _analyze(
        self,
        text: str,
        *,
        fuzzy_configured: bool,
    ) -> list[DetectedEntity]:
        """Compose automatic and configured detections according to the mode."""
        mode = self._config.resolved_entity_detection_mode
        if mode == "disabled":
            return []

        configured_entities = (
            _configured_entities(text, self._config, fuzzy=fuzzy_configured)
            if mode in {"configured", "combined"}
            else []
        )
        if mode == "configured":
            return configured_entities

        if self._base_analyzer is None:
            raise RuntimeError(
                "A base analyzer is required for automatic entity detection"
            )

        automatic_entities = list(self._base_analyzer.analyze(text))
        excluded_spans = _literal_spans(text, self._config.excluded)
        if excluded_spans:
            automatic_entities = [
                segment
                for entity in automatic_entities
                for segment in _subtract_spans(entity, excluded_spans)
            ]

        if configured_entities:
            configured_spans = [
                (entity.start, entity.end) for entity in configured_entities
            ]
            automatic_entities = [
                segment
                for entity in automatic_entities
                for segment in _subtract_spans(entity, configured_spans)
            ]

        return sorted(
            [*automatic_entities, *configured_entities],
            key=lambda entity: (entity.start, entity.end, entity.entity_type),
        )


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
    transformed_text: str,
    headings: Sequence[str],
) -> tuple[str, bool]:
    """Mask all non-whitespace text after the first configured heading."""
    original_span = find_heading_text_span(original_text, headings)
    if original_span is None:
        return transformed_text, False
    transformed_span = find_heading_text_span(transformed_text, headings)
    cutoff = (
        transformed_span[1]
        if transformed_span is not None
        else min(len(transformed_text), original_span[1])
    )
    characters = list(transformed_text)
    for index in range(cutoff, len(characters)):
        if not characters[index].isspace():
            characters[index] = "█"
    return "".join(characters), True
