"""Local Streamlit adapter for supported accounting-document operations."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import Any

import streamlit as st

from source_docs_processor.features.anonymization import AnonymizationProgress
from source_docs_processor.features.document_processing import ProcessingProgress

from .anonymization import (
    AnonymizationRequest,
    build_result_rows,
    execute_anonymization,
)
from .config import (
    UiConfig,
    discover_ui_configs,
    parse_launch_options,
    resolve_initial_language,
)
from .document_processing import (
    ProcessingRequest,
    build_generated_artifact_rows,
    build_processing_result_rows,
    execute_processing,
    get_processing_metadata,
)
from .path_validation import (
    ValidationIssue,
    validate_anonymization_paths,
    validate_processing_paths,
)


OperationRenderer = Callable[[UiConfig], None]


@st.cache_resource(show_spinner=False)
def _load_presidio_analyzer() -> Any:
    """Load the local Presidio/spaCy analyzer once for the local UI process."""
    from source_docs_processor.features.anonymization import create_presidio_analyzer

    return create_presidio_analyzer()


def _localized_issue(config: UiConfig, issue: ValidationIssue) -> str:
    """Render one language-neutral path validation issue."""
    template = config.text("validation", issue.code)
    return template.format(path=issue.path)


def _anonymization_progress_fraction(progress: AnonymizationProgress) -> float:
    """Return a bounded file-level fraction for one anonymization event."""
    if progress.file_count <= 0:
        return 0.0
    completed = (
        progress.file_index
        if progress.event == "file_finished"
        else progress.file_index - 1
    )
    return min(max(completed / progress.file_count, 0.0), 1.0)


def _anonymization_progress_message(
    config: UiConfig,
    progress: AnonymizationProgress,
) -> str:
    """Return a localized privacy-safe anonymization progress message."""
    values = {
        "file_index": progress.file_index,
        "file_count": progress.file_count,
        "file_name": progress.source_path.name,
        "unit_name": progress.unit_name or "",
        "unit_index": progress.unit_index or 0,
        "unit_count": progress.unit_count or 0,
    }
    if progress.event == "file_started":
        key = "progress_file_started"
    elif progress.event == "unit_started":
        key = "progress_unit_started"
    elif progress.error is None:
        key = "progress_file_finished"
    else:
        key = "progress_file_failed"
        values["error"] = progress.error
    return config.text("anonymize", key).format(**values)


def _render_anonymization_results(config: UiConfig) -> None:
    """Render the most recent anonymization summary for this session."""
    summary = st.session_state.get("anonymization_summary")
    if summary is None:
        return

    st.subheader(config.text("anonymize", "results_title"))
    columns = st.columns(4)
    columns[0].metric(
        config.text("anonymize", "metric_succeeded"),
        summary.succeeded_count,
    )
    columns[1].metric(
        config.text("anonymize", "metric_failed"),
        summary.failed_count,
    )
    columns[2].metric(
        config.text("anonymize", "metric_generated"),
        summary.generated_files_count,
    )
    columns[3].metric(
        config.text("anonymize", "metric_detected"),
        summary.detected_entities,
    )

    rows = []
    for row in build_result_rows(summary):
        row_data = asdict(row)
        rows.append(
            {
                config.text("anonymize", "column_source"): row_data["source_file"],
                config.text("anonymize", "column_status"): (
                    config.text("anonymize", "status_success")
                    if row_data["succeeded"]
                    else config.text("anonymize", "status_failed")
                ),
                config.text("anonymize", "column_outputs"): row_data["output_files"],
                config.text("anonymize", "column_detected"): row_data[
                    "detected_entities"
                ],
                config.text("anonymize", "column_error"): row_data["error"],
            }
        )
    if rows:
        st.dataframe(rows, hide_index=True)


def _render_anonymization(config: UiConfig) -> None:
    """Render and execute the local anonymization operation."""
    output_modes = ("source", "docx", "docx_and_source")
    if st.session_state.get("anonymization_output_mode") not in output_modes:
        st.session_state["anonymization_output_mode"] = output_modes[0]
    output_mode = st.selectbox(
        config.text("anonymize", "output_mode_label"),
        output_modes,
        format_func=lambda value: config.text(
            "anonymize", f"output_mode_{value}"
        ),
        key="anonymization_output_mode",
        help=config.text("anonymize", "output_mode_help"),
    )

    with st.form("anonymization_form"):
        source_value = st.text_input(
            config.text("anonymize", "source_label"),
            value=config.text("defaults", "source_path"),
            key="anonymization_source",
            help=config.text("anonymize", "source_help"),
        )
        output_value = st.text_input(
            config.text("anonymize", "output_label"),
            value=config.text("defaults", "output_path"),
            key="anonymization_output",
            help=config.text("anonymize", "output_help"),
        )
        config_value = st.text_input(
            config.text("anonymize", "config_label"),
            value=config.text("defaults", "anonymization_config_path"),
            key="anonymization_config",
            help=config.text("anonymize", "config_help"),
        )
        ocr_language = st.text_input(
            config.text("anonymize", "ocr_language_label"),
            value=config.text("defaults", "ocr_language"),
            key="anonymization_ocr_language",
            help=config.text("anonymize", "ocr_language_help"),
        )
        preserve_layout = st.checkbox(
            config.text("anonymize", "preserve_layout_label"),
            key="anonymization_preserve_layout",
            help=config.text("anonymize", "preserve_layout_help"),
        )
        clear_output = st.checkbox(
            config.text("anonymize", "clear_output_label"),
            key="anonymization_clear_output",
            help=config.text("anonymize", "clear_output_help"),
        )
        submitted = st.form_submit_button(
            config.text("anonymize", "run_button"),
            type="primary",
        )

    if submitted:
        request = AnonymizationRequest(
            source_dir=Path(source_value),
            output_dir=Path(output_value),
            config_path=Path(config_value),
            lang=ocr_language.strip() or "rus+eng",
            output_mode=output_mode,
            preserve_layout=preserve_layout,
            clear_output=clear_output,
        )
        issues = validate_anonymization_paths(
            request.source_dir,
            request.output_dir,
            request.config_path,
            clear_output=request.clear_output,
        )
        if issues:
            for issue in issues:
                st.error(_localized_issue(config, issue))
        else:
            st.session_state["anonymization_summary"] = None
            status = st.status(
                config.text("anonymize", "running_status"),
                expanded=True,
            )
            progress_bar = st.progress(0.0)
            progress_text = st.empty()

            def update_progress(progress: AnonymizationProgress) -> None:
                progress_bar.progress(_anonymization_progress_fraction(progress))
                progress_text.caption(
                    _anonymization_progress_message(config, progress)
                )

            try:
                summary = execute_anonymization(
                    request,
                    analyzer_provider=_load_presidio_analyzer,
                    progress_callback=update_progress,
                )
                st.session_state["anonymization_summary"] = summary
                progress_bar.progress(1.0)
                if summary.failed_count:
                    status.update(
                        label=config.text("anonymize", "completed_with_errors"),
                        state="error",
                        expanded=True,
                    )
                else:
                    status.update(
                        label=config.text("anonymize", "completed_status"),
                        state="complete",
                        expanded=False,
                    )
            except Exception as exc:
                status.update(
                    label=config.text("anonymize", "failed_status"),
                    state="error",
                    expanded=True,
                )
                st.error(
                    config.text("anonymize", "unexpected_error").format(error=exc)
                )

    _render_anonymization_results(config)


def _processing_progress_fraction(progress: ProcessingProgress) -> float:
    """Return a bounded file-level fraction for one processing event."""
    if progress.event == "run_finished":
        return 1.0
    if progress.file_count <= 0:
        return 0.0
    completed = (
        progress.file_index
        if progress.event == "file_finished"
        else progress.file_index - 1
    )
    if progress.event == "registry_written":
        completed = progress.file_count
    return min(max(completed / progress.file_count, 0.0), 1.0)


def _processing_progress_message(
    config: UiConfig,
    progress: ProcessingProgress,
) -> str:
    """Return a localized privacy-safe document-processing progress message."""
    values = {
        "file_index": progress.file_index,
        "file_count": progress.file_count,
        "file_name": progress.source_path.name if progress.source_path else "",
        "output_name": progress.output_path.name if progress.output_path else "",
    }
    key = {
        "scan_started": "progress_scan_started",
        "file_started": "progress_file_started",
        "file_finished": (
            "progress_file_failed" if progress.error else "progress_file_finished"
        ),
        "registry_written": "progress_registry_written",
        "run_finished": "progress_run_finished",
    }[progress.event]
    values["error"] = progress.error or ""
    return config.text("process", key).format(**values)


def _processing_status(config: UiConfig, recognized: bool, error: str) -> str:
    """Return the localized result status for one processed file."""
    if error:
        return config.text("process", "status_failed")
    if recognized:
        return config.text("process", "status_recognized")
    return config.text("process", "status_unrecognized")


def _render_processing_results(config: UiConfig, document_type: str) -> None:
    """Render the most recent document-processing summary for one type."""
    summary = st.session_state.get(f"processing_summary:{document_type}")
    if summary is None:
        return

    st.subheader(config.text("process", "results_title"))
    columns = st.columns(4)
    columns[0].metric(
        config.text("process", "metric_processed"),
        summary.processed_count,
    )
    columns[1].metric(
        config.text("process", "metric_recognized"),
        summary.recognized_count,
    )
    columns[2].metric(
        config.text("process", "metric_errors"),
        summary.error_count,
    )
    columns[3].metric(
        config.text("process", "metric_generated"),
        len(summary.generated_files),
    )

    result_rows = []
    for row in build_processing_result_rows(summary):
        row_data = asdict(row)
        result_rows.append(
            {
                config.text("process", "column_source"): row_data["source_file"],
                config.text("process", "column_status"): _processing_status(
                    config,
                    row_data["recognized"],
                    row_data["error"],
                ),
                config.text("process", "column_output"): row_data["output_file"],
                config.text("process", "column_warnings"): row_data["warning_count"],
                config.text("process", "column_error"): row_data["error"],
            }
        )
    if result_rows:
        st.dataframe(result_rows, hide_index=True)

    artifact_rows = []
    for row in build_generated_artifact_rows(summary):
        row_data = asdict(row)
        artifact_rows.append(
            {
                config.text("process", "column_artifact_type"): config.text(
                    "process", f"artifact_{row_data['artifact_type']}"
                ),
                config.text("process", "column_artifact_path"): row_data["path"],
            }
        )
    if artifact_rows:
        st.subheader(config.text("process", "artifacts_title"))
        st.dataframe(artifact_rows, hide_index=True)


def _render_document_processing(
    config: UiConfig,
    *,
    operation_id: str,
    document_type: str,
) -> None:
    """Render and execute one registered document-processing workflow."""
    metadata = get_processing_metadata(document_type)
    operation_section = f"operation.{operation_id}"
    key_prefix = f"processing_{document_type}"

    st.caption(
        config.text("process", "supported_extensions").format(
            extensions=", ".join(metadata.supported_extensions)
        )
    )

    with st.form(f"{key_prefix}_form"):
        source_value = st.text_input(
            config.text("process", "source_label"),
            value=config.text(operation_section, "source_path"),
            key=f"{key_prefix}_source",
            help=config.text("process", "source_help"),
        )
        output_value = st.text_input(
            config.text("process", "output_label"),
            value=config.text(operation_section, "output_path"),
            key=f"{key_prefix}_output",
            help=config.text("process", "output_help"),
        )
        target_dir_name = st.text_input(
            config.text("process", "target_dir_name_label"),
            value="",
            key=f"{key_prefix}_target_dir_name",
            help=config.text("process", "target_dir_name_help"),
        )
        ocr_language = st.text_input(
            config.text("process", "ocr_language_label"),
            value=config.text("defaults", "ocr_language"),
            key=f"{key_prefix}_ocr_language",
            help=config.text("process", "ocr_language_help"),
        )
        deep_ocr = (
            st.checkbox(
                config.text("process", "deep_ocr_label"),
                key=f"{key_prefix}_deep_ocr",
                help=config.text("process", "deep_ocr_help"),
            )
            if metadata.supports_deep_ocr
            else False
        )
        auto_rotate = (
            st.checkbox(
                config.text("process", "auto_rotate_label"),
                value=True,
                key=f"{key_prefix}_auto_rotate",
                help=config.text("process", "auto_rotate_help"),
            )
            if metadata.supports_auto_rotate
            else False
        )
        debug_crops = (
            st.checkbox(
                config.text("process", "debug_crops_label"),
                key=f"{key_prefix}_debug_crops",
                help=config.text("process", "debug_crops_help"),
            )
            if metadata.supports_debug_crops
            else False
        )
        dry_run = st.checkbox(
            config.text("process", "dry_run_label"),
            key=f"{key_prefix}_dry_run",
            help=config.text("process", "dry_run_help"),
        )
        submitted = st.form_submit_button(
            config.text("process", "run_button"),
            type="primary",
        )

    if submitted:
        request = ProcessingRequest(
            source_dir=Path(source_value),
            output_dir=Path(output_value),
            document_type=document_type,
            lang=ocr_language.strip() or "rus+eng",
            target_dir_name=target_dir_name.strip() or None,
            dry_run=dry_run,
            deep_ocr=deep_ocr,
            auto_rotate=auto_rotate,
            debug_crops=debug_crops,
        )
        issues = validate_processing_paths(request.source_dir, request.output_dir)
        if issues:
            for issue in issues:
                st.error(_localized_issue(config, issue))
        else:
            summary_key = f"processing_summary:{document_type}"
            st.session_state[summary_key] = None
            status = st.status(
                config.text("process", "running_status"),
                expanded=True,
            )
            progress_bar = st.progress(0.0)
            progress_text = st.empty()

            def update_progress(progress: ProcessingProgress) -> None:
                progress_bar.progress(_processing_progress_fraction(progress))
                progress_text.caption(_processing_progress_message(config, progress))

            try:
                summary = execute_processing(
                    request,
                    progress_callback=update_progress,
                )
                st.session_state[summary_key] = summary
                progress_bar.progress(1.0)
                if summary.error_count:
                    status.update(
                        label=config.text("process", "completed_with_errors"),
                        state="error",
                        expanded=True,
                    )
                else:
                    status.update(
                        label=config.text("process", "completed_status"),
                        state="complete",
                        expanded=False,
                    )
            except Exception as exc:
                status.update(
                    label=config.text("process", "failed_status"),
                    state="error",
                    expanded=True,
                )
                st.error(config.text("process", "unexpected_error").format(error=exc))

    _render_processing_results(config, document_type)


_OPERATION_RENDERERS: dict[str, OperationRenderer] = {
    "anonymize": _render_anonymization,
    "process_upd_invoices_status_1": partial(
        _render_document_processing,
        operation_id="process_upd_invoices_status_1",
        document_type="upd_invoices_status_1",
    ),
    "process_npd_receipts": partial(
        _render_document_processing,
        operation_id="process_npd_receipts",
        document_type="npd_receipts",
    ),
    "process_incoming_purchase_documents": partial(
        _render_document_processing,
        operation_id="process_incoming_purchase_documents",
        document_type="incoming_purchase_documents",
    ),
}


def run_app(argv: list[str] | None = None) -> None:
    """Run the localized local-only Streamlit interface."""
    launch_options = parse_launch_options(sys.argv[1:] if argv is None else argv)
    configs = discover_ui_configs()
    initial_language = resolve_initial_language(launch_options.language, configs)
    if "ui_language" not in st.session_state:
        st.session_state["ui_language"] = initial_language

    active_language = st.session_state["ui_language"]
    if active_language not in configs:
        active_language = initial_language
        st.session_state["ui_language"] = active_language
    config = configs[active_language]

    st.set_page_config(
        page_title=config.text("app", "page_title"),
        page_icon="📄",
        layout="wide",
    )

    language_codes = tuple(configs)
    st.selectbox(
        config.text("app", "language_label"),
        language_codes,
        format_func=lambda code: configs[code].language_name,
        key="ui_language",
    )

    st.title(config.text("app", "title"))
    st.markdown(config.text("app", "description"))

    unsupported_operations = tuple(
        operation_id
        for operation_id in config.operation_ids
        if operation_id not in _OPERATION_RENDERERS
    )
    if unsupported_operations:
        st.error(
            config.text("app", "unsupported_operations").format(
                operations=", ".join(unsupported_operations)
            )
        )
    configured_operations = tuple(
        operation_id
        for operation_id in config.operation_ids
        if operation_id in _OPERATION_RENDERERS
    )
    if not configured_operations:
        st.error(config.text("app", "no_supported_operations"))
        return
    if st.session_state.get("ui_operation") not in configured_operations:
        st.session_state["ui_operation"] = configured_operations[0]

    selector_column, description_column = st.columns((1, 2))
    with selector_column:
        selected_operation = st.selectbox(
            config.text("app", "operation_label"),
            configured_operations,
            format_func=config.operation_title,
            key="ui_operation",
            help=config.text("app", "operation_help"),
        )
    with description_column:
        st.subheader(config.operation_title(selected_operation))
        st.markdown(config.operation_description(selected_operation))

    st.divider()
    _OPERATION_RENDERERS[selected_operation](config)
