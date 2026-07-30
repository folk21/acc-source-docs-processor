"""Regression tests for the feature-oriented package dependency rules."""

from __future__ import annotations

import ast
from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "source_docs_processor"


def _imported_modules(package_dir: Path) -> list[tuple[Path, str]]:
    """Return imported module names from Python files below one package."""
    imports: list[tuple[Path, str]] = []
    for path in sorted(package_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend((path, alias.name) for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    module = f"{'.' * node.level}{module}"
                imports.append((path, module))
    return imports


def test_core_does_not_import_features() -> None:
    """Verify shared core utilities remain independent from feature code.

    Protected risk: moving feature-specific behavior into core would reverse the
    intended dependency direction and make independent operations tightly coupled.
    """
    violations = [
        (path, module)
        for path, module in _imported_modules(_PACKAGE_ROOT / "core")
        if module.startswith("source_docs_processor.features")
        or module.lstrip(".").startswith("features")
    ]

    assert violations == []


def test_independent_features_do_not_import_each_other() -> None:
    """Verify anonymization and document processing remain independent features.

    Protected risk: direct cross-feature imports would recreate the mixed package
    boundary that the feature-oriented refactor is intended to remove.
    """
    anonymization_violations = [
        (path, module)
        for path, module in _imported_modules(
            _PACKAGE_ROOT / "features" / "anonymization"
        )
        if "document_types" in module
    ]
    document_type_violations = [
        (path, module)
        for path, module in _imported_modules(
            _PACKAGE_ROOT / "features" / "document_types"
        )
        if "anonymization" in module
    ]

    assert anonymization_violations == []
    assert document_type_violations == []
