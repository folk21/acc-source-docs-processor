"""Document-processing copy operations built on generic core helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from ....core.files import safe_filename, unique_path
from ....core.images import write_image
from ..models import ExtractedDocument


__all__ = [
    "copy_processed_document",
    "copy_unrecognized_document",
    "safe_filename",
    "unique_path",
    "write_image",
]


def copy_processed_document(
    document: ExtractedDocument,
    target_dir: Path,
    filename_stem: str,
    oriented_image: np.ndarray | None = None,
) -> ExtractedDocument:
    """Copy a recognized image using a filename selected by its workflow."""
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(filename_stem, fallback="document")
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
