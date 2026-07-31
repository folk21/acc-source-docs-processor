# NPD receipts

## Purpose

Recognize scanned Russian NPD receipts, copy every source image, rename recognized
receipts, preserve relative folders, and write the compact linked XLSX registry.

## Framework-facing modules

The package root contains only integration modules:

- `definition.py` publishes the complete registered definition;
- `processor.py` recognizes one receipt image;
- `workflow.py` owns copying, naming, output selection, and workbook generation;
- `registry.py` defines the compact XLSX columns and row mapping.

## Private implementation

`_internal/` contains receipt OCR, field extraction, and local NPD QR parsing.
These modules are private to NPD receipts and must not be imported by shared
processing code or another document type.

## Allowed dependencies

Private modules may use root framework contracts, shared
`document_processing._internal` helpers, and feature-neutral `core` primitives. They must not import another document type, anonymization,
`definition.py`, `workflow.py`, or `registry.py`.

## Key invariants

- Copy all source images and rename only recognized receipts.
- Include only recognized receipts in `npd_receipts_registry.xlsx`.
- Do not generate a text report.
- Preserve the eight-column workbook contract and filename pattern.
- Require an explicit receipt-number label.
- Keep QR parsing local and report future QR/OCR conflicts explicitly.

## Development guide

Read the local [`AGENTS.md`](AGENTS.md) before changing this document type.

## Validation

```bash
make test-npd
```

Run `make test-document-processing` when shared processing code changes,
and run `make check` before completion.
