---
type: Specification
title: Incoming purchase document task workbooks
description: Reconstructed change contract for PDF/DOCX incoming UPD status 1 extraction and accountant-oriented task workbooks.
document_role: subspec
spec_status: completed
---

# Incoming purchase document task workbooks

## Status

Completed and released. Reconstructed from releases `0.10.0` through `0.10.2` and
current package invariants.

## Feature scope

- `PROCESSING.INCOMING_PURCHASE_DOCUMENTS`

## Goal

Process incoming electronic UPD status `1` files for later manual entry into 1C,
using native document structure before OCR and producing a reviewable task
workbook rather than copied source files.

## Reconstructed requirements

- Support PDF and DOCX; reject unsupported legacy `.doc` files.
- Read native PDF text/tables first and use OCR fallback when useful text is not
  available; `--deep-ocr` may force additional PDF OCR.
- Read DOCX paragraphs and tables directly.
- Extract UPD number/date/status, seller/buyer identifiers, totals, and repeating
  goods/service rows.
- Reject explicit UPD status `2`.
- Exclude official UPD column-designator rows from item extraction.
- Keep numeric OKEI codes distinct from textual unit names.
- Validate line and document arithmetic and surface conflicts as review warnings
  without silently replacing extracted values.
- Create a task workbook with `Documents`, `Items`, `Review`, and hidden
  `_metadata` sheets.
- Use hidden stable `task_id` values to link document and item rows.
- Keep incomplete documents visible for manual review.
- Use a `Нет`/`Да` document-level processed dropdown.
- Link to original PDF/DOCX files instead of copying them.
- Use duplicate-safe workbook names so repeated runs do not overwrite accountant
  state.
- With explicit `--output`, write the workbook/report directly to that directory.

## Validation evidence

Synthetic PDF/DOCX and workbook integration tests protect source linking, item
filtering, unit normalization, task identifiers, validation, and output layout.
