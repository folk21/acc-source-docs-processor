"""Tests for the anonymization command analyzer selection."""

from __future__ import annotations

import argparse
from pathlib import Path

from source_docs_processor.anonymization.models import AnonymizationSummary
from source_docs_processor.commands import anonymize as anonymize_command


def test_included_only_command_skips_presidio_model_loading(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify literal-only runs do not initialize Presidio or spaCy.

    Protected risk: loading unused NLP models adds a long startup delay and can
    fail an otherwise valid included-only anonymization run.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    config = tmp_path / "anonymization.ini"
    config.write_text(
        "[anonymization]\n"
        "excluded = ignored\n"
        "included = Иван Петров\n"
        "includedParagraphs =\n",
        encoding="utf-8",
    )
    captured = {}

    def fail_presidio_loading():
        raise AssertionError("Presidio must not load in included-only mode")

    def fake_anonymize_folder(**kwargs):
        captured["analyzer"] = kwargs["analyzer"]
        return AnonymizationSummary(source_root=source, output_root=output)

    monkeypatch.setattr(
        anonymize_command,
        "create_presidio_analyzer",
        fail_presidio_loading,
    )
    monkeypatch.setattr(
        anonymize_command,
        "anonymize_folder",
        fake_anonymize_folder,
    )

    result = anonymize_command._run_anonymize_command(
        argparse.Namespace(
            source=str(source),
            output=str(output),
            config=str(config),
        )
    )

    entities = captured["analyzer"].analyze("Контакт: Иван Петров")
    assert result == 0
    assert len(entities) == 1


def test_anonymize_parser_accepts_both_output_document_type_spellings() -> None:
    """Verify the CLI supports the requested camelCase name and project-style alias.

    Protected risk: documented invocations must not fail because argparse only
    registered one spelling of the new option.
    """
    from source_docs_processor.cli import build_parser

    for option in ("--outputDocumentType", "--output-document-type"):
        args = build_parser().parse_args(
            [
                "anonymize",
                "--source",
                "/tmp/source",
                "--output",
                "/tmp/output",
                option,
                "docx",
            ]
        )
        assert args.output_document_type == "docx"


def test_anonymize_parser_accepts_both_output_layout_spellings() -> None:
    """Verify preserve layout supports camelCase and project-style CLI names.

    Protected risk: the requested invocation must not depend on one undocumented
    spelling of the layout option.
    """
    from source_docs_processor.cli import build_parser

    for option in ("--outputLayout", "--output-layout"):
        args = build_parser().parse_args(
            [
                "anonymize",
                "--source",
                "/tmp/source",
                "--output",
                "/tmp/output",
                "--outputDocumentType",
                "docx",
                option,
                "preserve",
            ]
        )
        assert args.output_layout == "preserve"


def test_anonymize_parser_accepts_both_source_format_output_spellings() -> None:
    """Verify dual output supports camelCase and project-style CLI names.

    Protected risk: users must be able to request both anonymized variants with
    the same naming conventions supported by the other anonymization options.
    """
    from source_docs_processor.cli import build_parser

    for option in (
        "--alsoOutputSourceFormat",
        "--also-output-source-format",
    ):
        args = build_parser().parse_args(
            [
                "anonymize",
                "--source",
                "/tmp/source",
                "--output",
                "/tmp/output",
                "--outputDocumentType",
                "docx",
                option,
            ]
        )
        assert args.also_output_source_format is True
