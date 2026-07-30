# NPD receipts

## Purpose

Recognize scanned Russian NPD receipts, copy every source image, rename recognized
receipts, preserve relative folders, and write the compact linked XLSX registry.

## Public definition

`definition.py` exports `DOCUMENT_TYPE` and `DEFINITION`. The central catalog must
not import processor, workflow, or registry classes directly.

## Allowed dependencies

May import shared modules from `features.document_processing`. Must not import
another concrete document type or the anonymization feature.

## Key invariants

- Copy all source images and rename only recognized receipts.
- Include only recognized receipts in `npd_receipts_registry.xlsx`.
- Do not generate a text report.
- Preserve the eight-column workbook contract and filename pattern.
- Require an explicit receipt-number label.
- Keep QR parsing local and report future QR/OCR conflicts explicitly.

## Validation

```bash
python -m pytest -q \
  tests/unit/npd_receipts \
  tests/integration/npd_receipts
```
