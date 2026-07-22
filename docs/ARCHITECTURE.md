# Architecture

`acc-source-docs-processor` is a local OCR-based CLI for scanned accounting source documents.

The architecture separates a generic folder pipeline from document-specific processors:

```text
source folder
  -> generic file discovery and image loading
  -> explicit processor factory
  -> selected document processor
  -> orientation/OCR/extraction
  -> generic copy and registry output
  -> text report
```

The current released processor is `upd_invoices_status_1`. The shared architecture is intentionally suitable for later processors such as NPD receipts, acts, waybills, and generic invoices.

## Design goals

- Keep original scans unchanged.
- Process folders recursively and preserve relative subfolders.
- Keep OCR and extraction local.
- Keep generic pipeline code free from UPD-specific names and rules.
- Make a new single-page processor small to implement.
- Allow document-specific filename formats and CSV fields without modifying shared output code.
- Preserve existing UPD recognition heuristics and filenames.
- Keep tests deterministic and independent from real Tesseract where possible.

## Project structure

```text
source_docs_processor/
├── cli.py
├── document_processor.py
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

## Generic data model

`source_docs_processor/models.py` defines `ExtractedDocument`.

The model contains common source-document fields:

- `document_type`;
- `is_recognized`;
- `status`;
- `document_number`;
- `document_date`;
- `document_datetime`;
- issuer name, INN, and KPP;
- recipient name, INN, and KPP;
- amount without tax, tax amount, total amount, and currency;
- description;
- confidence, rotation, warnings, errors, and OCR preview;
- continuation-page state;
- `extra_fields` for processor-specific values.

The shared model deliberately avoids names such as `invoice_number`, `seller_name`, or `is_upd_invoice_transfer`. A UPD processor maps its seller to the generic issuer and its buyer to the generic recipient. A receipt processor can map the service provider to issuer and the customer to recipient without changing the pipeline.

### Processor-specific fields

`extra_fields` stores values that are not useful as universal accounting fields. Each processor declares its exported keys through `registry_extra_columns`.

For UPD the current extra fields are:

```text
request_number
request_date
vehicle
loading_datetime
unloading_datetime
```

The CSV writer validates that processor-specific columns do not collide with common columns.

## Generic OCR result

`source_docs_processor/ocr.py` contains document-neutral Tesseract helpers and
`OcrResult`. Anchored values are stored in `targeted_fields` rather than fixed
attributes such as an invoice number or receipt ID. Each processor defines and
interprets its own keys inside its package.

## Processor interface

`source_docs_processor/document_processor.py` contains:

- `DocumentProcessor` — structural protocol used by the pipeline;
- `BaseDocumentProcessor` — reusable default behavior.

A new single-page processor normally configures:

```python
class ExampleProcessor(BaseDocumentProcessor):
    document_type = "example"
    display_name = "Example document"
    default_target_dir_name = "example_documents"
    registry_extra_columns = ("example_field",)
