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

External modules should import the package API rather than private helpers from
format-specific modules.

## Dependency rules

- May import cross-feature helpers from `source_docs_processor.core`.
- Must not import `features.document_processing`.
- Format-specific modules may collaborate inside this feature.
- No external network or cloud OCR calls are allowed.

## Files and responsibilities

- `command.py` — CLI parsing, analyzer selection, and privacy-safe progress output.
- `workflow.py` — recursive traversal, output planning, atomic writes, and cleanup.
- `config.py` — INI parsing and configured mask/replacement matching.
- `text.py` — Presidio integration and text transformation.
- `image.py`, `pdf.py`, `docx.py`, `editable.py` — format-specific sanitization.
- `models.py` — anonymization-only contracts and result models.

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
