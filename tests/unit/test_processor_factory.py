import pytest

from source_docs_processor.document_types import (
    DEFAULT_DOCUMENT_TYPE,
    get_document_type_definition,
)
from source_docs_processor.processors import create_document_processor
from source_docs_processor.upd_invoices_status_1.registry import (
    UpdInvoicesStatus1RegistryDefinition,
)
from source_docs_processor.upd_invoices_status_1.workflow import (
    UpdInvoicesStatus1Workflow,
)


def test_document_type_definition_builds_independent_components():
    """Verify registration selects processor, workflow, and registry together.

    Protected risk: adding a new document type must not require conditional
    workflow or CSV logic in the CLI.
    """
    definition = get_document_type_definition(DEFAULT_DOCUMENT_TYPE)

    processor = definition.create_processor()
    workflow = definition.create_workflow()
    registry = definition.create_registry_definition()

    assert processor.document_type == "upd_invoices_status_1"
    assert isinstance(workflow, UpdInvoicesStatus1Workflow)
    assert isinstance(registry, UpdInvoicesStatus1RegistryDefinition)


def test_backward_compatible_processor_factory_uses_definition_registry():
    """Verify existing processor-only callers still use the new registry.

    Protected risk: internal refactoring should not unnecessarily break code that
    only needs the file-level UPD recognizer.
    """
    processor = create_document_processor(DEFAULT_DOCUMENT_TYPE)

    assert processor.document_type == "upd_invoices_status_1"


def test_definition_registry_rejects_unknown_document_type():
    """Verify unsupported document types fail before any workflow starts."""
    with pytest.raises(ValueError):
        get_document_type_definition("unknown_document_type")
