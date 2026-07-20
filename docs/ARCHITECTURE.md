# Architecture

`acc-source-docs-processor` is a local OCR-based utility for processing scanned Russian accounting source documents.

The current implementation focuses on UPD transfer documents with status `1`, where the document acts both as an invoice and as a transfer document. The project is intentionally named more broadly than the first supported document type because the processing pipeline can later be generalized for other primary document types.

## Goals

The main practical goals are:

- scan a source folder recursively;
- detect supported primary documents among image files;
- extract a reliable document number and document date;
- copy processed scans into a target folder;
- rename recognized files using extracted fields;
- keep unrecognized files visible in the result set;
- generate a CSV registry and a text report;
- handle poor scan quality, rotated pages, punch holes, weak dates, OCR over-read, and second pages.

The tool is fully local. It does not upload scanned documents anywhere.

## High-level pipeline

The current pipeline is:

```text
source folder
  -> image file discovery
  -> natural file ordering
  -> image loading
  -> orientation candidates
  -> OCR on each candidate orientation
  -> UPD status/document detection
  -> targeted field extraction
  -> document number/date adjustment
  -> continuation-page check when standalone detection fails
  -> copy/rename output image
  -> CSV registry row
  -> text report line
```

The most important design decision is that page processing is split into generic pipeline steps and document-specific recognition heuristics. At the moment, most document-specific logic is implemented in `extractor.py`, but the project can later evolve into a registry of pluggable document extractors.

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
    ├── extractor.py
    ├── file_ops.py
    ├── image_processing.py
    ├── models.py
    └── ocr.py
