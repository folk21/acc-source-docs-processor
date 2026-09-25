# Expense reconciliation development guide

This file narrows the root `AGENTS.md` rules for
`source_docs_processor/features/expense_reconciliation/`.

## Scope

Use this feature for reconciling local receipt and ticket files with one XLSX
bank statement. Keep document extraction, statement parsing, exact-amount
matching, workbook generation, and orchestration inside this feature unless a
technical primitive is genuinely feature-neutral.

Do not add this workflow as a document-processing `DocumentTypeDefinition`.
Reconciliation depends on two independent input sources and aggregate matching,
so it remains an independent operation.

## Public surface

- `api.py` owns the programmatic entry point and public result/data contracts.
- `command.py` owns argparse integration and privacy-safe console progress.
- `__init__.py` re-exports only the supported package API.

Everything under `_internal/` is private to this feature.

## Invariants

- Keep all processing local and preserve source files.
- Supporting documents are PDF or raster images; prefer native PDF text and use
  OCR only when a usable amount is not available.
- The primary document amount heuristic is the maximum valid two-decimal money
  value after excluding full date tokens.
- Dates and passenger names are optional secondary matching signals and must not
  prevent an exact amount match.
- Statement parsing targets the supported 1C-style XLSX account-card layout and
  reads cells directly rather than applying OCR.
- Matching supports one document to one statement position and one document to
  two statement positions whose amounts sum exactly.
- Matching uses `Decimal`, never binary floating-point equality.
- The global objective prioritizes covered statement amount before row count and
  secondary date/person signals.
- The reconciliation sheet is statement-centric. One two-position match repeats
  the supporting file and document amount on both statement rows and uses the
  `Позиция` column to show 1/2.
- Aggregate document totals count every input document only once.
- Never log extracted person names, statement descriptions, or accounting values.
- Use synthetic names, amounts, PDFs, and XLSX workbooks in tests.
- Unit tests must not call real Tesseract.

## Validation

Run the focused suite while developing:

```bash
make test-expense-reconciliation
```

Run public and architecture contracts after changing exports or CLI composition:

```bash
make test-public-api
make test-architecture
```

Run the complete project validation before completion:

```bash
make check
```
