"""Tests for feature-neutral file helpers."""

from pathlib import Path

import pytest

from source_docs_processor.core.files import safe_filename, unique_path


def test_safe_filename_uses_generic_and_domain_specific_fallbacks() -> None:
    """Verify empty sanitized values use the caller-selected fallback.

    Protected risk: moving naming into core must not hard-code the old document
    fallback or force unrelated features to inherit document-processing wording.
    """
    assert safe_filename('  ') == 'file'
    assert safe_filename('  ', fallback='document') == 'document'
    assert safe_filename('a/b : c') == 'a_b_c'


def test_safe_filename_rejects_an_unusable_fallback() -> None:
    """Verify a fallback cannot silently normalize to another hidden default.

    Protected risk: an invalid fallback would otherwise produce ambiguous output
    names and conceal a caller configuration error.
    """
    with pytest.raises(ValueError):
        safe_filename('', fallback='///')


def test_unique_path_adds_a_deterministic_suffix(tmp_path: Path) -> None:
    """Verify collision handling remains independent from workflow policy.

    Protected risk: repeated runs must not overwrite an existing artifact when a
    feature asks for a unique local output path.
    """
    original = tmp_path / 'registry.xlsx'
    original.touch()
    (tmp_path / 'registry_2.xlsx').touch()

    assert unique_path(original) == tmp_path / 'registry_3.xlsx'
