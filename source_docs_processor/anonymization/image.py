"""OCR-coordinate based redaction for raster images."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageSequence

from .config import (
    AnonymizationConfig,
    EMPTY_ANONYMIZATION_CONFIG,
    find_heading_token_range,
)
from .models import DetectedEntity, TextEntityAnalyzer, UnitProgressCallback
from .text import merge_entities


SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"})


@dataclass(frozen=True)
class OcrWord:
    """One OCR word with text offsets and a bounding rectangle."""

    text: str
    start: int
    end: int
    left: int
    top: int
    width: int
    height: int
    confidence: float


@dataclass(frozen=True)
class OcrPage:
    """OCR text and positioned words for one image orientation."""

    text: str
    words: tuple[OcrWord, ...]
    rotation_degrees: int
    original_width: int
    original_height: int


@dataclass
class ParagraphRedactionState:
    """Track whether a configured section continues onto later raster pages."""

    redact_all: bool = False


def _rotated_image(image: Image.Image, angle: int) -> Image.Image:
    """Rotate an image clockwise for OCR without changing the output image."""
    if angle == 0:
        return image
    return image.rotate(-angle, expand=True)


def _map_box_to_original(
    left: int,
    top: int,
    width: int,
    height: int,
    angle: int,
    original_width: int,
    original_height: int,
) -> tuple[int, int, int, int]:
    """Map a rectangle from a clockwise OCR rotation to original coordinates."""
    if angle == 0:
        return left, top, width, height
    if angle == 90:
        return top, original_height - left - width, height, width
    if angle == 180:
        return (
            original_width - left - width,
            original_height - top - height,
            width,
            height,
        )
    if angle == 270:
        return original_width - top - height, left, height, width
    raise ValueError(f"Unsupported OCR rotation: {angle}")


def _ocr_page(image: Image.Image, lang: str, angle: int) -> OcrPage:
    """Run Tesseract OCR and build stable text-to-box offsets."""
    original_width, original_height = image.size
    candidate = _rotated_image(image, angle)
    data = pytesseract.image_to_data(
        np.asarray(candidate.convert("RGB")),
        lang=lang,
        config="--psm 11",
        output_type=pytesseract.Output.DICT,
        timeout=30,
    )

    text_parts: list[str] = []
    words: list[OcrWord] = []
    offset = 0
    count = len(data.get("text", []))
    for index in range(count):
        value = str(data["text"][index]).strip()
        if not value:
            continue
        try:
            confidence = float(data["conf"][index])
        except (TypeError, ValueError):
            confidence = -1.0
        if confidence < 0:
            continue
        if text_parts:
            text_parts.append(" ")
            offset += 1
        start = offset
        text_parts.append(value)
        offset += len(value)
        mapped = _map_box_to_original(
            int(data["left"][index]),
            int(data["top"][index]),
            int(data["width"][index]),
            int(data["height"][index]),
            angle,
            original_width,
            original_height,
        )
        words.append(
            OcrWord(
                text=value,
                start=start,
                end=offset,
                left=mapped[0],
                top=mapped[1],
                width=mapped[2],
                height=mapped[3],
                confidence=confidence,
            )
        )

    return OcrPage(
        text="".join(text_parts),
        words=tuple(words),
        rotation_degrees=angle,
        original_width=original_width,
        original_height=original_height,
    )


def _choose_ocr_page(
    image: Image.Image,
    analyzer: TextEntityAnalyzer,
    lang: str,
    config: AnonymizationConfig,
) -> tuple[OcrPage, list[DetectedEntity]]:
    """Choose the orientation with the strongest PII and OCR signal."""
    candidates: list[tuple[OcrPage, list[DetectedEntity]]] = []
    for angle in (0, 90, 270, 180):
        try:
            page = _ocr_page(image, lang=lang, angle=angle)
        except RuntimeError:
            continue
        analyze_ocr = getattr(analyzer, "analyze_ocr", None)
        raw_entities = (
            analyze_ocr(page.text)
            if callable(analyze_ocr)
            else analyzer.analyze(page.text)
        )
        entities = merge_entities(raw_entities, len(page.text))
        candidates.append((page, entities))
    if not candidates:
        raise RuntimeError("Tesseract OCR did not return a usable result")
    return max(
        candidates,
        key=lambda candidate: (
            find_heading_token_range(
                [word.text for word in candidate[0].words],
                config.included_paragraphs,
            )
            is not None,
            len(candidate[1]),
            sum(word.confidence >= 35 for word in candidate[0].words),
            len(candidate[0].text),
            sum(word.confidence for word in candidate[0].words),
        ),
    )


def _overlaps(word: OcrWord, entity: DetectedEntity) -> bool:
    """Return True when one OCR word intersects a detected text span."""
    return word.start < entity.end and word.end > entity.start


def _redact_configured_section(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    page: OcrPage,
    config: AnonymizationConfig,
    state: ParagraphRedactionState,
    padding: int,
) -> bool:
    """Redact below a configured heading and activate later-page redaction."""
    token_range = find_heading_token_range(
        [word.text for word in page.words],
        config.included_paragraphs,
    )
    if token_range is None:
        return False
    start, end = token_range
    matched_words = page.words[start:end]
    if not matched_words:
        return False
    cutoff = min(
        image.height,
        max(word.top + word.height for word in matched_words) + padding,
    )
    if cutoff < image.height:
        draw.rectangle((0, cutoff, image.width, image.height), fill=(0, 0, 0))
    state.redact_all = True
    return True


def redact_pil_image(
    image: Image.Image,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    padding: int = 4,
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
    paragraph_state: ParagraphRedactionState | None = None,
) -> tuple[Image.Image, int]:
    """Redact detected PII and configured page sections on one raster image."""
    rgb = image.convert("RGB")
    state = paragraph_state or ParagraphRedactionState()
    if state.redact_all:
        return Image.new("RGB", rgb.size, "black"), 0

    page, entities = _choose_ocr_page(
        rgb,
        analyzer=analyzer,
        lang=lang,
        config=config,
    )
    draw = ImageDraw.Draw(rgb)
    for word in page.words:
        if not any(_overlaps(word, entity) for entity in entities):
            continue
        left = max(0, word.left - padding)
        top = max(0, word.top - padding)
        right = min(rgb.width, word.left + word.width + padding)
        bottom = min(rgb.height, word.top + word.height + padding)
        draw.rectangle((left, top, right, bottom), fill=(0, 0, 0))

    section_redacted = _redact_configured_section(
        rgb,
        draw,
        page,
        config,
        state,
        padding,
    )
    return rgb, len(entities) + int(section_redacted)


def _save_frames(frames: list[Image.Image], destination: Path, suffix: str) -> None:
    """Write sanitized raster frames without EXIF or source metadata."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if suffix in {".tif", ".tiff"}:
        frames[0].save(
            destination,
            format="TIFF",
            save_all=True,
            append_images=frames[1:],
            compression="tiff_deflate",
        )
        return
    if suffix in {".jpg", ".jpeg"}:
        frames[0].save(destination, format="JPEG", quality=95, optimize=True)
        return
    if suffix == ".bmp":
        frames[0].save(destination, format="BMP")
        return
    frames[0].save(destination, format="PNG", optimize=True)


