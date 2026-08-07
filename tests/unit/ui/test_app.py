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
    assert set(app._OPERATION_RENDERERS) == {
        "anonymize",
        "process_upd_invoices_status_1",
        "process_npd_receipts",
        "process_incoming_purchase_documents",
    }


class _RenderForm:
    """Minimal context manager used by the anonymization form smoke test."""

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        return None


class _RenderStreamlit:
    """Capture controls rendered before an anonymization form is submitted."""

    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.selectboxes: list[tuple[str, tuple[str, ...], int, str]] = []

    def selectbox(self, label, options, *, index=0, key, **_kwargs):
        normalized_options = tuple(options)
        self.selectboxes.append((label, normalized_options, index, key))
        return normalized_options[index]

    def form(self, _key):
        return _RenderForm()

    def text_input(self, _label, *, value, **_kwargs):
        return value

    def checkbox(self, _label, **_kwargs):
        return False

    def form_submit_button(self, _label, **_kwargs):
        return False


def test_anonymization_screen_renders_session_entity_detection_selector(monkeypatch) -> None:
    """Verify Streamlit exposes every supported mode with combined as the default.

    Protected risk: adding the runtime override only to the adapter model would
    leave users unable to select it from the actual Streamlit anonymization form.
    """
    monkeypatch.setitem(sys.modules, "streamlit", _fake_streamlit_module())
    sys.modules.pop("source_docs_processor.ui.app", None)
    app = importlib.import_module("source_docs_processor.ui.app")

    from source_docs_processor.features.anonymization import ENTITY_DETECTION_MODES
    from source_docs_processor.ui.config import discover_ui_configs

    rendered = _RenderStreamlit()
    monkeypatch.setattr(app, "st", rendered)

    app._render_anonymization(discover_ui_configs()["en"])

    mode_control = next(
        item for item in rendered.selectboxes if item[3] == "anonymization_entity_detection_mode"
    )
    assert mode_control[1] == ENTITY_DETECTION_MODES
    assert mode_control[1][mode_control[2]] == "combined"
