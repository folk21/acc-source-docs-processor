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


def test_core_owns_feature_neutral_file_image_and_text_helpers() -> None:
    """Verify generic technical primitives stay outside document processing.

    Protected risk: placing filename, OpenCV, or whitespace primitives back into
    one feature would make their ownership misleading and encourage duplicated
    implementations in other independent operations.
    """
    core_root = _PACKAGE_ROOT / "core"
    processing_root = _PACKAGE_ROOT / "features" / "document_processing"

    assert {"files.py", "images.py", "paths.py", "text.py"} <= {
        path.name for path in core_root.glob("*.py")
    }
    assert not (processing_root / "image_processing.py").exists()


def test_shared_document_normalizers_are_private_and_type_neutral() -> None:
    """Verify strict normalizers stay internal without format-specific heuristics.

    Protected risk: common date or decimal parsing must not expand the public API
    or acquire UPD, receipt, or incoming-document behavior.
    """
    internal_root = (
        _PACKAGE_ROOT / "features" / "document_processing" / "_internal"
    )
    normalizers = {
        internal_root / "date_normalization.py",
        internal_root / "money_normalization.py",
    }
    violations = [
        (path, module)
        for path in normalizers
        for module in _imported_modules_from_file(path)
        if any(name in module for name in _DOCUMENT_TYPE_NAMES)
    ]

    assert all(path.is_file() for path in normalizers)
    assert not (
        _PACKAGE_ROOT / "features" / "document_processing" / "normalization"
    ).exists()
    assert violations == []


def test_document_type_roots_expose_only_framework_modules() -> None:
    """Verify each document type root remains a readable integration map.

    Protected risk: placing OCR, extraction, reader, or validation modules beside
    framework entry points would obscure the definition, processor, workflow, and
    registry boundary that callers and AI agents need to see first.
    """
    document_types_root = (
        _PACKAGE_ROOT / "features" / "document_processing" / "document_types"
    )
    expected_root_modules = {
        "__init__.py",
        "definition.py",
        "processor.py",
        "registry.py",
        "workflow.py",
    }

    for package_name in _DOCUMENT_TYPE_NAMES:
        package_root = document_types_root / package_name
        assert {path.name for path in package_root.glob("*.py")} == expected_root_modules
        assert (package_root / "_internal" / "__init__.py").is_file()


def test_document_type_internal_modules_do_not_import_framework_policy() -> None:
    """Verify private algorithms stay below processor and output policy layers.

    Protected risk: an extractor or OCR helper importing definition, workflow, or
    registry modules would reverse the intended dependency direction and make
    isolated implementation work depend on folder or output behavior.
    """
    document_types_root = (
        _PACKAGE_ROOT / "features" / "document_processing" / "document_types"
    )
    forbidden_modules = {"definition", "registry", "workflow"}
    violations: list[tuple[Path, str]] = []

    for package_name in _DOCUMENT_TYPE_NAMES:
        internal_root = document_types_root / package_name / "_internal"
        for path, module in _imported_modules(internal_root):
            if module.lstrip(".").split(".")[-1] in forbidden_modules:
                violations.append((path, module))

    assert violations == []


def test_private_unit_tests_mirror_internal_packages() -> None:
    """Verify implementation tests are grouped below each document type.

    Protected risk: leaving private parser and OCR tests beside framework tests
    would recreate the same mixed visual structure that `_internal/` removes from
    production packages.
    """
    tests_root = Path(__file__).resolve().parent
    expected_private_tests = {
        "incoming_purchase_documents": {"test_extractor.py", "test_readers.py"},
        "npd_receipts": {"test_extractor.py", "test_qr.py"},
        "upd_invoices_status_1": {
            "test_continuation.py",
            "test_date_selection.py",
            "test_module_boundaries.py",
            "test_number_selection.py",
            "test_shipment_row.py",
        },
    }

    for package_name, expected_files in expected_private_tests.items():
        package_root = tests_root / package_name
        internal_root = package_root / "_internal"
        assert expected_files <= {path.name for path in internal_root.glob("test_*.py")}
        assert expected_files.isdisjoint(
            {path.name for path in package_root.glob("test_*.py")}
        )

