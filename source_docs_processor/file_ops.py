"""Low-level file copying, safe naming, and image output helpers."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import cv2
import numpy as np

from .models import ExtractedDocument


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


def copy_processed_document(
    document: ExtractedDocument,
    target_dir: Path,
    filename_stem: str,
    oriented_image: np.ndarray | None = None,
) -> ExtractedDocument:
    """Copy a recognized image using a filename selected by its workflow."""
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(filename_stem)
    destination = unique_path(
        target_dir / f"{stem}{document.source_path.suffix.lower()}"
    )

    if oriented_image is not None and document.rotation_degrees % 360 != 0:
        write_image(destination, oriented_image)
    else:
        shutil.copy2(document.source_path, destination)

    document.destination_path = destination
    return document


def copy_unrecognized_document(
    document: ExtractedDocument,
    target_dir: Path,
) -> ExtractedDocument:
    """Copy an unrecognized source image unchanged."""
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_path(target_dir / document.source_path.name)
    shutil.copy2(document.source_path, destination)
    document.destination_path = destination
    return document
