"""Shared models for local document anonymization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(frozen=True, order=True)
class DetectedEntity:
    """One sensitive text span returned by a PII analyzer."""

    start: int
    end: int
    entity_type: str
    score: float = 1.0


class TextEntityAnalyzer(Protocol):
    """Detect sensitive spans in Russian text without changing the text."""

    def analyze(self, text: str) -> Sequence[DetectedEntity]:
        """Return sensitive spans using zero-based character offsets."""
        ...


@dataclass
class AnonymizedFileResult:
    """Result of anonymizing one source file."""

    source_path: Path
    destination_path: Path | None = None
    detected_entities: int = 0
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """Return True when the anonymized output was created."""
        return self.error is None and self.destination_path is not None


@dataclass
class AnonymizationSummary:
    """Aggregate result for one recursive folder anonymization run."""

    source_root: Path
    output_root: Path
    results: list[AnonymizedFileResult] = field(default_factory=list)

    @property
    def succeeded_count(self) -> int:
        """Return the number of files written successfully."""
        return sum(result.succeeded for result in self.results)

    @property
    def failed_count(self) -> int:
        """Return the number of files that were not anonymized."""
        return sum(not result.succeeded for result in self.results)

    @property
    def detected_entities(self) -> int:
        """Return the total number of detected sensitive spans."""
        return sum(result.detected_entities for result in self.results)
