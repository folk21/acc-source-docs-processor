# Scanned UPD status 1 development guide

This file narrows the parent development rules for the
`upd_invoices_status_1` document type.

## Preferred scope

Keep UPD-specific changes inside this package and its matching tests. Shared
changes are allowed only in document-processing framework modules,
document-processing `_internal/`, or `core` when the contract is genuinely
reusable. Do not modify anonymization or another document type.

## Package boundary

- `definition.py`, `processor.py`, `workflow.py`, and `registry.py` are the
  framework-facing integration modules.
- `_internal/` owns crop geometry, OCR, extraction, source reconciliation,
  classification, continuation detection, confidence, and field-specific rules.
- Private modules must not import `definition.py`, `workflow.py`, or
  `registry.py`.

## Protected behavior

- Prefer targeted crops and the `Документ об отгрузке` row over global OCR.
- Replace suspicious short header numbers with reliable shipment-row values.
- Correct trailing OCR over-read only when a shorter reliable candidate exists.
- Reject template date `02-04-2021` when it comes from form text.
- Detect a standalone first page before continuation heuristics.
- Preserve rotation, debug crops, continuation suffixes, output naming, CSV, and
  report behavior.

## Tests

Put parser/OCR tests under
`tests/unit/upd_invoices_status_1/_internal/`. Keep filename/framework tests at
the document-type test root and folder workflow tests under integration.

Run the focused suite while developing:

```bash
make test-upd
```

Run `make test-document-processing` when shared processing code changes, and run
`make check` before completion.
