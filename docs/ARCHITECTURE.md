# Architecture

`acc-source-docs-processor` is a local OCR-based CLI for scanned accounting source documents.

The project separates three responsibilities that were previously combined in one folder pipeline:

```text
CLI args
  -> DocumentTypeDefinition
      -> DocumentProcessor
      -> ProcessingWorkflow
      -> RegistryDefinition
```

The current released definition is `upd_invoices_status_1`. It keeps the existing UPD copy, rename, registry, report, rotation, and continuation behavior.

## Why three components are necessary

Different document types may require different actions after recognition.

The UPD scenario requires:

```text
scan -> recognize -> rotate -> copy -> rename -> register all files -> report
```

A future receipt scenario may require:

```text
scan -> recognize receipts only -> do not copy -> write a short CSV beside source files
```

These differences are folder-level business rules. They must not be implemented as flags or conditionals inside OCR processors.

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
│   └── csv_writer.py
├── workflows/
│   ├── __init__.py
│   ├── base.py
│   └── copy_and_register.py
└── upd_invoices_status_1/
    ├── __init__.py
    ├── extractor.py
    ├── image_processing.py
    ├── ocr.py
    ├── processor.py
    ├── registry.py
    └── workflow.py
```

## Document type definition

`source_docs_processor/document_types.py` contains `DocumentTypeDefinition`:

```python
@dataclass(frozen=True)
class DocumentTypeDefinition:
    document_type: str
    processor_factory: Callable[[], DocumentProcessor]
    workflow_factory: Callable[[], ProcessingWorkflow]
    registry_definition_factory: Callable[[], RegistryDefinition]
```

The explicit registry binds all behavior for one CLI value:

```text
upd_invoices_status_1
  -> UpdInvoicesStatus1Processor
  -> UpdInvoicesStatus1Workflow
  -> UpdInvoicesStatus1RegistryDefinition
```

This registry is intentionally explicit. Plugin discovery is not useful until external processor packages actually exist.

`source_docs_processor/processors.py` remains as a small backward-compatible processor-only factory for callers that need just the recognizer.

## Document processor

`DocumentProcessor` handles one image. It owns:

- orientation candidates;
- targeted and optional full-page OCR;
- document detection;
- extraction and normalization;
- field confidence and warnings;
- optional continuation-page recognition.

It does not own:

- source folder traversal;
- output directory selection;
- copying or renaming;
- filename generation;
- CSV columns or row mapping;
- report generation.

`BaseDocumentProcessor` provides only recognition checks and a no-op continuation analyzer for ordinary single-page types.

This boundary means a future receipt processor can remain small even when its workflow does not copy files at all.

## Processing workflow

`source_docs_processor/workflows/base.py` defines:

- `ProcessingOptions` — CLI/runtime options;
- `ProcessingResult` — extracted documents and produced artifact paths;
- `ProcessingWorkflow` — folder-level protocol;
- common logging and path helpers.

`CopyAndRegisterWorkflow` is a reusable workflow for scenarios that need:

- recursive file discovery;
- natural ordering;
- optional continuation handling;
- copying recognized files;
- copying unrecognized files;
- corrected-orientation output;
- generated filenames;
- output subfolder preservation;
- CSV registry and text report.

The base workflow exposes document-specific hooks:

- `default_target_dir_name`;
- `supports_continuation_pages`;
- `build_primary_filename_stem()`;
- `build_output_filename_stem()`;
- `prepare_continuation_document()`.

These hooks belong to a workflow because they describe what happens to files after recognition.

A future registry-only workflow can implement `ProcessingWorkflow` directly without inheriting any copy behavior.

## Registry definition

`RegistryDefinition` owns only tabular shape and row conversion:

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

The generic CSV writer:

- validates column uniqueness;
- writes UTF-8 with BOM;
- uses semicolon delimiters;
- rejects undeclared row keys;
- knows nothing about UPD or receipts.

The selected workflow decides which document list is passed to the writer. Therefore one workflow may register every scanned file, while another may register only recognized documents.

The `source_root` argument allows future registry definitions to create portable relative file links without embedding this policy in the CSV writer.

## Generic extracted model

`ExtractedDocument` contains common accounting concepts:

- document type and recognition state;
- number, date, and datetime;
- issuer and recipient names/INN/KPP;
- amount without tax, tax amount, total amount, and currency;
- description and status;
- rotation, confidence, warnings, errors, and OCR preview;
- continuation metadata;
- `extra_fields` for document-specific extracted values.

The model does not define output-folder or filename policy.

### Common field mapping for UPD

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

UPD-only transport and request values remain in `extra_fields`.

## Low-level file operations

`source_docs_processor/file_ops.py` provides mechanical helpers only:

- safe filename normalization;
- duplicate-safe destination paths;
- image writing to non-ASCII paths;
- copying a processed image using a workflow-provided filename stem;
- copying an unrecognized source image unchanged.

The module does not know which files should be copied or what any document should be called.

## CLI orchestration

`source_docs_processor/cli.py` is deliberately small:

1. parse common runtime options;
2. resolve a `DocumentTypeDefinition`;
3. create the processor, workflow, and registry definition;
4. create `ProcessingOptions`;
5. run the selected workflow.

The CLI contains no UPD-specific branch.

`process_folder()` also accepts optional component injections for deterministic integration tests and embedded use. Normal CLI execution always uses the registered definition.

## UPD status 1 implementation

### Processor

`upd_invoices_status_1/processor.py` owns image-level recognition only:

- 0/90/180/270-degree orientation attempts;
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

- common document and party fields;
- recognition and continuation state;
- output filename;
- confidence, warnings, errors, and OCR preview;
- request number/date;
- vehicle;
- loading and unloading datetime.

Unrecognized rows remain minimal, preserving existing workflow behavior.

## Preserved UPD OCR rules

- Prefer structured and targeted OCR over one global text pass.
- Use `Документ об отгрузке` as a high-priority number/date source.
- Replace suspiciously short header values such as `4` with reliable values such as `405`.
- Correct over-read values such as `43007` or `4977` when a shorter reliable candidate exists.
- Reject the form-template date `02-04-2021` when it comes from regulation text.
- Recognize a standalone first page before testing continuation markers.
- Keep auto-rotation and debug-crop support.

## Adding a future document type

A new type should be added without changing the existing UPD processor or workflow:

1. Create a processor package with OCR and extraction logic.
2. Reuse or implement a `ProcessingWorkflow`.
3. Create a registry definition with the exact required columns.
4. Register all three factories in `document_types.py`.
5. Add processor unit tests and workflow/registry integration tests.
6. Update public documentation when CLI behavior changes.

For a registry-only receipt type, the new workflow would scan recursively, retain only recognized receipts, skip copying and renaming, and write its CSV in the source directory. None of those actions would require changes to the receipt OCR processor.

## Testing architecture

Tests are split by responsibility:

- extraction and OCR decision tests use prepared text and fake OCR values;
- workflow integration tests use a fake processor, a separate fake workflow, a separate registry definition, and generated tiny images;
- filename tests target the UPD workflow rather than the processor;
- registry factory tests verify that a document type definition creates all three independent components.

Real accounting scans and identifiers are not committed.