def test_feature_roots_expose_only_public_and_framework_modules() -> None:
    """Verify feature roots remain readable public integration maps.

    Protected risk: private handlers, registries, or contracts placed beside
    public and framework-facing modules would obscure the feature boundary.
    """
    features_root = _PACKAGE_ROOT / "features"
    expected_modules = {
        "anonymization": {"__init__.py", "api.py", "command.py"},
        "document_processing": {
            "__init__.py",
            "api.py",
            "command.py",
            "document_type_definition.py",
            "models.py",
            "processor_base.py",
            "registry_base.py",
            "workflow_base.py",
            "workflow_copy_and_register.py",
        },
    }

    for feature_name, expected in expected_modules.items():
        feature_root = features_root / feature_name
        assert {path.name for path in feature_root.glob("*.py")} == expected
        assert (feature_root / "_internal" / "__init__.py").is_file()


def test_document_processing_framework_and_private_infrastructure_are_separated() -> None:
    """Verify extension contracts stay visible and implementation details private.

    Protected risk: processor, registry, workflow, and registration contracts used
    by concrete document types must not be hidden beside serializers and services.
    """
    processing_root = _PACKAGE_ROOT / "features" / "document_processing"
    internal_root = processing_root / "_internal"

    assert {
        "document_type_definition.py",
        "processor_base.py",
        "registry_base.py",
        "workflow_base.py",
        "workflow_copy_and_register.py",
    } <= {path.name for path in processing_root.glob("*.py")}
    assert {
        "date_normalization.py",
        "file_ops.py",
        "money_normalization.py",
        "ocr.py",
        "service.py",
    } <= {path.name for path in internal_root.glob("*.py")}
    assert (internal_root / "registry" / "__init__.py").is_file()
    assert not (internal_root / "registry" / "base.py").exists()
    assert not (internal_root / "contracts.py").exists()
    assert not (internal_root / "processors.py").exists()
    assert not (internal_root / "workflows").exists()
    assert not (processing_root / "registry").exists()
    assert not (processing_root / "workflows").exists()

def test_feature_private_unit_tests_mirror_internal_packages() -> None:
    """Verify feature implementation tests are separated from API tests.

    Protected risk: mixing format and infrastructure tests beside command/API
    tests would hide ownership and force AI agents to inspect unrelated modules.
    """
    tests_root = Path(__file__).resolve().parent
    anonymization_root = tests_root / "anonymization"
    processing_root = tests_root / "document_processing"

    assert {path.name for path in anonymization_root.glob("test_*.py")} == {
        "test_api.py",
        "test_command.py",
    }
    assert {
        "test_config.py",
        "test_docx.py",
        "test_editable.py",
        "test_image.py",
        "test_pdf.py",
        "test_text.py",
    } <= {
        path.name
        for path in (anonymization_root / "_internal").glob("test_*.py")
    }
    assert {path.name for path in processing_root.glob("test_*.py")} == {
        "test_api.py",
        "test_document_types.py",
        "test_framework_api.py",
        "test_processor_base.py",
        "test_workflows.py",
    }
    assert {
        "test_normalization.py",
        "test_ocr.py",
    } <= {
        path.name
        for path in (processing_root / "_internal").glob("test_*.py")
    }



def test_features_and_document_types_publish_local_agent_guides() -> None:
    """Verify each independently owned scope has local AI instructions.

    Protected risk: without a nearby ownership and validation guide, an AI agent
    may inspect or modify unrelated features instead of working locally.
    """
    features_root = _PACKAGE_ROOT / "features"
    required_guides = {
        features_root / "anonymization" / "AGENTS.md",
        features_root / "document_processing" / "AGENTS.md",
    }
    document_types_root = features_root / "document_processing" / "document_types"
    required_guides.update(
        document_types_root / package_name / "AGENTS.md"
        for package_name in _DOCUMENT_TYPE_NAMES
    )

    assert all(path.is_file() for path in required_guides)
    assert all("make check" in path.read_text(encoding="utf-8") for path in required_guides)


def test_makefile_exposes_standard_focused_validation_targets() -> None:
    """Verify local scopes share one stable validation command vocabulary.

    Protected risk: ad hoc or undocumented test commands make local development
    inconsistent and encourage skipping the complete suite before delivery.
    """
    makefile = (_PACKAGE_ROOT.parent / "Makefile").read_text(encoding="utf-8")
    expected_targets = {
        "check",
        "test",
        "test-core",
        "test-public-api",
        "test-architecture",
        "test-anonymization",
        "test-document-processing",
        "test-upd",
        "test-npd",
        "test-incoming-purchase-documents",
    }

    for target in expected_targets:
        assert f"{target}:" in makefile
