"""File copying, output naming, and CSV registry generation."""

from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path

import cv2
import numpy as np

from .models import ExtractedDocument


CSV_COLUMNS = [
    "source_file",
    "destination_file",
    "is_upd_invoice_transfer",
    "is_continuation_page",
    "continued_from",
    "status",
    "invoice_number",
    "invoice_date",
    "rotation_degrees",
    "seller_name",
    "seller_inn",
    "seller_kpp",
    "buyer_name",
    "buyer_inn",
    "buyer_kpp",
    "amount_without_vat",
    "vat_amount",
    "amount_with_vat",
    "request_number",
    "request_date",
    "vehicle",
    "loading_datetime",
    "unloading_datetime",
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
    """Write image to a possibly non-ASCII path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        suffix = ".png"
    success, encoded = cv2.imencode(suffix, image)
    if not success:
        raise ValueError(f"Unable to encode image as {suffix}: {path}")
    encoded.tofile(str(path))


def copy_found_document(doc: ExtractedDocument, target_dir: Path, oriented_image: np.ndarray | None = None) -> ExtractedDocument:
    """Copy a recognized document using generated УПД_<number> output naming."""
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(doc.filename_stem())
    destination = unique_path(target_dir / f"{stem}{doc.source_path.suffix.lower()}")

    # If the best OCR result was obtained after rotation, save exactly that upright image.
    # For non-rotated documents keep the original file bytes and metadata.
    if oriented_image is not None and doc.rotation_degrees % 360 != 0:
        write_image(destination, oriented_image)
    else:
        shutil.copy2(doc.source_path, destination)

    doc.destination_path = destination
    return doc



def copy_continuation_document(
    doc: ExtractedDocument,
    previous_doc: ExtractedDocument,
    target_dir: Path,
    oriented_image: np.ndarray | None = None,
) -> ExtractedDocument:
    """Copy a continuation page using the previous document number and date."""
    target_dir.mkdir(parents=True, exist_ok=True)
    doc.invoice_number = previous_doc.invoice_number
    doc.invoice_date = previous_doc.invoice_date
    doc.seller_name = previous_doc.seller_name
    doc.seller_inn = previous_doc.seller_inn
    doc.buyer_name = previous_doc.buyer_name
    doc.buyer_inn = previous_doc.buyer_inn
    doc.continued_from = previous_doc.destination_path.name if previous_doc.destination_path else previous_doc.source_path.name
    stem = safe_filename(doc.continuation_filename_stem())
    destination = unique_path(target_dir / f"{stem}{doc.source_path.suffix.lower()}")

    if oriented_image is not None and doc.rotation_degrees % 360 != 0:
        write_image(destination, oriented_image)
    else:
        shutil.copy2(doc.source_path, destination)

    doc.destination_path = destination
    return doc


def copy_unrecognized_document(doc: ExtractedDocument, target_dir: Path) -> ExtractedDocument:
    """Copy an unrecognized source image unchanged."""
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_path(target_dir / doc.source_path.name)
    shutil.copy2(doc.source_path, destination)
    doc.destination_path = destination
    return doc


def _empty_row(doc: ExtractedDocument) -> dict[str, object]:
    """Build a minimal registry row for an unrecognized file."""
    row: dict[str, object] = {column: "" for column in CSV_COLUMNS}
    row["source_file"] = doc.source_path.name
    return row


def _recognized_row(doc: ExtractedDocument) -> dict[str, object]:
    """Build a detailed registry row for a recognized transfer document."""
    return {
        "source_file": doc.source_path.name,
        "destination_file": doc.destination_path.name if doc.destination_path else "",
        "is_upd_invoice_transfer": int(doc.is_upd_invoice_transfer),
        "is_continuation_page": int(doc.is_continuation_page),
        "continued_from": doc.continued_from or "",
        "status": doc.status or "",
        "invoice_number": doc.invoice_number or "",
        "invoice_date": doc.invoice_date or "",
        "rotation_degrees": doc.rotation_degrees,
        "seller_name": doc.seller_name or "",
        "seller_inn": doc.seller_inn or "",
        "seller_kpp": doc.seller_kpp or "",
        "buyer_name": doc.buyer_name or "",
        "buyer_inn": doc.buyer_inn or "",
        "buyer_kpp": doc.buyer_kpp or "",
        "amount_without_vat": doc.amount_without_vat or "",
        "vat_amount": doc.vat_amount or "",
        "amount_with_vat": doc.amount_with_vat or "",
        "request_number": doc.request_number or "",
        "request_date": doc.request_date or "",
        "vehicle": doc.vehicle or "",
        "loading_datetime": doc.loading_datetime or "",
        "unloading_datetime": doc.unloading_datetime or "",
        "confidence": doc.confidence,
        "warnings": " | ".join(doc.warnings),
        "error": doc.error or "",
        "text_preview": doc.text_preview,
    }


def write_registry(documents: list[ExtractedDocument], path: Path) -> None:
    """Write the Excel-friendly semicolon-separated registry file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS, delimiter=";")
        writer.writeheader()
        for doc in documents:
            if doc.is_upd_invoice_transfer or doc.is_continuation_page:
                writer.writerow(_recognized_row(doc))
            else:
                writer.writerow(_empty_row(doc))
