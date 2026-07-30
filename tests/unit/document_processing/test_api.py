"""Tests for the public document-processing API boundary."""

from inspect import signature

from source_docs_processor.features.document_processing import process_folder


def test_public_process_folder_hides_component_injection() -> None:
    """Verify callers select registered behavior without internal DI contracts.

    Protected risk: exposing processors, workflows, or registry definitions in
    the public signature would make internal architecture a compatibility burden.
    """
    parameters = signature(process_folder).parameters

    assert "document_type" in parameters
    assert "document_type_definition" not in parameters
    assert "document_processor" not in parameters
    assert "processing_workflow" not in parameters
    assert "registry_definition" not in parameters
