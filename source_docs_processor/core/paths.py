"""Cross-feature path relationship helpers."""

from pathlib import Path


def is_relative_to(path: Path, parent: Path) -> bool:
    """Return True when path is inside parent, including parent itself."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
