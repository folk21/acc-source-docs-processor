---
type: Specification
title: Fail-closed XLSX anonymization
description: Reconstructed change contract for sanitizing spreadsheet content while preserving numeric/formula behavior and rejecting unsafe opaque workbook structures.
document_role: subspec
spec_status: completed
---

# Fail-closed XLSX anonymization

## Status

Completed and released in `0.27.3`.

## Feature scope

- `ANONYMIZATION.XLSX`
- `ANONYMIZATION.LOCAL_REDACTION`

## Goal

Extend source-format anonymization to XLSX while preserving spreadsheet semantics
that can be carried safely and failing closed on content that could retain private
data invisibly.

## Reconstructed requirements

- Sanitize visible and hidden cell text, comments, headers/footers, workbook
  metadata, drawing/chart text, and supported embedded raster images.
- Preserve numeric cells and formulas when they are safe.
- Keep configured matching exact for native XLSX text rather than applying OCR
  fuzzy matching.
- Fail closed on external relationships, macros/active or embedded objects,
  unsupported media, pivot/query caches, and other opaque content that can retain
  unsanitized data.
- Reject detected PII inside formulas or structural workbook names rather than
  copying it unchanged.
- Do not apply page-continuation semantics such as `includedParagraphs` to
  workbook cells.
- Keep XLS/XLSM unsupported unless a later explicit design adds safe handling.

## Validation evidence

Unit/integration regressions protect numeric/formula preservation, hidden-sheet
sanitization, embedded raster handling, and fail-closed unsafe-workbook cases.
