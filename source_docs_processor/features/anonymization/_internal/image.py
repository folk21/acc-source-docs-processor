"""OCR-coordinate based redaction for raster images."""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont, ImageSequence

from .config import (
    AnonymizationConfig,
    EMPTY_ANONYMIZATION_CONFIG,
    _literal_spans,
    _subtract_spans,
    find_heading_token_range,
)
from .models import DetectedEntity, TextEntityAnalyzer, UnitProgressCallback
from .text import merge_entities


SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"})
_PASSENGER_LABEL_SEQUENCES = (
    ("passenger", "name"),
    ("name", "of", "passenger"),
    ("фамилия", "пассажира"),
)
_NAME_COMPONENT_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё]+(?:[-'’][A-Za-zА-Яа-яЁё]+)?")
_NAME_VALUE_WORD_PATTERN = re.compile(
    r"^[A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё/'’\-]*$"
)
_NAME_TITLES = frozenset({"mr", "mrs", "ms", "miss", "mstr", "dr"})


@dataclass(frozen=True)
class OcrWord:
    """One OCR word with redaction and upright-layout coordinates."""

    text: str
    start: int
    end: int
    left: int
    top: int
    width: int
    height: int
    confidence: float
    layout_left: int | None = None
    layout_top: int | None = None
    layout_width: int | None = None
    layout_height: int | None = None
    block_number: int = 0
    paragraph_number: int = 0
    line_number: int = 0


@dataclass(frozen=True)
class OcrPage:
    """OCR text plus original and upright-layout word coordinates."""

    text: str
    words: tuple[OcrWord, ...]
    rotation_degrees: int
    original_width: int
    original_height: int
    layout_width: int = 0
    layout_height: int = 0


@dataclass
class ParagraphRedactionState:
    """Track whether a configured section continues onto later raster pages."""

    redact_all: bool = False


def _layout_left(word: OcrWord) -> int:
    """Return one OCR word's upright left coordinate."""
    return word.layout_left if word.layout_left is not None else word.left


def _layout_top(word: OcrWord) -> int:
    """Return one OCR word's upright top coordinate."""
    return word.layout_top if word.layout_top is not None else word.top


def _layout_width(word: OcrWord) -> int:
    """Return one OCR word's upright width."""
    return word.layout_width if word.layout_width is not None else word.width


def _layout_height(word: OcrWord) -> int:
    """Return one OCR word's upright height."""
    return word.layout_height if word.layout_height is not None else word.height


def _normalized_label_tokens(words: tuple[OcrWord, ...]) -> tuple[str, ...]:
    """Return normalized alphabetic tokens for one OCR line."""
    return tuple(
        token.casefold().replace("ё", "е")
        for word in words
        for token in _NAME_COMPONENT_PATTERN.findall(word.text)
    )


def _contains_passenger_label(words: tuple[OcrWord, ...]) -> bool:
    """Return True when one OCR line contains a supported passenger-name label."""
    tokens = _normalized_label_tokens(words)
    for sequence in _PASSENGER_LABEL_SEQUENCES:
        size = len(sequence)
        if any(
            tokens[index : index + size] == sequence
            for index in range(len(tokens) - size + 1)
        ):
            return True
    return False


def _ocr_lines(page: OcrPage) -> list[tuple[OcrWord, ...]]:
    """Group OCR words into visual lines while preserving page order."""
    words = [word for word in page.words if word.text.strip()]
    if not words:
        return []

    if any(word.line_number > 0 for word in words):
        grouped: dict[tuple[int, int, int], list[OcrWord]] = {}
        for word in words:
            grouped.setdefault(
                (word.block_number, word.paragraph_number, word.line_number),
                [],
            ).append(word)
        lines = [
            tuple(sorted(group, key=_layout_left))
            for group in grouped.values()
        ]
        return sorted(
            lines,
            key=lambda line: (
                min(_layout_top(item) for item in line),
                min(_layout_left(item) for item in line),
            ),
        )

    ordered = sorted(words, key=lambda item: (_layout_top(item), _layout_left(item)))
    lines: list[list[OcrWord]] = []
    for word in ordered:
        center = _layout_top(word) + _layout_height(word) / 2
        selected: list[OcrWord] | None = None
        for candidate in reversed(lines):
            candidate_center = sum(
                _layout_top(item) + _layout_height(item) / 2
                for item in candidate
            ) / len(candidate)
            tolerance = max(
                6.0,
                max(_layout_height(word), *(_layout_height(item) for item in candidate))
                * 0.65,
            )
            if abs(center - candidate_center) <= tolerance:
                selected = candidate
                break
        if selected is None:
            lines.append([word])
        else:
            selected.append(word)
    return [tuple(sorted(line, key=_layout_left)) for line in lines]


def _line_box(words: tuple[OcrWord, ...]) -> tuple[int, int, int, int]:
    """Return one OCR line rectangle in upright layout coordinates."""
    return (
        min(_layout_left(word) for word in words),
        min(_layout_top(word) for word in words),
        max(_layout_left(word) + _layout_width(word) for word in words),
        max(_layout_top(word) + _layout_height(word) for word in words),
    )


def _passenger_name_value_words(words: tuple[OcrWord, ...]) -> tuple[OcrWord, ...]:
    """Return the leading name-like words from a candidate value line."""
    selected: list[OcrWord] = []
    components: list[str] = []
    for word in words:
        value = word.text.strip().strip(".,:;#")
        if not value or not _NAME_VALUE_WORD_PATTERN.fullmatch(value):
            if selected:
                break
            continue
        selected.append(word)
        components.extend(_NAME_COMPONENT_PATTERN.findall(value))

    meaningful = [
        component
        for component in components
        if component.casefold() not in _NAME_TITLES
    ]
    if len(meaningful) < 2:
        return ()
    return tuple(selected)


def _stacked_passenger_name_entities(page: OcrPage) -> list[DetectedEntity]:
    """Detect a passenger name directly below a strong OCR field label."""
    lines = _ocr_lines(page)
    matches: list[DetectedEntity] = []
    page_width = max(page.layout_width, page.original_width, 1)
    page_height = max(page.layout_height, page.original_height, 1)

    for index, label_line in enumerate(lines[:-1]):
        if not _contains_passenger_label(label_line):
            continue
        label_left, label_top, label_right, label_bottom = _line_box(label_line)
        label_height = max(1, label_bottom - label_top)
        for candidate_line in lines[index + 1 : index + 3]:
            candidate_left, candidate_top, _candidate_right, _candidate_bottom = (
                _line_box(candidate_line)
            )
            vertical_gap = candidate_top - label_bottom
            if vertical_gap < -label_height * 0.25:
                continue
            if vertical_gap > max(label_height * 4, page_height * 0.08):
                break
            horizontal_tolerance = max(
                label_right - label_left,
                page_width * 0.12,
            )
            if abs(candidate_left - label_left) > horizontal_tolerance:
                continue
            name_words = _passenger_name_value_words(candidate_line)
            if not name_words:
                continue
            matches.append(
                DetectedEntity(
                    start=min(word.start for word in name_words),
                    end=max(word.end for word in name_words),
                    entity_type="PERSON",
                    score=0.99,
                )
            )
            break
    return matches


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
        layout_left = int(data["left"][index])
        layout_top = int(data["top"][index])
        layout_width = int(data["width"][index])
        layout_height = int(data["height"][index])
        mapped = _map_box_to_original(
            layout_left,
            layout_top,
            layout_width,
            layout_height,
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
                layout_left=layout_left,
                layout_top=layout_top,
                layout_width=layout_width,
                layout_height=layout_height,
                block_number=int(data.get("block_num", [0] * count)[index]),
                paragraph_number=int(data.get("par_num", [0] * count)[index]),
                line_number=int(data.get("line_num", [0] * count)[index]),
            )
        )

    return OcrPage(
        text="".join(text_parts),
        words=tuple(words),
        rotation_degrees=angle,
        original_width=original_width,
        original_height=original_height,
        layout_width=candidate.width,
        layout_height=candidate.height,
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
        if config.uses_automatic_detection:
            excluded_spans = _literal_spans(page.text, config.excluded)
            configured_spans = [
                (entity.start, entity.end)
                for entity in entities
                if entity.entity_type.startswith("CONFIG_")
            ]
            structured_entities = [
                configured_segment
                for entity in _stacked_passenger_name_entities(page)
                for excluded_segment in _subtract_spans(entity, excluded_spans)
                for configured_segment in _subtract_spans(
                    excluded_segment,
                    configured_spans,
                )
            ]
            entities = merge_entities(
                [*entities, *structured_entities],
                len(page.text),
            )
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


def _replacement_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a local Unicode font without packaging or downloading font files."""
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_replacement_font(
    value: str,
    width: int,
    height: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Choose the largest local font that fits one replacement rectangle."""
    maximum_size = max(6, min(72, int(height * 0.82)))
    for size in range(maximum_size, 5, -1):
        font = _replacement_font(size)
        left, top, right, bottom = font.getbbox(value)
        if right - left <= width and bottom - top <= height:
            return font
    return _replacement_font(6)


def _draw_replacement(
    image: Image.Image,
    box: tuple[int, int, int, int],
    value: str,
    rotation_degrees: int,
) -> None:
    """Cover source pixels and draw a configured replacement in page orientation."""
    left, top, right, bottom = box
    box_width = max(1, right - left)
    box_height = max(1, bottom - top)
    upright_width = box_height if rotation_degrees in {90, 270} else box_width
    upright_height = box_width if rotation_degrees in {90, 270} else box_height
    layer = Image.new("RGB", (upright_width, upright_height), "white")
    draw = ImageDraw.Draw(layer)
    font = _fit_replacement_font(value, upright_width, upright_height)
    text_box = draw.textbbox((0, 0), value, font=font)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    x = max(0, (upright_width - text_width) // 2 - text_box[0])
    y = max(0, (upright_height - text_height) // 2 - text_box[1])
    try:
        draw.text((x, y), value, fill="black", font=font)
    except UnicodeEncodeError as exc:
        raise ValueError(
            "No local Unicode font is available for includedAndReplaced output"
        ) from exc
    if rotation_degrees:
        layer = layer.rotate(rotation_degrees, expand=True)
    if layer.size != (box_width, box_height):
        layer = layer.resize((box_width, box_height))
    image.paste(layer, (left, top))


def _entity_box(
    words: tuple[OcrWord, ...],
    entity: DetectedEntity,
    image: Image.Image,
    padding: int,
) -> tuple[int, int, int, int] | None:
    """Return a padded union box for OCR words intersecting one entity."""
    matched = [word for word in words if _overlaps(word, entity)]
    if not matched:
        return None
    return (
        max(0, min(word.left for word in matched) - padding),
        max(0, min(word.top for word in matched) - padding),
        min(image.width, max(word.left + word.width for word in matched) + padding),
        min(image.height, max(word.top + word.height for word in matched) + padding),
    )


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
    for entity in entities:
        box = _entity_box(page.words, entity, rgb, padding)
        if box is None:
            continue
        if entity.replacement is None:
            draw.rectangle(box, fill=(0, 0, 0))
        else:
            _draw_replacement(
                rgb,
                box,
                entity.replacement,
                page.rotation_degrees,
            )

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
