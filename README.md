# acc-source-docs-processor

`acc-source-docs-processor` is a local Python utility for processing scanned Russian accounting source documents.

The current released document processor focuses on scanned UPD transfer documents with status `1`. In the UPD form, status `1` means that the document acts both as an invoice and as a transfer document. In this README these input files are also called transfer documents or primary documents.

The program recursively scans a source folder, selects a document processor through the `--document-type` CLI parameter, detects supported primary documents, extracts the document number and document date, copies processed scans into a target folder, renames recognized files, and generates a CSV registry plus a text report.

Source files are never modified.

## Documentation

More detailed project documentation is available in:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — detailed architecture, components, OCR pipeline, decision logic, and recognition heuristics;
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — functional evolution and fixes by milestone;
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — current and planned tasks;
- [`AGENTS.md`](AGENTS.md) — rules for AI coding agents working on this project.

## Project layout

```text
acc-source-docs-processor/
├── README.md
├── AGENTS.md
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── main.py
├── run.sh
├── run_example.sh
├── archive.sh
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   └── ROADMAP.md
├── tests/
│   ├── unit/
│   └── integration/
└── source_docs_processor/
    ├── __init__.py
    ├── cli.py
    ├── file_ops.py
    ├── image_processing.py
    ├── models.py
    ├── ocr.py
    ├── processors.py
    └── upd_invoices_status_1/
        ├── __init__.py
        ├── extractor.py
        ├── image_processing.py
        ├── ocr.py
        └── processor.py
```

The repository/project folder uses hyphens. The internal Python package uses underscores so it can be imported normally:

```python
from source_docs_processor.cli import main
```

## What the program does

The current workflow is:

1. Recursively reads PNG/JPG/JPEG/TIFF/BMP scans from the source folder.
2. Sorts files in natural order so sequential scans are processed in the expected order.
3. Creates the selected document processor. The default processor is `upd_invoices_status_1`.
4. Detects UPD transfer documents with status `1`.
5. Extracts the document number and document date where possible.
6. Uses a dedicated document-number adjustment algorithm to improve recognition accuracy.
7. Uses the `Документ об отгрузке` row as a fallback source for the document number and date.
8. Tries 0, 90, 180, and 270 degree rotations and chooses the best recognition result.
9. Saves recognized sideways documents in the corrected orientation.
10. Detects likely continuation pages only after standalone UPD recognition fails.
11. Copies recognized, continuation, and unrecognized files to the target folder.
12. Preserves the source subfolder structure inside the target folder.
13. Generates an Excel-friendly CSV registry and a text report.
14. Optionally saves debug OCR crops for difficult documents.

The full recognition strategy is described in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Requirements

Python 3.10+ is recommended.

The program uses local OCR through Tesseract. Install Tesseract OCR with Russian and English language data.

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

### Python dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, create and activate a virtual environment using standard Windows commands, then run:

```bash
pip install -r requirements.txt
```

Tesseract must also be installed separately and available in `PATH`.

## Running tests

The project uses `pytest` for unit and integration tests. Test dependencies are developer-only dependencies, so install them from `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

`requirements.txt` intentionally contains only runtime dependencies needed to run the document processor. It does not include `pytest`.

Run the full current test suite from the project root:

```bash
python -m pytest -q
```

You can also run `pytest` directly if your shell resolves it from the active virtual environment.

The current test suite focuses on regression-prone logic around document-number adjustment, date selection, shipment-row parsing, continuation-page detection, filename generation, processor factory selection, and the generic folder-processing pipeline. The pipeline integration tests use a fake processor and synthetic tiny PNG files generated at test time, so they do not require Tesseract and do not include customer scanned accounting documents.

Markers are already configured for future OCR-heavy tests:

```bash
pytest -m ocr
pytest -m "not slow"
```

Future tests that depend on a real Tesseract installation should be marked with `@pytest.mark.ocr` and skipped when Tesseract is not available. Do not commit real customer/company scans to the repository; use anonymized or synthetic fixtures instead.

## Basic usage

Run the program from the project root:

```bash
python main.py --source "/path/to/scans"
```

The `--source` parameter points to the folder with input scans. Subfolders are processed recursively.

By default, the target folder is created in the current working directory, not inside the source scan folder:

```text
./передаточные_документы
```

The default output will contain:

```text
./передаточные_документы/
./передаточные_документы/передаточные_документы.csv
./передаточные_документы/передаточные_документы_report.txt
```


## Document type processor

The application is moving toward a more universal architecture. The currently available processor is:

```text
upd_invoices_status_1
```

It is also the default, so these two commands are equivalent:

```bash
python main.py --source "/path/to/scans"
python main.py --source "/path/to/scans" --document-type upd_invoices_status_1
```

Future document types should be added as separate processor packages and registered in the factory in `source_docs_processor/processors.py`.

## Custom target directory name

Use `--target-dir-name` to change the target folder name. This is the second most important parameter after `--source`.

```bash
python main.py --source "/path/to/scans" --target-dir-name "result_2023"
```

This creates the target folder in the current working directory:

```text
./result_2023/
./result_2023/result_2023.csv
./result_2023/result_2023_report.txt
```

The target directory name must be a folder name, not a full path. For example, use `result_2023`, not `/path/to/result_2023`.

## Custom output base folder

Use `--output` when the target folder should be created in a specific base directory:

```bash
python main.py --source "/path/to/scans" --output "/path/to/output" --target-dir-name "result_2023"
```

This creates:

```text
/path/to/output/result_2023/
/path/to/output/result_2023/result_2023.csv
/path/to/output/result_2023/result_2023_report.txt
```

## File naming

Recognized transfer documents are renamed using the extracted document number and date.

If both number and date are recognized:

```text
УПД_2548_от_27-12-2023.png
```

If only the document number is recognized:

```text
УПД_2548.png
```

If the document is recognized but the number is not recognized:

```text
УПД_без_номера.png
```

If the program detects a continuation page for the previous recognized document, the continuation page is named after the previous document with a page suffix:

```text
УПД_527_от_02-03-2023_2_страница.png
```

Duplicate filenames are resolved automatically by adding a numeric suffix. Unrecognized files are copied as is and keep their original file names.

## Output structure

The program preserves the source subfolder structure inside the target folder.

Example source structure:

```text
/path/to/scans/
├── 2023/
│   ├── scan_001.png
│   └── scan_002.png
└── 2024/
    └── scan_003.png
