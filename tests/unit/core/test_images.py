"""Tests for feature-neutral image helpers."""

from pathlib import Path

import numpy as np

from source_docs_processor.core.images import read_image, rotate_image, write_image


def test_image_io_supports_non_ascii_paths(tmp_path: Path) -> None:
    """Verify core image I/O works independently from document workflows.

    Protected risk: OpenCV's ordinary path functions may fail on non-ASCII local
    paths, which are common in accounting folder names.
    """
    path = tmp_path / 'изображение.png'
    image = np.zeros((3, 4, 3), dtype=np.uint8)

    write_image(path, image)

    assert read_image(path).shape == image.shape


def test_rotate_image_uses_clockwise_angles() -> None:
    """Verify the shared rotation convention remains clockwise.

    Protected risk: processors score orientation candidates using this convention;
    reversing it would silently associate OCR results with the wrong page view.
    """
    image = np.arange(6, dtype=np.uint8).reshape(2, 3)

    rotated = rotate_image(image, 90)

    assert rotated.tolist() == [[3, 0], [4, 1], [5, 2]]
