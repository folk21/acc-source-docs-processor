"""Shared models for local document anonymization."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, Sequence


@dataclass(frozen=True, order=True)
class DetectedEntity:
    """One sensitive text span returned by a PII analyzer."""

    start: int
    end: int
    entity_type: str
    score: float = 1.0
    replacement: str | None = field(default=None, compare=False)


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
    additional_destination_paths: list[Path] = field(default_factory=list)
    detected_entities: int = 0
    error: str | None = None

    @property
    def output_paths(self) -> tuple[Path, ...]:
        """Return all generated paths with the primary output first."""
        if self.destination_path is None:
            return ()
        return (self.destination_path, *self.additional_destination_paths)

    @property
    def succeeded(self) -> bool:
        """Return True when every requested anonymized output was created."""
        return self.error is None and bool(self.output_paths)


@dataclass(frozen=True)
class AnonymizationProgress:
    """Privacy-safe progress event for one anonymization run."""

    event: Literal["file_started", "unit_started", "file_finished"]
    source_path: Path
    file_index: int
    file_count: int
    unit_name: str | None = None
    unit_index: int | None = None
    unit_count: int | None = None
    detected_entities: int = 0
    output_count: int = 0
    error: str | None = None


AnonymizationProgressCallback = Callable[[AnonymizationProgress], None]
UnitProgressCallback = Callable[[str, int, int], None]


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

    @property
    def generated_files_count(self) -> int:
        """Return the number of anonymized artifacts written successfully."""
        return sum(
            len(result.output_paths)
            for result in self.results
            if result.succeeded
        )
