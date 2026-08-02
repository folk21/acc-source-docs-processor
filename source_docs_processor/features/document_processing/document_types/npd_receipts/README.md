# NPD receipts

Recognizes scanned Russian NPD receipts, copies every source image, renames
recognized receipts, preserves relative folders, and writes the compact linked
`npd_receipts_registry.xlsx` workbook.

## Package contract

- `definition.py` publishes the complete registered definition and metadata;
- `processor.py` recognizes one receipt image;
- `workflow.py` owns copying, naming, output selection, and workbook generation;
- `registry.py` defines the compact XLSX schema;
- `_internal/` owns receipt OCR, extraction, and local NPD QR parsing.

## User documentation

- [Installation](../../../../../docs/INSTALLATION.md)
- [Usage](../../../../../docs/USAGE.md#npd-receipts)

## Development

Read [AGENTS.md](AGENTS.md) before changing this document type.

```bash
make test-npd
make check
```
