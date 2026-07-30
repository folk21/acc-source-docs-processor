"""Public programmatic API for folder-based document processing."""

from __future__ import annotations

from pathlib import Path

from .contracts import DocumentTypeDefinition
from .document_processor import Processor
from .document_types.catalog import (
    DEFAULT_DOCUMENT_TYPE,
    get_document_type_definition,
)
from .models import ExtractedDocument
from .registry.base import RegistryDefinition
from .workflows.base import ProcessingOptions, ProcessingWorkflow


def process_folder(
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
    """Process one folder using independently selected processing components.

    Optional component injection keeps integration tests deterministic and allows
    embedded callers to replace one layer without coupling recognition to file
    actions. Normal execution obtains all components from the document-type
    catalog.
    """
    definition = document_type_definition or get_document_type_definition(
        document_type
    )
    processor = document_processor or definition.create_processor()
    workflow = processing_workflow or definition.create_workflow()
    selected_registry = (
        registry_definition or definition.create_registry_definition()
    )

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


__all__ = ["process_folder"]
