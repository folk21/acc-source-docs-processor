"""CLI command for recursive local document anonymization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ..anonymization import (
    AnonymizationProgress,
    ConfiguredTextAnalyzer,
    DEFAULT_CONFIG_PATH,
    anonymize_folder,
    create_presidio_analyzer,
    load_anonymization_config,
)


def _print_progress(progress: AnonymizationProgress, source_root: Path) -> None:
    """Print one immediate privacy-safe progress line."""
    relative_path = progress.source_path.relative_to(source_root)
    prefix = f"[{progress.file_index}/{progress.file_count}]"
    if progress.event == "file_started":
        print(f"{prefix} START: {relative_path}", flush=True)
        return
    if progress.event == "unit_started":
        unit_name = (progress.unit_name or "unit").upper()
        print(
            f"{prefix} {unit_name} {progress.unit_index}/{progress.unit_count}: "
            f"{relative_path}",
            flush=True,
        )
        return
    if progress.error is None:
        print(
            f"{prefix} DONE: {relative_path} "
            f"(outputs: {progress.output_count}, "
            f"detected entities: {progress.detected_entities})",
            flush=True,
        )
    else:
        print(
            f"{prefix} FAILED: {relative_path}: {progress.error}",
            file=sys.stderr,
            flush=True,
        )


def _run_anonymize_command(args: argparse.Namespace) -> int:
    """Anonymize one source directory and print a privacy-safe summary."""
    source_dir = Path(args.source).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()

    config = load_anonymization_config(config_path)
    print(
        "Anonymization config loaded: "
        f"{config_path} "
        f"(excluded={len(config.excluded)}, "
        f"included={len(config.included)}, "
        f"includedParagraphs={len(config.included_paragraphs)}, "
        f"includedFuzzy={config.included_fuzzy}, "
        f"includedFuzzyMaxErrors={config.included_fuzzy_max_errors})",
        flush=True,
    )
    if config.included_only:
        print(
            "Included-only mode enabled: default Presidio detections and "
            "excluded rules are ignored.",
            flush=True,
        )
        analyzer = ConfiguredTextAnalyzer(None, config)
    else:
        print("Loading local Presidio and spaCy models...", flush=True)
        analyzer = ConfiguredTextAnalyzer(create_presidio_analyzer(), config)
    output_document_type = getattr(args, "output_document_type", None)
    output_layout = getattr(args, "output_layout", None)
    also_output_source_format = getattr(
        args,
        "also_output_source_format",
        False,
    )
    if output_layout is not None and output_document_type != "docx":
        raise ValueError(
            "--outputLayout requires --outputDocumentType docx"
        )
    if also_output_source_format and output_document_type is None:
        raise ValueError(
            "--alsoOutputSourceFormat requires --outputDocumentType"
        )
    if also_output_source_format:
        print(
            "Dual output enabled: an anonymized source-format file and the "
            f"requested {output_document_type.upper()} file will be generated.",
            flush=True,
        )
    if output_document_type == "docx":
        if output_layout == "preserve":
            print(
                "Editable DOCX layout preservation enabled: page geometry, OCR "
                "lines, spacing, and approximate font sizes will be reconstructed.",
                flush=True,
            )
        else:
            print(
                "Editable DOCX output enabled: OCR text will be reconstructed and "
                "the original page layout may not be preserved.",
                flush=True,
            )
    print("Scanning source directory...", flush=True)
    summary = anonymize_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        analyzer=analyzer,
        config=config,
        progress_callback=lambda progress: _print_progress(progress, source_dir),
        output_document_type=output_document_type,
        output_layout=output_layout,
        also_output_source_format=also_output_source_format,
    )

    print(
        "Anonymization finished: "
        f"successful={summary.succeeded_count}, "
        f"failed={summary.failed_count}, "
        f"generated_files={summary.generated_files_count}, "
        f"detected_entities={summary.detected_entities}",
        flush=True,
    )
    return 0 if summary.failed_count == 0 else 1


def register_anonymize_command(subparsers: Any) -> None:
    """Register recursive directory anonymization."""
    parser = subparsers.add_parser(
        "anonymize",
        help="Create anonymized local copies of supported document files.",
        description=(
            "Anonymize supported files recursively with configured local rules, "
            "preserving relative folders and source file names."
        ),
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source directory. Subfolders are processed recursively.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for anonymized files.",
    )
    parser.add_argument(
        "--output-document-type",
        "--outputDocumentType",
        dest="output_document_type",
        choices=("docx",),
        default=None,
        help=(
            "Optional output format. Use docx to reconstruct editable anonymized "
            "text from PDF scans, images, TXT, or DOCX. When omitted, each file "
            "keeps its source format."
        ),
    )
    parser.add_argument(
        "--output-layout",
        "--outputLayout",
        dest="output_layout",
        choices=("preserve",),
        default=None,
        help=(
            "Optional DOCX reconstruction mode. Use preserve with "
            "--outputDocumentType docx to approximate source page size, "
            "orientation, OCR line positions, spacing, and font sizes."
        ),
    )
    parser.add_argument(
        "--also-output-source-format",
        "--alsoOutputSourceFormat",
        dest="also_output_source_format",
        action="store_true",
        help=(
            "Also write an anonymized copy in each file's source format when "
            "--outputDocumentType requests a different format. No duplicate is "
            "created when the source already has the requested format."
        ),
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=(
            "INI configuration file with included-only, excluded, and "
            "includedParagraphs rules plus optional OCR fuzzy matching. "
            "Default: config/anonymization.ini"
        ),
    )
    parser.set_defaults(command_handler=_run_anonymize_command)
