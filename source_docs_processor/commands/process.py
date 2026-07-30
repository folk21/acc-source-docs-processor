"""Document processing CLI command and reusable folder-processing API."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..features.document_types.document_processor import Processor
from ..features.document_types import (
    DEFAULT_DOCUMENT_TYPE,
    SUPPORTED_DOCUMENT_TYPES,
    DocumentTypeDefinition,
    get_document_type_definition,
)
from ..features.document_types.models import ExtractedDocument
from ..features.document_types.registry.base import RegistryDefinition
from ..features.document_types.workflows.base import (
    ProcessingOptions,
    ProcessingWorkflow,
)


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
    actions. Normal CLI execution obtains all components from the document-type
    registry.
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


def _run_process_command(args: argparse.Namespace) -> int:
    """Run the selected document-processing workflow from parsed CLI arguments."""
    source_dir = Path(args.source).expanduser().resolve()
    output_dir = (
        Path(args.output).expanduser().resolve() if args.output else None
    )
    process_folder(
        source_dir=source_dir,
        output_dir=output_dir,
        lang=args.lang,
        target_dir_name=args.target_dir_name,
        dry_run=args.dry_run,
        deep_ocr=args.deep_ocr,
        auto_rotate=not args.no_auto_rotate,
        debug_crops=args.debug_crops,
        document_type=args.document_type,
    )
    return 0


def register_process_command(subparsers: Any) -> None:
    """Register the document processing subcommand and its runtime options."""
    parser = subparsers.add_parser(
        "process",
        help="Recognize documents and generate workflow outputs.",
        description=(
            "Process accounting source documents using a selected document "
            "type workflow."
        ),
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source folder with documents. Subfolders are processed recursively.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional base output folder. Its meaning is defined by the selected "
            "workflow."
        ),
    )
    parser.add_argument(
        "--target-dir-name",
        default=None,
        help=(
            "Optional target folder name for workflows that create an output "
            "directory."
        ),
    )
    parser.add_argument(
        "--document-type",
        default=DEFAULT_DOCUMENT_TYPE,
        choices=SUPPORTED_DOCUMENT_TYPES,
        help=f"Document type definition. Default: {DEFAULT_DOCUMENT_TYPE}",
    )
    parser.add_argument(
        "--lang",
        default="rus+eng",
        help="Tesseract language combination. Default: rus+eng",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze files without copying files or writing the registry.",
    )
    parser.add_argument(
        "--deep-ocr",
        action="store_true",
        help=(
            "Allow the selected processor to run slower full-page OCR for "
            "additional fields."
        ),
    )
    parser.add_argument(
        "--no-auto-rotate",
        action="store_true",
        help=(
            "Do not try 90/180/270-degree rotations in image processors. "
            "This option has no effect on native PDF/DOCX reading."
        ),
    )
    parser.add_argument(
        "--debug-crops",
        action="store_true",
        help="Save processor-specific local debug data when supported.",
    )
    parser.set_defaults(command_handler=_run_process_command)
