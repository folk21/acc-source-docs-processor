# Anonymization feature

This feature creates privacy-safe local copies of supported documents. It owns
configuration loading, text analysis, OCR-backed raster redaction, PDF rebuilding,
DOCX sanitization, editable DOCX reconstruction, recursive folder processing,
and the `anonymize` CLI adapter.

## Public API

Supported entry points are exported through
`source_docs_processor.features.anonymization`, including:

- `anonymize_folder`;
- `load_anonymization_config`;
- `create_presidio_analyzer`;
- public configuration, progress, result, and analyzer models.

Callers import the package facade. Format handlers and workflow implementation
remain private under `_internal/`.

## Package map

```text
anonymization/
├── api.py                    # public programmatic surface
├── command.py                # CLI adapter
└── _internal/
    ├── config.py             # INI rules and configured analyzers
    ├── models.py             # private shared contracts
    ├── workflow.py           # recursive planning and atomic output
    ├── text.py               # Presidio integration and text transforms
    ├── image.py              # OCR-coordinate raster redaction
    ├── pdf.py                # image-only PDF rebuilding
    ├── docx.py               # fail-closed OOXML sanitization
    └── editable.py           # OCR-to-DOCX reconstruction
```

## Related documentation

- [Installation](../../../docs/INSTALLATION.md)
- [Anonymization usage](../../../docs/USAGE.md#anonymize-document-folders)
- [Architecture](../../../docs/ARCHITECTURE.md#anonymization)
- [Development invariants](AGENTS.md)

## Validation

```bash
make test-anonymization
make check
```
