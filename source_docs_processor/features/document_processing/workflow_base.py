"""Shared workflow contracts, options, results, and logging helpers."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import (
    ExtractedDocument,
    ProcessingProgress,
    ProcessingProgressCallback,
    ProcessingProgressEvent,
)
from .processor_base import Processor
from .registry_base import RegistryDefinition


@dataclass(frozen=True)
class ProcessingOptions:
    """Runtime options passed from an adapter to a processing workflow."""

    source_dir: Path
    output_dir: Path | None
    target_dir_name: str | None
    lang: str
    dry_run: bool = False
    deep_ocr: bool = False
    auto_rotate: bool = True
    debug_crops: bool = False
    progress_callback: ProcessingProgressCallback | None = None

    def report_progress(
        self,
        event: ProcessingProgressEvent,
        *,
        file_index: int = 0,
        file_count: int = 0,
        source_path: Path | None = None,
        recognized: bool | None = None,
        error: str | None = None,
        output_path: Path | None = None,
    ) -> None:
        """Emit one synchronous progress event when a callback is configured."""
        if self.progress_callback is None:
            return
        self.progress_callback(
            ProcessingProgress(
                event=event,
                file_index=file_index,
                file_count=file_count,
                source_path=source_path,
                recognized=recognized,
                error=error,
                output_path=output_path,
            )
        )


@dataclass
class ProcessingResult:
    """Internal workflow outcome before public summary adaptation."""

    found_documents: list[ExtractedDocument]
    all_documents: list[ExtractedDocument]
    output_root: Path | None = None
    registry_path: Path | None = None
    report_path: Path | None = None


class ProcessingWorkflow(Protocol):
    """Process a folder using one processor and one registry definition."""

    def process(
        self,
        processor: Processor,
        registry_definition: RegistryDefinition,
        options: ProcessingOptions,
    ) -> ProcessingResult:
        """Run the selected folder-level business workflow."""
        ...


class RunLogger:
    """Write run messages to the console and optionally to a text report."""

    def __init__(self, report_path: Path | None = None) -> None:
        """Create the report file eagerly when a path is configured."""
        self.report_path = report_path
        if self.report_path:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            self.report_path.write_text("", encoding="utf-8")

    def log(self, message: str = "", *, error: bool = False) -> None:
        """Print one message and append it to the report file when configured."""
        print(message, file=sys.stderr if error else sys.stdout)
        if self.report_path:
            with self.report_path.open("a", encoding="utf-8") as file:
                file.write(message + "\n")


def natural_sort_key(path: Path) -> list[object]:
    """Sort paths so scan_2 appears before scan_10."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", str(path))
    ]


def normalize_target_dir_name(value: str) -> str:
    """Validate that a target directory value is a name rather than a path."""
    target_dir_name = value.strip().strip("/\\")
    if not target_dir_name:
        raise ValueError("Target directory name must not be empty")
    if Path(target_dir_name).name != target_dir_name:
        raise ValueError("Target directory name must be a folder name, not a path")
    return target_dir_name


__all__ = [
    "ProcessingOptions",
    "ProcessingResult",
    "ProcessingWorkflow",
    "RunLogger",
    "natural_sort_key",
    "normalize_target_dir_name",
]
