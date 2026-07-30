"""Conservative continuation-page classification for scanned UPD."""

from __future__ import annotations

import re


def continuation_marker_score(text: str) -> int:
    """Score OCR text as a probable continuation page of a UPD document."""
    compact = re.sub(r"\s+", " ", text.lower())
    score = 0
    markers = [
        ("наименование экономического субъекта", 35),
        ("составителя документа", 35),
        ("ответственный за правильность", 30),
        ("оформления факта хозяйственной жизни", 25),
        ("м.п", 15),
        ("подпись", 10),
        ("должность", 10),
        ("траст", 15),
        ("эталон", 15),
    ]
    for marker, weight in markers:
        if marker in compact:
            score += weight

    if re.search(r"сч[её]т\s*[-–]?\s*фактур", compact) or "универсальн" in compact:
        return 0
    return max(score, 0)


def is_probable_continuation_page(text: str) -> bool:
    """Return True when OCR markers point to page 2 without an invoice header."""
    return continuation_marker_score(text) >= 60
