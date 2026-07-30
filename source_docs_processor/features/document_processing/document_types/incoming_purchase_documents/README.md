# Incoming purchase documents

## Purpose

Read incoming PDF/DOCX purchase documents for accountant entry into 1C. The
current implementation recognizes UPD status `1`, extracts document and item data,
links original files, and writes a task-oriented workbook plus report.

## Public definition

`definition.py` exports `DOCUMENT_TYPE` and `DEFINITION`. The central catalog must
not import processor, workflow, or registry classes directly.

## Allowed dependencies

May import shared modules from `features.document_processing`. Must not import
another concrete document type or the anonymization feature.

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
