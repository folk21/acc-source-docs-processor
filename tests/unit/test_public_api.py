"""Regression tests for package-level and CLI public entry points."""

from inspect import signature

import source_docs_processor
from source_docs_processor import cli
from source_docs_processor.features import document_processing


def test_root_package_exports_only_version_metadata() -> None:
    """Verify the root package does not become an accidental feature facade.

    Protected risk: re-exporting feature internals from the root would obscure
    ownership and create a second unsupported import path.
    """
    assert tuple(source_docs_processor.__all__) == ("__version__",)
    assert isinstance(source_docs_processor.__version__, str)


def test_cli_module_exports_exact_supported_entry_points() -> None:
    """Verify the CLI keeps one parser, one runner, and the legacy process alias.

    Protected risk: accidental command helper exports would expand the embedded
    API while removing the process alias would break existing imports.
    """
    assert tuple(cli.__all__) == ("build_parser", "main", "process_folder")
    assert cli.process_folder is document_processing.process_folder


def test_cli_function_signatures_are_stable() -> None:
    """Verify embedded CLI callers retain the supported parser and main contracts.

    Protected risk: requiring internal parser state or changing argv handling
    would break tests, wrappers, and local launch integrations.
    """
    assert tuple(signature(cli.build_parser).parameters) == ()
    assert tuple(signature(cli.main).parameters) == ("argv",)
    assert signature(cli.main).parameters["argv"].default is None
