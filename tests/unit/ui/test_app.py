"""Smoke tests for the optional Streamlit adapter."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType


def _fake_streamlit_module() -> ModuleType:
    """Create the minimum Streamlit surface required during module import."""
    module = ModuleType("streamlit")

    def cache_resource(**_options):
        def decorate(function):
            return function

        return decorate

    module.cache_resource = cache_resource  # type: ignore[attr-defined]
    return module


def test_streamlit_adapter_imports_without_running_the_application(monkeypatch) -> None:
    """Verify the UI modules can be imported without starting OCR or Streamlit.

    Protected risk: the optional UI dependency must remain outside normal CLI
    imports, while the entry point must stay safe for test discovery and tooling.
    """
    monkeypatch.setitem(sys.modules, "streamlit", _fake_streamlit_module())
    sys.modules.pop("source_docs_processor.ui.app", None)
    sys.modules.pop("streamlit_app", None)

    module = importlib.import_module("streamlit_app")
    app = importlib.import_module("source_docs_processor.ui.app")

    assert callable(module.run_app)
    assert callable(app.run_app)
