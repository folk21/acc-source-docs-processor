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
