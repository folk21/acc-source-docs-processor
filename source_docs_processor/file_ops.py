"""File copying, output naming, and generic CSV registry generation."""

from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path

import cv2
import numpy as np

from .document_processor import DocumentProcessor
from .models import ExtractedDocument


COMMON_CSV_COLUMNS = [
    "source_file",
    "destination_file",
    "document_type",
    "is_recognized",
    "is_continuation_page",
    "continued_from",
    "status",
    "document_number",
    "document_date",
    "document_datetime",
    "rotation_degrees",
    "issuer_name",
    "issuer_inn",
    "issuer_kpp",
    "recipient_name",
    "recipient_inn",
    "recipient_kpp",
    "amount_without_tax",
    "tax_amount",
    "total_amount",
    "currency",
    "description",
    "confidence",
    "warnings",
    "error",
    "text_preview",
]


def safe_filename(value: str) -> str:
    """Make a value safe for use as a cross-platform file name."""
    value = value.strip()
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_.") or "document"


def unique_path(path: Path) -> Path:
    """Return a non-existing path by adding a numeric suffix when needed."""
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def write_image(path: Path, image: np.ndarray) -> None:
    """Write an image to a possibly non-ASCII path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        suffix = ".png"
    success, encoded = cv2.imencode(suffix, image)
    if not success:
        raise ValueError(f"Unable to encode image as {suffix}: {path}")
    encoded.tofile(str(path))


def _copy_processed_image(
    doc: ExtractedDocument,
    target_dir: Path,
    processor: DocumentProcessor,
    oriented_image: np.ndarray | None,
) -> ExtractedDocument:
    """Copy a recognized image using the processor's filename policy."""
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(processor.build_output_filename_stem(doc))
    destination = unique_path(target_dir / f"{stem}{doc.source_path.suffix.lower()}")

    if oriented_image is not None and doc.rotation_degrees % 360 != 0:
        write_image(destination, oriented_image)
    else:
        shutil.copy2(doc.source_path, destination)

    doc.destination_path = destination
    return doc


def copy_recognized_document(
    doc: ExtractedDocument,
    target_dir: Path,
    processor: DocumentProcessor,
    oriented_image: np.ndarray | None = None,
) -> ExtractedDocument:
    """Copy a recognized primary document using processor-specific naming."""
    return _copy_processed_image(doc, target_dir, processor, oriented_image)


def copy_continuation_document(
    doc: ExtractedDocument,
    target_dir: Path,
    processor: DocumentProcessor,
    oriented_image: np.ndarray | None = None,
) -> ExtractedDocument:
    """Copy a prepared continuation page using processor-specific naming."""
    return _copy_processed_image(doc, target_dir, processor, oriented_image)


def copy_unrecognized_document(
    doc: ExtractedDocument,
    target_dir: Path,
) -> ExtractedDocument:
    """Copy an unrecognized source image unchanged."""
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_path(target_dir / doc.source_path.name)
    shutil.copy2(doc.source_path, destination)
    doc.destination_path = destination
    return doc


def _registry_columns(processor: DocumentProcessor) -> list[str]:
    """Return common columns followed by validated processor-specific columns."""
    extra_columns = list(processor.registry_extra_columns)
    duplicates = set(COMMON_CSV_COLUMNS).intersection(extra_columns)
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Processor registry columns duplicate common columns: {duplicate_list}"
        )
    if len(extra_columns) != len(set(extra_columns)):
        raise ValueError("Processor registry columns must be unique")
    return COMMON_CSV_COLUMNS + extra_columns


def _empty_row(
    doc: ExtractedDocument,
    columns: list[str],
    processor: DocumentProcessor,
) -> dict[str, object]:
    """Build a minimal registry row for an unrecognized file."""
    row: dict[str, object] = {column: "" for column in columns}
    row.update(
        {
            "source_file": doc.source_path.name,
            "document_type": doc.document_type or processor.document_type,
            "is_recognized": 0,
            "warnings": " | ".join(doc.warnings),
            "error": doc.error or "",
        }
    )
    return row


def _recognized_row(
    doc: ExtractedDocument,
    columns: list[str],
    processor: DocumentProcessor,
) -> dict[str, object]:
    """Build a generic registry row and append processor-specific values."""
    row: dict[str, object] = {column: "" for column in columns}
    row.update(
        {
            "source_file": doc.source_path.name,
            "destination_file": doc.destination_path.name if doc.destination_path else "",
            "document_type": doc.document_type or processor.document_type,
            "is_recognized": int(doc.is_recognized),
            "is_continuation_page": int(doc.is_continuation_page),
            "continued_from": doc.continued_from or "",
            "status": doc.status or "",
            "document_number": doc.document_number or "",
            "document_date": doc.document_date or "",
            "document_datetime": doc.document_datetime or "",
            "rotation_degrees": doc.rotation_degrees,
            "issuer_name": doc.issuer_name or "",
            "issuer_inn": doc.issuer_inn or "",
            "issuer_kpp": doc.issuer_kpp or "",
            "recipient_name": doc.recipient_name or "",
            "recipient_inn": doc.recipient_inn or "",
            "recipient_kpp": doc.recipient_kpp or "",
            "amount_without_tax": doc.amount_without_tax or "",
            "tax_amount": doc.tax_amount or "",
            "total_amount": doc.total_amount or "",
            "currency": doc.currency or "",
            "description": doc.description or "",
            "confidence": doc.confidence,
            "warnings": " | ".join(doc.warnings),
            "error": doc.error or "",
            "text_preview": doc.text_preview,
        }
    )
    row.update(processor.registry_extra_values(doc))
    return row


def write_registry(
    documents: list[ExtractedDocument],
    path: Path,
    processor: DocumentProcessor,
) -> None:
    """Write an Excel-friendly registry with common and processor-specific fields."""
    columns = _registry_columns(processor)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, delimiter=";")
        writer.writeheader()
        for doc in documents:
            if doc.is_recognized:
                writer.writerow(_recognized_row(doc, columns, processor))
            else:
                writer.writerow(_empty_row(doc, columns, processor))
