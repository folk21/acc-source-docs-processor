"""Tests for image OCR coordinate transformations."""

from __future__ import annotations

from source_docs_processor.anonymization.image import _map_box_to_original


def test_clockwise_rotation_box_maps_back_to_original_coordinates() -> None:
    """Verify redaction boxes found on a rotated scan cover the original pixels.

    Protected risk: OCR may select a 90-degree orientation while the output file
    remains in its original orientation.
    """
    mapped = _map_box_to_original(
        left=70,
        top=20,
        width=15,
        height=30,
        angle=90,
        original_width=200,
        original_height=100,
    )

    assert mapped == (20, 15, 30, 15)
