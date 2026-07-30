# Architecture

`acc-source-docs-processor` is a local CLI for scanned and electronic accounting source documents.

The CLI selects an operation first:

```text
CLI subcommand
  -> process
      -> DocumentTypeDefinition
          -> Processor
          -> ProcessingWorkflow
          -> RegistryDefinition
  -> anonymize
      -> recursive folder workflow
          -> Presidio text analyzer
          -> PDF / DOCX / image / text sanitizer
```

Document types belong to the `process` operation. Anonymization is an independent directory operation and is not registered as a document type.

Registered document types:

- `upd_invoices_status_1` — scan-oriented UPD status `1` processing and tax-report preparation;
- `npd_receipts` — scanned NPD receipt processing;
- `incoming_purchase_documents` — incoming purchase-document extraction for manual entry into 1C; the current scope is PDF/DOCX UPD status `1`.

The default remains `upd_invoices_status_1`.

## Component boundaries

A processor owns recognition and extraction for one input file. Two specialized protocols are available:

- `DocumentProcessor` for images, orientation candidates, OCR, and continuation recognition;
- `SourceFileProcessor` for structured or paged source files such as PDF and DOCX.

A processor does not own recursive traversal, output directories, copying, reports, or registry serialization.

A workflow owns:

- recursive source-file selection;
- output-directory policy;
- copying and naming;
- selection of documents written to registries;
- report generation.

A registry definition owns tabular shape and row mapping. Generic writers own CSV/XLSX serialization.

## Project structure

```text
source_docs_processor/
├── cli.py
├── core/
│   └── paths.py
└── features/
    ├── anonymization/
    │   ├── README.md
    │   ├── command.py
    │   ├── config.py
    │   ├── docx.py
    │   ├── editable.py
    │   ├── image.py
    │   ├── models.py
    │   ├── pdf.py
    │   ├── text.py
    │   └── workflow.py
    └── document_processing/
        ├── README.md
        ├── api.py
        ├── command.py
        ├── contracts.py
        ├── document_processor.py
        ├── file_ops.py
        ├── image_processing.py
        ├── models.py
        ├── ocr.py
        ├── processors.py
        ├── registry/
        │   ├── base.py
        │   ├── common.py
        │   ├── csv_writer.py
        │   ├── xlsx_writer.py
        │   └── task_workbook.py
        ├── workflows/
        │   ├── base.py
        │   └── copy_and_register.py
        └── document_types/
            ├── catalog.py
            ├── upd_invoices_status_1/
            │   ├── README.md
            │   ├── definition.py
            │   ├── extractor.py
            │   ├── image_processing.py
            │   ├── ocr.py
            │   ├── processor.py
            │   ├── registry.py
            │   └── workflow.py
            ├── npd_receipts/
            │   ├── README.md
            │   ├── definition.py
            │   ├── extractor.py
            │   ├── ocr.py
            │   ├── processor.py
            │   ├── qr.py
            │   ├── registry.py
            │   └── workflow.py
            └── incoming_purchase_documents/
                ├── README.md
                ├── definition.py
                ├── extractor.py
                ├── processor.py
                ├── readers.py
                ├── registry.py
                └── workflow.py
```

The dependency direction is deliberately small and explicit:

```text
cli -> feature command -> feature API / implementation -> core
catalog -> document type definition -> concrete implementation
core -X-> features
one concrete document type -X-> another concrete document type
```

`core/` contains only behavior used by more than one independent feature. At present this is limited to path relationship helpers. Document models, OCR helpers, registry writers, workflows, and file-copying utilities belong to the document-processing feature because anonymization neither depends on nor implements those contracts.

Each feature and concrete document type contains a local technical `README.md` with its public entry points, allowed dependencies, invariants, and focused validation command. Architectural tests enforce the dependency direction, prevent cross-feature and cross-document-type imports, keep shared processing modules implementation-neutral, and restrict the catalog to `definition.py` modules.

## Anonymization pipeline

