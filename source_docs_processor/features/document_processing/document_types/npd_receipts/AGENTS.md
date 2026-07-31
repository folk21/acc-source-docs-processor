# NPD receipt development guide

This file narrows the parent development rules for the `npd_receipts` document
type.

## Preferred scope

Keep NPD-specific changes inside this package and its matching tests. Shared
changes are allowed only in document-processing framework modules,
document-processing `_internal/`, or `core` when the contract is genuinely
reusable. Do not modify anonymization or another document type.

## Package boundary

- `definition.py`, `processor.py`, `workflow.py`, and `registry.py` are the
  framework-facing integration modules.
- `_internal/` owns receipt OCR, extraction, and NPD QR parsing.
- Private modules must not import `definition.py`, `workflow.py`, or
  `registry.py`.

## Protected behavior

- Copy every source image and rename only recognized receipts.
- Include only recognized receipts in `npd_receipts_registry.xlsx`.
- Do not generate a text report.
- Preserve the compact eight-column workbook and portable file hyperlinks.
- Require an explicit label before accepting a receipt number.
- Keep QR parsing local and report future QR/OCR conflicts explicitly.

## Tests

Put OCR/extraction/QR tests under `tests/unit/npd_receipts/_internal/`. Keep
filename/framework tests at the document-type test root and workflow tests under
integration.

Run the focused suite while developing:

```bash
make test-npd
```

Run `make test-document-processing` when shared processing code changes, and run
`make check` before completion.
