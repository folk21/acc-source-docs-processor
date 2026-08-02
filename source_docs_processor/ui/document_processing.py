"""UI-facing adapter helpers for the public document-processing API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from source_docs_processor.features.document_processing import (
    DocumentTypeMetadata,
    ExtractedDocument,
    ProcessingProgress,
    ProcessingSummary,
    get_document_type_metadata,
    process_folder,
)


ProgressCallback = Callable[[ProcessingProgress], None]


@dataclass(frozen=True)
class ProcessingRequest:
    """Validated UI values required for one document-processing run."""

    source_dir: Path
    output_dir: Path
    document_type: str
    lang: str = "rus+eng"
    target_dir_name: str | None = None
    dry_run: bool = False
    deep_ocr: bool = False
    auto_rotate: bool = True
    debug_crops: bool = False


@dataclass(frozen=True)
class ProcessingResultRow:
    """Privacy-conscious table row for one processed source file."""

    source_file: str
    recognized: bool
    output_file: str
    error: str
    warning_count: int


@dataclass(frozen=True)
class GeneratedArtifactRow:
    """One generated registry, report, or copied output path."""

    artifact_type: str
    path: str


def get_processing_metadata(document_type: str) -> DocumentTypeMetadata:
    """Return public document-type metadata for a configured UI operation."""
    return get_document_type_metadata(document_type)


def execute_processing(
    request: ProcessingRequest,
    *,
    progress_callback: ProgressCallback | None = None,
) -> ProcessingSummary:
    """Execute one local processing request through the public feature API."""
    return process_folder(
        source_dir=request.source_dir,
        output_dir=request.output_dir,
        lang=request.lang,
        target_dir_name=request.target_dir_name,
        dry_run=request.dry_run,
        deep_ocr=request.deep_ocr,
        auto_rotate=request.auto_rotate,
        debug_crops=request.debug_crops,
        document_type=request.document_type,
        progress_callback=progress_callback,
    )


def _relative_or_name(path: Path, root: Path | None) -> str:
    """Return a portable relative path when the declared root contains it."""
    if root is not None:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            pass
    return path.name


def _document_output_path(
    document: ExtractedDocument,
    output_root: Path | None,
) -> str:
    """Return a portable destination path for one processed document."""
    if document.destination_path is None:
        return ""
    return _relative_or_name(document.destination_path, output_root)


def build_processing_result_rows(
    summary: ProcessingSummary,
) -> tuple[ProcessingResultRow, ...]:
    """Convert one processing summary into relative-path result rows."""
    rows: list[ProcessingResultRow] = []
    for document in summary.all_documents:
        rows.append(
            ProcessingResultRow(
                source_file=_relative_or_name(document.source_path, summary.source_root),
                recognized=document.is_recognized,
                output_file=_document_output_path(document, summary.output_root),
                error=document.error or "",
                warning_count=len(document.warnings),
            )
        )
    return tuple(rows)


def build_generated_artifact_rows(
    summary: ProcessingSummary,
) -> tuple[GeneratedArtifactRow, ...]:
    """Return de-duplicated generated artifacts with stable UI categories."""
    registry_paths = set(summary.registry_paths)
    report_paths = set(summary.report_paths)
    rows: list[GeneratedArtifactRow] = []
    for path in summary.generated_files:
        if path in registry_paths:
            artifact_type = "registry"
        elif path in report_paths:
            artifact_type = "report"
        else:
            artifact_type = "document"
        rows.append(
            GeneratedArtifactRow(
                artifact_type=artifact_type,
                path=_relative_or_name(path, summary.output_root),
            )
        )
    return tuple(rows)
