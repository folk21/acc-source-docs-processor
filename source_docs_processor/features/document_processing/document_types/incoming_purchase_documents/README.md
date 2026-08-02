# Incoming purchase documents

Reads incoming PDF/DOCX purchase documents for accountant entry into 1C. The
current implementation recognizes UPD status `1`, extracts document and item
data, links original files, and writes a task-oriented workbook plus report.

## Package contract

- `definition.py` publishes the complete registered definition and metadata;
- `processor.py` dispatches one PDF or DOCX file;
- `workflow.py` owns recursive task-workbook behavior and source links;
- `registry.py` defines document, item, review, and metadata rows;
- `_internal/readers.py` owns native PDF/DOCX reading and OCR fallback;
- `_internal/extractor.py` owns recognition, extraction, totals, and validation.

## User documentation

- [Installation](../../../../../docs/INSTALLATION.md)
- [Usage](../../../../../docs/USAGE.md#incoming-purchase-documents)

## Development

Read [AGENTS.md](AGENTS.md) before changing this document type.

```bash
make test-incoming-purchase-documents
make check
```
