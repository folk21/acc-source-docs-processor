# Scanned UPD status 1

## Purpose

Recognize scanned Russian UPD invoice-transfer documents with status `1`, correct
orientation, extract document identity, copy and rename pages, attach conservative
continuations, and write the detailed CSV/report output.

## Framework-facing modules

The package root is an integration map:

- `definition.py` exports `DOCUMENT_TYPE` and `DEFINITION`;
- `processor.py` recognizes one image and delegates OCR and extraction;
- `workflow.py` owns folder, copy, naming, continuation, and report behavior;
- `registry.py` defines the detailed CSV schema and row mapping.

The central catalog imports only `definition.py`.

## Private implementation

`_internal/` contains document-specific OCR and parsing details:

- `extractor.py` assembles `ExtractedDocument` and warnings;
- `identity_extraction.py`, `number_extraction.py`, `date_extraction.py`, and
  `shipment_row.py` reconcile document identity sources;
- `classification.py`, `continuation.py`, and `confidence.py` classify pages;
- `party_extraction.py`, `financial_extraction.py`, and
  `transport_extraction.py` extract focused field groups;
- `image_processing.py` and `ocr.py` own UPD crop and OCR behavior.

These modules are private to this document type. Other document types and shared
processing modules must not import them.

## Allowed dependencies

Private modules may import root framework contracts, strict document
normalizers from `features.document_processing._internal`, and neutral primitives from
`source_docs_processor.core`. They must not import another concrete document type,
anonymization, `definition.py`, `workflow.py`, or `registry.py`.

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
