"""Structural regression tests for the decomposed scanned-UPD extractor."""

from __future__ import annotations

import ast
from pathlib import Path


_PACKAGE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "source_docs_processor"
    / "features"
    / "document_processing"
    / "document_types"
    / "upd_invoices_status_1"
)


def test_extractor_defines_only_document_orchestration() -> None:
    """Verify detailed parsing rules stay outside the extractor orchestrator.

    Protected risk: adding number, date, shipment, continuation, or party parsing
    back to extractor.py would recreate the large multi-responsibility module and
    force unrelated changes to share one AI context.
    """
    extractor_path = _PACKAGE_ROOT / "extractor.py"
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


def test_focused_extraction_modules_are_present() -> None:
    """Verify stable UPD extraction responsibilities have dedicated modules.

    Protected risk: deleting a focused module and merging its rules into another
    broad file would reduce local readability and isolated testability.
    """
    expected_modules = {
        "classification.py",
        "confidence.py",
        "continuation.py",
        "date_extraction.py",
        "financial_extraction.py",
        "identity_extraction.py",
        "normalization.py",
        "number_extraction.py",
        "party_extraction.py",
        "shipment_row.py",
        "transport_extraction.py",
    }

    assert expected_modules <= {
        path.name for path in _PACKAGE_ROOT.glob("*.py")
    }


def test_extractor_keeps_legacy_helper_reexports() -> None:
    """Verify old helper imports continue to resolve after decomposition.

    Protected risk: internal callers outside the current test suite may still
    import established helper names from extractor.py. The compatibility layer
    must forward those names without moving their implementations back there.
    """
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1 import (
        extractor,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1.continuation import (
        is_probable_continuation_page,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1.date_extraction import (
        normalize_date,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1.number_extraction import (
        normalize_number,
    )
    from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1.shipment_row import (
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
