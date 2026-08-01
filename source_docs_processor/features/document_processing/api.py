"""Public programmatic API for folder-based document processing."""

from __future__ import annotations

from pathlib import Path

from ._internal.service import process_folder_with_components
from .document_types.catalog import DEFAULT_DOCUMENT_TYPE
from .models import ProcessingProgressCallback, ProcessingSummary


def process_folder(
    source_dir: Path,
    output_dir: Path | None,
    lang: str,
    target_dir_name: str | None = None,
    dry_run: bool = False,
    deep_ocr: bool = False,
    auto_rotate: bool = True,
    debug_crops: bool = False,
    document_type: str = DEFAULT_DOCUMENT_TYPE,
    progress_callback: ProcessingProgressCallback | None = None,
) -> ProcessingSummary:
    """Process one folder using the registered document type definition."""
    return process_folder_with_components(
        source_dir=source_dir,
        output_dir=output_dir,
        lang=lang,
        target_dir_name=target_dir_name,
        dry_run=dry_run,
        deep_ocr=deep_ocr,
        auto_rotate=auto_rotate,
        debug_crops=debug_crops,
        document_type=document_type,
        progress_callback=progress_callback,
    )


__all__ = ["process_folder"]
