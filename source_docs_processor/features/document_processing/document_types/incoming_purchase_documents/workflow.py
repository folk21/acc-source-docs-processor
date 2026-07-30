"""Folder workflow for electronic UPD status 1 PDF and DOCX files."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path

from ...document_processor import Processor, SourceFileProcessor
from source_docs_processor.core.files import unique_path
from ...models import ExtractedDocument
from ...registry.base import RegistryDefinition
from ...registry.task_workbook import TaskWorkbookDefinition, write_task_workbook
from ...workflows.base import (
    ProcessingOptions,
    ProcessingResult,
    RunLogger,
    natural_sort_key,
    normalize_target_dir_name,
)


class IncomingPurchaseDocumentsWorkflow:
    """Reference PDF/DOCX sources and create a task-oriented workbook."""

    default_target_dir_name = "упд_для_ввода_в_1с"
    default_registry_name = "реестр_упд_для_ввода_в_1с.xlsx"

    def _is_relative_to(self, path: Path, parent: Path) -> bool:
        """Return True when path is located inside parent."""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

    def _iter_source_files(
        self,
        source_dir: Path,
        target_root: Path,
        extensions: frozenset[str],
    ) -> list[Path]:
        """Return supported files recursively while excluding generated output."""
        excluded_roots = (
            (target_root / "documents").resolve(),
            (target_root / "_debug").resolve(),
        )
        files = [
            path
            for path in source_dir.rglob("*")
            if path.is_file()
            and path.suffix.lower() in extensions
            and not any(
                self._is_relative_to(path.resolve(), excluded)
                for excluded in excluded_roots
            )
        ]
        return sorted(files, key=natural_sort_key)

    def _task_id(self, source_path: Path, source_root: Path) -> str:
        """Create a stable task UUID from relative path and file content."""
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        relative = source_path.relative_to(source_root).as_posix()
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{relative}:{digest}"))

    def _resolve_target_root(self, options: ProcessingOptions) -> tuple[Path, str]:
        """Resolve output without adding an unnecessary nested default folder."""
        target_name = normalize_target_dir_name(
            options.target_dir_name or self.default_target_dir_name
        )
        if options.output_dir is None:
            return Path.cwd() / target_name, target_name
        if options.target_dir_name:
            return options.output_dir / target_name, target_name
        return options.output_dir, target_name

    def process(
        self,
        processor: Processor,
        registry_definition: RegistryDefinition,
        options: ProcessingOptions,
    ) -> ProcessingResult:
        """Process electronic UPD files and create an XLSX task workbook."""
        source_dir = options.source_dir
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(
                "Source directory does not exist or is not a directory: "
                f"{source_dir}"
            )
        if not hasattr(processor, "analyze_source_file") or not hasattr(
            processor, "supported_extensions"
        ):
            raise TypeError("Selected processor does not support source files")
        if not all(
            hasattr(registry_definition, attribute)
            for attribute in (
                "document_columns",
                "item_columns",
                "review_columns",
                "build_document_row",
                "build_item_rows",
                "build_review_rows",
                "build_metadata",
            )
        ):
            raise TypeError("Selected registry is not a task workbook definition")

        file_processor: SourceFileProcessor = processor  # type: ignore[assignment]
        workbook_definition: TaskWorkbookDefinition = registry_definition  # type: ignore[assignment]
        target_root, target_name = self._resolve_target_root(options)
        registry_path = unique_path(target_root / self.default_registry_name)
        report_path = unique_path(target_root / f"{target_name}_report.txt")
        debug_root = target_root / "_debug" if options.debug_crops else None
        logger = RunLogger(report_path)
        found_documents: list[ExtractedDocument] = []
        all_documents: list[ExtractedDocument] = []
        files = self._iter_source_files(
            source_dir,
            target_root,
            file_processor.supported_extensions,
        )

        logger.log(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.log(f"Source directory: {source_dir}")
        logger.log(f"Target directory: {target_root}")
        logger.log(f"Registry file: {registry_path}")
        logger.log("Source PDF/DOCX files are referenced directly and are not copied.")
        logger.log(f"Found PDF/DOCX files: {len(files)}")
        logger.log(
            f"Document type: {processor.document_type} ({processor.display_name})"
        )

        for index, source_path in enumerate(files, start=1):
            logger.log(f"[{index}/{len(files)}] Processing: {source_path}")
            try:
                document = file_processor.analyze_source_file(
                    source_path=source_path,
                    lang=options.lang,
                    deep_ocr=options.deep_ocr,
                    debug_root=debug_root,
                )
                document.extra_fields["task_id"] = self._task_id(
                    source_path,
                    source_dir,
                )
                if file_processor.is_supported_document(document):
                    found_documents.append(document)
                    logger.log(
                        "  FOUND: "
                        f"number={document.document_number or '-'} "
                        f"date={document.document_date or '-'} "
                        f"issuer_inn={document.issuer_inn or '-'} "
                        f"items={len(document.items)} "
                        f"total={document.total_amount or '-'}"
                    )
                else:
                    logger.log("  review required: UPD status 1 was not confirmed")
                all_documents.append(document)
            except Exception as exc:
                document = ExtractedDocument(
                    source_path=source_path,
                    document_type=processor.document_type,
                    error=str(exc),
                    warnings=["Source file processing failed"],
                    extra_fields={
                        "task_id": self._task_id(source_path, source_dir),
                        "requires_review": True,
                    },
                )
                all_documents.append(document)
                logger.log(f"  ERROR: {exc}", error=True)

        if not options.dry_run:
            write_task_workbook(
                all_documents,
                registry_path,
                workbook_definition,
                source_root=source_dir,
            )
            logger.log(f"Registry written: {registry_path}")
        else:
            logger.log("Dry run mode: no workbook was written.")

        logger.log(f"Recognized UPD status 1 documents: {len(found_documents)}")
        logger.log(f"Total processed files: {len(all_documents)}")
        logger.log(f"Run finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return ProcessingResult(
            found_documents=found_documents,
            all_documents=all_documents,
            output_root=target_root,
            registry_path=None if options.dry_run else registry_path,
            report_path=report_path,
        )
