"""Top-level command-line interface for independent document features."""

from __future__ import annotations

import argparse
import sys

from .features.anonymization.command import register_anonymize_command
from .features.document_processing import process_folder
from .features.document_processing.command import register_process_command


def build_parser() -> argparse.ArgumentParser:
    """Create the application parser and register available feature commands."""
    parser = argparse.ArgumentParser(
        description="Process and anonymize accounting source documents locally.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
    )
    register_process_command(subparsers)
    register_anonymize_command(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and execute the selected feature command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.command_handler(args)
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1


__all__ = ["build_parser", "main", "process_folder"]


if __name__ == "__main__":
    raise SystemExit(main())
