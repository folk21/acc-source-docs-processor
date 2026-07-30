# Anonymization feature

## Purpose

This feature creates privacy-safe local copies of supported documents. It owns
configuration, PII detection, OCR-backed raster redaction, PDF rebuilding, DOCX
sanitization, editable DOCX reconstruction, recursive folder processing, and the
`anonymize` CLI adapter.

## Public entry points

- `source_docs_processor.features.anonymization.anonymize_folder`
- `source_docs_processor.features.anonymization.load_anonymization_config`
- `source_docs_processor.features.anonymization.command.register_anonymize_command`

External modules should import the package API. Format handlers, configuration
matching, workflow machinery, and anonymization-only models are private
implementation details exposed only through `api.py` when required by callers.

## Dependency rules

- May import feature-neutral helpers from `source_docs_processor.core`.
- Must not import `features.document_processing`.
- The feature root contains only `api.py`, `command.py`, and package exports.
- Configuration, models, workflow, text analysis, and format handlers belong
  under `_internal/`.
- Modules outside this feature must not import `anonymization._internal`.
- No external network or cloud OCR calls are allowed.

## Structure

```text
anonymization/
├── README.md
├── __init__.py
├── api.py                    # public programmatic surface
├── command.py                # CLI adapter
└── _internal/
    ├── config.py
    ├── models.py
    ├── workflow.py
    ├── text.py
    ├── image.py
    ├── pdf.py
    ├── docx.py
    └── editable.py
```

## Invariants

- Unsupported or opaque content fails closed.
- Recognized PII values are never logged.
- Source names and relative folders are preserved unless output conversion
  requires deterministic collision handling.
- PDF source text layers and metadata are not retained.
- The output root inode is preserved by `--clearOutput`.

## Validation

```bash
python -m pytest -q tests/unit/anonymization tests/integration/anonymization
```
