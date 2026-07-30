"""Structural regression tests for private scanned-UPD implementation modules."""

from __future__ import annotations

import ast
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_DOCUMENT_TYPE_ROOT = (
    _PROJECT_ROOT
    / "source_docs_processor"
    / "features"
    / "document_processing"
    / "document_types"
    / "upd_invoices_status_1"
)
_INTERNAL_ROOT = _DOCUMENT_TYPE_ROOT / "_internal"


def test_extractor_defines_only_document_orchestration() -> None:
    """Verify detailed parsing rules stay outside the extractor orchestrator.

    Protected risk: adding number, date, shipment, continuation, or party parsing
    back to extractor.py would recreate the large multi-responsibility module and
    force unrelated changes to share one AI context.
    """
    extractor_path = _INTERNAL_ROOT / "extractor.py"
    tree = ast.parse(
        extractor_path.read_text(encoding="utf-8"),
        filename=str(extractor_path),
    )
    function_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert function_names == {"extract_document"}


def test_focused_extraction_modules_are_private() -> None:
    """Verify focused UPD algorithms live in the private implementation package.

    Protected risk: returning extraction modules to the document-type root would
    hide the framework-facing processor, workflow, registry, and definition map.
    """
    expected_modules = {
        "classification.py",
        "confidence.py",
        "continuation.py",
        "date_extraction.py",
        "extractor.py",
        "financial_extraction.py",
        "identity_extraction.py",
        "image_processing.py",
        "number_extraction.py",
        "ocr.py",
        "party_extraction.py",
        "shipment_row.py",
        "transport_extraction.py",
    }

    internal_modules = {path.name for path in _INTERNAL_ROOT.glob("*.py")}
    root_modules = {path.name for path in _DOCUMENT_TYPE_ROOT.glob("*.py")}

    assert expected_modules <= internal_modules
    assert root_modules == {
        "__init__.py",
        "definition.py",
        "processor.py",
        "registry.py",
        "workflow.py",
    }
    assert "normalization.py" not in internal_modules


def test_private_helpers_are_imported_from_internal_modules() -> None:
    """Verify focused helpers resolve from their owning private modules.

    Protected risk: reintroducing top-level compatibility wrappers would clutter
    the framework-facing package root and weaken the private API boundary.
    """
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1._internal import (
        extractor,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1._internal.continuation import (
        is_probable_continuation_page,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1._internal.date_extraction import (
        normalize_date,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1._internal.number_extraction import (
        normalize_number,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1._internal.shipment_row import (
        extract_number_date_from_shipment_document,
    )

    assert extractor.normalize_number is normalize_number
    assert extractor.normalize_date is normalize_date
    assert (
        extractor._extract_number_date_from_shipment_document
        is extract_number_date_from_shipment_document
    )
    assert (
        extractor._is_probable_continuation_page
        is is_probable_continuation_page
    )
