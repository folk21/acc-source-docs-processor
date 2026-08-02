"""Path validation helpers for local UI operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ValidationIssue:
    """One language-neutral validation issue rendered by the UI."""

    code: str
    path: Path


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Return True when a resolved path is inside another resolved path."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_anonymization_paths(
    source_dir: Path,
    output_dir: Path,
    config_path: Path,
    *,
    clear_output: bool,
) -> tuple[ValidationIssue, ...]:
    """Validate paths before invoking the anonymization feature API."""
    source = source_dir.expanduser().resolve()
    output = output_dir.expanduser().resolve()
    config = config_path.expanduser().resolve()
    issues: list[ValidationIssue] = []

    if not source.exists():
        issues.append(ValidationIssue("source_missing", source))
    elif not source.is_dir():
        issues.append(ValidationIssue("source_not_directory", source))

    if output.exists() and not output.is_dir():
        issues.append(ValidationIssue("output_not_directory", output))
    if source == output:
        issues.append(ValidationIssue("source_equals_output", output))
    if clear_output and _is_relative_to(source, output):
        issues.append(ValidationIssue("unsafe_clear_output", output))

    if not config.exists():
        issues.append(ValidationIssue("config_missing", config))
    elif not config.is_file():
        issues.append(ValidationIssue("config_not_file", config))

    return tuple(issues)


def validate_processing_paths(
    source_dir: Path,
    output_dir: Path,
) -> tuple[ValidationIssue, ...]:
    """Validate paths before invoking the document-processing public API."""
    source = source_dir.expanduser().resolve()
    output = output_dir.expanduser().resolve()
    issues: list[ValidationIssue] = []

    if not source.exists():
        issues.append(ValidationIssue("source_missing", source))
    elif not source.is_dir():
        issues.append(ValidationIssue("source_not_directory", source))

    if output.exists() and not output.is_dir():
        issues.append(ValidationIssue("output_not_directory", output))
    if source == output:
        issues.append(ValidationIssue("source_equals_output", output))

    return tuple(issues)
