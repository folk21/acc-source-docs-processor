"""Generic image loading, rotation, and OCR preprocessing helpers.

This module intentionally contains only document-type-neutral image utilities.
Template-specific crop coordinates live in the corresponding document processor
package, for example `source_docs_processor.features.document_processing.document_types.upd_invoices_status_1`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from ...core.paths import is_relative_to


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
ROTATION_ANGLES = (0, 90, 180, 270)


def iter_image_files(source_dir: Path, exclude_dirs: Iterable[Path] = ()) -> Iterable[Path]:
    """Yield supported image files from source_dir recursively.

    The exclusion list prevents the program from re-processing its own output
    folder when the output folder is placed under the source tree.
    """
    resolved_excludes = [directory.resolve() for directory in exclude_dirs]
    for path in source_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        resolved_path = path.resolve()
        if any(is_relative_to(resolved_path, excluded) for excluded in resolved_excludes):
            continue
        yield path


def read_image(path: Path) -> np.ndarray:
    """Read an image from a path that may contain non-ASCII characters."""
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def rotate_image(image: np.ndarray, angle: int) -> np.ndarray:
    """Rotate image clockwise by 0, 90, 180, or 270 degrees."""
    normalized = angle % 360
    if normalized == 0:
        return image
    if normalized == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if normalized == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    if normalized == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    raise ValueError(f"Unsupported rotation angle: {angle}")


def crop_relative(image: np.ndarray, left: float, top: float, right: float, bottom: float) -> np.ndarray:
    """Crop an image using relative coordinates in the 0..1 range."""
    height, width = image.shape[:2]
    x1 = max(0, min(width, int(width * left)))
    y1 = max(0, min(height, int(height * top)))
    x2 = max(0, min(width, int(width * right)))
    y2 = max(0, min(height, int(height * bottom)))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid crop coordinates")
    return image[y1:y2, x1:x2]


def create_ocr_variants(image: np.ndarray) -> list[np.ndarray]:
    """Create a small set of full-area variants for general OCR.

    The list is intentionally short because full-page OCR is expensive on large
    scan archives. Document-specific processors may add stronger preprocessing
    for small targeted crops.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    variants: list[np.ndarray] = []

    # Normalized grayscale is usually the safest baseline for clean scans.
    norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    variants.append(norm)

    # Upscaling helps Tesseract read small printed text in table cells.
    upscaled = cv2.resize(norm, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    variants.append(upscaled)

    # Adaptive thresholding can recover text on low-contrast scans.
    adaptive = cv2.adaptiveThreshold(
        norm,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    variants.append(adaptive)

    return variants
