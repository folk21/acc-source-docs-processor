# Incoming purchase documents

## Purpose

Read incoming PDF/DOCX purchase documents for accountant entry into 1C. The
current implementation recognizes UPD status `1`, extracts document and item data,
links original files, and writes a task-oriented workbook plus report.

## Framework-facing modules

The package root contains only integration modules:

- `definition.py` publishes the complete registered definition;
- `processor.py` dispatches one PDF or DOCX source file;
- `workflow.py` owns recursive task-workbook behavior;
- `registry.py` defines document, item, review, and metadata rows.

## Private implementation

`_internal/readers.py` reads native PDF/DOCX content and OCR fallback pages.
`_internal/extractor.py` recognizes UPD status `1` and extracts document, party,
item, total, and validation data. These modules are private to this document type.

## Allowed dependencies

Private modules may use public document models, root framework contracts,
shared `document_processing._internal` helpers, and feature-neutral `core`
primitives. They must not import another document type,
anonymization, `definition.py`, `workflow.py`, or `registry.py`.

## Key invariants

- Prefer native PDF/DOCX text and tables before OCR fallback.
- Reject explicit UPD status `2` and unsupported legacy `.doc` files.
- Keep one document task linked to item rows through hidden `task_id` values.
- Keep incomplete files visible in `Documents` and `Review`.
- Keep numeric OKEI codes separate from textual units.
- Report arithmetic conflicts without silently replacing extracted values.

## Validation

```bash
python -m pytest -q \
  tests/unit/incoming_purchase_documents \
  tests/integration/incoming_purchase_documents
```
