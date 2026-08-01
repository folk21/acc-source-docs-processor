"""Reusable workflow for copy, rename, registry, and report scenarios."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .processor_base import DocumentProcessor
from ._internal.file_ops import copy_processed_document, copy_unrecognized_document
from source_docs_processor.core.images import iter_image_files, read_image
from .models import ExtractedDocument
from .registry_base import RegistryDefinition
from ._internal.registry.csv_writer import write_csv_registry
from .workflow_base import (
    ProcessingOptions,
    ProcessingResult,
    RunLogger,
    natural_sort_key,
    normalize_target_dir_name,
)


class CopyAndRegisterWorkflow:
    """Copy all images, rename recognized files, and write CSV plus report.

    Subclasses define the document-type-specific output directory, filename
    convention, and continuation-page policy. The OCR processor remains focused
    exclusively on recognizing and extracting one image.
    """

    default_target_dir_name = "processed_documents"
    supports_continuation_pages = False
    registry_suffix = ".csv"
    report_suffix = "_report.txt"

    def build_primary_filename_stem(self, document: ExtractedDocument) -> str:
        """Build a conservative generic filename for a primary document."""
        prefix = document.document_type or "document"
        number = document.document_number or "without_number"
        if document.document_date:
            return f"{prefix}_{number}_{document.document_date}"
        return f"{prefix}_{number}"

    def build_output_filename_stem(self, document: ExtractedDocument) -> str:
        """Build a filename stem for a primary or continuation page."""
        stem = self.build_primary_filename_stem(document)
        if document.is_continuation_page:
            page_number = document.continuation_page_number or 2
            return f"{stem}_page_{page_number}"
        return stem

    def prepare_continuation_document(
        self,
        document: ExtractedDocument,
        previous_document: ExtractedDocument,
        page_number: int,
    ) -> None:
        """Attach inherited metadata and numbering to a continuation page."""
        document.inherit_common_metadata(previous_document)
        document.is_continuation_page = True
        document.continuation_page_number = page_number
        document.continued_from = (
            previous_document.destination_path.name
            if previous_document.destination_path
            else previous_document.source_path.name
        )

    def _target_subdir(
        self,
        source_dir: Path,
        target_root: Path,
        image_path: Path,
    ) -> Path:
        """Mirror the input subfolder structure under the target root."""
        relative_parent = image_path.parent.relative_to(source_dir)
        if str(relative_parent) == ".":
            return target_root
        return target_root / relative_parent

    def process(
        self,
        processor: DocumentProcessor,
        registry_definition: RegistryDefinition,
        options: ProcessingOptions,
    ) -> ProcessingResult:
        """Run the copy-and-register workflow for one source directory."""
        source_dir = options.source_dir
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(
                "Source directory does not exist or is not a directory: "
                f"{source_dir}"
            )

        target_name = normalize_target_dir_name(
            options.target_dir_name or self.default_target_dir_name
        )
        target_root = (options.output_dir or Path.cwd()) / target_name
        registry_path = target_root / f"{target_name}{self.registry_suffix}"
        report_path = target_root / f"{target_name}{self.report_suffix}"
        debug_root = target_root / "_debug" if options.debug_crops else None
        logger = RunLogger(report_path)
        found_documents: list[ExtractedDocument] = []
        all_documents: list[ExtractedDocument] = []
        active_document: ExtractedDocument | None = None
        active_continuation_page = 1

        files = sorted(
            iter_image_files(source_dir, exclude_dirs=[target_root]),
            key=natural_sort_key,
        )
        logger.log(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log(f"Source directory: {source_dir}")
        logger.log(f"Target directory: {target_root}")
        logger.log(f"Registry file: {registry_path}")
        logger.log(f"Report file: {report_path}")
        logger.log(f"Found image files: {len(files)}")
        logger.log(
            f"Document type: {processor.document_type} ({processor.display_name})"
        )
        logger.log(f"Workflow: {type(self).__name__}")
        logger.log(f"Auto-rotate: {'on' if options.auto_rotate else 'off'}")
        logger.log(f"Deep OCR: {'on' if options.deep_ocr else 'off'}")
        logger.log(f"Dry run: {'on' if options.dry_run else 'off'}")
        logger.log(f"Debug crops: {'on' if options.debug_crops else 'off'}")
        options.report_progress("scan_started", file_count=len(files))

        for index, image_path in enumerate(files, start=1):
            options.report_progress(
                "file_started",
                file_index=index,
                file_count=len(files),
                source_path=image_path,
            )
            logger.log(f"[{index}/{len(files)}] Processing: {image_path}")
            target_subdir = self._target_subdir(
                source_dir,
                target_root,
                image_path,
            )
            try:
                image = read_image(image_path)
                document, oriented_image = processor.analyze_image_orientations(
                    image_path=image_path,
                    image=image,
                    lang=options.lang,
                    deep_ocr=options.deep_ocr,
                    auto_rotate=options.auto_rotate,
                    debug_root=debug_root,
                )

                if (
                    active_document is not None
                    and self.supports_continuation_pages
                    and not processor.is_supported_document(document)
                ):
                    continuation_candidate = (
                        processor.analyze_continuation_orientations(
                            image_path=image_path,
                            image=image,
                            lang=options.lang,
                            auto_rotate=options.auto_rotate,
                        )
                    )
                    if continuation_candidate is not None:
                        continuation_document, continuation_image = (
                            continuation_candidate
                        )
                        if processor.is_continuation_page(continuation_document):
                            document = continuation_document
                            oriented_image = continuation_image

                if processor.is_supported_document(document):
                    if not options.dry_run:
                        copy_processed_document(
                            document,
                            target_subdir,
                            self.build_output_filename_stem(document),
                            oriented_image=oriented_image,
                        )
                    found_documents.append(document)
                    active_document = document
                    active_continuation_page = 1
                    logger.log(
                        f"  FOUND: document={document.document_number or '-'} "
                        f"date={document.document_date or document.document_datetime or '-'} "
                        f"status={document.status or '-'} "
                        f"rotation={document.rotation_degrees} "
                        f"confidence={document.confidence}"
                    )
                    if document.destination_path:
                        logger.log(f"  copied as: {document.destination_path}")
                elif (
                    processor.is_continuation_page(document)
                    and active_document is not None
                ):
                    active_continuation_page += 1
                    self.prepare_continuation_document(
                        document,
                        active_document,
                        active_continuation_page,
                    )
                    if not options.dry_run:
                        copy_processed_document(
                            document,
                            target_subdir,
                            self.build_output_filename_stem(document),
                            oriented_image=oriented_image,
                        )
                    logger.log(
                        f"  CONTINUATION: page={document.continuation_page_number} "
                        f"for document={active_document.document_number or '-'} "
                        f"date={active_document.document_date or active_document.document_datetime or '-'} "
                        f"rotation={document.rotation_degrees} "
                        f"confidence={document.confidence}"
                    )
                    if document.destination_path:
                        logger.log(f"  copied as: {document.destination_path}")
                else:
                    if not options.dry_run:
                        copy_unrecognized_document(document, target_subdir)
                    active_document = None
                    active_continuation_page = 1
                    logger.log(
                        f"  unrecognized: copied as is; "
                        f"status={document.status or '-'} "
                        f"rotation={document.rotation_degrees} "
                        f"confidence={document.confidence}"
                    )
                    if document.destination_path:
                        logger.log(f"  copied as: {document.destination_path}")
                all_documents.append(document)
                options.report_progress(
                    "file_finished",
                    file_index=index,
                    file_count=len(files),
                    source_path=image_path,
                    recognized=document.is_recognized,
                    error=document.error,
                    output_path=document.destination_path,
                )
            except Exception as exc:
                document = ExtractedDocument(
                    source_path=image_path,
                    document_type=processor.document_type,
                    error=str(exc),
                )
                if not options.dry_run:
                    try:
                        copy_unrecognized_document(document, target_subdir)
                    except Exception as copy_exc:
                        document.warnings.append(
                            f"Could not copy unrecognized file: {copy_exc}"
                        )
                all_documents.append(document)
                active_document = None
                active_continuation_page = 1
                logger.log(f"  ERROR: {exc}", error=True)
                if document.destination_path:
                    logger.log(f"  copied as: {document.destination_path}")
                options.report_progress(
                    "file_finished",
                    file_index=index,
                    file_count=len(files),
                    source_path=image_path,
                    recognized=document.is_recognized,
                    error=document.error,
                    output_path=document.destination_path,
                )

        if not options.dry_run:
            write_csv_registry(
                all_documents,
                registry_path,
                registry_definition,
                source_root=source_dir,
            )
            logger.log(f"Registry written: {registry_path}")
            options.report_progress(
                "registry_written",
                file_count=len(files),
                output_path=registry_path,
            )
        else:
            logger.log(
                "Dry run mode: no files were copied and no registry was written."
            )

        logger.log(f"Found supported documents: {len(found_documents)}")
        logger.log(f"Total processed documents: {len(all_documents)}")
        logger.log(f"Run finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        options.report_progress("run_finished", file_count=len(files))
        return ProcessingResult(
            found_documents=found_documents,
            all_documents=all_documents,
            output_root=target_root,
            registry_path=None if options.dry_run else registry_path,
            report_path=report_path,
        )


__all__ = ["CopyAndRegisterWorkflow"]
