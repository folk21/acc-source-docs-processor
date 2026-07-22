"""Command-line interface and high-level folder processing workflow."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .document_processor import DocumentProcessor
from .file_ops import (
    copy_continuation_document,
    copy_recognized_document,
    copy_unrecognized_document,
    write_registry,
)
from .image_processing import iter_image_files, read_image
from .models import ExtractedDocument
from .processors import (
    DEFAULT_DOCUMENT_TYPE,
    SUPPORTED_DOCUMENT_TYPES,
    create_document_processor,
)


DEFAULT_REGISTRY_SUFFIX = ".csv"
DEFAULT_REPORT_SUFFIX = "_report.txt"


class RunLogger:
    """Write run messages both to the console and to a report file."""

    def __init__(self, report_path: Path | None = None) -> None:
        """Create the report file eagerly so later log writes can append safely."""
        self.report_path = report_path
        if self.report_path:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            self.report_path.write_text("", encoding="utf-8")

    def log(self, message: str = "", *, error: bool = False) -> None:
        """Print one message and append it to the report file when configured."""
        print(message, file=sys.stderr if error else sys.stdout)
        if self.report_path:
            with self.report_path.open("a", encoding="utf-8") as file:
                file.write(message + "\n")


def _natural_sort_key(path: Path) -> list[object]:
    """Sort paths so scan_2 appears before scan_10."""
    import re

    relative = str(path)
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", relative)
    ]


def _target_subdir(
    source_dir: Path,
    target_root: Path,
    image_path: Path,
) -> Path:
    """Mirror the input subfolder structure under the target root."""
    relative_parent = image_path.parent.relative_to(source_dir)
    if str(relative_parent) == ".":
        return target_root
    return target_root / relative_parent


def _normalize_target_dir_name(value: str) -> str:
    """Validate that target-dir-name is a folder name, not a path."""
    target_dir_name = value.strip().strip("/\\")
    if not target_dir_name:
        raise ValueError("Target directory name must not be empty")
    if Path(target_dir_name).name != target_dir_name:
        raise ValueError("Target directory name must be a folder name, not a path")
    return target_dir_name


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
    document_processor: DocumentProcessor | None = None,
) -> tuple[list[ExtractedDocument], list[ExtractedDocument]]:
    """Process one source folder and write copied documents, registry, and report."""
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(
            f"Source directory does not exist or is not a directory: {source_dir}"
        )

    processor = document_processor or create_document_processor(document_type)
    resolved_target_name = _normalize_target_dir_name(
        target_dir_name or processor.default_target_dir_name
    )

    target_root = (output_dir or Path.cwd()) / resolved_target_name
    registry_name = f"{resolved_target_name}{DEFAULT_REGISTRY_SUFFIX}"
    report_name = f"{resolved_target_name}{DEFAULT_REPORT_SUFFIX}"
    report_path = target_root / report_name
    debug_root = target_root / "_debug" if debug_crops else None
    logger = RunLogger(report_path)
    found_docs: list[ExtractedDocument] = []
    all_docs: list[ExtractedDocument] = []
    active_document: ExtractedDocument | None = None
    active_continuation_page = 1

    files = sorted(
        iter_image_files(source_dir, exclude_dirs=[target_root]),
        key=_natural_sort_key,
    )
    logger.log(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(f"Source directory: {source_dir}")
    logger.log(f"Target directory: {target_root}")
    logger.log(f"Registry file: {target_root / registry_name}")
    logger.log(f"Report file: {report_path}")
    logger.log(f"Found image files: {len(files)}")
    logger.log(f"Document type: {processor.document_type} ({processor.display_name})")
    logger.log(f"Auto-rotate: {'on' if auto_rotate else 'off'}")
    logger.log(f"Deep OCR: {'on' if deep_ocr else 'off'}")
    logger.log(f"Dry run: {'on' if dry_run else 'off'}")
    logger.log(f"Debug crops: {'on' if debug_crops else 'off'}")

    for index, image_path in enumerate(files, start=1):
        logger.log(f"[{index}/{len(files)}] Processing: {image_path}")
        target_subdir = _target_subdir(source_dir, target_root, image_path)
        try:
            image = read_image(image_path)

            # Always recognize a standalone document before attempting to attach
            # the scan to the previous document as a continuation page.
            doc, oriented_image = processor.analyze_image_orientations(
                image_path=image_path,
                image=image,
                lang=lang,
                deep_ocr=deep_ocr,
                auto_rotate=auto_rotate,
                debug_root=debug_root,
            )

            if (
                active_document is not None
                and processor.supports_continuation_pages
                and not processor.is_supported_document(doc)
            ):
                continuation_candidate = (
                    processor.analyze_continuation_orientations(
                        image_path=image_path,
                        image=image,
                        lang=lang,
                        auto_rotate=auto_rotate,
                    )
                )
                if continuation_candidate is not None:
                    continuation_doc, continuation_image = continuation_candidate
                    if processor.is_continuation_page(continuation_doc):
                        doc, oriented_image = continuation_doc, continuation_image

            if processor.is_supported_document(doc):
                if not dry_run:
                    copy_recognized_document(
                        doc,
                        target_subdir,
                        processor,
                        oriented_image=oriented_image,
                    )
                found_docs.append(doc)
                active_document = doc
                active_continuation_page = 1
                logger.log(
                    f"  FOUND: document={doc.document_number or '-'} "
                    f"date={doc.document_date or doc.document_datetime or '-'} "
                    f"status={doc.status or '-'} rotation={doc.rotation_degrees} "
                    f"confidence={doc.confidence}"
                )
                if doc.destination_path:
                    logger.log(f"  copied as: {doc.destination_path}")
            elif (
                processor.is_continuation_page(doc)
                and active_document is not None
            ):
                active_continuation_page += 1
                processor.prepare_continuation_document(
                    doc,
                    active_document,
                    active_continuation_page,
                )
                if not dry_run:
                    copy_continuation_document(
                        doc,
                        target_subdir,
                        processor,
                        oriented_image=oriented_image,
                    )
                logger.log(
                    f"  CONTINUATION: page={doc.continuation_page_number} "
                    f"for document={active_document.document_number or '-'} "
                    f"date={active_document.document_date or active_document.document_datetime or '-'} "
                    f"rotation={doc.rotation_degrees} confidence={doc.confidence}"
                )
                if doc.destination_path:
                    logger.log(f"  copied as: {doc.destination_path}")
            else:
                if not dry_run:
                    copy_unrecognized_document(doc, target_subdir)
                active_document = None
                active_continuation_page = 1
                logger.log(
                    f"  unrecognized: copied as is; status={doc.status or '-'} "
                    f"rotation={doc.rotation_degrees} confidence={doc.confidence}"
                )
                if doc.destination_path:
                    logger.log(f"  copied as: {doc.destination_path}")
            all_docs.append(doc)
        except Exception as exc:
            doc = ExtractedDocument(
                source_path=image_path,
                document_type=processor.document_type,
                error=str(exc),
            )
            if not dry_run:
                try:
                    copy_unrecognized_document(doc, target_subdir)
                except Exception as copy_exc:
                    doc.warnings.append(
                        f"Could not copy unrecognized file: {copy_exc}"
                    )
            all_docs.append(doc)
            active_document = None
            active_continuation_page = 1
            logger.log(f"  ERROR: {exc}", error=True)
            if doc.destination_path:
                logger.log(f"  copied as: {doc.destination_path}")

    if not dry_run:
        registry_path = target_root / registry_name
        write_registry(all_docs, registry_path, processor)
        logger.log(f"Registry written: {registry_path}")
    else:
        logger.log(
            "Dry run mode: no files were copied and no registry was written."
        )

    logger.log(f"Found supported documents: {len(found_docs)}")
    logger.log(f"Total processed documents: {len(all_docs)}")
    logger.log(f"Run finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return found_docs, all_docs


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Process scanned accounting documents using a selected local OCR processor."
        ),
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source folder with scans. Subfolders are processed recursively.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional base output folder. By default the target folder is created "
            "in the current working directory."
        ),
    )
    parser.add_argument(
        "--target-dir-name",
        default=None,
        help=(
            "Optional target folder name. When omitted, the selected processor "
            "provides its default folder name."
        ),
    )
    parser.add_argument(
        "--document-type",
        default=DEFAULT_DOCUMENT_TYPE,
        choices=SUPPORTED_DOCUMENT_TYPES,
        help=f"Document type processor. Default: {DEFAULT_DOCUMENT_TYPE}",
    )
    parser.add_argument(
        "--lang",
        default="rus+eng",
        help="Tesseract language combination. Default: rus+eng",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze files without copying or writing the registry.",
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
            "Do not try 90/180/270-degree rotations. Faster, but sideways "
            "documents may be skipped."
        ),
    )
    parser.add_argument(
        "--debug-crops",
        action="store_true",
        help=(
            "Save processor-specific OCR crops into the target _debug folder."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and run the processing workflow."""
    parser = build_parser()
    args = parser.parse_args(argv)
    source_dir = Path(args.source).expanduser().resolve()
    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else None
    )
    try:
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
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
