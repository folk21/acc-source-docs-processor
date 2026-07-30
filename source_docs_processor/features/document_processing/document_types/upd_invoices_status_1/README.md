# Scanned UPD status 1

## Purpose

Recognize scanned Russian UPD invoice-transfer documents with status `1`, correct
orientation, extract document identity, copy and rename pages, attach conservative
continuations, and write the detailed CSV/report output.

## Public definition

`definition.py` exports `DOCUMENT_TYPE` and `DEFINITION`. The central catalog must
not import processor, workflow, or registry classes directly.

## Allowed dependencies

May import shared modules from `features.document_processing`. Must not import
another concrete document type or the anonymization feature.

## Key invariants

- Prefer targeted crops and the `Документ об отгрузке` row over global OCR.
- Preserve short-number and trailing over-read corrections.
- Reject the static form date `02-04-2021` when it comes from template text.
- Recognize a standalone first page before continuation heuristics.
- Preserve rotation, debug crops, output naming, and continuation suffixes.

## Validation

```bash
python -m pytest -q \
  tests/unit/upd_invoices_status_1 \
  tests/integration/upd_invoices_status_1
```
