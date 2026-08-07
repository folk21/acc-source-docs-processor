# Anonymization feature

This feature creates privacy-safe local copies of supported documents. It owns
configuration loading, text analysis, OCR-backed raster redaction, PDF rebuilding,
DOCX sanitization, editable DOCX reconstruction, recursive folder processing,
and the `anonymize` CLI adapter.

`entityDetectionMode` selects whether entity masking comes from local
Presidio/spaCy recognition, explicit configured literals, both sources, or
neither. Automatic recognition uses both Russian and English local spaCy NER and
a targeted set of project/privacy recognizers. It intentionally excludes broad
generic recognizers which can hide receipt amounts or dates and rejects
single-token name/location/organization NER guesses. Explicit international `+`
phone patterns remain supported. `includedParagraphs` remains an independent
structural redaction rule.
Legacy configurations without `entityDetectionMode` retain the historical
inference: configured literals select configured-only detection; otherwise
automatic detection is used.

## Public API

Supported entry points are exported through
`source_docs_processor.features.anonymization`, including:

- `anonymize_folder`;
- `load_anonymization_config`;
- `create_presidio_analyzer`;
- `ENTITY_DETECTION_MODES` for adapters that render supported mode choices;
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
