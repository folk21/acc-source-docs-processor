# Architecture

`acc-source-docs-processor` is a local OCR-based utility for processing scanned Russian accounting source documents.

The current released processor focuses on UPD transfer documents with status `1`, where the document acts both as an invoice and as a transfer document. The project has now been refactored so this UPD logic is a document-specific processor selected by the CLI, while the generic pipeline stays independent from the concrete document template.

## Goals

The main practical goals are:

- scan a source folder recursively;
- detect supported primary documents among image files;
- extract a reliable document number and document date;
- copy processed scans into a target folder;
- rename recognized files using extracted fields;
- keep unrecognized files visible in the result set;
- generate a CSV registry and a text report;
- handle poor scan quality, rotated pages, punch holes, weak dates, OCR over-read, and second pages;
- support future document types through processor packages instead of hardcoding all logic into one module.

The tool is fully local. It does not upload scanned documents anywhere.

## High-level pipeline

The current pipeline is:

```text
source folder
  -> image file discovery
  -> natural file ordering
  -> image loading
  -> document processor factory
  -> processor-specific orientation candidates
  -> processor-specific OCR on each candidate orientation
  -> processor-specific document detection and field extraction
  -> processor-specific number/date adjustment
  -> processor-specific continuation-page check when standalone detection fails
  -> generic copy/rename output image
  -> generic CSV registry row
  -> generic text report line
```

The main architectural split is:

- generic code owns file traversal, image loading, rotation primitives, output, registry, report, and CLI orchestration;
- processor code owns template crop coordinates, targeted OCR, field extraction, and document-specific decision logic.

## Current project structure

