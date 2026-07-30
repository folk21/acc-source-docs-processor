"""Generic local file-name and collision helpers."""

from __future__ import annotations

import re
from pathlib import Path


_INVALID_FILENAME_CHARACTERS = re.compile(r"[\\/:*?\"<>|]+")
_WHITESPACE = re.compile(r"\s+")
_REPEATED_UNDERSCORES = re.compile(r"_+")


def _sanitize_filename_component(value: str) -> str:
    """Return one sanitized filename component without applying a fallback."""
    normalized = _INVALID_FILENAME_CHARACTERS.sub("_", value.strip())
    normalized = _WHITESPACE.sub("_", normalized)
    normalized = _REPEATED_UNDERSCORES.sub("_", normalized)
    return normalized.strip("_.")


def safe_filename(value: str, *, fallback: str = "file") -> str:
    """Return a cross-platform-safe filename component.

    ``fallback`` is used only when ``value`` contains no usable characters after
    sanitization. Callers should provide a domain-specific fallback when the
    generic ``file`` value is not appropriate.
    """
    sanitized = _sanitize_filename_component(value)
    if sanitized:
        return sanitized

    sanitized_fallback = _sanitize_filename_component(fallback)
    if not sanitized_fallback:
        raise ValueError("Filename fallback must contain at least one usable character")
    return sanitized_fallback


def unique_path(path: Path) -> Path:
    """Return a non-existing path by adding a numeric suffix when needed."""
    if not path.exists():
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1
