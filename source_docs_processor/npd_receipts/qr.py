"""Local QR decoding and NPD receipt URL parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

import cv2
import numpy as np


_NPD_RECEIPT_PATH = re.compile(
    r"^/api/v1/receipt/(?P<issuer_inn>\d{10,12})/"
    r"(?P<receipt_number>[^/]+)/print/?$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class NpdReceiptQrData:
    """Structured values encoded by an official NPD receipt QR URL."""

    url: str
    issuer_inn: str
    receipt_number: str


def parse_npd_receipt_qr_url(value: str | None) -> NpdReceiptQrData | None:
    """Parse an official local NPD receipt print URL without network access."""
    if not value:
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        return None
    if parsed.netloc.lower().split(":", 1)[0] != "lknpd.nalog.ru":
        return None
    match = _NPD_RECEIPT_PATH.fullmatch(unquote(parsed.path))
    if not match:
        return None
    return NpdReceiptQrData(
        url=value.strip(),
        issuer_inn=match.group("issuer_inn"),
        receipt_number=match.group("receipt_number"),
    )


def _decode_candidate(detector: cv2.QRCodeDetector, image: np.ndarray) -> str:
    """Decode one QR candidate while tolerating OpenCV failures."""
    try:
        value, _points, _straight = detector.detectAndDecode(image)
    except cv2.error:
        return ""
    return value.strip()


def decode_qr_url(image: np.ndarray) -> str | None:
    """Decode the first QR URL from an image using a few inexpensive variants."""
    detector = cv2.QRCodeDetector()
    candidates: list[np.ndarray] = [image]
    gray = (
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image.ndim == 3
        else image
    )
    candidates.append(gray)
    if min(gray.shape[:2]) < 1000:
        candidates.append(
            cv2.resize(
                gray,
                None,
                fx=1.5,
                fy=1.5,
                interpolation=cv2.INTER_CUBIC,
            )
        )

    for candidate in candidates:
        value = _decode_candidate(detector, candidate)
        if value:
            return value
    return None
