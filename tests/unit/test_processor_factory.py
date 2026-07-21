import pytest

from source_docs_processor.processors import DEFAULT_DOCUMENT_TYPE, create_document_processor


def test_factory_returns_default_upd_processor():
    """Verify factory selection for the currently released document type.

    Fixed problem verified: after the generalization refactor, the CLI should get
    UPD-specific logic through the processor factory rather than importing it directly.
    """
    processor = create_document_processor(DEFAULT_DOCUMENT_TYPE)

    assert processor.document_type == "upd_invoices_status_1"


def test_factory_rejects_unknown_document_type():
    """Verify a clear failure for unsupported document-type CLI values.

    Fixed problem verified: the project is now extensible, so invalid processor
    names must fail explicitly instead of silently falling back to UPD logic.
    """
    with pytest.raises(ValueError):
        create_document_processor("unknown_document_type")
