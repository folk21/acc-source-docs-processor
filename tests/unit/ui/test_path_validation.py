"""Tests for local UI path validation."""

from __future__ import annotations

from pathlib import Path

from source_docs_processor.ui.path_validation import validate_anonymization_paths


def _codes(issues) -> set[str]:
    """Return issue codes without depending on localized display text."""
    return {issue.code for issue in issues}


def test_valid_paths_allow_a_new_output_directory(tmp_path: Path) -> None:
    """Verify the UI accepts an output directory that will be created later.

    Protected risk: requiring the output directory to pre-exist would make the
    UI stricter than the public anonymization workflow.
    """
    source = tmp_path / "source"
    source.mkdir()
    config = tmp_path / "anonymization.ini"
    config.write_text("[anonymization]\n", encoding="utf-8")

    issues = validate_anonymization_paths(
        source,
        tmp_path / "new-output",
        config,
        clear_output=False,
    )

    assert issues == ()


def test_missing_source_and_config_are_reported_by_stable_codes(tmp_path: Path) -> None:
    """Verify invalid paths can be rendered through any language configuration.

    Protected risk: validation logic must not embed Russian or English messages
    that would bypass the selected UI locale.
    """
    issues = validate_anonymization_paths(
        tmp_path / "missing-source",
        tmp_path / "output",
        tmp_path / "missing-config.ini",
        clear_output=False,
    )

    assert _codes(issues) == {"source_missing", "config_missing"}


def test_clear_output_rejects_a_source_nested_inside_output(tmp_path: Path) -> None:
    """Verify UI validation protects source files before output cleanup.

    Protected risk: clearing an ancestor output directory could delete the source
    tree before the anonymization feature gets a chance to reject the request.
    """
    output = tmp_path / "output"
    source = output / "source"
    source.mkdir(parents=True)
    config = tmp_path / "anonymization.ini"
    config.write_text("[anonymization]\n", encoding="utf-8")

    issues = validate_anonymization_paths(
        source,
        output,
        config,
        clear_output=True,
    )

    assert "unsafe_clear_output" in _codes(issues)
