# Scanned UPD status 1

Recognizes scanned Russian UPD invoice-transfer documents with status `1`,
corrects orientation, extracts document identity, copies and renames pages,
attaches conservative continuations, and writes the detailed CSV and text report.

## Package contract

- `definition.py` publishes the complete registered definition and metadata;
- `processor.py` recognizes one image and delegates private OCR/extraction;
- `workflow.py` owns folder traversal, copy/naming, continuations, and reports;
- `registry.py` defines the detailed CSV schema;
- `_internal/` owns UPD crops, OCR, extraction, source reconciliation,
  classification, confidence, and field-specific rules.

## User documentation

- [Installation](../../../../../docs/INSTALLATION.md)
- [Usage](../../../../../docs/USAGE.md#scanned-upd-status-1)

## Development

Read [AGENTS.md](AGENTS.md) before changing this document type.

```bash
make test-upd
make check
```
