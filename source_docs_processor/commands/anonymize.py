"""CLI command for recursive local document anonymization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ..anonymization import anonymize_folder, create_presidio_analyzer


def _run_anonymize_command(args: argparse.Namespace) -> int:
    """Anonymize one source directory and print a privacy-safe summary."""
    source_dir = Path(args.source).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    analyzer = create_presidio_analyzer()
    summary = anonymize_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        analyzer=analyzer,
    )

    for result in summary.results:
        relative_path = result.source_path.relative_to(summary.source_root)
        if result.succeeded:
            print(
                f"ANONYMIZED: {relative_path} "
                f"(detected entities: {result.detected_entities})"
            )
        else:
            print(
                f"FAILED: {relative_path}: {result.error}",
                file=sys.stderr,
            )

    print(
        "Anonymization finished: "
        f"successful={summary.succeeded_count}, "
        f"failed={summary.failed_count}, "
        f"detected_entities={summary.detected_entities}"
    )
    return 0 if summary.failed_count == 0 else 1


def register_anonymize_command(subparsers: Any) -> None:
    """Register recursive directory anonymization."""
    parser = subparsers.add_parser(
        "anonymize",
        help="Create anonymized local copies of supported document files.",
        description=(
            "Anonymize supported files recursively with Microsoft Presidio, "
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
    parser.set_defaults(command_handler=_run_anonymize_command)
