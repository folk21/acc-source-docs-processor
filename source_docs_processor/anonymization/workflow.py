"""Recursive folder workflow for local anonymization."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .config import AnonymizationConfig, EMPTY_ANONYMIZATION_CONFIG, mask_after_heading
from .docx import anonymize_docx_file
from .image import SUPPORTED_IMAGE_EXTENSIONS, anonymize_image_file
from .models import (
    AnonymizationProgress,
    AnonymizationProgressCallback,
    AnonymizationSummary,
    AnonymizedFileResult,
    TextEntityAnalyzer,
    UnitProgressCallback,
)
from .pdf import anonymize_pdf_file
from .text import mask_text


SUPPORTED_EXTENSIONS = frozenset({".pdf", ".docx", ".txt"}) | SUPPORTED_IMAGE_EXTENSIONS


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return True when path is inside parent, including parent itself."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _read_text(source: Path) -> tuple[str, str]:
    """Read a text file using supported local encodings."""
    raw = source.read_bytes()
    encodings = (
        ("utf-8-sig",) if raw.startswith(b"\xef\xbb\xbf") else ("utf-8", "cp1251")
    )
    for encoding in encodings:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("Text file is neither UTF-8 nor Windows-1251")


def _anonymize_text_file(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    config: AnonymizationConfig,
) -> int:
    """Anonymize a plain text file while preserving its detected encoding."""
    text, encoding = _read_text(source)
    masked, entities = mask_text(text, analyzer)
    masked, heading_found = mask_after_heading(
        text,
        masked,
        config.included_paragraphs,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(masked.encode(encoding))
    return len(entities) + int(heading_found)


def _anonymize_one_file(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    lang: str,
    config: AnonymizationConfig,
    progress_callback: UnitProgressCallback | None,
) -> int:
    """Dispatch one supported file to its format-specific anonymizer."""
    suffix = source.suffix.lower()
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return anonymize_image_file(
            source,
            destination,
            analyzer,
            lang=lang,
            config=config,
            progress_callback=progress_callback,
        )
    if suffix == ".pdf":
        return anonymize_pdf_file(
            source,
            destination,
            analyzer,
            lang=lang,
            config=config,
            progress_callback=progress_callback,
        )
    if suffix == ".docx":
        return anonymize_docx_file(
            source,
            destination,
            analyzer,
            lang=lang,
            config=config,
        )
    if suffix == ".txt":
        return _anonymize_text_file(source, destination, analyzer, config)
    raise ValueError(f"Unsupported file type: {suffix or '<no extension>'}")


def _atomic_anonymize(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    lang: str,
    config: AnonymizationConfig,
    progress_callback: UnitProgressCallback | None,
) -> int:
    """Write one anonymized file atomically so failures leave no partial output."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        detected = _anonymize_one_file(
            source,
            temporary_path,
            analyzer=analyzer,
            lang=lang,
            config=config,
            progress_callback=progress_callback,
        )
        temporary_path.replace(destination)
        return detected
    finally:
        temporary_path.unlink(missing_ok=True)


def _emit_progress(
    callback: AnonymizationProgressCallback | None,
    progress: AnonymizationProgress,
) -> None:
    """Emit one progress event when a callback is configured."""
    if callback is not None:
        callback(progress)


def anonymize_folder(
    source_dir: Path,
    output_dir: Path,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
    progress_callback: AnonymizationProgressCallback | None = None,
) -> AnonymizationSummary:
    """Anonymize supported files recursively while preserving names and folders."""
    source_root = source_dir.expanduser().resolve()
    output_root = output_dir.expanduser().resolve()
    if not source_root.exists() or not source_root.is_dir():
        raise ValueError(
            f"Source directory does not exist or is not a directory: {source_root}"
        )
    if output_root.exists() and not output_root.is_dir():
        raise ValueError(f"Output path is not a directory: {output_root}")
    if source_root == output_root:
        raise ValueError("Source and output directories must be different")

    summary = AnonymizationSummary(
        source_root=source_root,
        output_root=output_root,
    )
    files = sorted(
        (
            path
            for path in source_root.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and not _is_relative_to(path.resolve(), output_root)
        ),
        key=lambda path: path.relative_to(source_root).as_posix().lower(),
    )
    file_count = len(files)

    for file_index, source_path in enumerate(files, start=1):
        relative_path = source_path.relative_to(source_root)
        destination = output_root / relative_path
        result = AnonymizedFileResult(source_path=source_path)
        _emit_progress(
            progress_callback,
            AnonymizationProgress(
                event="file_started",
                source_path=source_path,
                file_index=file_index,
                file_count=file_count,
            ),
        )

        def unit_progress(unit_name: str, unit_index: int, unit_count: int) -> None:
            _emit_progress(
                progress_callback,
                AnonymizationProgress(
                    event="unit_started",
                    source_path=source_path,
                    file_index=file_index,
                    file_count=file_count,
                    unit_name=unit_name,
                    unit_index=unit_index,
                    unit_count=unit_count,
                ),
            )

        try:
            if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type: {source_path.suffix or '<no extension>'}"
                )
            result.detected_entities = _atomic_anonymize(
                source_path,
                destination,
                analyzer=analyzer,
                lang=lang,
                config=config,
                progress_callback=unit_progress,
            )
            result.destination_path = destination
        except Exception as exc:
            destination.unlink(missing_ok=True)
            result.error = str(exc)
        summary.results.append(result)
        _emit_progress(
            progress_callback,
            AnonymizationProgress(
                event="file_finished",
                source_path=source_path,
                file_index=file_index,
                file_count=file_count,
                detected_entities=result.detected_entities,
                error=result.error,
            ),
        )
    return summary
