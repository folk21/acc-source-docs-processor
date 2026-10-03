# Anonymization feature

This feature creates privacy-safe local copies of supported documents. It owns
configuration loading, text analysis, OCR-backed raster redaction, PDF rebuilding,
DOCX/XLSX package sanitization, editable DOCX reconstruction, recursive folder
processing, and the `anonymize` CLI adapter.

`entityDetectionMode` selects whether entity masking comes from local
Presidio/spaCy recognition, explicit configured literals, both sources, or
neither. Automatic recognition uses Russian and English local spaCy PERSON NER
plus a targeted set of project/privacy recognizers. Generic organization/location
NER is intentionally excluded. Generic PERSON NER is limited to conservative
name-shaped spans, rejecting single-token guesses, ordinary lowercase prose, form
labels, and implausibly long fragments so normal document text is preserved. High-confidence
passenger-name layouts are handled by narrow supplemental recognizers. They
support same-line forms such as `NAME OF PASSENGER: SMITH/JOHN MR` and OCR
layouts where `Passenger name` or `Фамилия пассажира` is printed above the
passenger value. Explicit international `+` phone patterns
remain supported. `includedParagraphs`, `redactLines`, and `redactLineRanges`
remain independent structural redaction rules. `redactLines` masks configured OCR
lines from the top or bottom of 1-based PDF/raster pages. `redactLineRanges` masks
an inclusive OCR-line range beginning at a configured line fragment and ending at
an optional second fragment or the page end. Both remain active even when entity
detection is disabled.
Configured `included` and `includedAndReplaced` values use exact matching for
native TXT/DOCX/XLSX text. OCR-derived PDF/raster text additionally uses safe
normalized exact matching before optional fuzzy matching. OCR-only whitespace
and token boundaries are ignored while significant punctuation is retained, so
spaces around email punctuation, spaces inside long numbers, and Unicode dash
variants do not break an explicit mapping. When replacement rules overlap, the
longest configured source wins, and replacement spans take priority over
overlapping `included` masks. Fragment mappings inside one OCR word are composed
before raster rendering, so replacing `BBB -> CCC` inside
`AAA.BBB@GMAIL.COM` preserves the rest of the email as
`AAA.CCC@GMAIL.COM`. For source-format PDF/raster sanitization, long numeric
configured replacements also use a targeted table-oriented band OCR retry to
recover occurrences omitted by sparse-text OCR. Configured textual replacements
also get one exact table-oriented OCR retry in the selected page orientation so
an alternate segmentation can recover a word that sparse-text OCR misread or
omitted. The retry applies only explicit normalized-exact replacement mappings;
it does not enable automatic detection or fuzzy character edits. Character
content must still match unless `includedFuzzy` is enabled.

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
- `LineRedactionRule` for parsed page-edge structural redaction settings;
- `LineRangeRedactionRule` for parsed anchored OCR-line range settings;
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
