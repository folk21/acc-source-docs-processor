"""UI-facing adapter helpers for the public anonymization API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from source_docs_processor.features.anonymization import (
    AnonymizationProgress,
    AnonymizationSummary,
    ConfiguredTextAnalyzer,
    TextEntityAnalyzer,
    anonymize_folder,
    create_presidio_analyzer,
    load_anonymization_config,
)


AnonymizationOutputMode = Literal["source", "docx", "docx_and_source"]
AnalyzerProvider = Callable[[], TextEntityAnalyzer]
ProgressCallback = Callable[[AnonymizationProgress], None]


@dataclass(frozen=True)
class AnonymizationRequest:
    """Validated UI values required for one anonymization run."""

    source_dir: Path
    output_dir: Path
    config_path: Path
    lang: str = "rus+eng"
    output_mode: AnonymizationOutputMode = "source"
    preserve_layout: bool = False
    clear_output: bool = False


@dataclass(frozen=True)
class AnonymizationResultRow:
    """Privacy-safe table row derived from one anonymized source file."""

    source_file: str
    succeeded: bool
    output_files: str
    detected_entities: int
    error: str


def resolve_output_options(
    output_mode: AnonymizationOutputMode,
    preserve_layout: bool,
) -> tuple[str | None, str | None, bool]:
    """Map one UI output mode to the public anonymization API options."""
    if output_mode == "source":
        return None, None, False
    if output_mode == "docx":
        return "docx", "preserve" if preserve_layout else None, False
    if output_mode == "docx_and_source":
        return "docx", "preserve" if preserve_layout else None, True
    raise ValueError(f"Unsupported anonymization output mode: {output_mode}")


def execute_anonymization(
    request: AnonymizationRequest,
    *,
    analyzer_provider: AnalyzerProvider = create_presidio_analyzer,
    progress_callback: ProgressCallback | None = None,
) -> AnonymizationSummary:
    """Execute one local anonymization request through the public feature API."""
    config = load_anonymization_config(request.config_path)
    base_analyzer = analyzer_provider() if config.uses_automatic_detection else None
    analyzer = ConfiguredTextAnalyzer(base_analyzer, config)
    output_document_type, output_layout, also_output_source_format = (
        resolve_output_options(request.output_mode, request.preserve_layout)
    )
    return anonymize_folder(
        source_dir=request.source_dir,
        output_dir=request.output_dir,
        analyzer=analyzer,
        lang=request.lang,
        config=config,
        progress_callback=progress_callback,
        output_document_type=output_document_type,
        output_layout=output_layout,
        also_output_source_format=also_output_source_format,
        clear_output=request.clear_output,
    )


def build_result_rows(
    summary: AnonymizationSummary,
) -> tuple[AnonymizationResultRow, ...]:
    """Convert one summary into privacy-safe relative-path table rows."""
    rows: list[AnonymizationResultRow] = []
    for result in summary.results:
        source_file = result.source_path.relative_to(summary.source_root).as_posix()
        output_files = "\n".join(
            path.relative_to(summary.output_root).as_posix()
            for path in result.output_paths
        )
        rows.append(
            AnonymizationResultRow(
                source_file=source_file,
                succeeded=result.succeeded,
                output_files=output_files,
                detected_entities=result.detected_entities,
                error=result.error or "",
            )
        )
    return tuple(rows)