```

With the default target folder, the output will look like:

```text
./передаточные_документы/
├── 2023/
│   ├── УПД_2548_от_27-12-2023.png
│   └── scan_002.png
├── 2024/
│   └── scan_003.png
├── передаточные_документы.csv
└── передаточные_документы_report.txt
```

## CSV registry

The CSV registry is written inside the target folder.

For the default target folder:

```text
./передаточные_документы/передаточные_документы.csv
```

For a custom target folder:

```text
./result_2023/result_2023.csv
```

The registry uses semicolon delimiters and UTF-8 with BOM, so it opens correctly in Excel.

For recognized transfer documents and continuation pages, the CSV contains information such as:

- source file name;
- destination file name;
- recognition status;
- continuation-page flag;
- previous document file for continuation pages;
- UPD status;
- document number;
- document date;
- rotation used for recognition;
- seller and buyer names/identifiers where available;
- amounts where available;
- optional vehicle/loading/unloading fields when deep OCR is enabled;
- confidence score;
- warnings;
- text preview.

Only file names are written to the CSV, not full local paths.

For unrecognized files, only the first column is filled with the original source file name. This makes it clear that the file was processed and copied, but no reliable document data was extracted.

## Text report

Each run creates a report file inside the target folder.

For the default target folder:

```text
./передаточные_документы/передаточные_документы_report.txt
```

The report contains the same processing messages that are printed to the console, including run settings, per-file status, recognized document numbers and dates, selected rotations, and errors if any.

## Debug OCR crops

Use `--debug-crops` to save OCR crop images for analysis:

```bash
python main.py --source "/path/to/scans" --debug-crops
```

Debug files are written under the target folder:

```text
./передаточные_документы/_debug/
```

This mode is useful when a document number, date, or status is not recognized and crop coordinates need to be tuned.

## Other useful options

Select the current UPD status 1 processor explicitly:

```bash
python main.py --source "/path/to/scans" --document-type upd_invoices_status_1
```

Disable rotation attempts:

```bash
python main.py --source "/path/to/scans" --no-auto-rotate
```

Use slower full-page extraction for more optional details:

```bash
python main.py --source "/path/to/scans" --deep-ocr
```

Analyze files without copying images or writing the registry:

```bash
python main.py --source "/path/to/scans" --dry-run
```

## Common commands

Default run:

```bash
python main.py --source "/path/to/scans"
```

Custom target folder name:

```bash
python main.py --source "/path/to/scans" --target-dir-name "result_2023"
```

Custom output base folder:

```bash
python main.py --source "/path/to/scans" --output "/path/to/output" --target-dir-name "result_2023"
```

Debug problematic scans:

```bash
python main.py --source "/path/to/scans" --document-type upd_invoices_status_1 --debug-crops
```

Analyze without writing output:

```bash
python main.py --source "/path/to/scans" --dry-run
```

## Notes and limitations

The default processor is optimized for a specific family of UPD transfer documents. Recognition quality depends on scan quality, crop alignment, text contrast, and document layout.

The document-number adjustment algorithm significantly improves document-number detection for the supported template, but final business-critical submissions should still be reviewed by a human, especially for low-quality scans or documents listed in tax authority requests.
