"""Internal composition service for folder-based document processing."""

from __future__ import annotations

from pathlib import Path

from ..document_types.catalog import DEFAULT_DOCUMENT_TYPE, get_document_type_definition
from ..models import ExtractedDocument
from ..document_type_definition import DocumentTypeDefinition
from ..processor_base import Processor
from ..registry_base import RegistryDefinition
from ..workflow_base import ProcessingOptions, ProcessingWorkflow


def process_folder_with_components(
    source_dir: Path,
    output_dir: Path | None,
    lang: str,
    target_dir_name: str | None = None,
    dry_run: bool = False,
    deep_ocr: bool = False,
    auto_rotate: bool = True,
    debug_crops: bool = False,
    document_type: str = DEFAULT_DOCUMENT_TYPE,
    document_type_definition: DocumentTypeDefinition | None = None,
    document_processor: Processor | None = None,
    processing_workflow: ProcessingWorkflow | None = None,
    registry_definition: RegistryDefinition | None = None,
) -> tuple[list[ExtractedDocument], list[ExtractedDocument]]:
    """Run processing with optional component injection for internal tests."""
    definition = document_type_definition or get_document_type_definition(document_type)
    processor = document_processor or definition.create_processor()
    workflow = processing_workflow or definition.create_workflow()
    selected_registry = registry_definition or definition.create_registry_definition()

    result = workflow.process(
        processor=processor,
        registry_definition=selected_registry,
        options=ProcessingOptions(
            source_dir=source_dir,
            output_dir=output_dir,
            target_dir_name=target_dir_name,
            lang=lang,
            dry_run=dry_run,
            deep_ocr=deep_ocr,
            auto_rotate=auto_rotate,
            debug_crops=debug_crops,
        ),
    )
    return result.found_documents, result.all_documents
