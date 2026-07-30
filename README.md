# acc-source-docs-processor

`acc-source-docs-processor` is a local Python CLI for processing accounting source documents.

All processing is local. Source files are never modified and are not uploaded to external services.

The CLI is organized by operation:

```text
python main.py process ...
python main.py anonymize ...
```

`process` recognizes supported accounting documents. `anonymize` creates local, redacted copies of supported files from one directory tree into another.

Each processable document type combines three independent components:

```text
process command
  -> DocumentTypeDefinition
      -> Processor
      -> ProcessingWorkflow
      -> RegistryDefinition
```

- A processor recognizes and extracts one image or source file.
- A workflow owns recursive folder behavior, copying, output selection, and reports.
- A registry definition owns tabular schemas and row mapping.
- Generic CSV and XLSX writers serialize document-specific registry data.

Internal code is grouped by feature:

```text
source_docs_processor/
├── cli.py                    # composes feature entry points
├── core/                     # feature-neutral file, image, path, text primitives
└── features/
    ├── anonymization/        # anonymize API, CLI adapter, and implementation
    └── document_processing/  # process API, shared infrastructure, and types
        └── document_types/   # isolated concrete document implementations
```

Each feature contains a technical `README.md`. Every concrete document type also
contains a local guide describing its public definition, dependency rules,
invariants, and focused test commands. The `process` and `anonymize` CLI syntax
and all `--document-type` values are unchanged by this internal layout.

## Supported document types

| Document type | Purpose | Input | Output |
|---|---|---|---|
| `upd_invoices_status_1` | Scan-oriented Russian UPD invoice-transfer documents with status `1` | PNG, JPG, TIFF, BMP | Corrected and renamed images; CSV registry; text report |
| `npd_receipts` | Russian NPD receipts issued by self-employed persons | PNG, JPG, TIFF, BMP | Copied and renamed images; linked XLSX registry |
| `incoming_purchase_documents` | Incoming purchase documents for 1C entry; current scope is UPD status `1` | PDF, DOCX | Task-oriented XLSX workbook with links to source files; text report |

The default processing document type remains `upd_invoices_status_1`.

## Requirements

Python 3.10 or newer is required. Tesseract OCR with Russian and English language data is required for image workflows and scanned PDF fallback.

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
python -m spacy download ru_core_news_sm
```

The Russian spaCy pipeline is required by Microsoft Presidio for person, organization, and location detection. Presidio and the model run locally; the command does not call external services.

## Processing documents

Run commands from the project root:

```bash
python main.py process \
  --source "/path/to/documents" \
  --document-type upd_invoices_status_1
```

Without `--output`, workflow output is created below the current working directory. `--target-dir-name` overrides the selected workflow's default folder name.

### Scanned UPD status 1

```bash
python main.py process \
  --source "/path/to/upd-scans" \
  --output "/path/to/output" \
  --document-type upd_invoices_status_1
```

The scan workflow recognizes status `1`, corrects orientation, copies and renames recognized images, preserves source subfolders, attaches continuation pages conservatively, and writes a detailed semicolon-separated CSV plus a report.

The default output folder is `./передаточные_документы`.

```text
УПД_511_от_21-03-2023.png
УПД_511_от_21-03-2023_2_страница.png
```

### Incoming purchase documents

```bash
python main.py process \
  --source "/path/to/upd-input" \
  --output "/path/to/output" \
  --document-type incoming_purchase_documents
