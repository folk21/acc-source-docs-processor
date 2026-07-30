# Scanned UPD status 1

## Purpose

Recognize scanned Russian UPD invoice-transfer documents with status `1`, correct
orientation, extract document identity, copy and rename pages, attach conservative
continuations, and write the detailed CSV/report output.

## Public definition

`definition.py` exports `DOCUMENT_TYPE` and `DEFINITION`. The central catalog must
not import processor, workflow, or registry classes directly. `processor.py` is the
file-level recognizer and `extractor.py` is the single document-assembly entry point.

## Extraction modules

- `extractor.py` assembles `ExtractedDocument` and must not contain detailed parsing rules.
- `identity_extraction.py` reconciles header, targeted-crop, and shipment-row identity sources.
- `number_extraction.py` owns number normalization, short-value replacement, and trailing over-read correction.
- `date_extraction.py` owns date parsing, crop recovery, source selection, and form-template date rejection.
- `shipment_row.py` parses the repeated `Документ об отгрузке` number/date row.
- `continuation.py` scores sparse continuation pages while vetoing normal UPD headers.
- `classification.py` classifies primary and continuation pages.
- `party_extraction.py` extracts seller and buyer names plus INN/KPP values.
- `financial_extraction.py` extracts normalized net, VAT, and gross amounts.
- `transport_extraction.py` extracts the service row and transport metadata.
- `confidence.py` owns the practical recognition score.
- `normalization.py` contains shared OCR whitespace normalization for this package.

Compatibility imports remain available from `extractor.py`, but new tests and code
should import focused helpers from their owning modules.

## Allowed dependencies

May import shared modules from `features.document_processing`. Must not import
another concrete document type or the anonymization feature. Focused extraction
modules may import one another only when their responsibility requires it; none may
import workflow or registry policy.

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
