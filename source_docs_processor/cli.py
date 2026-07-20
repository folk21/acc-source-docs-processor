"""Command-line interface and high-level folder processing workflow."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from .extractor import extract_document
from .file_ops import copy_continuation_document, copy_found_document, copy_unrecognized_document, safe_filename, write_registry
from .image_processing import ROTATION_ANGLES, iter_image_files, read_image, rotate_image
from .models import ExtractedDocument
from .ocr import OcrResult, read_continuation_text_by_crop, run_ocr


DEFAULT_TARGET_FOLDER = "передаточные_документы"
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
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", relative)]


def _score_document(doc: ExtractedDocument) -> int:
    """Score a recognition candidate so the best page orientation can be selected.

    The score is not meant to be a statistical OCR confidence value. It is a
    practical ranking heuristic that lets the pipeline choose between rotations:
    a real first page must outrank noisy text, while a continuation page can
    still win when no standalone document markers are found.
    """
    score = doc.confidence
    if doc.is_upd_invoice_transfer:
        score += 1000
    if doc.status == "1":
        score += 100
    if doc.invoice_number:
        score += 50
    if doc.invoice_date:
        score += 30
    if doc.is_continuation_page:
        score += 450 + doc.confidence
    return score



def _analyze_continuation_orientations(
    image_path: Path,
    image: np.ndarray,
    lang: str,
    auto_rotate: bool,
) -> tuple[ExtractedDocument, np.ndarray] | None:
    """Quickly check whether the image is a continuation page.

    When a recognized document was just processed, the next scan is often page 2.
    A continuation page does not need the full UPD header OCR path: signature and
    company-name marker areas are enough to attach it to the previous document.
    """
    if not auto_rotate:
        angles = (0,)
    elif image.shape[0] > image.shape[1]:
        # Continuation pages are often scanned sideways. Try the two most likely
        # landscape corrections before the less common 0/180-degree cases.
        angles = (90, 270, 0, 180)
    else:
        angles = ROTATION_ANGLES

    best_doc: ExtractedDocument | None = None
    best_image: np.ndarray | None = None
    for angle in angles:
        rotated = rotate_image(image, angle)

        # Continuation recognition deliberately reads only small marker regions.
        # A full-page OCR pass is unnecessary here because page 2 has no document
        # number/date header and is used only to inherit metadata from page 1.
        continuation_text = read_continuation_text_by_crop(rotated, lang=lang)
        ocr_result = OcrResult(
            text="",
            header_text="",
            status_digit=None,
            mean_confidence=0,
            rotation_degrees=angle,
            targeted_text=f"Continuation marker text:\n{continuation_text}",
            continuation_text=continuation_text,
        )
        doc = extract_document(image_path, ocr_result)
        doc.rotation_degrees = angle
        if best_doc is None or _score_document(doc) > _score_document(best_doc):
            best_doc = doc
            best_image = rotated
        # Do not fast-return continuation pages from the normal OCR path.
        # A continuation result is only accepted by the main loop after normal
        # standalone UPD recognition has failed for the same scan.

    if best_doc and best_doc.is_continuation_page and best_image is not None:
        return best_doc, best_image
    return None


def _analyze_image_orientations(
    image_path: Path,
    image: np.ndarray,
    lang: str,
    deep_ocr: bool,
    auto_rotate: bool,
    debug_root: Path | None = None,
) -> tuple[ExtractedDocument, np.ndarray]:
    """Run OCR for candidate rotations and return the strongest recognition result.

    This function is the first-page recognizer. It may detect a continuation-like
    signal, but the main workflow accepts that signal only after standalone UPD
    recognition has failed, preventing normal first pages from being attached to
    the previous document by mistake.
    """
    if not auto_rotate:
        angles = (0,)
    elif image.shape[0] > image.shape[1]:
        # Most UPD scans are landscape. If the image is portrait, try sideways corrections first.
        angles = (90, 270, 0, 180)
    else:
        angles = ROTATION_ANGLES
    best_doc: ExtractedDocument | None = None
    best_image: np.ndarray | None = None

    for angle in angles:
        rotated = rotate_image(image, angle)

        # Save debug crops per rotation. This makes it possible to compare why a
        # particular angle was selected or why a field was missed.
        debug_dir = None
        if debug_root:
            debug_dir = debug_root / safe_filename(image_path.stem) / f"rotation_{angle}"
        ocr_result = run_ocr(rotated, lang=lang, deep=deep_ocr, rotation_degrees=angle, debug_dir=debug_dir)
        doc = extract_document(image_path, ocr_result)
        doc.rotation_degrees = angle

        # Keep the oriented image together with its extracted metadata. If this
        # rotation wins, the copied output image will be saved in this orientation.
        if best_doc is None or _score_document(doc) > _score_document(best_doc):
            best_doc = doc
            best_image = rotated

        # Fast path: when status, number, and date are recognized, further rotations are very unlikely to improve the answer.
        if doc.is_upd_invoice_transfer and doc.invoice_number and doc.invoice_date:
            return doc, rotated
        # Do not fast-return continuation pages from the normal OCR path.
        # A continuation result is only accepted by the main loop after normal
        # standalone UPD recognition has failed for the same scan.

    assert best_doc is not None
    assert best_image is not None
    return best_doc, best_image


def _target_subdir(source_dir: Path, target_root: Path, image_path: Path) -> Path:
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
    target_dir_name: str = DEFAULT_TARGET_FOLDER,
    dry_run: bool = False,
    deep_ocr: bool = False,
    auto_rotate: bool = True,
    debug_crops: bool = False,
) -> tuple[list[ExtractedDocument], list[ExtractedDocument]]:
    """Process one source folder and write copied documents, registry, and report."""
    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"Source directory does not exist or is not a directory: {source_dir}")

    target_dir_name = _normalize_target_dir_name(target_dir_name)

    # By default the target directory is created in the current working
    # directory, not inside the scan archive. This avoids re-processing output
    # files when the source archive is scanned repeatedly.
    target_root = (output_dir or Path.cwd()) / target_dir_name
    registry_name = f"{target_dir_name}{DEFAULT_REGISTRY_SUFFIX}"
    report_name = f"{target_dir_name}{DEFAULT_REPORT_SUFFIX}"
    report_path = target_root / report_name
    debug_root = target_root / "_debug" if debug_crops else None
    logger = RunLogger(report_path)
    found_docs: list[ExtractedDocument] = []
    all_docs: list[ExtractedDocument] = []
    active_document: ExtractedDocument | None = None
    active_continuation_page = 1

    # Natural ordering is important for continuation pages: page 2 must be seen
    # immediately after page 1 so it can inherit the previous document metadata.
    files = sorted(iter_image_files(source_dir, exclude_dirs=[target_root]), key=_natural_sort_key)
    logger.log(f"Run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(f"Source directory: {source_dir}")
    logger.log(f"Target directory: {target_root}")
    logger.log(f"Registry file: {target_root / registry_name}")
    logger.log(f"Report file: {report_path}")
    logger.log(f"Found image files: {len(files)}")
    logger.log(f"Auto-rotate: {'on' if auto_rotate else 'off'}")
    logger.log(f"Deep OCR: {'on' if deep_ocr else 'off'}")
    logger.log(f"Dry run: {'on' if dry_run else 'off'}")
    logger.log(f"Debug crops: {'on' if debug_crops else 'off'}")

    for index, image_path in enumerate(files, start=1):
        logger.log(f"[{index}/{len(files)}] Processing: {image_path}")
        target_subdir = _target_subdir(source_dir, target_root, image_path)
        try:
            image = read_image(image_path)

            # Always try normal first-page UPD recognition before attaching the
            # scan to the previous document as a continuation page. A normal UPD
            # first page also contains signature blocks and company-name fields
            # at the bottom, so continuation-marker OCR alone can produce false
            # positives. The safe order is therefore:
            # 1) recognize the scan as a standalone document;
            # 2) only if that fails, try to attach it as a continuation page.
            doc, oriented_image = _analyze_image_orientations(
                image_path=image_path,
                image=image,
                lang=lang,
                deep_ocr=deep_ocr,
                auto_rotate=auto_rotate,
                debug_root=debug_root,
            )

            if active_document is not None and not doc.is_upd_invoice_transfer:
                # Only now try the page-2 heuristic. A normal first page has many
                # signature/stamp markers too, so running this before first-page
                # recognition caused false continuation matches in earlier versions.
                continuation_candidate = _analyze_continuation_orientations(
                    image_path=image_path,
                    image=image,
                    lang=lang,
                    auto_rotate=auto_rotate,
                )
                if continuation_candidate is not None:
                    continuation_doc, continuation_image = continuation_candidate
                    if continuation_doc.is_continuation_page:
                        doc, oriented_image = continuation_doc, continuation_image
            if doc.is_upd_invoice_transfer:
                # A newly recognized first page becomes the active document for a
                # possible next-page continuation scan.
                if not dry_run:
                    copy_found_document(doc, target_subdir, oriented_image=oriented_image)
                found_docs.append(doc)
                active_document = doc
                active_continuation_page = 1
                logger.log(
                    f"  FOUND: document={doc.invoice_number or '-'} date={doc.invoice_date or '-'} "
                    f"status={doc.status or '-'} rotation={doc.rotation_degrees} confidence={doc.confidence}"
                )
                if doc.destination_path:
                    logger.log(f"  copied as: {doc.destination_path}")
            elif doc.is_continuation_page and active_document is not None:
                # Continuation pages inherit number/date/party metadata from the
                # previous recognized document and get an explicit page suffix.
                active_continuation_page += 1
                doc.continuation_page_number = active_continuation_page
                if not dry_run:
                    copy_continuation_document(doc, active_document, target_subdir, oriented_image=oriented_image)
                logger.log(
                    f"  CONTINUATION: page={doc.continuation_page_number} "
                    f"for document={active_document.invoice_number or '-'} date={active_document.invoice_date or '-'} "
                    f"rotation={doc.rotation_degrees} confidence={doc.confidence}"
                )
                if doc.destination_path:
                    logger.log(f"  copied as: {doc.destination_path}")
            else:
                # An unrecognized scan breaks the continuation chain because the
                # next file can no longer be safely attached to an older document.
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
            # Keep the run resilient: one corrupt image should not stop the whole
            # archive. The problematic file is copied unchanged and recorded in CSV.
            doc = ExtractedDocument(source_path=image_path, error=str(exc))
            if not dry_run:
                try:
                    copy_unrecognized_document(doc, target_subdir)
                except Exception as copy_exc:
                    doc.warnings.append(f"Could not copy unrecognized file: {copy_exc}")
            all_docs.append(doc)
            logger.log(f"  ERROR: {exc}", error=True)
            if doc.destination_path:
                logger.log(f"  copied as: {doc.destination_path}")

    if not dry_run:
        registry_path = target_root / registry_name
        write_registry(all_docs, registry_path)
        logger.log(f"Registry written: {registry_path}")
    else:
        logger.log("Dry run mode: no files were copied and no registry was written.")

    logger.log(f"Found UPD invoice-transfer documents: {len(found_docs)}")
    logger.log(f"Total processed documents: {len(all_docs)}")
    logger.log(f"Run finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return found_docs, all_docs


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Find Russian UPD status 1 primary document scans and copy them to a target folder.",
    )
    parser.add_argument("--source", required=True, help="Source folder with scans. Subfolders are processed recursively.")
    parser.add_argument("--output", default=None, help="Optional base output folder. By default the target folder is created in the current working directory.")
    parser.add_argument("--target-dir-name", default=DEFAULT_TARGET_FOLDER, help=f"Target folder name. Default: {DEFAULT_TARGET_FOLDER}")
    parser.add_argument("--lang", default="rus+eng", help="Tesseract language combination. Default: rus+eng")
    parser.add_argument("--dry-run", action="store_true", help="Analyze files without copying or writing the registry.")
    parser.add_argument("--deep-ocr", action="store_true", help="Run OCR on the full page after header/status extraction. Slower, but may extract more fields.")
    parser.add_argument("--no-auto-rotate", action="store_true", help="Do not try 90/180/270-degree rotations. Faster, but sideways scans may be skipped.")
    parser.add_argument("--debug-crops", action="store_true", help="Save header, status, document number/date, shipment-row, and continuation-marker crops into the target _debug folder.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and run the processing workflow."""
    parser = build_parser()
    args = parser.parse_args(argv)
    source_dir = Path(args.source).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve() if args.output else None
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
        )
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
