# Architecture

`acc-source-docs-processor` is a local OCR-based CLI for scanned accounting source documents.

Each CLI-selectable document type combines three independent components:

```text
CLI arguments
  -> DocumentTypeDefinition
      -> DocumentProcessor
      -> ProcessingWorkflow
      -> RegistryDefinition
```

The registered document types are `upd_invoices_status_1` and `npd_receipts`. The default is `upd_invoices_status_1`.

## Component boundaries

Different document types can require different actions after recognition.

The UPD workflow performs:

```text
scan -> recognize -> rotate -> copy -> rename -> register all files -> report
```

The NPD receipt workflow performs:

```text
scan -> recognize -> copy all images -> rename recognized receipts
     -> register recognized receipts in XLSX -> report
```

These are folder-level business rules. They belong to workflows rather than OCR processors.

## Project structure

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
│   ├── __init__.py
│   ├── base.py
│   ├── common.py
│   ├── csv_writer.py
│   └── xlsx_writer.py
├── workflows/
│   ├── __init__.py
│   ├── base.py
│   └── copy_and_register.py
├── upd_invoices_status_1/
│   ├── extractor.py
│   ├── image_processing.py
│   ├── ocr.py
│   ├── processor.py
│   ├── registry.py
│   └── workflow.py
└── npd_receipts/
    ├── extractor.py
    ├── ocr.py
    ├── processor.py
    ├── qr.py
    ├── registry.py
    └── workflow.py
```

## Document type definition

`source_docs_processor/document_types.py` contains the complete CLI-selectable definition:

```python
@dataclass(frozen=True)
class DocumentTypeDefinition:
    document_type: str
    processor_factory: Callable[[], DocumentProcessor]
    workflow_factory: Callable[[], ProcessingWorkflow]
    registry_definition_factory: Callable[[], RegistryDefinition]
```

The explicit registry binds one CLI value to all required behavior:

```text
upd_invoices_status_1
  -> UpdInvoicesStatus1Processor
  -> UpdInvoicesStatus1Workflow
  -> UpdInvoicesStatus1RegistryDefinition

npd_receipts
  -> NpdReceiptProcessor
  -> NpdReceiptRegistryWorkflow
  -> NpdReceiptRegistryDefinition
```

The registry remains explicit because external processor packages and plugin discovery are not currently required.

`source_docs_processor/processors.py` is a backward-compatible processor-only factory for callers that need only a recognizer.

## Document processor

`DocumentProcessor` handles one image. It owns:

- orientation candidates;
- targeted and optional full-page OCR;
- document detection;
- field extraction and normalization;
- confidence and warnings;
- optional continuation-page recognition.

It does not own:

- source folder traversal;
- output directory selection;
- copying or renaming;
- filename generation;
- registry columns or row mapping;
- CSV/XLSX serialization;
- report generation.

`BaseDocumentProcessor` provides common recognition checks and a no-op continuation analyzer for ordinary single-page document types.

## Processing workflow

`source_docs_processor/workflows/base.py` defines:

- `ProcessingOptions` — runtime options received from the CLI;
- `ProcessingResult` — extracted documents and produced artifact paths;
- `ProcessingWorkflow` — the folder-level protocol;
- common logging, sorting, and target-name helpers.

`CopyAndRegisterWorkflow` is reusable for scenarios that require:

- recursive image discovery;
- natural ordering;
- optional continuation handling;
- copying recognized and unrecognized files;
- corrected-orientation output;
- workflow-defined filenames;
- relative output subfolder preservation;
- CSV registry and text report generation.

Its document-specific hooks include:

- `default_target_dir_name`;
- `supports_continuation_pages`;
- `build_primary_filename_stem()`;
- `build_output_filename_stem()`;
- `prepare_continuation_document()`.

A workflow may implement `ProcessingWorkflow` directly when its output behavior differs from `CopyAndRegisterWorkflow`. `NpdReceiptRegistryWorkflow` does this to produce a linked XLSX registry while still copying all source images.

## Registry definition

`RegistryDefinition` describes tabular shape and row conversion:

```python
class RegistryDefinition(Protocol):
    columns: tuple[str, ...]

    def build_row(
        self,
        document: ExtractedDocument,
        source_root: Path,
    ) -> Mapping[str, RegistryValue]:
        ...
