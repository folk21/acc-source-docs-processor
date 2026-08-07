# Usage

Run all commands from the project root with the Python virtual environment
activated. See [Installation](INSTALLATION.md) before the first run.

## Local Streamlit interface

Start the Russian interface:

```bash
python -m streamlit run streamlit_app.py -- --lang ru
```

Use `-- --lang en` for English. The language can also be changed inside the
interface.

The UI runs on the same computer as the source and output folders and calls the
public Python APIs directly. It does not upload files, invoke the CLI through a
subprocess, or provide remote hosting and authentication.

The localized operation selector provides:

- document anonymization;
- scanned UPD status 1 processing;
- NPD receipt processing;
- incoming PDF/DOCX UPD registration for later entry into 1C.

Each processing screen uses the registered document-type metadata to show only
supported controls. All screens accept local source/output paths, render
privacy-safe progress, and show relative-path result and artifact tables.

The anonymization screen also exposes the four supported entity-detection modes.
Its selection overrides `entityDetectionMode` from the chosen anonymization INI
for that run only. The INI file is never rewritten by the UI. `combined` is the
default Streamlit selection.

## Command-line interface

The CLI is organized by operation:

```text
python main.py process ...
python main.py anonymize ...
```

Display command-specific help:

```bash
python main.py process --help
python main.py anonymize --help
```

Relative source, output, and configuration paths are resolved from the current
working directory.

## Process accounting documents

General form:

```bash
python main.py process \
  --source "/path/to/documents" \
  --output "/path/to/output" \
  --document-type <document-type>
```

Without `--output`, each workflow uses its default output folder below the
current working directory. `--target-dir-name` requests an additional workflow
folder name.

### Scanned UPD status 1

```bash
python main.py process \
  --source "/path/to/upd-scans" \
  --output "/path/to/output" \
  --document-type upd_invoices_status_1
```

The workflow:

- scans supported images recursively;
- recognizes Russian UPD invoice-transfer documents with status `1`;
- tries supported rotations and saves recognized pages upright;
- extracts the document number and date;
- preserves relative source subfolders;
- attaches conservative continuation pages;
- writes renamed images, a semicolon-separated CSV registry, and a text report.

Without an explicit output path, the default folder is
`./передаточные_документы`.

Example names:

```text
УПД_511_от_21-03-2023.png
УПД_511_от_21-03-2023_2_страница.png
```

### NPD receipts

```bash
python main.py process \
  --source "/path/to/receipts" \
  --output "/path/to/output" \
  --document-type npd_receipts
```

The workflow copies every supported source image, preserves relative folders,
renames recognized receipts, and writes `npd_receipts_registry.xlsx`. Only
recognized receipts are included in the workbook; unrecognized images are still
copied without renaming. No text report is generated.

With an explicit `--output` and no `--target-dir-name`, files are written directly
into the selected output directory. Without `--output`, the default folder is
`./чеки_нпд`.

### Incoming purchase documents

```bash
python main.py process \
  --source "/path/to/upd-input" \
  --output "/path/to/output" \
  --document-type incoming_purchase_documents
```

The current implementation supports UPD status `1` in PDF and DOCX files. It:

- reads native PDF text and tables before OCR fallback;
- reads DOCX paragraphs and tables directly;
- extracts document identity, parties, totals, and goods or service rows;
- validates item arithmetic and document totals;
- links to original files without copying them;
- writes `реестр_упд_для_ввода_в_1с.xlsx` and a text report;
- creates duplicate-safe workbook names on repeated runs.

The workbook contains `Documents`, `Items`, `Review`, and hidden `_metadata`
sheets. The `processed` field is a document-level `Нет`/`Да` dropdown. Hidden
`task_id` values link documents to item rows.

Legacy binary `.doc` files are not supported. Convert them to DOCX or PDF before
processing.

With an explicit `--output` and no `--target-dir-name`, the workbook and report
are written directly into that directory. Without `--output`, the default folder
is `./упд_для_ввода_в_1с`.

## Processing options

Common examples:

```bash
python main.py process --source "/path/to/documents" --debug-crops
python main.py process --source "/path/to/documents" --deep-ocr
python main.py process --source "/path/to/documents" --no-auto-rotate
python main.py process --source "/path/to/documents" --dry-run
```

Each workflow interprets options according to its input contract. For
`incoming_purchase_documents`, `--deep-ocr` also OCRs PDF pages that already
contain a usable native text layer.

## Anonymize document folders

The anonymization operation accepts directories and preserves relative
subfolders and source names unless output-format conversion requires a
deterministic collision-safe name.

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --outputDocumentType docx \
  --outputLayout preserve \
  --alsoOutputSourceFormat \
  --clearOutput \
  --config "config/examples/anonymization.ini"
```

Supported input formats are PDF, DOCX, XLSX, TXT encoded as UTF-8 or Windows-1251,
PNG, JPG/JPEG, BMP, and single- or multi-page TIFF. XLSX is anonymized only in
its source format; legacy XLS and macro-enabled XLSM files are not supported.

### Output modes

Without `--outputDocumentType`, each supported source is anonymized in its source
format.

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents"
```

