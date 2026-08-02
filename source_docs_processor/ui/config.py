"""Language-specific configuration loading for the local Streamlit adapter."""

from __future__ import annotations

import argparse
import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_UI_LANGUAGE = "ru"
DEFAULT_UI_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config" / "ui"
_CONFIG_FILE_PATTERN = re.compile(r"ui_(?P<language>[a-z][a-z0-9_-]*)\.ini$")
_OPERATION_ID_PATTERN = re.compile(r"[a-z][a-z0-9_]*")


@dataclass(frozen=True)
class UiLaunchOptions:
    """Command-line options passed to the Streamlit script."""

    language: str = DEFAULT_UI_LANGUAGE


@dataclass(frozen=True)
class UiConfig:
    """One validated language-specific UI configuration."""

    language_code: str
    language_name: str
    operation_ids: tuple[str, ...]
    sections: Mapping[str, Mapping[str, str]]
    source_path: Path

    def text(self, section: str, key: str) -> str:
        """Return one required localized value."""
        try:
            return self.sections[section][key]
        except KeyError as exc:
            raise ValueError(
                f"Missing UI configuration value [{section}] {key}: {self.source_path}"
            ) from exc

    def operation_title(self, operation_id: str) -> str:
        """Return the localized title for one configured operation."""
        return self.text(f"operation.{operation_id}", "title")

    def operation_description(self, operation_id: str) -> str:
        """Return the localized explanation for one configured operation."""
        return self.text(f"operation.{operation_id}", "description")


def parse_launch_options(argv: Sequence[str] | None = None) -> UiLaunchOptions:
    """Parse Streamlit script arguments without consuming Streamlit options."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--lang", default=DEFAULT_UI_LANGUAGE)
    arguments, _unknown = parser.parse_known_args(argv)
    language = str(arguments.lang).strip().lower() or DEFAULT_UI_LANGUAGE
    return UiLaunchOptions(language=language)


def _split_identifiers(raw_value: str) -> tuple[str, ...]:
    """Parse a comma-separated or multiline operation identifier list."""
    identifiers: list[str] = []
    seen: set[str] = set()
    for raw_part in re.split(r"[,\n]", raw_value):
        identifier = raw_part.strip()
        if not identifier:
            continue
        if not _OPERATION_ID_PATTERN.fullmatch(identifier):
            raise ValueError(f"Invalid UI operation identifier: {identifier}")
        if identifier in seen:
            continue
        identifiers.append(identifier)
        seen.add(identifier)
    if not identifiers:
        raise ValueError("UI configuration must define at least one operation")
    return tuple(identifiers)


def load_ui_config(path: Path) -> UiConfig:
    """Load and validate one language-specific INI configuration."""
    config_path = path.expanduser().resolve()
    file_match = _CONFIG_FILE_PATTERN.fullmatch(config_path.name)
    if file_match is None:
        raise ValueError(
            "UI configuration file names must use the ui_<language>.ini pattern: "
            f"{config_path}"
        )
    if not config_path.is_file():
        raise ValueError(f"UI configuration file does not exist: {config_path}")

    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower
    try:
        with config_path.open("r", encoding="utf-8-sig") as stream:
            parser.read_file(stream)
    except (OSError, configparser.Error) as exc:
        raise ValueError(f"Cannot read UI configuration: {config_path}: {exc}") from exc

    language_code = parser.get("locale", "code", fallback="").strip().lower()
    language_name = parser.get("locale", "name", fallback="").strip()
    suffix_language = file_match.group("language")
    if not language_code or language_code != suffix_language:
        raise ValueError(
            "UI locale code must match its file suffix: "
            f"file={suffix_language}, configured={language_code or '<empty>'}"
        )
    if not language_name:
        raise ValueError(f"UI locale name is empty: {config_path}")

    operation_ids = _split_identifiers(
        parser.get("operations", "ids", fallback="")
    )
    sections = {
        section: {key: value.strip() for key, value in parser.items(section)}
        for section in parser.sections()
    }
    for operation_id in operation_ids:
        operation_section = f"operation.{operation_id}"
        if operation_section not in sections:
            raise ValueError(
                f"Missing [{operation_section}] in UI configuration: {config_path}"
            )
        for key in ("title", "description"):
            if not sections[operation_section].get(key):
                raise ValueError(
                    f"Missing [{operation_section}] {key}: {config_path}"
                )

    return UiConfig(
        language_code=language_code,
        language_name=language_name,
        operation_ids=operation_ids,
        sections=sections,
        source_path=config_path,
    )


def discover_ui_configs(
    config_dir: Path = DEFAULT_UI_CONFIG_DIR,
) -> dict[str, UiConfig]:
    """Load every valid language configuration from one directory."""
    resolved_dir = config_dir.expanduser().resolve()
    if not resolved_dir.is_dir():
        raise ValueError(f"UI configuration directory does not exist: {resolved_dir}")

    configs: dict[str, UiConfig] = {}
    for path in sorted(resolved_dir.glob("ui_*.ini")):
        config = load_ui_config(path)
        if config.language_code in configs:
            raise ValueError(
                f"Duplicate UI language configuration: {config.language_code}"
            )
        configs[config.language_code] = config
    if DEFAULT_UI_LANGUAGE not in configs:
        raise ValueError(
            f"Default UI language is missing: {DEFAULT_UI_LANGUAGE}"
        )
    return configs


def resolve_initial_language(
    requested_language: str,
    configs: Mapping[str, UiConfig],
) -> str:
    """Return a configured launch language or the project default."""
    normalized = requested_language.strip().lower()
    return normalized if normalized in configs else DEFAULT_UI_LANGUAGE