```

The name is intentionally narrower than `OutputProcessor`:

- the workflow decides which documents are written and where artifacts are created;
- `file_ops.py` handles image copying;
- a registry definition declares columns and maps one document to one row;
- a registry writer serializes those rows as CSV or XLSX.

This separation prevents document-specific schemas from leaking into generic writers.

## Registry writers

`registry/csv_writer.py` writes document-neutral CSV output:

- UTF-8 with BOM;
- semicolon delimiter;
- declared-column validation;
- rejection of undeclared row keys.

`registry/xlsx_writer.py` writes formatted XLSX output:

- document-defined column order and optional display headers;
- frozen header row and autofilter;
- typed formatting for values such as amounts and INNs;
- portable external hyperlinks to copied files when requested by the workflow.

`registry/common.py` contains shared validation helpers. Writer validation should remain behaviorally consistent; further deduplication can use this module without changing registry contracts.

The selected workflow decides whether all scanned images or only recognized documents are passed to a writer.

## Generic extracted model

`ExtractedDocument` contains common accounting concepts:

- document type and recognition state;
- number, date, and datetime;
- issuer and recipient names, INNs, and KPPs;
- amount without tax, tax amount, total amount, and currency;
- description and status;
- rotation, confidence, warnings, errors, and OCR preview;
- continuation metadata;
- `extra_fields` for document-specific extracted values.

The model does not define output-folder or filename policy.

### UPD field mapping

```text
UPD number          -> document_number
UPD date            -> document_date
seller              -> issuer
buyer               -> recipient
amount without VAT  -> amount_without_tax
VAT amount          -> tax_amount
amount with VAT     -> total_amount
service text        -> description
```

UPD-specific transport and request values remain in `extra_fields`.

### NPD receipt field mapping

```text
receipt number      -> document_number
receipt date        -> document_date
self-employed payee -> issuer
customer            -> recipient
receipt amount      -> total_amount
service text        -> description
```

The compact NPD workbook intentionally exports only the business-requested eight columns, even though the generic model can hold additional extracted values.

## Low-level file operations

`source_docs_processor/file_ops.py` provides mechanical helpers only:

- safe filename normalization;
- duplicate-safe destination paths;
- image writing to non-ASCII paths;
- copying a processed image using a workflow-provided filename stem;
- copying an unrecognized source image unchanged.

The module does not decide which files should be copied or what a document should be called.

## CLI orchestration

`source_docs_processor/cli.py` performs five steps:

1. parse common runtime options;
2. resolve a `DocumentTypeDefinition`;
3. create the processor, workflow, and registry definition;
4. create `ProcessingOptions`;
5. run the selected workflow.

The CLI contains no UPD- or NPD-specific branch.

`process_folder()` accepts optional component injections for deterministic integration tests and embedded use. Normal CLI execution obtains all components from the registered document type definition.

## UPD status 1 implementation

### Processor

`upd_invoices_status_1/processor.py` owns image-level recognition:

- 0°, 90°, 180°, and 270° orientation attempts;
- targeted status, number, date, and shipment-row OCR;
- field extraction and scoring;
- conservative continuation recognition.

### Workflow

`upd_invoices_status_1/workflow.py` owns:

- default output folder `передаточные_документы`;
- copy-and-register scenario selection;
- continuation-page support;
- `УПД_<number>_от_<date>` naming;
- `_2_страница` continuation suffix.

### Registry

`upd_invoices_status_1/registry.py` owns the detailed UPD CSV schema, including:

- source and output filenames;
- document, party, amount, and status fields;
- recognition and continuation state;
- confidence, warnings, errors, and OCR preview;
- request number and date;
- vehicle;
- loading and unloading datetime.

Unrecognized rows remain minimal and are still included in the CSV.

### Preserved OCR rules

- Prefer structured and targeted OCR over one global text pass.
- Use `Документ об отгрузке` as a high-priority number/date source.
- Replace suspiciously short values such as `4` with reliable values such as `405`.
- Correct over-read values such as `43007` or `4977` when a shorter reliable candidate exists.
- Reject the form-template date `02-04-2021` when it comes from regulation text.
- Recognize a standalone first page before testing continuation markers.
- Keep auto-rotation and debug-crop support.

## NPD receipt implementation

### Processor

`npd_receipts/processor.py` owns:

- portrait-first orientation attempts;
- complete-receipt and sparse-text OCR;
- receipt recognition scoring;
- selection of the strongest orientation.

`npd_receipts/extractor.py` owns:

- receipt date, amount, and explicitly labelled receipt-number extraction;
- INN extraction in receipt order;
- self-employed payee name extraction from one-line or split-line layouts;
- optional recipient organization and service-description extraction;
- receipt-specific warnings.

### Workflow

`npd_receipts/workflow.py` owns:

- default output folder `чеки_нпд`;
- copying every source image;
- preserving relative subfolders;
- renaming recognized receipts;
- copying unrecognized images without renaming;
- writing `реестр_чеков_нпд.xlsx`;
- passing only recognized receipts to the workbook writer;
- text report generation.

### Registry

`npd_receipts/registry.py` owns the exact compact workbook contract:

```text
target_file_name
source_file_name
receipt_date
amount
payee_name
receipt_number
payee_inn
generation_comments
```

Display headers may be Russian. Only `target_file_name` is written as a hyperlink; `source_file_name` remains plain text.

### QR support

`npd_receipts/qr.py` contains local utilities that:

- decode a QR value with OpenCV;
- validate official `lknpd.nalog.ru` receipt print URLs;
- parse issuer INN and receipt number from a valid URL.

These utilities are not yet integrated into `NpdReceiptProcessor`. Future integration must reconcile QR and OCR values and surface conflicts rather than silently replacing OCR results. No network request is required or permitted.

## Testing architecture

Tests are separated by responsibility:

- extraction and decision tests use prepared OCR text and fake OCR values;
- workflow integration tests use fake processors and generated images;
- filename tests target workflows rather than processors;
- registry tests verify exact columns, rows, hyperlinks, and writer behavior;
- factory tests verify that a document type creates all three independent components.

Real accounting scans and identifiers are not committed. Optional real-OCR tests must be marked and skipped when Tesseract is unavailable.

## Adding a document type

A new type should be added without modifying existing document-specific packages:

1. Create a processor package with OCR and extraction logic.
2. Reuse or implement a `ProcessingWorkflow`.
3. Create a registry definition with the exact required columns and row mapping.
4. Register all three factories in `document_types.py`.
5. Add processor unit tests and workflow/registry integration tests.
6. Update public documentation when CLI behavior or output contracts change.

Avoid broader abstractions until at least two real document types require the same extension point.