To reconstruct editable DOCX output:

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --outputDocumentType docx
```

Add `--outputLayout preserve` to approximate page dimensions, line placement,
spacing, and font sizes. The source scan is never embedded as a background image.
This is an OCR-based approximation, not a lossless PDF-to-Word conversion.

Add `--alsoOutputSourceFormat` to generate both an anonymized source-format file
and the requested DOCX output. A source already in DOCX format produces one DOCX
instead of a duplicate. Converted-name collisions are resolved deterministically.

### Anonymization configuration

Configuration uses the `[anonymization]` section:

```ini
[anonymization]
entityDetectionMode = combined
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

Rules:

- `entityDetectionMode` accepts `automatic`, `configured`, `combined`, or
  `disabled`;
- `automatic` uses a targeted privacy set from local Presidio with Russian and
  English spaCy NER plus project recognizers and ignores `included` and
  `includedAndReplaced`; it masks multiword person names, high-confidence
  passenger-name layouts such as `NAME OF PASSENGER: SMITH/JOHN MR`, plus OCR
  layouts where `Passenger name` or `Фамилия пассажира` appears directly above
  the passenger value; explicit organization patterns, Russian identifiers,
  bank/card identifiers, email/IP
  values, document or vehicle identifiers, and explicit phone patterns including
  common international numbers beginning with `+`;
- automatic detection intentionally does not request broad Presidio date/time or
  generic phone recognizers, so receipt amounts, dates, totals, and ordinary
  financial text remain available for recognition; generic organization/location
  NER is not used and single-token PERSON guesses are ignored to reduce false
  positives in receipts, tickets, and boarding passes;
- when a real single-word proper name must be hidden, add it explicitly through
  `included` or `includedAndReplaced` and use `combined` mode;
- `configured` uses only `included` and `includedAndReplaced` and does not load
  Presidio/spaCy;
- `combined` uses automatic detections plus configured rules; configured spans
  take priority over overlapping automatic detections;
- `disabled` performs no entity detection; `includedParagraphs` remains active;
- when `entityDetectionMode` is absent, legacy behavior is preserved: a
  non-empty `included` or `includedAndReplaced` selects `configured`, otherwise
  `automatic` is used;
- `included` masks case-insensitive literal matches in `configured` and
  `combined` modes;
- `includedAndReplaced` replaces matching source text with the configured value
  in `configured` and `combined` modes;
- a replacement rule takes priority over an identical mask rule;
- `includedFuzzy = true` enables bounded OCR-only matching for configured source
  values; native TXT, DOCX, and XLSX text remains exact;
- `includedFuzzyMaxErrors` accepts values from `0` to `3`;
- `excluded` filters only automatic detections in `automatic` and `combined`
  modes and never cancels an explicit `included` or `includedAndReplaced` rule;
- `includedParagraphs` masks content after a matched heading and activates
  stronger following-page handling for raster pages independently from
  `entityDetectionMode`. XLSX has no page-continuation semantics, so
  `includedParagraphs` is not applied to workbook cells.

Comma-separated and multiline values are supported for ordinary lists.
`includedAndReplaced` uses one `source -> replacement` rule per line. Multiword
sources tolerate whitespace differences.

The example configuration is:

```text
config/examples/anonymization.ini
```

When anonymization is started from Streamlit, the form's entity-detection mode
selection overrides the INI `entityDetectionMode` only in memory for that run.
Other configuration rules continue to come from the selected INI file, which is
not modified.

### Safety behavior

Anonymization is designed to fail closed:

- unsupported files are not copied unchanged;
- PDFs are rebuilt without their source text layer and metadata;
- supported DOCX text, metadata, relationships, custom XML, and embedded raster
  images are sanitized;
- DOCX macros, OLE/ActiveX objects, embedded workbooks, and unsupported vector
  media cause the file to fail;
- XLSX visible/hidden cell text, comments, headers/footers, metadata, drawing/chart
  text, and supported embedded raster images are sanitized while numeric values
  and formulas are preserved;
- XLSX external relationships, active/embedded objects, pivot/query caches,
  unsupported media, structural-name PII, and detected PII inside formulas cause
  the file to fail rather than being copied unchanged;
- partial temporary output is removed after a failure;
- the command returns a non-zero exit code when any source file fails.

File and directory names are not analyzed. Rename them separately when names
contain private data.

OCR and PII detection are heuristic. Review all anonymized output before sharing
it, especially low-quality scans, handwriting, stamps, signatures, and logos.

## Safe output cleanup

`--clearOutput` removes existing files and symlinks recursively while preserving
the output root and existing directory objects:

```bash
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --clearOutput
```

This prevents stale-current-directory behavior when another terminal is already
open in the output folder. Do not combine the option with an external `rm -rf`
of the output directory. Cleanup is rejected when the source directory is inside
the output directory.

## Example scripts

Portable examples with placeholder paths are stored under `scripts/examples/`:

```text
scripts/examples/
├── process_upd_scans.sh
├── process_npd_receipts.sh
├── process_incoming_purchase_documents.sh
└── anonymize_document.sh
```

Replace the placeholder paths and run a script from the project root.

## Embedded Python API

Local adapters should call the public feature packages rather than invoking the
CLI through `subprocess` or importing `_internal` modules.

The document-processing API, progress model, metadata catalog, and extension
contracts are documented in:

- [Document-processing feature](../source_docs_processor/features/document_processing/README.md)

The Streamlit adapter contract is documented in:

- [Local Streamlit adapter](../source_docs_processor/ui/README.md)
