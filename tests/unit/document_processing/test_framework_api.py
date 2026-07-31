"""Regression tests for document-processing framework extension points."""

from dataclasses import fields
from inspect import signature

from source_docs_processor.features.document_processing import (
    document_type_definition,
    processor_base,
    registry_base,
    workflow_base,
    workflow_copy_and_register,
)


def _field_names(model: type[object]) -> tuple[str, ...]:
    """Return dataclass field names in their public constructor order."""
    return tuple(field.name for field in fields(model))


def test_framework_modules_export_exact_extension_points() -> None:
    """Verify concrete document types see one explicit framework surface.

    Protected risk: leaking writers or services into framework modules would
    encourage document types to depend on implementation details.
    """
    expected_exports = {
        document_type_definition: ("DocumentTypeDefinition",),
        processor_base: (
            "BaseDocumentProcessor",
            "BaseSourceFileProcessor",
            "DocumentProcessor",
            "Processor",
            "SourceFileProcessor",
        ),
        registry_base: ("RegistryDefinition",),
        workflow_base: (
            "ProcessingOptions",
            "ProcessingResult",
            "ProcessingWorkflow",
            "RunLogger",
            "natural_sort_key",
            "normalize_target_dir_name",
        ),
        workflow_copy_and_register: ("CopyAndRegisterWorkflow",),
    }

    for module, names in expected_exports.items():
        assert tuple(module.__all__) == names
        for name in names:
            assert getattr(module, name).__module__ == module.__name__


def test_framework_dataclass_schemas_are_stable() -> None:
    """Verify registration and workflow composition models keep stable fields.

    Protected risk: concrete document definitions and workflows instantiate these
    dataclasses directly, so field drift would affect every registered type.
    """
    assert _field_names(document_type_definition.DocumentTypeDefinition) == (
        "document_type",
        "processor_factory",
        "workflow_factory",
        "registry_definition_factory",
    )
    assert _field_names(workflow_base.ProcessingOptions) == (
        "source_dir",
        "output_dir",
        "target_dir_name",
        "lang",
        "dry_run",
        "deep_ocr",
        "auto_rotate",
        "debug_crops",
    )
    assert _field_names(workflow_base.ProcessingResult) == (
        "found_documents",
        "all_documents",
        "output_root",
        "registry_path",
        "report_path",
    )


def test_processor_protocol_signatures_are_stable() -> None:
    """Verify image and source-file processors retain their extension contracts.

    Protected risk: changing a protocol method without an explicit framework
    migration would break every concrete processor implementation.
    """
    assert tuple(
        signature(processor_base.DocumentProcessor.analyze_image_orientations).parameters
    ) == (
        "self",
        "image_path",
        "image",
        "lang",
        "deep_ocr",
        "auto_rotate",
        "debug_root",
    )
    assert tuple(
        signature(
            processor_base.DocumentProcessor.analyze_continuation_orientations
        ).parameters
    ) == ("self", "image_path", "image", "lang", "auto_rotate")
    assert tuple(
        signature(processor_base.SourceFileProcessor.analyze_source_file).parameters
    ) == ("self", "source_path", "lang", "deep_ocr", "debug_root")
    assert tuple(
        signature(processor_base.DocumentProcessor.is_supported_document).parameters
    ) == ("self", "doc")
    assert tuple(
        signature(processor_base.DocumentProcessor.is_continuation_page).parameters
    ) == ("self", "doc")


def test_registry_and_workflow_protocol_signatures_are_stable() -> None:
    """Verify registry and folder-workflow contracts remain implementation-neutral.

    Protected risk: concrete registry and workflow modules must not need private
    writer or service knowledge to satisfy the shared framework.
    """
    assert tuple(signature(registry_base.RegistryDefinition.build_row).parameters) == (
        "self",
        "document",
        "source_root",
    )
    assert tuple(signature(workflow_base.ProcessingWorkflow.process).parameters) == (
        "self",
        "processor",
        "registry_definition",
        "options",
    )


def test_copy_and_register_workflow_hooks_are_stable() -> None:
    """Verify concrete copy workflows retain their supported override points.

    Protected risk: renaming or reshaping hooks would break document-specific
    filename and continuation policies even when the pipeline still imports.
    """
    workflow = workflow_copy_and_register.CopyAndRegisterWorkflow

    assert tuple(signature(workflow.build_primary_filename_stem).parameters) == (
        "self",
        "document",
    )
    assert tuple(signature(workflow.build_output_filename_stem).parameters) == (
        "self",
        "document",
    )
    assert tuple(signature(workflow.prepare_continuation_document).parameters) == (
        "self",
        "document",
        "previous_document",
        "page_number",
    )
    assert tuple(signature(workflow.process).parameters) == (
        "self",
        "processor",
        "registry_definition",
        "options",
    )
