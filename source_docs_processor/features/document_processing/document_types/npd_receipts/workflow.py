"""Copy, rename, and register NPD receipt images."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ...document_processor import DocumentProcessor
from source_docs_processor.core.files import safe_filename
from source_docs_processor.core.images import iter_image_files, read_image

from ...file_ops import copy_processed_document, copy_unrecognized_document
from ...models import ExtractedDocument
from ...registry.base import RegistryDefinition
from ...registry.xlsx_writer import write_xlsx_registry
from ...workflows.base import (
    ProcessingOptions,
    ProcessingResult,
    RunLogger,
    natural_sort_key,
    normalize_target_dir_name,
)


class NpdReceiptRegistryWorkflow:
    """Copy all images, rename recognized receipts, and write an XLSX registry."""

    default_target_dir_name = "чеки_нпд"
    default_registry_name = "npd_receipts_registry.xlsx"

    def build_output_filename_stem(self, document: ExtractedDocument) -> str:
        """Build ``date_amount_fullName_receiptNumber`` for a copied receipt."""
        date = safe_filename(document.document_date or "без_даты", fallback="document")
        amount = safe_filename(document.total_amount or "без_суммы", fallback="document")
        full_name = safe_filename(document.issuer_name or "без_фио", fallback="document").replace("_", "")
        number = safe_filename(document.document_number or "без_номера", fallback="document")
        return f"{date}_{amount}_{full_name}_{number}"

    def _target_subdir(
        self,
        source_dir: Path,
        target_root: Path,
        image_path: Path,
    ) -> Path:
        """Mirror source subfolders below the target directory."""
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
        """Process receipts and create copied files plus a linked Excel registry."""
        source_dir = options.source_dir
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(
                "Source directory does not exist or is not a directory: "
                f"{source_dir}"
            )

        target_name = normalize_target_dir_name(
            options.target_dir_name or self.default_target_dir_name
        )
        if options.output_dir is None:
            target_root = Path.cwd() / target_name
        elif options.target_dir_name:
            target_root = options.output_dir / target_name
        else:
            target_root = options.output_dir
        registry_path = target_root / self.default_registry_name
        debug_root = target_root / "_debug" if options.debug_crops else None
        logger = RunLogger()
        found_documents: list[ExtractedDocument] = []
        all_documents: list[ExtractedDocument] = []
        files = sorted(
            iter_image_files(source_dir, exclude_dirs=[target_root]),
            key=natural_sort_key,
        )

        logger.log(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log(f"Source directory: {source_dir}")
        logger.log(f"Target directory: {target_root}")
        logger.log(f"Registry file: {registry_path}")
        logger.log(f"Found image files: {len(files)}")
        logger.log(f"Document type: {processor.document_type} ({processor.display_name})")

        for index, image_path in enumerate(files, start=1):
            logger.log(f"[{index}/{len(files)}] Processing: {image_path}")
            target_subdir = self._target_subdir(source_dir, target_root, image_path)
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

                if processor.is_supported_document(document):
                    if not options.dry_run:
                        copy_processed_document(
                            document,
                            target_subdir,
                            self.build_output_filename_stem(document),
                            oriented_image=oriented_image,
                        )
                    found_documents.append(document)
                    logger.log(
                        "  FOUND: "
                        f"number={document.document_number or '-'} "
                        f"date={document.document_date or '-'} "
                        f"issuer={document.issuer_name or '-'} "
                        f"issuer_inn={document.issuer_inn or '-'} "
                        f"amount={document.total_amount or '-'}"
                    )
                else:
                    if not options.dry_run:
                        copy_unrecognized_document(document, target_subdir)
                    logger.log("  unrecognized: copied without renaming")

                all_documents.append(document)
                if document.destination_path:
                    logger.log(f"  copied as: {document.destination_path}")
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
                logger.log(f"  ERROR: {exc}", error=True)

        if not options.dry_run:
            headers = getattr(registry_definition, "headers", None)
            write_xlsx_registry(
                found_documents,
                registry_path,
                registry_definition,
                source_root=source_dir,
                headers=headers,
            )
            logger.log(f"Registry written: {registry_path}")
        else:
            logger.log("Dry run mode: no files or registry were written.")

        logger.log(f"Recognized NPD receipts: {len(found_documents)}")
        logger.log(f"Total processed images: {len(all_documents)}")
        return ProcessingResult(
            found_documents=found_documents,
            all_documents=all_documents,
            output_root=target_root,
            registry_path=None if options.dry_run else registry_path,
            report_path=None,
        )
