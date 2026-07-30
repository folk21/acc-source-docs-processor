"""UPD status 1 crop definitions.

The crop coordinates in this module are specific to the current landscape UPD
form family. They are kept out of the generic image module so another document
processor can define a completely different template without touching shared
pipeline code.
"""

from __future__ import annotations

import numpy as np

from ..image_processing import crop_relative


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
