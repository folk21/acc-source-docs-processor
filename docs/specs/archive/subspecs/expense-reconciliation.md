---
type: Specification
title: Expense receipt/ticket reconciliation
description: Reconstructed change contract for matching local receipt/ticket files to supported XLSX bank-statement positions and producing an accountant review workbook.
document_role: subspec
spec_status: completed
---

# Expense receipt/ticket reconciliation

## Status

Completed and released in `0.28.0`; local Streamlit integration followed in
`0.28.1`.

## Feature scope

- `RECONCILIATION.EXPENSES`
- `PLATFORM.CLI`
- `PLATFORM.PUBLIC_APIS`
- `PLATFORM.STREAMLIT_UI`

## Goal

Reconcile one folder of local receipt/ticket evidence against one supported XLSX
bank statement without forcing the two-input aggregate workflow into the
single-document processing framework.

## Reconstructed requirements

- Keep reconciliation as an independent feature and CLI operation, not a
  `DocumentTypeDefinition`.
- Discover supported PDF/raster evidence recursively.
- Prefer native PDF text and use local OCR fallback when a usable amount is not
  available.
- Extract the maximum valid two-decimal money value while excluding full date
  tokens, plus optional date/passenger hints and lightweight document class.
- Parse the supported 1C-style account-card XLSX structurally from cells without
  OCR.
- Use exact `Decimal` amounts for matching.
- Support one document to one statement position and one document to two
  positions whose values sum exactly.
- Optimize globally for covered statement amount, then covered positions, then
  matched documents; use optional date/person hints only to choose among duplicate
  equal-amount rows.
- Missing names/dates must not block an exact amount match.
- Write `expense_reconciliation.xlsx` with statement-centric `Reconciliation` and
  document-centric `Documents` sheets, local relative hyperlinks, unmatched
  highlighting, totals, differences, and review counts.
- Count each supporting document once in aggregate totals even when it covers two
  statement positions.
- Preserve all source files.
- Expose a public API, CLI adapter, and privacy-safe synchronous progress.
- Streamlit must show only aggregate counts and the portable workbook name, not
  extracted names, dates, amounts, or row contents.

## Validation evidence

Deterministic unit/integration tests cover statement parsing, extraction, exact
matching, aggregate optimization, workbook output, CLI/public APIs, and UI
forwarding/privacy behavior.
