# acc-source-docs-processor

`acc-source-docs-processor` is a local Python CLI for processing folders of scanned accounting source documents.

All processing is local. Source files are never modified, and scans are not uploaded to external services.

The application supports different document types. Each document type combines three independent components:

```text
CLI arguments
  -> DocumentTypeDefinition
      -> DocumentProcessor
      -> ProcessingWorkflow
      -> RegistryDefinition
```

- `DocumentProcessor` recognizes one image, extracts its fields, and determines the correct orientation.
- `ProcessingWorkflow` scans source folders and controls file processing: which files are copied, how output copies are named and organized, and which documents are included in registries and reports. Shared file-operation helpers perform the actual copying and image writing.
- `RegistryDefinition` defines registry columns and maps each extracted document to a row. CSV and XLSX writers serialize those rows into registry files.

## Supported document types

| Document type | Purpose | Output |
|---|---|---|
| `upd_invoices_status_1` | Russian UPD invoice-transfer documents with status `1` | Corrected (rotated to normal view), copied and renamed images; CSV registry; text report |
| `npd_receipts` | Russian NPD receipts issued by self-employed persons | Copied and renamed images; linked XLSX registry; text report |

The default document type is `upd_invoices_status_1`.

Supported source image formats are `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, and `.bmp`. Source folders are scanned recursively.

## Requirements

Python 3.10 or newer is required. Install Tesseract OCR with Russian and English language data.

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

Run commands from the project root.

```bash
python main.py --source "/path/to/scans"
```

Select a document type explicitly with `--document-type`:

```bash
python main.py \
  --source "/path/to/scans" \
  --document-type upd_invoices_status_1
```

Without `--output`, workflow output is created below the current working directory. `--target-dir-name` overrides the selected workflow's default folder name.

### UPD status 1

```bash
python main.py \
  --source "/path/to/upd-scans" \
  --output "/path/to/output" \
  --target-dir-name "result_2026" \
  --document-type upd_invoices_status_1
```

The UPD workflow:

1. recognizes UPD status `1` documents;
2. corrects orientation;
3. copies and renames recognized files;
4. copies unrecognized files unchanged;
5. attaches continuation pages conservatively;
6. preserves source subfolders;
7. writes a detailed semicolon-separated CSV registry and a text report.

The default output folder is `./передаточные_документы`.

Established filename examples:

```text
УПД_511_от_21-03-2023.png
УПД_511_от_21-03-2023_2_страница.png
```

### NPD receipts

```bash
python main.py \
  --source "/path/to/receipts" \
  --output "/path/to/output" \
  --target-dir-name "processed_receipts" \
  --document-type npd_receipts
```

The NPD receipt workflow:

1. scans source images recursively;
2. copies every image while preserving source subfolders;
3. renames recognized receipts as `<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>.<extension>`;
4. copies unrecognized images without renaming;
5. writes `реестр_чеков_нпд.xlsx` and a text report;
6. includes only recognized receipts in the XLSX registry.

The workbook contains exactly these columns, in order:

```text
target_file_name
source_file_name
дата
сумма
фио получателя суммы
номер_чека
ИНН получателя
комментарии о генерации
```

Only `target_file_name` is a hyperlink to the copied receipt. `source_file_name` remains plain text. The default output folder is `./чеки_нпд`.

## Common options

```bash
python main.py --source "/path/to/scans" --debug-crops
python main.py --source "/path/to/scans" --deep-ocr
python main.py --source "/path/to/scans" --no-auto-rotate
python main.py --source "/path/to/scans" --dry-run
```

Each workflow interprets output-related options according to its output policy.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Most tests use prepared OCR text, fake processors, independent fake workflows, custom registry definitions, and generated images. Real accounting scans and identifiers must not be committed to the repository.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Changelog](docs/CHANGELOG.md)
- [Roadmap](docs/ROADMAP.md)
- [Development rules](AGENTS.md)
