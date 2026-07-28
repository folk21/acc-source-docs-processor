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


def test_anonymize_subcommand_has_a_reserved_interface(capsys) -> None:
    """Verify anonymization is explicit while its implementation is pending.

    Protected risk: a placeholder command must not silently claim successful
    anonymization or route the document through the processing workflow.
    """
    exit_code = main(
        [
            "anonymize",
            "--source",
            "/tmp/source.pdf",
            "--output",
            "/tmp/output.pdf",
            "--document-type",
            "incoming_purchase_documents",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "not implemented yet" in captured.err


def test_cli_requires_an_explicit_subcommand() -> None:
    """Verify the obsolete flat CLI syntax is rejected.

    Protected risk: accepting arguments without a command would preserve two
    ambiguous invocation styles and complicate future command-specific options.
    """
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["--source", "/tmp/input"])

    assert exc_info.value.code == 2