```

The `incoming_purchase_documents` workflow currently supports only UPD status `1` files:

1. scans PDF and DOCX files recursively;
2. reads native PDF text and tables before using OCR fallback;
3. reads DOCX paragraphs and tables directly;
4. extracts document number, date, seller and buyer details, totals, and goods or service rows;
5. validates item arithmetic and document totals;
6. links directly to source PDF/DOCX files without copying them;
7. writes `реестр_упд_для_ввода_в_1с.xlsx` and a text report;
8. creates a duplicate-safe workbook name on repeated runs instead of overwriting prior processing state.

When `--output` is provided without `--target-dir-name`, workbook and report files are written directly into that directory. Without `--output`, the default output folder is `./упд_для_ввода_в_1с`.

The workbook contains:

- `Documents` — one accountant task per source document with a binary `обработано` dropdown (`Нет`/`Да`);
- `Items` — extracted goods and service rows linked through a hidden `task_id`;
- `Review` — missing fields, recognition warnings, and arithmetic conflicts;
- `_metadata` — a hidden schema/version sheet for future task aggregation.

The processing dropdown belongs to the complete document, not to individual item rows. `task_id` is an internal stable identifier used to link sheets and future task summaries; its columns are hidden and must not be edited. Files that cannot be confirmed as UPD status `1` remain visible and are marked for review. Legacy binary `.doc` files are not supported; convert them to `.docx` or PDF first.

### NPD receipts

```bash
python main.py process \
  --source "/path/to/receipts" \
  --output "/path/to/output" \
  --document-type npd_receipts
```

The receipt workflow copies every image, renames recognized receipts, preserves source subfolders, and writes `npd_receipts_registry.xlsx`. Only recognized receipts are included in the workbook.

When `--output` is provided without `--target-dir-name`, copied receipts and the workbook are written directly into that directory. Without `--output`, the default output folder is `./чеки_нпд`.

## Processing options

```bash
python main.py process --source "/path/to/documents" --debug-crops
python main.py process --source "/path/to/documents" --deep-ocr
python main.py process --source "/path/to/documents" --no-auto-rotate
python main.py process --source "/path/to/documents" --dry-run
```

Each workflow interprets options according to its input and output policy. For `incoming_purchase_documents`, `--deep-ocr` also OCRs PDF pages that already contain native text; normal runs OCR only pages without a useful text layer.

## Anonymizing document folders

The anonymization operation accepts directories, not individual file paths:

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --outputDocumentType docx \
  --outputLayout preserve \
  --alsoOutputSourceFormat \
  --clearOutput \
  --config "config/anonymization.ini"
```

The command prints immediate file progress and page/frame progress for scanned PDFs and multi-page images. Configuration uses the `[anonymization]` INI section:

```ini
[anonymization]
excluded =
included =
    Учебная организация
    Иван Петров
includedAndReplaced =
    Учебная организация -> Учебная компания
    Иван Петров -> Петр Иванов
includedFuzzy = true
includedFuzzyMaxErrors = 1
includedParagraphs = 9. Реквизиты и подписи сторон
```

- A non-empty `included` or `includedAndReplaced` enables configured-only mode. Default Presidio detections and `excluded` are ignored, and Presidio/spaCy models are not loaded.
- `included` masks matching case-insensitive literals.
- `includedAndReplaced` uses one `source -> replacement` rule per line. The source is matched case-insensitively and the replacement is written exactly as configured. A replacement rule takes priority when the same source is also present in `included`.
- `includedFuzzy = true` enables OCR-only tolerant matching for both `included` and the source side of `includedAndReplaced` on raster images, scanned PDFs, and embedded raster images in DOCX files. Native TXT and DOCX text remains exact.
- `includedFuzzyMaxErrors` sets the maximum total insertions, deletions, or substitutions for one configured source value. The accepted range is `0` to `3`; `1` is the recommended conservative value.
- OCR fuzzy matching normalizes `ё`/`е`, punctuation, whitespace, and common visually identical Latin/Cyrillic characters. Values shorter than five normalized characters remain exact to reduce false matches.
- When both configured include lists are empty, default Presidio detection is enabled. `excluded` then contains case-insensitive literal fragments which remain visible inside default detections.
- `includedParagraphs` is independent from both modes. On raster images and PDFs, everything below a matched heading is covered and all following pages are fully covered. In TXT and DOCX text, all following text is masked.

Comma-separated and multiline values are supported for ordinary lists. `includedAndReplaced` is multiline and requires `source -> replacement` syntax. Multiword source literals tolerate spaces, tabs, or line breaks between their words. The default file is `config/anonymization.ini`; another file can be selected with `--config`.

