"""Generic local image I/O, geometry, and OCR preprocessing helpers."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

import cv2
import numpy as np

from .paths import is_relative_to


SUPPORTED_IMAGE_EXTENSIONS = frozenset(
    {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
)
ROTATION_ANGLES = (0, 90, 180, 270)


def iter_image_files(
    source_dir: Path,
    exclude_dirs: Iterable[Path] = (),
) -> Iterator[Path]:
    """Yield supported image files recursively outside excluded directories."""
    resolved_excludes = [directory.resolve() for directory in exclude_dirs]
    for path in source_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
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


def write_image(path: Path, image: np.ndarray) -> None:
    """Write an OpenCV image to a path that may contain non-ASCII characters."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        suffix = ".png"
    success, encoded = cv2.imencode(suffix, image)
    if not success:
        raise ValueError(f"Unable to encode image as {suffix}: {path}")
    encoded.tofile(str(path))


def rotate_image(image: np.ndarray, angle: int) -> np.ndarray:
    """Rotate an image clockwise by 0, 90, 180, or 270 degrees."""
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


def crop_relative(
    image: np.ndarray,
    left: float,
    top: float,
    right: float,
    bottom: float,
) -> np.ndarray:
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
    """Create a compact set of document-neutral OCR preprocessing variants."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    variants: list[np.ndarray] = []

    normalized = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    variants.append(normalized)

    upscaled = cv2.resize(
        normalized,
        None,
        fx=1.5,
        fy=1.5,
        interpolation=cv2.INTER_CUBIC,
    )
    variants.append(upscaled)

    adaptive = cv2.adaptiveThreshold(
        normalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    variants.append(adaptive)

    return variants
