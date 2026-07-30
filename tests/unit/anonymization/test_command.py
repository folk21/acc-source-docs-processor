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


def test_anonymize_parser_accepts_camel_case_output_options() -> None:
    """Verify anonymization output options use one consistent camelCase style.

    Protected risk: documentation and scripts must not alternate between two
    spellings for the same public CLI option.
    """
    from source_docs_processor.cli import build_parser

    args = build_parser().parse_args(
        [
            "anonymize",
            "--source",
            "/tmp/source",
            "--output",
            "/tmp/output",
            "--outputDocumentType",
            "docx",
            "--outputLayout",
            "preserve",
            "--alsoOutputSourceFormat",
        ]
    )

    assert args.output_document_type == "docx"
    assert args.output_layout == "preserve"
    assert args.also_output_source_format is True


def test_anonymize_parser_rejects_removed_kebab_case_output_options() -> None:
    """Verify obsolete mixed-style output option spellings are rejected.

    Protected risk: keeping undocumented aliases would prevent the CLI from
    converging on the requested single naming convention.
    """
    import pytest

    from source_docs_processor.cli import build_parser

    for option in (
        "--output-document-type",
        "--output-layout",
        "--also-output-source-format",
    ):
        arguments = [
            "anonymize",
            "--source",
            "/tmp/source",
            "--output",
            "/tmp/output",
            option,
        ]
        if option == "--output-document-type":
            arguments.append("docx")
        with pytest.raises(SystemExit):
            build_parser().parse_args(arguments)


def test_replacement_only_command_skips_presidio_model_loading(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify replacement-only runs do not initialize Presidio or spaCy.

    Protected risk: pseudonym-only configurations must keep the same fast local
    startup behavior as ordinary included rules.
    """
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    config = tmp_path / "anonymization.ini"
    config.write_text(
        "[anonymization]\n"
        "included =\n"
        "includedAndReplaced = Васильев -> Иванов\n",
        encoding="utf-8",
    )
    captured = {}

    def fail_presidio_loading():
        raise AssertionError("Presidio must not load in configured-only mode")

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

    transformed = captured["analyzer"].analyze("Контакт: Васильев")
    assert result == 0
    assert len(transformed) == 1
    assert transformed[0].replacement == "Иванов"


def test_anonymize_parser_accepts_clear_output_option() -> None:
    """Verify safe in-place output cleanup uses the public camelCase option.

    Protected risk: users must not need an external rm -rf command that replaces
    the output directory inode while another terminal is opened inside it.
    """
    from source_docs_processor.cli import build_parser

    args = build_parser().parse_args(
        [
            "anonymize",
            "--source",
            "/tmp/source",
            "--output",
            "/tmp/output",
            "--clearOutput",
        ]
    )

    assert args.clear_output is True
