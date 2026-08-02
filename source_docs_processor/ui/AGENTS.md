# Local UI development guide

This file narrows the root `AGENTS.md` rules for
`source_docs_processor/ui/` and `streamlit_app.py`.

## Scope

The UI is a local Streamlit adapter for the public feature APIs. It owns only
localized presentation, input validation, session state, progress rendering,
and conversion of public result models into privacy-safe tables.

Do not move OCR, anonymization, document processing, registry, or file-format
behavior into this package.

## Dependency rules

- Import supported operations only through their public feature package facades.
- Never import a feature `_internal` module.
- `core` and `features` must not import the UI package or Streamlit.
- Keep Streamlit imports inside `source_docs_processor/ui/` and the root
  `streamlit_app.py` adapter.
- Keep operation identifiers explicit in Python. Language configuration may
  enable and order known operations, but it must not contain executable import
  paths or arbitrary callables.
- Build processing controls from public `DocumentTypeMetadata` capability flags;
  do not duplicate processor capabilities in localized configuration.
- Keep one generic processing adapter for registered document types instead of
  copying Streamlit execution logic into document-specific UI modules.

## Localization

- Store localized static UI text in `config/ui/ui_<language>.ini`.
- The locale code inside a file must match its filename suffix.
- Keep operation identifiers and configuration keys language-neutral.
- Add the same required text contract to every supported language.
- Russian remains the default UI language.

## Privacy and execution

- Run locally and do not add upload, network, telemetry, or cloud processing.
- Do not display OCR text or extracted private accounting values in progress
  events.
- Prefer relative paths in result tables.
- Processing result tables may show recognition state and counts, but must not
  expose OCR text, extracted accounting values, or warning contents.
- Do not invoke `main.py` or feature CLI commands through `subprocess`; call the
  public Python APIs directly.
- Keep Streamlit callbacks small because feature progress callbacks execute
  synchronously in the processing thread.

## Validation

Run the focused UI tests while developing:

```bash
make test-ui
```

Run public API tests when feature-call contracts change:

```bash
make test-public-api
```

Run complete validation before completion:

```bash
make check
```
