# acc-source-docs-processor

`acc-source-docs-processor` is a local Python CLI for folders of scanned accounting source documents.

The application now separates three responsibilities:

```text
CLI args
  -> document type definition
      -> document processor
      -> folder workflow
      -> registry definition
```

The currently released document types are:

```text
upd_invoices_status_1
npd_receipts
```

It recognizes Russian UPD invoice-transfer documents with status `1`. Source files are never modified, and no scans are uploaded to external services.

## Why the architecture is split

A document processor answers only:

- whether one image is a supported document;
- which orientation is correct;
- which fields can be extracted.

A workflow decides folder-level actions such as:

- copy or do not copy files;
- rename or preserve filenames;
- create an output folder or write beside source files;
- include unrecognized files;
- generate a report.

A registry definition decides:

- CSV columns;
- which extracted values are written to each column;
- how file references are represented.

This allows each document type to select its own copy, rename, and registry behavior without placing folder rules inside OCR code.

## Project layout

```text
source_docs_processor/
├── cli.py
├── document_processor.py
├── document_types.py
├── file_ops.py
├── image_processing.py
├── models.py
├── ocr.py
├── processors.py
├── registry/
│   ├── base.py
│   └── csv_writer.py
├── workflows/
│   ├── base.py
│   └── copy_and_register.py
└── upd_invoices_status_1/
    ├── extractor.py
    ├── image_processing.py
    ├── ocr.py
    ├── processor.py
    ├── registry.py
    └── workflow.py
```

Detailed design is described in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

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

The default document type is `upd_invoices_status_1`:

```bash
python main.py \
  --source "/path/to/scans" \
  --document-type upd_invoices_status_1
```

The UPD workflow creates this output folder by default:

```text
./передаточные_документы
```

Override its name or base directory:

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

The meaning of output-related options is defined by the selected workflow. The current UPD workflow uses them exactly as before.

## Current UPD behavior

The UPD workflow:

1. scans image files recursively;
2. recognizes UPD status `1` documents;
3. corrects orientation;
4. copies and renames recognized files;
5. copies unrecognized files unchanged;
6. attaches continuation pages conservatively;
7. preserves source subfolders;
8. writes a detailed CSV registry and text report.

Established filenames remain unchanged:

```text
УПД_511_от_21-03-2023.png
УПД_511_от_21-03-2023_2_страница.png
```

## Adding a document type

A new type should provide:

1. a processor package for file-level OCR and extraction;
2. a workflow, either reusable or document-specific;
3. a registry definition with its own columns and row mapping;
4. one `DocumentTypeDefinition` entry in `source_docs_processor/document_types.py`;
5. deterministic tests.

## NPD receipt behavior

Run the receipt workflow with:

```bash
python main.py \
  --source "/path/to/receipts" \
  --output "/path/to/output" \
  --target-dir-name "processed_receipts" \
  --document-type npd_receipts
```

The workflow copies every source image into the target directory. Recognized
receipts use the filename pattern
`<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>.<extension>`;
unrecognized images are copied without renaming. The target directory also
contains `реестр_чеков_нпд.xlsx`. Only the `target_file_name` cell is a hyperlink
to the copied receipt; `source_file_name` remains plain text.

The workbook contains exactly these columns in order: `target_file_name`,
`source_file_name`, receipt date, amount, self-employed payee full name, receipt
number, self-employed payee INN, and generation comments. The first INN in
receipt order is treated as the self-employed payee INN. Full names are
recognized both on one line and as a surname line followed by a
first-name/patronymic line.

Without `--output`, the target directory is created below the current working
directory. Without `--target-dir-name`, its name is `чеки_нпд`.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Most tests use prepared OCR text, fake processors, independent fake workflows, custom registry definitions, and synthetic images. Real accounting scans must not be committed to the repository.
