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
│   ├── files.py
│   ├── images.py
│   ├── paths.py
│   └── text.py
└── features/
    ├── anonymization/
    │   ├── README.md
    │   ├── __init__.py
    │   ├── api.py
    │   ├── command.py
    │   └── _internal/
    │       ├── config.py
    │       ├── models.py
    │       ├── workflow.py
    │       ├── text.py
    │       ├── image.py
    │       ├── pdf.py
    │       ├── docx.py
    │       └── editable.py
    └── document_processing/
        ├── README.md
        ├── __init__.py
        ├── api.py
        ├── command.py
        ├── models.py
        ├── document_type_definition.py
        ├── processor_base.py
        ├── registry_base.py
        ├── workflow_base.py
        ├── workflow_copy_and_register.py
        ├── _internal/
        │   ├── service.py
        │   ├── file_ops.py
        │   ├── ocr.py
        │   ├── date_normalization.py
        │   ├── money_normalization.py
        │   └── registry/
        └── document_types/
            ├── catalog.py
            ├── upd_invoices_status_1/
            │   ├── README.md
            │   ├── definition.py
            │   ├── processor.py
            │   ├── registry.py
            │   ├── workflow.py
            │   └── _internal/
            ├── npd_receipts/
            │   ├── README.md
            │   ├── definition.py
            │   ├── processor.py
            │   ├── registry.py
            │   ├── workflow.py
            │   └── _internal/
            └── incoming_purchase_documents/
                ├── README.md
                ├── definition.py
                ├── processor.py
                ├── registry.py
                ├── workflow.py
                └── _internal/
```

The dependency direction is deliberately small and explicit:

```text
cli -> feature command -> feature API -> feature _internal -> core
document-processing API -> internal composition service -> catalog
catalog -> document type definition -> framework-facing modules -> type _internal
core -X-> features
one feature -X-> another feature's _internal
shared processing _internal -X-> concrete document type _internal
one concrete document type -X-> another concrete document type
```

`core/` contains feature-neutral technical primitives whose meaning does not
depend on a document type or operation. It owns safe filename and collision
helpers, local OpenCV image I/O and geometry, whitespace normalization, and path
relationships. A core module never imports a feature and its API contains no
processor, workflow, registry, UPD, receipt, or invoice concepts.

A feature root is an integration map, not an implementation directory.
Anonymization exposes only package exports, `api.py`, and `command.py` at its
root. Document processing additionally exposes public extracted-document models,
the visible `document_types/` catalog, and two framework-facing workflow modules:
`workflow_base.py` and `workflow_copy_and_register.py`. Configuration, handlers,
processor and registry contracts, component injection, OCR containers, strict
date/decimal normalizers, processing-specific file actions, and registry writers
live under the owning feature's `_internal/` package.

The public `process_folder()` API accepts only runtime options and a registered
document type identifier. Internal integration tests use
`document_processing/_internal/service.py::process_folder_with_components()` to
inject fake processors, workflows, or registry definitions. This preserves
testability without treating the project as an external plugin SDK.

Strict date and decimal normalization is shared only inside the document-
processing feature, so the two focused modules are flat under
`document_processing/_internal/` rather than wrapped in a small
`normalization/` package. They deliberately exclude OCR aliases, template-date
filtering, source priorities, and positional table rules; those remain in the
concrete document type that requires them.

Each feature and concrete document type contains a local technical `README.md`
with its public entry points, allowed dependencies, invariants, and focused
validation command. Feature-private unit tests mirror feature `_internal/`
packages. Shared workflow extension points remain visible at the document-
processing feature root, while concrete document type roots expose only
`definition.py`, `processor.py`, `workflow.py`, and `registry.py`; OCR, readers,
extraction, classification, validation, and other details live under the type's
private `_internal/` package. Architectural tests enforce these boundaries.

## Anonymization pipeline

`source_docs_processor/features/anonymization/` is independent from the document processing registry:

```text
source directory
  -> recursive supported-file selection
      -> configured mask/replacement analyzer or Presidio Russian NER
          -> format-specific sanitizer
              -> source-format output and/or requested editable output below the same relative folder