```

## Components

### `main.py`

A very small entry point. It delegates command-line execution to the package-level CLI module.

### `source_docs_processor/cli.py`

Contains command-line argument parsing and the high-level folder processing workflow.

Responsibilities:

- validate the source folder;
- resolve the target folder;
- collect image files;
- apply natural sorting;
- run OCR and extraction per image;
- track the last recognized document for possible continuation pages;
- coordinate copying, registry generation, and report generation;
- write console messages and report messages through `RunLogger`.

Important behavior:

- The target directory is created in the current working directory by default.
- `--target-dir-name` changes the folder name, not the base path.
- `--output` changes the base output directory.
- Each scan is first tested as a standalone UPD document.
- Continuation-page detection is attempted only if standalone UPD detection fails.

### `source_docs_processor/image_processing.py`

Contains low-level image utilities.

Responsibilities:

- recursively find supported image files;
- skip output folders when necessary;
- read images with non-ASCII paths;
- rotate images;
- create OCR preprocessing variants;
- crop known UPD zones.

Important crop areas include:

- header area;
- status digit area;
- document number candidates;
- document date candidates;
- transfer/shipment date candidates;
- `Документ об отгрузке` row candidates;
- continuation-page marker candidates.

The crop coordinates are tuned for the current family of landscape UPD scans. They are intentionally duplicated across a few nearby candidate boxes because real scans may be shifted, scaled, or slightly cropped.

### `source_docs_processor/ocr.py`

Contains the OCR adapter and targeted OCR helpers.

Responsibilities:

- call Tesseract through `pytesseract`;
- run OCR on selected full-page or cropped areas;
- apply different preprocessing strategies for different field types;
- extract digit-only candidates for status and document number;
- save debug crop files when `--debug-crops` is enabled;
- return an `OcrResult` object with general OCR text and targeted OCR fields.

Full-page OCR is deliberately limited because it is expensive on large archives. The application prefers targeted OCR for high-value fields such as status, document number, date, and shipment-row data.

### `source_docs_processor/extractor.py`

Contains text normalization and document-specific extraction logic.

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

This is currently the most document-specific module.

### `source_docs_processor/models.py`

Contains the main data structures.

Important models:

- `ExtractedDocument` — structured result of document recognition;
- filename-generation helpers for recognized documents and continuation pages.

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

## Recognition strategy

## Orientation selection

The program tries several orientations:

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

## UPD status detection

The status field is visually simple but OCR can be misleading because the left-side area contains explanatory text:

```text
1 - счет-фактура и передаточный документ
2 - передаточный документ (акт)
```

A naive OCR approach may accidentally read the explanation as status `2`. The application therefore uses tighter crops around the framed status digit and treats surrounding explanatory text cautiously.

The supported document type requires status `1`, an invoice marker, and a transfer-document marker.

## Document number extraction

The document number is extracted from multiple sources:

1. OCR text near the header.
2. Targeted crops around the document-number field.
3. The `Документ об отгрузке` row.

The `Документ об отгрузке` row often looks like this:

```text
№ п/п 1 № 511 от 21 марта 2023 г.
```

The first `1` is only the row number. The actual document number is after the next `№` sign.

## Document-number adjustment algorithm

Full-page OCR is not reliable enough for document numbers. In real scans, the number may be affected by:

- table lines;
- weak contrast;
- horizontal form strokes;
- punch holes;
- neighboring date digits;
- slightly shifted scans;
- over-wide OCR crops.

The adjustment algorithm compares candidates from the header/crop path and the shipment-row path.

It handles cases such as:

```text
2 548 -> 2548
2.548 -> 2548
2-548 -> 2548
43007 -> 430
4977  -> 497
4     -> 405, when the shipment row reliably contains 405
```

For the supported UPD template and normal-quality scans, this algorithm is intended to determine the document number practically in 100% of cases. Very poor scans, cropped headers, severe blur, or handwriting over the number can still require manual review.

## Date extraction

The document date is extracted from multiple sources:

1. `Документ об отгрузке` row.
2. Targeted document-date crop.
3. Header OCR.
4. General OCR only if the candidate is not a known service/template date.

The shipment row has high priority because it repeats the real document number and date in a compact field and is often less affected by punch holes than the top header date.

## Template-date filtering

The standard UPD form contains a service note in the top-right corner. That note mentions a government decree and the form revision date:

```text
2 апреля 2021 г. № 534
```

OCR can accidentally pick this date when the real document date is weak or partly hidden. This caused false filenames like:

```text
УПД_426_от_02-04-2021.png
```

The current logic explicitly ignores this template date when it comes from text containing service markers such as:

- `постановление`;
- `Правительства`;
- `Российской Федерации`;
- `1137`;
- `534`.

When a valid shipment-row date exists, it can replace a conflicting header/general OCR date.

## Continuation-page handling

Some documents are scanned as two sequential images. The second page may be almost empty and may not contain the `Счет-фактура` header, but it can still be important because it contains stamps and signatures.

The current continuation logic is conservative:

1. The program first tries to recognize every scan as a standalone UPD first page.
2. Only if standalone recognition fails does it check whether the scan is a continuation of the previous recognized document.
3. Continuation detection looks for markers such as signature fields, `Наименование экономического субъекта`, `составителя документа`, `М.П.`, `ТРАСТ`, and `Эталон`.
4. If the scan looks like a continuation, it inherits the previous document number and date.
5. The copied file name gets the `_2_страница` suffix.

This order prevents normal first-page UPD scans from being incorrectly attached to the previous document.

## Output model

For every input image, the result is one of:

### Recognized UPD transfer document

The file is copied and renamed:

```text
УПД_2548_от_27-12-2023.png
```

A detailed CSV row is written.

### Continuation page

The file is copied and named after the previous recognized document:

```text
УПД_2548_от_27-12-2023_2_страница.png
```

The CSV row contains inherited document metadata and a `continued_from` value.

### Unrecognized file

The file is copied unchanged. The CSV row intentionally contains only the source filename, so it is obvious that the file was processed but no reliable metadata was extracted.

## Debugging strategy

The `--debug-crops` option saves intermediate OCR crops under:

```text
<target_dir>/_debug/
```

This is the main tool for tuning recognition. It helps answer these questions:

- Did the crop hit the expected field?
- Was the document rotated correctly?
- Did preprocessing make the field readable?
- Did Tesseract read the status digit, number, date, or shipment row correctly?

## Known limitations

- The crop coordinates are currently tuned for one family of UPD layouts.
- Very poor scans still require manual review.
- Handwriting over printed fields is not reliably extracted.
- The project currently supports one primary document type in depth.
- There is no persistent OCR cache yet.
- Processing is currently sequential.

## Direction for generalization

A natural next architecture step is to introduce pluggable document extractors:

```text
DocumentExtractor
  -> can_handle(ocr_result) -> confidence
  -> extract(image, ocr_result) -> ExtractedDocument
```

The core pipeline would remain the same:

```text
scan -> OCR -> detect type -> extract fields -> actions
```

Document-specific modules would handle UPD, acts, waybills, invoices, contracts, or other accounting documents. Output behavior could also become action-based: copy/rename, registry only, statistics only, review folder, and so on.
