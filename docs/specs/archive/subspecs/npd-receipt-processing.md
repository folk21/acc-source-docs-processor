---
type: Specification
title: NPD receipt processing
description: Reconstructed change contract for scanned NPD receipt recognition, copy/rename output, and the compact linked XLSX registry.
document_role: subspec
spec_status: completed
---

# NPD receipt processing

## Status

Completed and released. Reconstructed from `0.9.1`, `0.11.1`, `0.11.2`, current
NPD tests, and the local NPD development guide.

## Feature scope

- `PROCESSING.NPD_RECEIPTS`

## Goal

Add a document type for scanned NPD receipts without changing scanned-UPD behavior
or embedding NPD rules in the shared framework.

## Reconstructed requirements

- Recognize NPD receipts from local raster images and keep all NPD OCR/extraction
  logic inside the owning document-type package.
- Treat the first INN in receipt order as the self-employed issuer and preserve a
  second INN as recipient data when present.
- Support issuer names on one line or split across surname and first-name/
  patronymic lines.
- Accept a receipt number only after an explicit receipt-number label.
- Copy every supported source image; rename only recognized receipts.
- Use `<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>` naming for
  recognized copies.
- Preserve relative source subfolders.
- Include only recognized receipts in `npd_receipts_registry.xlsx`.
- Keep the compact eight-column workbook and portable hyperlink to the copied
  target file; keep source filename plain text.
- Do not generate a text report.
- With explicit `--output` and no target directory name, write directly into that
  output directory.
- Keep the local QR decoder/parser private; initial delivery did not integrate it
  into recognition.

## Validation evidence

Current tests cover extraction, filename generation, QR URL parsing, workbook
columns/hyperlinks, copying, and registered workflow behavior.