The command scans `--source` recursively and writes anonymized files below `--output`. Without `--outputDocumentType`, relative folders, file names, and formats are preserved. `--outputDocumentType docx` reconstructs editable anonymized text in DOCX files. Add `--outputLayout preserve` to approximate the source page size, orientation, OCR line positions, spacing, and font sizes. Add `--alsoOutputSourceFormat` to generate both an anonymized source-format artifact and the requested DOCX artifact. For example, `contract.pdf` produces `contract.pdf` plus `contract.docx`. A DOCX source produces only one DOCX because the requested and source formats already match. Files with colliding converted names receive a source-format suffix such as `document__pdf.docx`. Dual output performs both format-specific rendering paths and can take longer for scanned PDF or image input. The command does not use `--document-type`.

`preserve` is an OCR-based approximation rather than a lossless PDF-to-Word conversion. Simple paragraphs and aligned text usually remain recognizable, while complex tables, exact fonts, stamps, signatures, and decorative elements may require manual correction. The source scan is never embedded as a background image.

Supported input formats:

- PDF;
- DOCX;
- TXT encoded as UTF-8 or Windows-1251;
- PNG, JPG/JPEG, BMP, and single- or multi-page TIFF.

Detection combines the Russian `ru_core_news_sm` spaCy NER pipeline with Microsoft Presidio pattern recognizers for Russian accounting and identity values, including INN, KPP, OGRN, SNILS, passport-like values, bank accounts, BIK, phone numbers, email addresses, vehicle identifiers, and labeled document numbers.

Output safety behavior:

- PDF pages are rendered and rebuilt as image-only pages so the original searchable text layer and metadata are not retained when the source format is preserved. Mask rules create opaque rectangles. Replacement rules cover the source region and draw the configured replacement text.
- With DOCX output, OCR text is transformed and reconstructed without embedding the source page image; `--outputLayout preserve` additionally approximates page geometry and text positioning.
- Raster images are OCRed in multiple orientations and saved without source EXIF metadata.
- DOCX text, headers, footers, tables, drawing text, package metadata, and supported embedded raster images are sanitized. External relationships and custom XML are removed.
- DOCX files containing OLE/ActiveX objects, embedded workbooks, macros, or unsupported vector images fail instead of copying opaque content unchanged.
- Unsupported source files fail and are not copied into the output directory.
- A partial temporary output is removed when one file fails. The command returns exit code `1` when any source file could not be anonymized.

File and directory names are preserved exactly as requested and are not analyzed; rename them separately when names themselves contain private data. OCR and NER are heuristic. Review anonymized files before sharing them, especially low-quality scans, handwritten fields, stamps, signatures, logos containing names, and unusual document layouts.

## Example scripts

Runnable processing and anonymization examples are under:

```text
scripts/examples/
├── process_upd_scans.sh
├── process_npd_receipts.sh
├── process_incoming_purchase_documents.sh
└── anonymize_document.sh
```

Replace placeholder paths and run a script from the project root, for example:

```bash
bash scripts/examples/process_incoming_purchase_documents.sh
```

## Safe output cleanup

Use `--clearOutput` when each run should replace prior anonymized artifacts:

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --clearOutput
```

The command removes existing files and symlinks recursively but preserves the
output directory and existing subdirectory objects. A macOS Terminal already
opened in the output directory therefore continues to see newly generated files.
Do not combine this option with an external `rm -rf` of the output directory.
The command rejects `--clearOutput` when the source directory is inside the
output directory.

## Tests

```bash
pip install -r requirements-dev.txt
python -m compileall -q main.py source_docs_processor tests
python -m pytest -q
```

Tests use prepared text, synthetic PDF/DOCX files, fake processors, and generated images. Document-specific tests are grouped under folders matching their production packages, while shared behavior remains at the unit or integration root. Real accounting scans, company names, and identifiers must not be committed.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Changelog](docs/CHANGELOG.md)
- [Roadmap](docs/ROADMAP.md)
- [Development rules](AGENTS.md)
- [Anonymization module guide](source_docs_processor/features/anonymization/README.md)
- [Document processing module guide](source_docs_processor/features/document_processing/README.md)

All relative `--source`, `--output`, and `--config` paths are resolved from the current working directory. The anonymization command prints the working directory plus the resolved source and output paths before scanning. A scan that finds no source files exits with an error instead of reporting a successful zero-file run.

