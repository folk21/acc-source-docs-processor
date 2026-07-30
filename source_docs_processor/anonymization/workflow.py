"""Recursive folder workflow for local anonymization."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .config import AnonymizationConfig, EMPTY_ANONYMIZATION_CONFIG, mask_after_heading
from .docx import anonymize_docx_file
from .editable import (
    anonymize_image_to_docx,
    anonymize_pdf_to_docx,
    anonymize_text_to_docx,
)
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
    output_document_type: str | None,
    output_layout: str | None,
) -> int:
    """Dispatch one supported file to its format-specific anonymizer."""
    suffix = source.suffix.lower()
    if output_document_type == "docx":
        if suffix in SUPPORTED_IMAGE_EXTENSIONS:
            return anonymize_image_to_docx(
                source, destination, analyzer, lang, config, progress_callback,
                output_layout=output_layout,
            )
        if suffix == ".pdf":
            return anonymize_pdf_to_docx(
                source, destination, analyzer, lang, config, progress_callback,
                output_layout=output_layout,
            )
        if suffix == ".docx":
            return anonymize_docx_file(
                source, destination, analyzer, lang=lang, config=config
            )
        if suffix == ".txt":
            text, _encoding = _read_text(source)
            return anonymize_text_to_docx(text, destination, analyzer, config)
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
    output_document_type: str | None,
    output_layout: str | None,
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
            output_document_type=output_document_type,
            output_layout=output_layout,
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


def _unique_relative_path(candidate: Path, used_paths: set[Path]) -> Path:
    """Return a deterministic unused relative output path."""
    if candidate not in used_paths:
        return candidate
    counter = 2
    while True:
        numbered = candidate.with_name(
            f"{candidate.stem}_{counter}{candidate.suffix}"
        )
        if numbered not in used_paths:
            return numbered
        counter += 1


def _plan_docx_destinations(
    files: list[Path],
    source_root: Path,
    also_output_source_format: bool,
) -> dict[Path, Path]:
    """Plan collision-safe DOCX destinations for every supported source path."""
    candidate_counts: dict[Path, int] = {}
    for source_path in files:
        relative_path = source_path.relative_to(source_root)
        if also_output_source_format and relative_path.suffix.lower() == ".docx":
            continue
        candidate = relative_path.with_suffix(".docx")
        candidate_counts[candidate] = candidate_counts.get(candidate, 0) + 1

    used_paths = (
        {source_path.relative_to(source_root) for source_path in files}
        if also_output_source_format
        else set()
    )
    destinations: dict[Path, Path] = {}
    for source_path in files:
        relative_path = source_path.relative_to(source_root)
        if also_output_source_format and relative_path.suffix.lower() == ".docx":
            destinations[source_path] = relative_path
            continue

        candidate = relative_path.with_suffix(".docx")
        if candidate_counts.get(candidate, 0) > 1 or (
            candidate in used_paths and candidate != relative_path
        ):
            source_type = relative_path.suffix.lower().lstrip(".") or "file"
            candidate = candidate.with_name(
                f"{candidate.stem}__{source_type}.docx"
            )
        candidate = _unique_relative_path(candidate, used_paths)
        destinations[source_path] = candidate
        used_paths.add(candidate)
    return destinations


def anonymize_folder(
    source_dir: Path,
    output_dir: Path,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
    progress_callback: AnonymizationProgressCallback | None = None,
    output_document_type: str | None = None,
    output_layout: str | None = None,
    also_output_source_format: bool = False,
) -> AnonymizationSummary:
    """Anonymize supported files recursively and write requested output variants."""
    if output_document_type not in {None, "docx"}:
        raise ValueError(
            f"Unsupported output document type: {output_document_type}"
        )
    if output_layout not in {None, "preserve"}:
        raise ValueError(f"Unsupported output layout: {output_layout}")
    if output_layout is not None and output_document_type != "docx":
        raise ValueError(
            "--outputLayout requires --outputDocumentType docx"
        )
    if also_output_source_format and output_document_type is None:
        raise ValueError(
            "--alsoOutputSourceFormat requires --outputDocumentType"
        )

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
    output_is_inside_source = _is_relative_to(output_root, source_root)
    files = sorted(
        (
            path
            for path in source_root.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and not (
                output_is_inside_source
                and _is_relative_to(path.resolve(), output_root)
            )
        ),
        key=lambda path: path.relative_to(source_root).as_posix().lower(),
    )
    if not files:
        raise ValueError(
            "No source files were found to anonymize. "
            f"Resolved source directory: {source_root}. "
            f"Resolved output directory: {output_root}. "
            "Check relative paths and the current working directory."
        )
    file_count = len(files)
    docx_destinations = (
        _plan_docx_destinations(
            files,
            source_root,
            also_output_source_format=also_output_source_format,
        )
        if output_document_type == "docx"
        else {}
    )

    for file_index, source_path in enumerate(files, start=1):
        relative_path = source_path.relative_to(source_root)
        target_relative = docx_destinations.get(source_path, relative_path)
        target_destination = output_root / target_relative
        source_format_destination = output_root / relative_path

        jobs: list[tuple[Path, str | None, str | None, str | None]]
        if also_output_source_format and target_relative != relative_path:
            jobs = [
                (source_format_destination, None, None, "source"),
                (
                    target_destination,
                    output_document_type,
                    output_layout,
                    output_document_type,
                ),
            ]
            primary_destination = target_destination
            additional_destinations = [source_format_destination]
        else:
            jobs = [
                (
                    target_destination,
                    output_document_type,
                    output_layout,
                    None,
                )
            ]
            primary_destination = target_destination
            additional_destinations = []

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

        def unit_progress(
            variant_name: str | None,
            unit_name: str,
            unit_index: int,
            unit_count: int,
        ) -> None:
            display_name = (
                f"{variant_name} {unit_name}" if variant_name else unit_name
            )
            _emit_progress(
                progress_callback,
                AnonymizationProgress(
                    event="unit_started",
                    source_path=source_path,
                    file_index=file_index,
                    file_count=file_count,
                    unit_name=display_name,
                    unit_index=unit_index,
                    unit_count=unit_count,
                ),
            )

        def progress_for_variant(
            variant_name: str | None,
        ) -> UnitProgressCallback:
            """Bind unit progress to one output variant label."""

            def report(
                unit_name: str,
                unit_index: int,
                unit_count: int,
            ) -> None:
                unit_progress(
                    variant_name,
                    unit_name,
                    unit_index,
                    unit_count,
                )

            return report

        created_destinations: list[Path] = []
        detected_counts: list[int] = []
        try:
            if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file type: {source_path.suffix or '<no extension>'}"
                )
            for destination, document_type, layout, variant_name in jobs:
                detected_counts.append(
                    _atomic_anonymize(
                        source_path,
                        destination,
                        analyzer=analyzer,
                        lang=lang,
                        config=config,
                        progress_callback=progress_for_variant(variant_name),
                        output_document_type=document_type,
                        output_layout=layout,
                    )
                )
                created_destinations.append(destination)

            result.detected_entities = max(detected_counts, default=0)
            result.destination_path = primary_destination
            result.additional_destination_paths = additional_destinations
        except Exception as exc:
            for destination, _document_type, _layout, _variant_name in jobs:
                destination.unlink(missing_ok=True)
            for destination in created_destinations:
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
                output_count=len(result.output_paths),
                error=result.error,
            ),
        )
    return summary