```

`anonymization/_internal/text.py` configures `ru_core_news_sm` through Presidio's `SpacyNlpEngine`, maps Russian spaCy labels to Presidio entities, and registers Russian accounting and identity patterns. Detected spans are normalized into the project-owned `DetectedEntity` model so tests do not require real NLP models.

`anonymization/_internal/config.py` loads `excluded`, masked `included`, `includedAndReplaced` pseudonym rules, and `includedParagraphs` from an INI file. A non-empty `included` or `includedAndReplaced` list enables configured-only mode, bypasses Presidio and `excluded`, and supports flexible whitespace inside multiword sources. Replacement entries use `source -> replacement` syntax and take priority over an identical masked include. Optional `includedFuzzy` and `includedFuzzyMaxErrors` settings add bounded OCR-only edit-distance matching for raster content while native TXT and DOCX text remains exact. OCR matching also normalizes common Latin/Cyrillic lookalikes. When both configured include lists are empty, Presidio remains the base analyzer and `excluded` subtracts explicit false-positive ranges. Section headings operate independently and activate full redaction below the heading and across later raster pages.

`anonymization/_internal/image.py` runs local Tesseract OCR against four orientation candidates, retains both original redaction coordinates and upright layout coordinates, maps detected text spans back to original pixels, draws opaque masks or privacy-safe replacement text, and writes images without source metadata.

`anonymization/_internal/editable.py` creates editable DOCX output. Its default mode writes plain masked OCR text. The optional `preserve` layout mode groups Tesseract words into lines and approximates source page dimensions, orientation, horizontal placement, vertical spacing, and font sizes. It never embeds the source scan as a background image. Native DOCX input continues through the OOXML sanitizer so existing formatting is retained where possible.

`anonymization/_internal/pdf.py` renders each page, delegates pixel redaction to the image sanitizer, and creates a new image-only PDF. It intentionally does not preserve the source text layer, annotations, attachments, forms, or metadata because those channels may contain recoverable private data.

`anonymization/_internal/docx.py` processes the OOXML ZIP package directly. It masks or replaces paragraph text across run boundaries, sanitizes remaining XML text and author attributes, strips core/custom metadata, removes external relationships and custom XML, and transforms supported embedded raster images. It rejects opaque embedded or active content instead of copying it unchanged.

`anonymization/_internal/workflow.py` preserves relative paths, writes each output atomically, and excludes generated files only when the output directory is nested below the source tree. An output directory that is an ancestor of the source remains valid, including `--output .` runs launched from the destination directory. A zero-file effective scan fails with resolved path diagnostics instead of returning a misleading successful summary. The workflow emits privacy-safe file/page progress events and records failures without logging recognized values. Optional dual-output mode writes the anonymized source format plus the requested editable format, skips a redundant second artifact when both formats match, and resolves converted-name collisions deterministically. If either requested variant fails, all artifacts for that source file are removed. Unsupported files remain absent from output and cause a non-zero command result.

## Document-processing framework boundary

Concrete document types import their extension contracts from visible feature-root
modules:

- `processor_base.py` for processor protocols and reusable base defaults;
- `registry_base.py` for the document-specific registry schema protocol;
- `workflow_base.py` and `workflow_copy_and_register.py` for folder workflows;
- `document_type_definition.py` for registered component composition.

These modules are visible because concrete `processor.py`, `registry.py`,
`workflow.py`, and `definition.py` modules depend on them directly. Component
injection, file actions, OCR containers, value normalizers, and registry
serializers remain private under `_internal/`.

## Document type registry

`source_docs_processor/features/document_processing/document_type_definition.py` defines the common `DocumentTypeDefinition` framework contract. Each concrete package exports one complete definition from `definition.py`, and `source_docs_processor/features/document_processing/document_types/catalog.py` registers only those definitions:

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

`features/document_processing/_internal/registry/csv_writer.py` writes document-neutral UTF-8 BOM semicolon-separated CSV files.

`features/document_processing/_internal/registry/xlsx_writer.py` writes ordinary single-sheet XLSX registries with formatted values and portable external links.

`features/document_processing/_internal/registry/task_workbook.py` writes accountant task workbooks with:

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

### Private extraction boundary

The package root exposes only the registered definition, processor, workflow, and
registry. `processor.py` delegates UPD-specific OCR and extraction to `_internal/`.

`_internal/extractor.py` is an assembly layer. It combines prepared OCR, focused
extraction results, classification, confidence, and warnings into
`ExtractedDocument`; it does not own detailed regex or candidate-selection rules.
Identity processing remains split across private number, date, shipment-row, and
source-selection modules. Continuation, classification, parties, amounts, transport
fields, confidence, crop coordinates, and targeted OCR also have focused private
modules. Matching unit tests live under
`tests/unit/upd_invoices_status_1/_internal/`.

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

`features/document_processing/document_types/incoming_purchase_documents/_internal/readers.py` supports:

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

The NPD processor delegates OCR, receipt extraction, and local QR parsing to `_internal/`. Its workflow copies all images, renames recognized receipts, preserves relative subfolders, and writes the compact eight-column `npd_receipts_registry.xlsx` workbook. An explicit `--output` directory is the final artifact directory unless `--target-dir-name` requests an additional nested folder. The NPD workflow does not generate a text report.

Only `target_file_name` is a hyperlink. Receipt-number extraction requires an explicit label, and the first INN in receipt order is treated as the self-employed issuer INN.

Local QR decoding utilities exist but are not integrated into receipt processing.

## CLI orchestration

`source_docs_processor/cli.py` owns only top-level operation selection:

1. create the root parser;
2. register command parsers;
3. parse the selected subcommand;
4. invoke its command handler;
5. convert unexpected failures into a stable non-zero exit code.

`source_docs_processor/features/document_processing/api.py` owns the stable reusable `process_folder()` API. `source_docs_processor/features/document_processing/command.py` owns processing arguments and adapts them to that API. The public API forwards runtime options to `_internal/service.py`, which resolves a complete definition from the catalog, creates the processor, workflow, and registry definition, builds `ProcessingOptions`, and runs the selected workflow. Optional component injection exists only on the internal service for deterministic integration tests.

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

Tests mirror both feature and document-type public/private splits:

```text
tests/
├── unit/
│   ├── anonymization/
│   │   ├── test_command.py
│   │   └── _internal/
│   │       └── test_*.py
│   ├── document_processing/
│   │   ├── test_document_types.py
│   │   └── _internal/
│   │       ├── test_components.py
│   │       ├── test_normalization.py
│   │       └── test_ocr.py
│   ├── incoming_purchase_documents/
│   │   └── _internal/
│   ├── npd_receipts/
│   │   └── _internal/
│   ├── upd_invoices_status_1/
│   │   └── _internal/
│   └── test_package_boundaries.py
└── integration/
    ├── anonymization/
    ├── incoming_purchase_documents/
    ├── npd_receipts/
    ├── upd_invoices_status_1/
    └── test_pipeline_with_fake_processor.py
```

Private configuration, format, workflow, OCR, parser, reader, and infrastructure
tests live under the matching `_internal/` test package. Command, public model,
catalog, framework-facing filename, and registered-workflow tests remain at the
matching feature or document-type test root. Synthetic component-injection tests
import the internal composition service explicitly.

The suite uses prepared OCR/text tests, synthetic PDF and DOCX files, generated images, fake processors, workbook contract checks, and factory tests for all registered definitions. Real accounting documents, names, INNs/KPPs, addresses, and private debug output must not be committed.

## Anonymization output cleanup

`--clearOutput` removes existing files and symlinks while preserving the output
root and existing directory objects. This prevents the Unix/macOS stale-current-
directory behavior caused by deleting and recreating a directory that is open in
another terminal. Cleanup is rejected when source is nested below output.