`source_docs_processor/features/anonymization/` is independent from the document processing registry:

```text
source directory
  -> recursive supported-file selection
      -> configured mask/replacement analyzer or Presidio Russian NER
          -> format-specific sanitizer
              -> source-format output and/or requested editable output below the same relative folder
```

`text.py` configures `ru_core_news_sm` through Presidio's `SpacyNlpEngine`, maps Russian spaCy labels to Presidio entities, and registers Russian accounting and identity patterns. Detected spans are normalized into the project-owned `DetectedEntity` model so tests do not require real NLP models.

`config.py` loads `excluded`, masked `included`, `includedAndReplaced` pseudonym rules, and `includedParagraphs` from an INI file. A non-empty `included` or `includedAndReplaced` list enables configured-only mode, bypasses Presidio and `excluded`, and supports flexible whitespace inside multiword sources. Replacement entries use `source -> replacement` syntax and take priority over an identical masked include. Optional `includedFuzzy` and `includedFuzzyMaxErrors` settings add bounded OCR-only edit-distance matching for raster content while native TXT and DOCX text remains exact. OCR matching also normalizes common Latin/Cyrillic lookalikes. When both configured include lists are empty, Presidio remains the base analyzer and `excluded` subtracts explicit false-positive ranges. Section headings operate independently and activate full redaction below the heading and across later raster pages.

`image.py` runs local Tesseract OCR against four orientation candidates, retains both original redaction coordinates and upright layout coordinates, maps detected text spans back to original pixels, draws opaque masks or privacy-safe replacement text, and writes images without source metadata.

`editable.py` creates editable DOCX output. Its default mode writes plain masked OCR text. The optional `preserve` layout mode groups Tesseract words into lines and approximates source page dimensions, orientation, horizontal placement, vertical spacing, and font sizes. It never embeds the source scan as a background image. Native DOCX input continues through the OOXML sanitizer so existing formatting is retained where possible.

`pdf.py` renders each page, delegates pixel redaction to the image sanitizer, and creates a new image-only PDF. It intentionally does not preserve the source text layer, annotations, attachments, forms, or metadata because those channels may contain recoverable private data.

`docx.py` processes the OOXML ZIP package directly. It masks or replaces paragraph text across run boundaries, sanitizes remaining XML text and author attributes, strips core/custom metadata, removes external relationships and custom XML, and transforms supported embedded raster images. It rejects opaque embedded or active content instead of copying it unchanged.

`workflow.py` preserves relative paths, writes each output atomically, and excludes generated files only when the output directory is nested below the source tree. An output directory that is an ancestor of the source remains valid, including `--output .` runs launched from the destination directory. A zero-file effective scan fails with resolved path diagnostics instead of returning a misleading successful summary. The workflow emits privacy-safe file/page progress events and records failures without logging recognized values. Optional dual-output mode writes the anonymized source format plus the requested editable format, skips a redundant second artifact when both formats match, and resolves converted-name collisions deterministically. If either requested variant fails, all artifacts for that source file are removed. Unsupported files remain absent from output and cause a non-zero command result.

## Document type registry

`source_docs_processor/features/document_processing/contracts.py` defines the common `DocumentTypeDefinition` contract. Each concrete package exports one complete definition from `definition.py`, and `source_docs_processor/features/document_processing/document_types/catalog.py` registers only those definitions:

```text
upd_invoices_status_1
  -> UpdInvoicesStatus1Processor
  -> UpdInvoicesStatus1Workflow
  -> UpdInvoicesStatus1RegistryDefinition

npd_receipts
  -> NpdReceiptProcessor
  -> NpdReceiptRegistryWorkflow
  -> NpdReceiptRegistryDefinition

incoming_purchase_documents
  -> IncomingPurchaseDocumentsProcessor
  -> IncomingPurchaseDocumentsWorkflow
  -> IncomingPurchaseDocumentsRegistryDefinition
```

The explicit catalog remains preferable to plugin discovery while all processors live inside the document-processing feature.

