import pytest

from source_docs_processor.features.document_processing.document_types.catalog import (
    DEFAULT_DOCUMENT_TYPE,
    get_document_type_definition,
)
from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1.registry import (
    UpdInvoicesStatus1RegistryDefinition,
)
from source_docs_processor.features.document_processing.document_types.upd_invoices_status_1.workflow import (
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



def test_definition_creates_the_registered_processor():
    """Verify processor construction is owned by the complete definition.

    Protected risk: a separate compatibility factory would duplicate catalog
    behavior and expand the public feature surface without adding a real use case.
    """
    processor = get_document_type_definition(DEFAULT_DOCUMENT_TYPE).create_processor()

    assert processor.document_type == "upd_invoices_status_1"

def test_definition_registry_rejects_unknown_document_type():
    """Verify unsupported document types fail before any workflow starts."""
    with pytest.raises(ValueError):
        get_document_type_definition("unknown_document_type")


def test_replaced_electronic_upd_identifier_is_not_registered():
    """Verify the superseded new identifier does not remain as a hidden alias.

    Protected risk: workbook metadata and CLI selection must use one canonical
    identifier before task aggregation is introduced.
    """
    with pytest.raises(ValueError):
        get_document_type_definition("upd_invoices_status_1_files")


def test_electronic_upd_definition_builds_source_file_components():
    """Verify electronic UPD registration does not replace the scan definition.

    Protected risk: adding PDF and DOCX processing must preserve the existing
    default scan processor while exposing a separate selectable workflow.
    """
    from source_docs_processor.features.document_processing.document_types.incoming_purchase_documents.registry import (
        IncomingPurchaseDocumentsRegistryDefinition,
    )
    from source_docs_processor.features.document_processing.document_types.incoming_purchase_documents.workflow import (
        IncomingPurchaseDocumentsWorkflow,
    )

    definition = get_document_type_definition("incoming_purchase_documents")

    processor = definition.create_processor()
    workflow = definition.create_workflow()
    registry = definition.create_registry_definition()

    assert DEFAULT_DOCUMENT_TYPE == "upd_invoices_status_1"
    assert processor.document_type == "incoming_purchase_documents"
    assert processor.supported_extensions == frozenset({".pdf", ".docx"})
    assert isinstance(workflow, IncomingPurchaseDocumentsWorkflow)
    assert isinstance(registry, IncomingPurchaseDocumentsRegistryDefinition)
