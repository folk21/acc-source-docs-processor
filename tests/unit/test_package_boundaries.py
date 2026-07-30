"""Regression tests for the feature-oriented package dependency rules."""

from __future__ import annotations

import ast
from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "source_docs_processor"
_DOCUMENT_TYPE_NAMES = (
    "incoming_purchase_documents",
    "npd_receipts",
    "upd_invoices_status_1",
)


def _imported_modules_from_file(path: Path) -> list[str]:
    """Return imported module names from one Python file."""
    imports: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = f"{'.' * node.level}{module}"
            imports.append(module)
    return imports


def _imported_modules(package_dir: Path) -> list[tuple[Path, str]]:
    """Return imported module names from Python files below one package."""
    return [
        (path, module)
        for path in sorted(package_dir.rglob("*.py"))
        for module in _imported_modules_from_file(path)
    ]


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
    boundary that the feature-oriented layout is intended to remove.
    """
    anonymization_violations = [
        (path, module)
        for path, module in _imported_modules(
            _PACKAGE_ROOT / "features" / "anonymization"
        )
        if "document_processing" in module
    ]
    processing_violations = [
        (path, module)
        for path, module in _imported_modules(
            _PACKAGE_ROOT / "features" / "document_processing"
        )
        if "anonymization" in module
    ]

    assert anonymization_violations == []
    assert processing_violations == []


def test_shared_processing_modules_do_not_import_concrete_document_types() -> None:
    """Verify reusable processing infrastructure stays implementation-neutral.

    Protected risk: a shared writer, workflow, model, or API helper must not gain
    knowledge of one concrete document package and become unsafe to reuse.
    """
    processing_root = _PACKAGE_ROOT / "features" / "document_processing"
    document_types_root = processing_root / "document_types"
    violations: list[tuple[Path, str]] = []
    for path in sorted(processing_root.rglob("*.py")):
        if path.is_relative_to(document_types_root):
            continue
        for module in _imported_modules_from_file(path):
            if any(name in module for name in _DOCUMENT_TYPE_NAMES):
                violations.append((path, module))

    assert violations == []


def test_concrete_document_types_do_not_import_each_other() -> None:
    """Verify each document implementation can be changed in isolation.

    Protected risk: cross-imports between concrete packages force unrelated OCR
    implementations and their tests to change together.
    """
    document_types_root = (
        _PACKAGE_ROOT / "features" / "document_processing" / "document_types"
    )
    violations: list[tuple[Path, str]] = []
    for package_name in _DOCUMENT_TYPE_NAMES:
        package_root = document_types_root / package_name
        other_names = set(_DOCUMENT_TYPE_NAMES) - {package_name}
        for path, module in _imported_modules(package_root):
            if any(name in module for name in other_names):
                violations.append((path, module))

    assert violations == []


def test_document_type_catalog_imports_only_complete_definitions() -> None:
    """Verify catalog composition does not know implementation class details.

    Protected risk: importing processor, workflow, or registry classes directly
    would make the catalog change whenever a package reorganizes its internals.
    """
    catalog = (
        _PACKAGE_ROOT
        / "features"
        / "document_processing"
        / "document_types"
        / "catalog.py"
    )
    concrete_imports = [
        module
        for module in _imported_modules_from_file(catalog)
        if any(name in module for name in _DOCUMENT_TYPE_NAMES)
    ]

    assert concrete_imports
    assert all(module.endswith(".definition") for module in concrete_imports)


def test_top_level_cli_imports_only_feature_entry_points() -> None:
    """Verify top-level CLI stays a small feature composition root.

    Protected risk: importing format handlers, workflows, or registries into the
    root CLI would spread feature internals across the application package.
    """
    cli_imports = {
        module
        for module in _imported_modules_from_file(_PACKAGE_ROOT / "cli.py")
        if module.startswith(".")
    }

    assert cli_imports == {
        ".features.anonymization.command",
        ".features.document_processing",
        ".features.document_processing.command",
    }


def test_each_document_type_publishes_definition_and_local_readme() -> None:
    """Verify every implementation exposes one composition contract and guide.

    Protected risk: a new package without a definition or local instructions
    would require the catalog or an AI agent to infer internal class wiring.
    """
    document_types_root = (
        _PACKAGE_ROOT / "features" / "document_processing" / "document_types"
    )

    for package_name in _DOCUMENT_TYPE_NAMES:
        package_root = document_types_root / package_name
        assert (package_root / "definition.py").is_file()
        assert (package_root / "README.md").is_file()
