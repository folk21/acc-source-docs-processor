# Local Streamlit UI

This package is an optional local adapter for non-technical users:

```text
Streamlit UI -> public feature API -> existing workflow
CLI          -> feature command    -> existing workflow
```

The adapter exposes document anonymization and every registered document-
processing workflow.

## Responsibilities

The UI owns localized presentation, input validation, session state, privacy-safe
progress, and result tables. Processing screens resolve capabilities from public
document-type metadata and call `process_folder()` directly. The UI does not own
OCR, redaction, document extraction, registry generation, or output policy.

`streamlit_app.py` is the minimal entry point. Implementation modules live in
`source_docs_processor/ui/`, while localized text and enabled operation order
live in `config/ui/ui_<language>.ini`.

Configuration can enable and order known language-neutral operation identifiers.
Executable handlers remain an explicit Python mapping. The current identifiers are
`anonymize`, `process_upd_invoices_status_1`, `process_npd_receipts`, and
`process_incoming_purchase_documents`.

## User documentation

- [Installation](../../docs/INSTALLATION.md)
- [Usage](../../docs/USAGE.md#local-streamlit-interface)

The UI is intended for localhost use on the computer that contains the source and
output folders. Browser upload, remote storage, authentication, and background
job queues are not part of the current adapter.

## Development

Read the local [AGENTS.md](AGENTS.md) before changing the adapter.

```bash
make test-ui
make check
```
