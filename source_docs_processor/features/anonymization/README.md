# Anonymization feature

This feature creates privacy-safe local copies of supported documents. It owns
configuration loading, text analysis, OCR-backed raster redaction, PDF rebuilding,
DOCX/XLSX package sanitization, editable DOCX reconstruction, recursive folder
processing, and the `anonymize` CLI adapter.

`entityDetectionMode` selects whether entity masking comes from local
Presidio/spaCy recognition, explicit configured literals, both sources, or
neither. Automatic recognition uses Russian and English local spaCy PERSON NER
plus a targeted set of project/privacy recognizers. Generic organization/location
NER is intentionally excluded, and single-token PERSON guesses are rejected so
receipt, ticket, and boarding-pass content is preserved. High-confidence
passenger-name layouts are handled by narrow supplemental recognizers. They
support same-line forms such as `NAME OF PASSENGER: SMITH/JOHN MR` and OCR
layouts where `Passenger name` or `Фамилия пассажира` is printed above the
passenger value. Explicit international `+` phone patterns
remain supported. `includedParagraphs` remains an independent structural
redaction rule.
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
    ├── docx.py               # fail-closed DOCX sanitization
    ├── xlsx.py               # fail-closed XLSX sanitization
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