## Generic models

`ExtractedDocument` contains common accounting concepts:

- document identity and recognition state;
- issuer and recipient details;
- net, tax, and gross amounts;
- currency and description;
- confidence, warnings, errors, and output path;
- continuation metadata for scan workflows;
- `items` for repeating goods or service rows;
- `extra_fields` for document-specific scalar values.

`ExtractedDocumentItem` contains:

- line number and name;
- unit, quantity, and unit price;
- amount without tax, tax rate, tax amount, and total amount;
- confidence and line-level warnings.

Repeating item data must not be placed in `extra_fields`.

## Registry writers

`features/document_processing/registry/csv_writer.py` writes document-neutral UTF-8 BOM semicolon-separated CSV files.

`features/document_processing/registry/xlsx_writer.py` writes ordinary single-sheet XLSX registries with formatted values and portable external links.

`features/document_processing/registry/task_workbook.py` writes accountant task workbooks with:

- a `Documents` sheet;
- an `Items` sheet;
- a `Review` sheet;
- a hidden `_metadata` sheet;
- list-validated binary processing fields;
- hidden internal identifier columns with header comments;
- links to original source documents.

The task workbook writer receives sheet columns and row builders from a document-specific definition. It does not contain UPD parsing rules.

## Scan-oriented UPD status 1

### Processor

`features/document_processing/document_types/upd_invoices_status_1/processor.py` owns image-level recognition:

- 0°, 90°, 180°, and 270° attempts;
- targeted status, number, date, and shipment-row OCR;
- field extraction and orientation scoring;
- conservative continuation recognition.

### Workflow

The workflow preserves:

- output folder `передаточные_документы`;
- corrected and renamed image copies;
- source subfolders;
- continuation-page attachment;
- detailed CSV and text report generation.

### Preserved OCR rules

- Prefer structured targeted crops over one global OCR pass.
- Use `Документ об отгрузке` as a high-priority number/date source.
- Replace suspiciously short values such as `4` with reliable values such as `405`.
- Correct over-read values such as `43007` or `4977` when a shorter reliable candidate exists.
- Reject the form-template date `02-04-2021` when it comes from regulation text.
- Recognize a standalone first page before testing continuation markers.
- Preserve auto-rotation and debug-crop support.

This document type is intentionally not part of the accountant task queue because its purpose is scan selection and report preparation rather than entering documents into 1C.

## Incoming purchase documents

### Source readers

`features/document_processing/document_types/incoming_purchase_documents/readers.py` supports:

- PDF native text extraction with PyMuPDF;
- PDF table detection with PyMuPDF when table structure is available;
- OCR fallback for PDF pages without a useful text layer;
- optional forced PDF OCR with `--deep-ocr`;
- DOCX paragraphs and table extraction with `python-docx`.

No network calls are used. Legacy `.doc` files are outside the supported input contract.

### Processor

`IncomingPurchaseDocumentsProcessor` owns one PDF/DOCX file and extracts:

- UPD status and invoice-transfer markers;
- number and date;
- seller and buyer names, INNs, and KPPs;
- structured goods or service rows;
- net, VAT, and gross totals;
- line and document arithmetic warnings.

An explicit status `2` document is rejected. A file with incomplete extraction remains visible and is marked for review rather than silently omitted.

### Workflow

`IncomingPurchaseDocumentsWorkflow`:

- scans `.pdf` and `.docx` recursively;
- references original source files without copying unchanged PDF/DOCX inputs;
- assigns a stable task UUID derived from relative path and file content;
- writes `реестр_упд_для_ввода_в_1с.xlsx`;
- writes directly into an explicit `--output` directory unless a target name is requested;
- uses duplicate-safe workbook and report names on repeated runs;
- writes a text report.

Without `--output`, the default output folder is `упд_для_ввода_в_1с`.

### Workbook contract

`Documents` contains one task per source file. `processed` is a binary `Нет`/`Да` dropdown initially set to `Нет`. It belongs to the complete UPD, not to individual goods rows.

