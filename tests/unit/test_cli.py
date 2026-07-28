"""Tests for top-level CLI command selection."""

from __future__ import annotations

import pytest

from source_docs_processor.cli import build_parser, main


def test_process_subcommand_preserves_document_processing_options() -> None:
    """Verify processing options belong to the process subcommand.

    Protected risk: introducing additional operations must not remove the
    established document-type and OCR options from normal processing.
    """
    args = build_parser().parse_args(
        [
            "process",
            "--source",
            "/tmp/input",
            "--document-type",
            "incoming_purchase_documents",
            "--deep-ocr",
        ]
    )

    assert args.command == "process"
    assert args.document_type == "incoming_purchase_documents"
    assert args.deep_ocr is True


def test_anonymize_subcommand_accepts_directory_paths_only() -> None:
    """Verify anonymization is independent from processing document types.

    Protected risk: coupling anonymization to the process registry would force
    unrelated document-specific branches into the operation command.
    """
    args = build_parser().parse_args(
        [
            "anonymize",
            "--source",
            "/tmp/source",
            "--output",
            "/tmp/output",
        ]
    )

    assert args.command == "anonymize"
    assert args.source == "/tmp/source"
    assert args.output == "/tmp/output"
    assert not hasattr(args, "document_type")


def test_cli_requires_an_explicit_subcommand() -> None:
    """Verify the obsolete flat CLI syntax is rejected.

    Protected risk: accepting arguments without a command would preserve two
    ambiguous invocation styles and complicate future command-specific options.
    """
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["--source", "/tmp/input"])

    assert exc_info.value.code == 2
