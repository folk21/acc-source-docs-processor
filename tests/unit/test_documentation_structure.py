"""Regression tests for the specification-driven documentation structure."""

from __future__ import annotations

import re
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DOCS_ROOT = _PROJECT_ROOT / "docs"
_FEATURE_ID_PATTERN = re.compile(r"`([A-Z][A-Z0-9_]+(?:\.[A-Z][A-Z0-9_]+)+)`")
_FRONTMATTER_VALUE = re.compile(r"^([a-z_]+):\s*(.+?)\s*$", re.MULTILINE)


def _frontmatter(path: Path) -> dict[str, str]:
    """Return the simple scalar YAML frontmatter used by managed Markdown files."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _separator, raw, _body = text.split("---", 2)
    return {
        key: value.strip().strip('"')
        for key, value in _FRONTMATTER_VALUE.findall(raw)
    }


def _declared_feature_ids() -> set[str]:
    """Return stable feature identifiers declared by the feature catalog."""
    return set(_FEATURE_ID_PATTERN.findall((_DOCS_ROOT / "FEATURES.md").read_text(encoding="utf-8")))


def test_managed_documentation_entry_points_exist() -> None:
    """Verify the repository keeps the documented navigation and ownership entry points.

    Protected risk: removing one owner document would force contributors to infer
    specification lifecycle, feature vocabulary, or validation policy from stale
    references spread across the repository.
    """
    required = {
        _DOCS_ROOT / "FEATURES.md",
        _DOCS_ROOT / "TESTS.md",
        _DOCS_ROOT / "QUALITY.md",
        _DOCS_ROOT / "specs" / "README.md",
    }

    assert all(path.is_file() for path in required)


def test_active_umbrella_points_to_one_existing_active_focus() -> None:
    """Verify the umbrella current focus resolves to an active specification.

    Protected risk: a stale current_focus path would make the specification index
    disagree with the active tree and send implementation work to an archived or
    missing contract.
    """
    umbrella = _DOCS_ROOT / "specs" / "active" / "spec-accounting-source-document-platform.md"
    metadata = _frontmatter(umbrella)
    focus_path = umbrella.parent / metadata["current_focus"]

    assert metadata["document_role"] == "umbrella"
    assert metadata["spec_status"] == "active"
    assert focus_path.is_file()
    assert _frontmatter(focus_path)["spec_status"] in {"active", "verification-pending"}


def test_archived_specs_are_completed_and_not_duplicated_in_active_tree() -> None:
    """Verify completed specs live only in the archive lifecycle location.

    Protected risk: duplicate active/archive copies would create two competing
    change contracts and make later edits ambiguous.
    """
    active_root = _DOCS_ROOT / "specs" / "active"
    archive_root = _DOCS_ROOT / "specs" / "archive" / "subspecs"
    active_names = {path.name for path in active_root.rglob("*.md")}
    archived = sorted(archive_root.glob("*.md"))

    assert archived
    assert active_names.isdisjoint({path.name for path in archived})
    assert all(_frontmatter(path)["spec_status"] == "completed" for path in archived)


def test_specification_feature_ids_are_declared_in_feature_catalog() -> None:
    """Verify specifications reference only stable catalogued feature IDs.

    Protected risk: ad-hoc feature codes in specs would fragment the project
    vocabulary and make cross-document references unstable.
    """
    declared = _declared_feature_ids()
    referenced: set[str] = set()
    for path in (_DOCS_ROOT / "specs").rglob("*.md"):
        referenced.update(_FEATURE_ID_PATTERN.findall(path.read_text(encoding="utf-8")))

    assert referenced <= declared
