"""Placeholder CLI command for future local document anonymization."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from ..document_types import SUPPORTED_DOCUMENT_TYPES


def _run_anonymize_command(_args: argparse.Namespace) -> int:
    """Report that anonymization is registered but not implemented yet."""
    print(
        "The anonymize command is not implemented yet; its interface is reserved for the next iteration.",
        file=sys.stderr,
    )
    return 2


def register_anonymize_command(subparsers: Any) -> None:
    """Register the future anonymization command with its initial interface."""
    parser = subparsers.add_parser(
        "anonymize",
        help="Create an anonymized document copy (not implemented yet).",
        description=(
            "Create an anonymized local copy of a document. The command-line "
            "interface is reserved, but anonymization is not implemented yet."
        ),
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source document or folder to anonymize.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination file or folder for anonymized output.",
    )
    parser.add_argument(
        "--document-type",
        choices=SUPPORTED_DOCUMENT_TYPES,
        default=None,
        help=(
            "Optional document type for future document-specific anonymization "
            "rules."
        ),
    )
    parser.set_defaults(command_handler=_run_anonymize_command)