def anonymize_image_file(
    source: Path,
    destination: Path,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
    progress_callback: UnitProgressCallback | None = None,
) -> int:
    """Anonymize every frame in one supported raster image file."""
    redacted_frames: list[Image.Image] = []
    detected = 0
    state = ParagraphRedactionState()
    with Image.open(source) as image:
        frame_count = getattr(image, "n_frames", 1)
        for frame_index, frame in enumerate(ImageSequence.Iterator(image), start=1):
            if progress_callback is not None:
                progress_callback("frame", frame_index, frame_count)
            redacted, frame_detected = redact_pil_image(
                frame.copy(),
                analyzer=analyzer,
                lang=lang,
                config=config,
                paragraph_state=state,
            )
            redacted_frames.append(redacted)
            detected += frame_detected
    if not redacted_frames:
        raise ValueError(f"Image has no readable frames: {source}")
    _save_frames(redacted_frames, destination, source.suffix.lower())
    return detected


def anonymize_image_bytes(
    content: bytes,
    suffix: str,
    analyzer: TextEntityAnalyzer,
    lang: str = "rus+eng",
    config: AnonymizationConfig = EMPTY_ANONYMIZATION_CONFIG,
) -> tuple[bytes, int]:
    """Anonymize every frame in one embedded raster image."""
    frames: list[Image.Image] = []
    detected = 0
    state = ParagraphRedactionState()
    with Image.open(BytesIO(content)) as image:
        for frame in ImageSequence.Iterator(image):
            redacted, frame_detected = redact_pil_image(
                frame.copy(),
                analyzer=analyzer,
                lang=lang,
                config=config,
                paragraph_state=state,
            )
            frames.append(redacted)
            detected += frame_detected
    if not frames:
        raise ValueError("Embedded image has no readable frames")

    output = BytesIO()
    normalized_suffix = suffix.lower()
    if normalized_suffix in {".jpg", ".jpeg"}:
        frames[0].save(output, format="JPEG", quality=95, optimize=True)
    elif normalized_suffix == ".bmp":
        frames[0].save(output, format="BMP")
    elif normalized_suffix in {".tif", ".tiff"}:
        frames[0].save(
            output,
            format="TIFF",
            save_all=True,
            append_images=frames[1:],
            compression="tiff_deflate",
        )
    else:
        frames[0].save(output, format="PNG", optimize=True)
    return output.getvalue(), detected