```text
acc-source-docs-processor/
├── README.md
├── AGENTS.md
├── requirements.txt
├── main.py
├── run.sh
├── run_example.sh
├── archive.sh
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   └── ROADMAP.md
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

## Generic components

### `main.py`

A very small entry point. It delegates command-line execution to the package-level CLI module.

### `source_docs_processor/cli.py`

Contains command-line argument parsing and the high-level folder processing workflow.

Responsibilities:

- validate the source folder;
- resolve the target folder;
- select the document processor using `--document-type`;
- collect image files;
- apply natural sorting;
- call the selected processor for OCR/extraction per image;
- track the last recognized document for possible continuation pages;
- coordinate copying, registry generation, and report generation;
- write console messages and report messages through `RunLogger`.

Important behavior:

- The target directory is created in the current working directory by default.
- `--target-dir-name` changes the folder name, not the base path.
- `--output` changes the base output directory.
- `--document-type` selects the processor. The current default is `upd_invoices_status_1`.
- Each scan is first tested as a standalone document by the selected processor.
- Continuation-page detection is attempted only if standalone document detection fails.

### `source_docs_processor/processors.py`

Contains the processor factory and shared processor protocol.

The factory currently uses a simple switch:

```text
upd_invoices_status_1 -> UpdInvoicesStatus1Processor
```

This is intentionally simple. When more processors are added, the switch can evolve into a registry or plugin mechanism.

The CLI does not import UPD extraction code directly. It asks the factory for a processor and then calls the processor interface.

### `source_docs_processor/image_processing.py`

Contains document-type-neutral image utilities.

Responsibilities:

- recursively find supported image files;
- skip output folders when necessary;
- read images with non-ASCII paths;
- rotate images;
- crop by relative coordinates;
- create generic OCR preprocessing variants.

Template-specific crop coordinates do not belong here anymore. They belong to the processor package.

### `source_docs_processor/ocr.py`

Contains generic OCR primitives.

Responsibilities:

- call Tesseract through `pytesseract`;
- provide the `OcrResult` data object;
- choose the best text result from preprocessing variants;
- allow document processors to pass marker patterns for scoring.

This module does not contain UPD crop coordinates or status-specific logic.

### `source_docs_processor/models.py`

Contains the main data structures.

Important model:

- `ExtractedDocument` — structured result of document recognition and processing.

The field names currently keep UPD/invoice terminology because the first processor handles UPD invoice-transfer documents. Future refactoring can introduce more generic field aliases once more document types exist.

Recognized first-page UPD files are named with the current convention:

```text
УПД_<document_number>_от_<document_date>.png
```

When the date is missing:

```text
УПД_<document_number>.png
```

Continuation pages inherit the previous document stem and add:

```text
_2_страница
```

### `source_docs_processor/file_ops.py`

Contains output operations.

Responsibilities:

- sanitize filenames;
- avoid duplicate output filenames;
- copy recognized documents;
- copy continuation pages;
- copy unrecognized files unchanged;
- preserve source subfolder structure;
- write an Excel-friendly CSV registry.

The CSV uses semicolon delimiters and UTF-8 with BOM. It stores file names, not full local paths.

## UPD status 1 processor

The package `source_docs_processor/upd_invoices_status_1/` contains all logic specific to the current UPD template.

### `upd_invoices_status_1/processor.py`

Boundary class between the generic pipeline and the UPD implementation.

Responsibilities:

- expose `document_type = "upd_invoices_status_1"`;
- score rotated OCR candidates;
- analyze a scan as a standalone UPD first page;
- analyze a scan as a possible continuation page;
- decide whether an `ExtractedDocument` is supported by this processor;
- hide UPD-specific OCR/extraction details from the CLI.

### `upd_invoices_status_1/image_processing.py`

Contains UPD-specific crop coordinates.

Important crop areas include:

- header area;
- status digit area;
- document number candidates;
- document date candidates;
- transfer/shipment date candidates;
- `Документ об отгрузке` row candidates;
- continuation-page marker candidates.

The crop coordinates are tuned for the current family of landscape UPD scans. They are intentionally duplicated across a few nearby candidate boxes because real scans may be shifted, scaled, or slightly cropped.

### `upd_invoices_status_1/ocr.py`

Contains targeted OCR helpers for UPD documents.

Responsibilities:

- run header OCR;
- read the framed status digit;
- read the document number from fixed crop areas;
- read document date crops;
- read the `Документ об отгрузке` row;
- read continuation-page marker crops;
- save debug crop files when `--debug-crops` is enabled;
- return an `OcrResult` object to the UPD extractor.

Full-page OCR is deliberately limited because it is expensive on large archives. The application prefers targeted OCR for high-value fields such as status, document number, date, and shipment-row data.

### `upd_invoices_status_1/extractor.py`

Contains text normalization and UPD-specific extraction logic.

Responsibilities:

- normalize OCR text;
- normalize document numbers;
- normalize Russian textual dates;
- normalize money values;
- detect UPD status `1`;
- detect whether a scan is a UPD invoice-transfer document;
- extract document number and date;
- extract number/date fallback data from `Документ об отгрузке`;
- reject false form-template dates;
- correct OCR over-read in document numbers;
- detect probable continuation pages;
- extract optional party, amount, and transport fields.

## Recognition strategy

### Orientation selection

The processor tries several orientations:

```text
0°, 90°, 180°, 270°
```

If the source image is portrait-shaped, sideways rotations are tried first because most supported UPD scans are landscape.

Each orientation receives a score. The score increases when the candidate has:

- UPD/invoice-transfer markers;
- status `1`;
- a document number;
- a document date;
- strong continuation-page markers, but only in the continuation-specific path.

When a sideways document is recognized, the output copy is saved in the corrected orientation. The source file is never modified.

### UPD status detection

The status field is visually simple but OCR can be misleading because the left-side area contains explanatory text:

```text
1 - счет-фактура и передаточный документ
2 - передаточный документ (акт)
```

A naive OCR approach may accidentally read the explanation as status `2`. The processor therefore uses tighter crops around the framed status digit and treats surrounding explanatory text cautiously.

### Document number extraction

The document number is extracted from multiple sources:

1. header crop near `Счет-фактура №`;
2. general header OCR;
3. `Документ об отгрузке` row.

A dedicated adjustment algorithm compares candidates. It fixes common scan/OCR issues such as:

- internal spaces: `2 548 -> 2548`;
- punctuation: `2.548 -> 2548`;
- partial header values: `4 -> 405` when shipment row has `405`;
- over-read values: `43007 -> 430`, `4977 -> 497`.

The adjustment algorithm is intentionally heuristic-based and records warnings when it changes a field.

### Document date extraction

The document date is also extracted from multiple sources:

1. `Документ об отгрузке` row;
2. top document date crop;
3. bottom transfer/shipment date crop;
4. general OCR only as a lower-priority source.

The row `Документ об отгрузке № п/п 1 № 511 от 21 марта 2023 г.` is treated as a high-priority source because it repeats the actual document number/date.

The processor explicitly rejects the standard UPD form-template date `02-04-2021` when it is associated with the government-decree service text in the upper-right corner.

### Continuation pages

Some documents are scanned as two sequential files. The second page can contain only signature/stamp blocks and may not have the invoice header.

The processor detects continuation pages conservatively:

1. First try to recognize the scan as a standalone UPD first page.
2. If standalone recognition fails and there is a previous recognized document, run continuation marker OCR.
3. If continuation markers are strong, copy the scan using the previous document number/date and add a page suffix.

This order prevents normal first pages from being incorrectly classified as continuation pages merely because they also contain signatures and stamps.

## How to add a new document type

A new document type should not be implemented by modifying `cli.py` directly.

Recommended steps:

1. Create a new package under `source_docs_processor/`, for example `acts_status_1/` or `generic_invoices/`.
2. Add a `processor.py` class implementing the same methods as `UpdInvoicesStatus1Processor`.
3. Add template-specific OCR/crop/extractor modules inside that package.
4. Register the new processor in `source_docs_processor/processors.py`.
5. Add the processor id to `SUPPORTED_DOCUMENT_TYPES`.
6. Update README, architecture, changelog, and roadmap.

The CLI should then be able to run the new processor with:

```bash
python main.py --source "/path/to/scans" --document-type new_processor_id
```

## Current limitations

- Only one document type is currently released: `upd_invoices_status_1`.
- The output model still uses invoice-oriented field names internally.
- Crop coordinates are tuned for the currently observed UPD scan layout.
- Field confidence is document-level and heuristic-based, not a calibrated probability.
- There are no automated regression tests yet for the problematic scan examples.
