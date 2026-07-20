"""Low-level image loading, rotation, cropping, and OCR preprocessing helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
ROTATION_ANGLES = (0, 90, 180, 270)


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return True when path is inside parent, including parent itself."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


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
        if any(_is_relative_to(resolved_path, excluded) for excluded in resolved_excludes):
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
    scan archives. Targeted crops use stronger preprocessing separately.
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


def crop_header(image: np.ndarray) -> np.ndarray:
    """Crop the upper part of the UPD form where document metadata is located."""
    height, width = image.shape[:2]
    return image[0 : int(height * 0.30), 0:width]


def crop_status_area(image: np.ndarray) -> np.ndarray:
    """Crop the left-side area containing the framed UPD status digit."""
    height, width = image.shape[:2]
    return image[int(height * 0.07) : int(height * 0.18), int(width * 0.04) : int(width * 0.14)]


def crop_invoice_number_candidates(image: np.ndarray) -> list[np.ndarray]:
    """Return candidate crops for the document number field.

    The boxes are tuned for the official landscape UPD template. Multiple boxes
    are used because scans may be slightly shifted, scaled, or cropped.
    """
    boxes = [
        (0.215, 0.035, 0.310, 0.067),
        (0.220, 0.037, 0.315, 0.062),
        (0.215, 0.030, 0.340, 0.073),
    ]
    return [crop_relative(image, *box) for box in boxes]


def crop_invoice_date_candidates(image: np.ndarray) -> list[np.ndarray]:
    """Return candidate crops for the top document date field."""
    boxes = [
        (0.335, 0.035, 0.490, 0.067),
        (0.330, 0.030, 0.500, 0.077),
        (0.345, 0.035, 0.490, 0.067),
    ]
    return [crop_relative(image, *box) for box in boxes]


def crop_transfer_date_candidates(image: np.ndarray) -> list[np.ndarray]:
    """Return fallback crops for transfer/shipment date fields near the bottom."""
    boxes = [
        (0.200, 0.740, 0.360, 0.775),
        (0.180, 0.720, 0.400, 0.785),
    ]
    return [crop_relative(image, *box) for box in boxes]


def crop_status_digit_candidates(image: np.ndarray) -> list[np.ndarray]:
    """Return tight crops for the framed status digit."""
    boxes = [
        (0.080, 0.070, 0.105, 0.130),
        (0.075, 0.070, 0.110, 0.140),
        (0.070, 0.065, 0.115, 0.150),
    ]
    return [crop_relative(image, *box) for box in boxes]


def crop_shipment_document_row_candidates(image: np.ndarray) -> list[np.ndarray]:
    """Return candidate crops for the `Document about shipment` row.

    This row often repeats the document number and date in the form
    `№ п/п 1 № <number> от <date>`. It is a reliable fallback when the
    top invoice date is covered by punch holes, stains, or weak contrast.
    """
    boxes = [
        (0.245, 0.185, 0.585, 0.230),
        (0.235, 0.175, 0.600, 0.240),
        (0.105, 0.185, 0.600, 0.235),
    ]
    return [crop_relative(image, *box) for box in boxes]


def crop_continuation_marker_candidates(image: np.ndarray) -> list[np.ndarray]:
    """Return text areas that help identify a second page of the same document.

    Continuation pages usually do not contain the main `Счет-фактура` header,
    but they still contain signature blocks, company names, stamps, and fields
    such as `Наименование экономического субъекта`.
    """
    boxes = [
        (0.000, 0.000, 1.000, 0.220),
        (0.000, 0.720, 1.000, 1.000),
        (0.000, 0.000, 0.550, 0.350),
        (0.450, 0.000, 1.000, 0.350),
    ]
    return [crop_relative(image, *box) for box in boxes]