```

It must implement `analyze_image_orientations()`. The base class already provides:

- recognition checks based on `document_type` and `is_recognized`;
- no-op continuation-page analysis;
- continuation metadata inheritance when enabled;
- neutral fallback filename generation;
- export of declared values from `extra_fields`.

A processor may override:

- `build_primary_filename_stem()`;
- `build_output_filename_stem()`;
- continuation recognition and preparation;
- registry value conversion.

This keeps business naming and document layout outside generic file operations.

## Processor factory

`source_docs_processor/processors.py` contains the explicit registry:

```text
PROCESSOR_FACTORIES
```

Adding a processor requires one lazy factory function and one registry entry. This is simpler and more transparent than plugin discovery for the current project size.

The CLI uses only `create_document_processor()` and does not import concrete OCR packages.

## Generic folder pipeline

`source_docs_processor/cli.py` owns orchestration:

1. Validate source and output paths.
2. Create or receive an injected processor.
3. Resolve the output folder from `--target-dir-name` or the processor default.
4. Discover image files recursively and sort them naturally.
5. Load one image.
6. Ask the processor to analyze standalone orientations.
7. Attempt continuation recognition only when:
   - a previous primary document exists;
   - the processor declares continuation support;
   - standalone recognition failed.
8. Ask the processor to prepare inherited continuation metadata.
9. Copy recognized or unrecognized files through generic file operations.
10. Write the common plus processor-specific CSV registry.
11. Write console messages to the text report.

The pipeline contains no UPD status, seller, invoice-number, or filename rules.

## Output and filename policy

`source_docs_processor/file_ops.py` owns filesystem mechanics:

- safe filenames;
- duplicate-safe paths;
- copying original bytes when rotation is unnecessary;
- writing the selected upright image after rotation;
- copying unrecognized files unchanged;
- writing UTF-8 BOM semicolon-separated CSV.

The selected processor owns the filename stem. This allows formats such as:

```text
УПД_511_от_21-03-2023
RECEIPT_204hy1b28u_02-04-2026
ACT_17_30-04-2026
```

The current UPD processor overrides the neutral base policy to preserve existing Russian filenames and continuation suffixes.

## Registry schema

The common registry is stable across document types:

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
rotation_degrees
issuer_name
issuer_inn
issuer_kpp
recipient_name
recipient_inn
recipient_kpp
amount_without_tax
tax_amount
total_amount
currency
description
confidence
warnings
error
text_preview
```

Processor columns are appended after the common schema. A folder run uses one selected processor, so its CSV has one deterministic schema.

Unrecognized rows remain minimal but include source filename, attempted document type, warnings, and error information. Absolute local paths are never written by default.

## UPD status 1 processor

The package `source_docs_processor/upd_invoices_status_1/` retains all current UPD-specific behavior.

### OCR and crop rules

- Try 0, 90, 180, and 270 degree orientations.
- Prefer targeted OCR over one global text pass.
- Read status, document number, date, and shipment row from dedicated crops.
- Use `Документ об отгрузке` as a high-priority fallback.
- Ignore the form-template date `02-04-2021` when it belongs to regulation text.
- Correct suspicious short and over-read document numbers.
- Save debug crops when requested.

### Continuation-page rules

- Recognize a standalone UPD first.
- Attempt continuation detection only after standalone recognition fails.
- Require strong sparse-page markers and reject pages containing a normal UPD header.
- Inherit common and UPD-specific metadata from the previous primary page.
- Preserve the `_2_страница` naming convention.

### Generic field mapping

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

## Adding an NPD receipt processor

A future package can be structured as:

```text
source_docs_processor/npd_receipts/
├── __init__.py
├── extractor.py
├── image_processing.py
├── ocr.py
├── processor.py
└── qr.py
```

The processor can populate:

```text
document_number
document_datetime
issuer_name / issuer_inn
recipient_name / recipient_inn
total_amount
currency
description
```

QR URL or payment-specific values can be additional registry columns. It does not need continuation support and does not require changes to the generic CSV writer or folder pipeline.

## Testing architecture

### Unit tests

Pure tests cover:

- number normalization and over-read correction;
- date normalization and template-date filtering;
- shipment-row parsing;
- continuation decisions;
- processor-controlled filenames;
- generic metadata inheritance;
- processor factory behavior.

### Integration tests

The pipeline tests use a synthetic fake receipt processor and tiny generated PNG files. They verify:

- non-UPD filename policy;
- common generic metadata;
- processor-specific CSV columns;
- continuation inheritance;
- relative folder preservation;
- unrecognized file copying;
- processor-provided default output directory.

These tests do not call Tesseract and contain no customer data.

### Future OCR tests

Real OCR tests may be marked `ocr` and `slow`, skipped when Tesseract is unavailable, and must use synthetic or confirmed anonymized fixtures.