`Items` contains one row per extracted goods or service line and links rows to the document through `task_id`. The `task_id` columns are hidden and carry an English header comment explaining that the value is an internal stable identifier.

The item parser rejects the official row of column designators such as `1а` and distinguishes numeric OKEI codes from textual units such as `шт` or `кг`. Numeric codes are not exported as unit names.

`Review` contains document warnings, missing required fields, status conflicts, extraction errors, and line arithmetic conflicts.

`_metadata` contains:

```text
registry_schema = incoming_purchase_documents_tasks
registry_schema_version = 2
document_type = incoming_purchase_documents
```

This metadata is intended for a later task-summary generator that reads multiple working workbooks without relying only on visible sheet labels.

## NPD receipts

The NPD processor owns OCR and receipt extraction. Its workflow copies all images, renames recognized receipts, preserves relative subfolders, and writes the compact eight-column `npd_receipts_registry.xlsx` workbook. An explicit `--output` directory is the final artifact directory unless `--target-dir-name` requests an additional nested folder. The NPD workflow does not generate a text report.

Only `target_file_name` is a hyperlink. Receipt-number extraction requires an explicit label, and the first INN in receipt order is treated as the self-employed issuer INN.

Local QR decoding utilities exist but are not integrated into receipt processing.

## CLI orchestration

`source_docs_processor/cli.py` owns only top-level operation selection:

1. create the root parser;
2. register command parsers;
3. parse the selected subcommand;
4. invoke its command handler;
5. convert unexpected failures into a stable non-zero exit code.

`source_docs_processor/features/document_processing/api.py` owns the reusable `process_folder()` API. `source_docs_processor/features/document_processing/command.py` owns processing arguments and adapts them to that API. The API resolves a `DocumentTypeDefinition`, creates the processor, workflow, and registry definition, builds `ProcessingOptions`, and runs the selected workflow.

`source_docs_processor/features/anonymization/command.py` accepts source and output directories, an optional editable DOCX output type, `preserve` layout mode, and optional dual source-format output, creates the local Presidio analyzer when required, runs the recursive anonymization workflow, and returns a non-zero code when any source file fails. It has no document-type argument. PDF and raster pages are OCRed into masked editable text; preserve mode approximates layout without embedding original page images.

No document-specific branch belongs in the CLI or command handlers. Document-type behavior remains in the explicit document-type registry and its selected components.

## Example scripts

Example command wrappers live under `scripts/examples/` rather than the project root:

```text
scripts/examples/
├── process_upd_scans.sh
├── process_npd_receipts.sh
├── process_incoming_purchase_documents.sh
└── anonymize_document.sh
```

The folder contains replaceable path templates, not environment-specific production configuration. The anonymization script uses directory paths and preserves relative file names below the selected output root.

## Testing

Tests are separated first by responsibility and then by document type:

```text
tests/
├── unit/
│   ├── incoming_purchase_documents/
│   ├── npd_receipts/
│   ├── upd_invoices_status_1/
│   └── test_*.py
└── integration/
    ├── incoming_purchase_documents/
    ├── npd_receipts/
    ├── upd_invoices_status_1/
    └── test_pipeline_with_fake_processor.py
```

Document-specific folders contain extraction, reader, filename, registry, and registered-workflow tests for the matching production package. Generic model, OCR container, factory, writer, and synthetic cross-component tests remain directly under the corresponding `unit` or `integration` folder.

The suite uses prepared OCR/text tests, synthetic PDF and DOCX files, generated images, fake processors, workbook contract checks, and factory tests for all registered definitions. Real accounting documents, names, INNs/KPPs, addresses, and private debug output must not be committed.

## Anonymization output cleanup

`--clearOutput` removes existing files and symlinks while preserving the output
root and existing directory objects. This prevents the Unix/macOS stale-current-
directory behavior caused by deleting and recreating a directory that is open in
another terminal. Cleanup is rejected when source is nested below output.
