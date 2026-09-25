# Expense reconciliation feature

This independent feature matches local supporting expense documents to an XLSX
bank statement and writes `expense_reconciliation.xlsx`.

It is intentionally not a document-processing type. A reconciliation run uses
multiple receipt/ticket files plus a separate bank statement and makes aggregate
cross-document matching decisions.

## Inputs

- source folder: PDF, PNG, JPG/JPEG, BMP, TIFF receipt and ticket files;
- statement: XLSX exported in the supported 1C account-card layout;
- output folder: receives one reconciliation workbook.

PDF native text is preferred. Raster files and PDFs without a usable amount use
local Tesseract OCR. The primary amount is the maximum recognized two-decimal
money value. Date and passenger name extraction are optional and are used only
as secondary matching signals.

## Matching

Supported exact amount relationships are:

```text
1 document <-> 1 statement position
1 document <-> 2 statement positions
```

The matcher selects a global non-overlapping set with this priority:

1. covered statement amount;
2. covered statement positions;
3. matched documents;
4. date agreement;
5. person agreement;
6. one-to-one simplicity.

## Output workbook

`Reconciliation` contains one row per statement position with the requested
employee, statement date/amount, found state, position within a multi-position
match, supporting filename, and supporting-document amount. A summary block
contains totals, difference, unmatched counts, and unmatched amounts.

`Documents` contains every input file, extracted fields, match state, number of
covered statement positions, and extraction warnings. File cells use relative
local hyperlinks when possible.

## CLI

```bash
python main.py reconcile-expenses \
  --source "/path/to/receipts-and-tickets" \
  --statement "/path/to/payments.xlsx" \
  --output "/path/to/output"
```

## Validation

```bash
make test-expense-reconciliation
make check
```
