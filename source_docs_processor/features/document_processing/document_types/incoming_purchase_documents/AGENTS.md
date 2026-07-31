# Incoming purchase-document development guide

This file narrows the parent development rules for the
`incoming_purchase_documents` document type.

## Preferred scope

Keep source-reader and extraction changes inside this package and its matching
tests. Shared changes are allowed only in document-processing framework modules,
document-processing `_internal/`, or `core` when the contract is genuinely
reusable. Do not modify anonymization or another document type.

## Package boundary

- `definition.py`, `processor.py`, `workflow.py`, and `registry.py` are the
  framework-facing integration modules.
- `_internal/readers.py` owns native PDF/DOCX reading and OCR fallback.
- `_internal/extractor.py` owns recognition, document/item extraction, totals,
  and validation.
- Private modules must not import `definition.py`, `workflow.py`, or
  `registry.py`.

## Protected behavior

- Prefer native PDF/DOCX text and tables before OCR fallback.
- Reject explicit UPD status `2` and unsupported legacy `.doc` files.
- Link document and item rows through hidden `task_id` values.
- Keep incomplete documents visible in both task and review outputs.
- Keep numeric OKEI codes separate from textual units.
- Report arithmetic conflicts without silently replacing extracted values.

## Tests

Put reader/extractor tests under
`tests/unit/incoming_purchase_documents/_internal/`. Keep framework tests at the
document-type test root and registered workflow tests under integration.

Run the focused suite while developing:

```bash
make test-incoming-purchase-documents
```

Run `make test-document-processing` when shared processing code changes, and run
`make check` before completion.
