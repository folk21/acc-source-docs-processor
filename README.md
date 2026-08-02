# acc-source-docs-processor

`acc-source-docs-processor` is a local Python application for processing and
anonymizing accounting source documents.

All processing runs on the local computer. Source files are never modified and
are not uploaded to external services.

## Capabilities

The application provides two operations:

- `process` recognizes supported accounting documents, extracts fields, and
  creates workflow-specific files and registries;
- `anonymize` creates privacy-safe copies of PDF, DOCX, TXT, and raster-image
  files according to configurable masking and replacement rules.

An optional local Streamlit interface is available for browser-based use on the
same computer. It exposes anonymization plus all three registered document-
processing workflows through the same public Python APIs used by the CLI.

### Supported processing types

| Document type | Input | Main output |
|---|---|---|
| `upd_invoices_status_1` | PNG, JPG, TIFF, BMP | Corrected and renamed images, CSV registry, text report |
| `npd_receipts` | PNG, JPG, TIFF, BMP | Copied and renamed images, linked XLSX registry |
| `incoming_purchase_documents` | PDF, DOCX | Task-oriented XLSX workbook and text report |

The default processing type is `upd_invoices_status_1`.

## Install

Start with the platform-specific guide:

- [Installation on Windows, Linux, and macOS](docs/INSTALLATION.md)

It covers cloning or downloading the project from GitHub, Python virtual
environments, Tesseract OCR, Russian language data, CLI dependencies, and the
optional Streamlit UI.

## Quick start

Run commands from the project root with the virtual environment activated.

### Local Streamlit interface

```bash
python -m streamlit run streamlit_app.py -- --lang ru
```

Use `-- --lang en` for English. The UI works with local filesystem paths; it
does not upload documents through the browser.

### Process documents

```bash
python main.py process \
  --source "/path/to/documents" \
  --output "/path/to/output" \
  --document-type npd_receipts
```

### Anonymize documents

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --config "config/examples/anonymization.ini"
```

See [Usage](docs/USAGE.md) for all document types, processing options,
anonymization configuration, output behavior, and example scripts.

## Privacy and review

OCR, document recognition, and PII detection are heuristic. Review generated
files before using them or sharing them with third parties, especially when
source documents contain handwriting, stamps, signatures, low-quality scans, or
unusual layouts.

Anonymization is fail-closed for unsupported or opaque content: the application
does not silently copy such content unchanged into the anonymized output.

## Development

Install development dependencies and run the complete validation suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-ui.txt
make check
```

Focused validation targets are listed by:

```bash
make help
```

## Documentation

- [Installation](docs/INSTALLATION.md) — Windows, Linux, macOS, CLI, and Streamlit setup
- [Usage](docs/USAGE.md) — commands, options, configurations, and outputs
- [Architecture](docs/ARCHITECTURE.md) — component boundaries and ownership
- [Roadmap](docs/ROADMAP.md) — active and planned work
- [Changelog](docs/CHANGELOG.md) — completed changes by release
- [Development rules](AGENTS.md) — cross-project engineering rules
- [Anonymization feature](source_docs_processor/features/anonymization/README.md)
- [Document-processing feature](source_docs_processor/features/document_processing/README.md)
- [Local Streamlit adapter](source_docs_processor/ui/README.md)
