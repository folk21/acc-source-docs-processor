# acc-source-docs-processor

`acc-source-docs-processor` is a local Python CLI for folders of scanned accounting source documents.

The application uses a generic folder-processing pipeline and document-specific processors:

```text
CLI args -> processor factory -> selected processor -> scan/extract/copy/register/report
```

The currently released processor is:

```text
upd_invoices_status_1
```

It recognizes Russian UPD invoice-transfer documents with status `1`. Source files are never modified and no documents are uploaded to external services.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — processor boundary, generic model, registry schema, and OCR design;
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — completed changes and bug fixes;
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — current and planned work;
- [`AGENTS.md`](AGENTS.md) — development rules for AI coding agents.

## Project layout

```text
acc-source-docs-processor/
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── source_docs_processor/
│   ├── cli.py
│   ├── document_processor.py
│   ├── file_ops.py
│   ├── image_processing.py
│   ├── models.py
│   ├── ocr.py
│   ├── processors.py
│   └── upd_invoices_status_1/
│       ├── extractor.py
│       ├── image_processing.py
│       ├── ocr.py
│       └── processor.py
├── tests/
└── docs/
```

## Generic processor model

Shared code no longer contains UPD/invoice field names. `ExtractedDocument` provides common fields suitable for receipts, acts, invoices, and other source documents:

- document type, number, date, and datetime;
- issuer and recipient names/INN/KPP;
- amount without tax, tax amount, total amount, and currency;
- description, status, confidence, warnings, and OCR preview;
- continuation-page metadata;
- `extra_fields` for processor-specific values.

Each processor controls:

- recognition and OCR;
- default output directory name;
- output filename format;
- continuation-page support;
- additional CSV columns.

The UPD processor still produces established filenames such as:

```text
УПД_511_от_21-03-2023.png
УПД_511_от_21-03-2023_2_страница.png
```

## Requirements

Python 3.10+ is recommended. Install Tesseract OCR with Russian and English language data.

### macOS

```bash
brew install tesseract
brew install tesseract-lang
```

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run from the project root:

```bash
python main.py --source "/path/to/scans"
```

The default processor is `upd_invoices_status_1`, so the following command is equivalent:

```bash
python main.py \
  --source "/path/to/scans" \
  --document-type upd_invoices_status_1
```

The selected processor provides its default output directory name. For the UPD processor it remains:

```text
./передаточные_документы
```

Override it when needed:

```bash
python main.py \
  --source "/path/to/scans" \
  --target-dir-name "result_2026"
```

Choose a different output base directory:

```bash
python main.py \
  --source "/path/to/scans" \
  --output "/path/to/output" \
  --target-dir-name "result_2026"
```

Useful options:

```bash
python main.py --source "/path/to/scans" --debug-crops
python main.py --source "/path/to/scans" --deep-ocr
python main.py --source "/path/to/scans" --no-auto-rotate
python main.py --source "/path/to/scans" --dry-run
```

## Output

The target folder contains copied images, an Excel-friendly semicolon-separated CSV file, and a text report:

```text
result_2026/
├── ... copied documents ...
├── result_2026.csv
└── result_2026_report.txt
```

Source subfolder structure is preserved. Recognized rotated images are copied in the corrected orientation. Unrecognized files are copied unchanged.

## CSV registry

The common registry schema includes:

```text
source_file
destination_file
document_type
is_recognized
is_continuation_page
continued_from
status
document_number
document_date
document_datetime
issuer_name / issuer_inn / issuer_kpp
recipient_name / recipient_inn / recipient_kpp
amount_without_tax
tax_amount
total_amount
currency
description
rotation_degrees
confidence
warnings
error
text_preview
```

A processor may append its own columns. The UPD processor currently adds:

```text
request_number
request_date
vehicle
loading_datetime
unloading_datetime
```

Only file names are written to the registry, not absolute local paths.

## Adding a document type

A new processor should:

1. Create a separate package under `source_docs_processor/`.
2. Extend `BaseDocumentProcessor`.
3. Populate the generic `ExtractedDocument` fields.
4. Override filename generation only when a business-specific format is required.
5. Declare optional `registry_extra_columns` and place their values in `extra_fields`.
6. Register one factory entry in `source_docs_processor/processors.py`.
7. Add deterministic unit and integration tests.

The planned NPD receipt processor is not included in this version; this release prepares the shared architecture for it.

## Tests

Install developer dependencies and run the suite:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Most tests use prepared OCR text, fake processors, or synthetic tiny images. Real customer scans must not be committed to the repository.
