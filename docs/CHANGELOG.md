# Changelog

## NPD receipt filename and compact workbook layout

- Changed copied receipt names to `<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>`.
- Reduced the NPD workbook to the requested eight columns.
- Added a hyperlink only to `target_file_name`; `source_file_name` is plain text.
- Kept the first receipt INN as the self-employed payment recipient INN.
- Added regression coverage for filename generation, exact column order, and hyperlink placement.

## NPD receipt copy, naming, and workbook regression fixes

- Restored copying and renaming of recognized NPD receipt images.
- Excel file hyperlinks now point to copied target files using relative external links.
- Restored the stable business-column order and the service-description column.
- Receipt numbers are accepted only after an explicit `Чек №`, `N`, `No`, or receipt-number label.
- Full names may span two consecutive lines: one surname line plus a two-word first-name/patronymic line.
- Added regression tests for split names, explicit receipt numbers, copied files, column order, and hyperlinks.

## NPD receipt registry and issuer identity extraction

- Added the `npd_receipts` document type and registry-only XLSX workflow.
- The first INN in receipt order is now treated as the self-employed issuer INN.
- The issuer's full name is selected from the same information block, with the
  second non-empty block used as an additional layout hint.
- The second INN remains available as the recipient organization INN.
- Added regression tests for full-name extraction and first-INN ownership.

This changelog describes the project evolution by functional milestones. The project is still pre-release and does not use strict semantic version tags yet.

## Independent processors, workflows, and registry definitions

### Added

- `source_docs_processor/document_types.py` with `DocumentTypeDefinition`.
- `source_docs_processor/workflows/` with workflow contracts, runtime options, results, logging helpers, and reusable `CopyAndRegisterWorkflow`.
- `source_docs_processor/registry/` with a registry definition protocol and generic validated CSV writer.
- `upd_invoices_status_1/workflow.py` for UPD copy, rename, continuation, and output-folder behavior.
- `upd_invoices_status_1/registry.py` for the detailed UPD CSV schema and row mapping.
- Integration tests that inject a fake processor, a separate fake workflow, and a separate registry definition.

### Changed

- `DocumentProcessor` now owns only image-level recognition and extraction.
- Removed target directory, filename, continuation preparation, and CSV policy from `BaseDocumentProcessor` and the UPD processor.
- Moved folder processing out of `cli.py` into the selected workflow.
- Reduced `file_ops.py` to low-level copying and image-output mechanics.
- The CLI now resolves one complete document type definition and runs its selected workflow.
- Bumped the package version to `0.9.0`.

### Preserved

- Existing UPD output directory behavior.
- Copying and renaming recognized UPD files.
- Copying unrecognized files unchanged.
- Relative subfolder preservation.
- Detailed UPD CSV and text report generation.
- Established UPD filenames and continuation suffixes.
- All current OCR heuristics and regression tests.

### Reason

Document types can require fundamentally different folder actions and CSV schemas. A future receipt type should be able to generate only a short registry in the source folder without inheriting UPD copy and rename behavior.

## Generic document model and initial output-policy generalization (superseded)

### Added

- `source_docs_processor/document_processor.py` with `DocumentProcessor` and `BaseDocumentProcessor`.
- A generic `ExtractedDocument` model with document identity, issuer/recipient, amount, currency, description, continuation state, and `extra_fields`.
- A document-neutral `OcrResult.targeted_fields` mapping for anchored processor OCR values.
- Processor-provided default target directory names.
- Processor-controlled primary and continuation filename generation.
- Common CSV columns plus validated processor-specific registry columns.
- Integration coverage using a synthetic non-UPD fake receipt processor.
- Unit coverage for generic continuation metadata inheritance and processor isolation.

### Changed

- Removed invoice- and UPD-specific fields from shared models, CLI logic, file operations, and common CSV output.
- Mapped UPD seller/buyer and VAT fields to generic issuer/recipient and tax fields.
- Moved the established UPD filename convention into `UpdInvoicesStatus1Processor`.
- Replaced the factory switch with a small explicit `PROCESSOR_FACTORIES` registry.
- Changed the shared CSV schema from invoice-oriented names to document-neutral names.
- Bumped the package version to `0.8.0`.

### Preserved

- UPD status `1` OCR and extraction heuristics.
- Rotation handling and corrected-orientation output.
- Shipment-row number/date fallback.
- Template-date filtering.
- Conservative continuation-page recognition.
- Existing `УПД_<number>_от_<date>` filenames and Russian page suffixes.

### Reason

The first processor boundary still left invoice-specific data names and output behavior in shared code. The new model allows receipts, acts, and other document types to reuse the pipeline without pretending that every document is an invoice.


## Privacy cleanup for tests and documentation

### Changed

- Replaced real company names in tests with clearly fictional sample company names.
- Clarified that integration tests use fake processors and generated tiny PNG files, not customer accounting scans.
- Restored dependency separation: runtime dependencies stay in `requirements.txt`, while `pytest` belongs to `requirements-dev.txt`.

### Reason

The project may be published to GitHub, so tests and documentation should not contain real company names or customer scanned documents.

## Test suite and pipeline testability

### Added

- `pytest.ini` with test discovery and markers for future OCR/slow tests.
- `requirements-dev.txt` for installing runtime plus test dependencies.
- `tests/unit/` with regression tests for document-number adjustment, date selection, shipment-row parsing, continuation-page detection, filename generation, and processor factory selection.
- `tests/integration/` with a fake-processor pipeline test that verifies copy/rename behavior, continuation pages, unrecognized files, output subfolders, and CSV registry rows.

### Changed

- `process_folder()` now accepts an optional injected document processor for tests and future embedded use. The CLI still uses the document processor factory by default.
- Continuation scoring now treats UPD/invoice header markers as a hard veto for continuation-page classification.

### Reason

The project had several regressions where one OCR fix accidentally reintroduced an older issue. The new tests focus on already observed bugs so future changes can safely refactor OCR and extraction logic.

## Processor factory and first generalization refactor

### Added

- `--document-type` CLI parameter.
- `source_docs_processor/processors.py` with a simple processor factory.
- `DocumentProcessor` protocol for document-specific processors.
- `source_docs_processor/upd_invoices_status_1/` package for UPD status 1 logic.
- `UpdInvoicesStatus1Processor` as the first registered processor.

### Changed

- Moved UPD-specific extraction logic from the top-level package into `upd_invoices_status_1/extractor.py`.
- Moved UPD-specific targeted OCR logic into `upd_invoices_status_1/ocr.py`.
- Moved UPD-specific crop coordinates into `upd_invoices_status_1/image_processing.py`.
- Kept generic image loading, rotation, OCR wrappers, file operations, and CLI orchestration in the top-level package.
- The CLI now asks the processor factory for the selected processor instead of importing UPD extraction functions directly.

### Reason

The project is evolving from a single-purpose UPD finder into a more general accounting source-document processor. The first step is to isolate document-template-specific logic behind a processor boundary while preserving current behavior.

## Initial prototype

### Added

- Recursive image scan processing.
- Detection of UPD transfer documents with status `1`.
- Extraction of document number and document date from OCR text.
- Creation of the default target directory `передаточные_документы`.
- Copying recognized scans into the target directory.
- Renaming recognized files using document number and date.
- CSV registry generation.

### Reason

The first goal was to reduce manual work when searching large folders of PNG scans for source documents requested by tax authorities.

## Rotation support

### Added

- Recognition attempts for 0°, 90°, 180°, and 270° orientations.
- Saving recognized sideways documents in the corrected orientation.
- `--no-auto-rotate` option.
- `rotation_degrees` in the registry.

### Fixed

- Sideways scans that previously had zero recognition confidence.

### Reason

Real archives contained scans rotated by 90 degrees.

## Output behavior improvements

### Added

- Copying unrecognized files into the target directory unchanged.
- CSV rows for unrecognized files with only the source filename filled.
- Preservation of source subfolder structure inside the target folder.
- Text report file with the same processing messages printed to the console.
- Skipping output folders to avoid reprocessing generated files.

### Changed

- CSV no longer stores full local file paths, only file names.

### Reason

The output folder should be useful for manual review, not only for fully recognized documents.

## Configurable target folder

### Added

- `--target-dir-name` parameter.
- Target folder creation in the current working directory by default.
- `--output` parameter for selecting a custom output base directory.

### Changed

- The default target folder is still `./передаточные_документы`, but it is no longer created inside the source scan directory unless that is also the current/output directory.

### Reason

Generated files should not be mixed into the original scan archive by default.

## Project rename and package cleanup

### Changed

- Project folder/repository name became `acc-source-docs-processor`.
- Internal Python package became `source_docs_processor`.
- Imports were updated.
- README was updated.
- Main files and methods received English docstrings/comments.

### Reason

The repository name describes the business purpose, while the Python package name is import-friendly and does not use hyphens.

## Targeted OCR and document-number adjustment

### Added

- Targeted crop OCR for document number.
- Targeted crop OCR for document date.
- Targeted crop OCR for status field.
- Debug crop output with `--debug-crops`.
- Document-number normalization.
- Adjustment algorithm for values like `2 548`, `2.548`, and `2-548`.

### Fixed

- Cases where the document number was visually present but general OCR did not connect it to the `Счет-фактура №` label.

### Reason

Full-page OCR is too noisy for scanned accounting forms. Targeted OCR is more reliable for key fields.

## `Документ об отгрузке` fallback

### Added

- Extraction of document number and date from the `Документ об отгрузке` row.
- Correct handling of rows like `№ п/п 1 № 511 от 21 марта 2023 г.`.
- Date fallback when the header date is unreadable.
- Number fallback when the header number is missing or suspiciously short.

### Fixed

- Documents where the top header date was hidden by punch holes or weak contrast.
- Documents where the header number was partially recognized.

### Reason

The shipment row repeats the actual document number and date and is often a more reliable OCR source than the top header.

## Continuation-page support

### Added

- Detection of probable second pages.
- Inheritance of previous document number/date for continuation pages.
- Naming convention with `_2_страница` suffix.
- Registry columns for continuation-page metadata.

### Fixed

- Second pages that were previously treated as unrecognized files even though they belonged to a recognized document.

### Reason

Some source documents are scanned as two sequential files, and second pages can contain important stamps or signatures.

## Template-date filtering

### Added

- Detection and rejection of the UPD form template date `02-04-2021` when it comes from the government-decree note.
- Date-source priority that allows the `Документ об отгрузке` date to override a conflicting template/header date.
- Warnings such as `ignored_form_template_date` and `document_date_replaced_by_shipment_row`.

### Fixed

- False output dates like `УПД_426_от_02-04-2021.png`.

### Reason

The standard UPD form contains a service date in the top-right corner. OCR sometimes captured it instead of the actual document date.

## Document-number over-read correction

### Added

- Comparison of header/crop number candidates with the shipment-row candidate.
- Correction of extra trailing digits in document numbers.
- Prefix-based selection rules for cases like `43007 -> 430` and `4977 -> 497`.

### Fixed

- Document numbers with one or two extra digits appended by OCR.

### Reason

Tesseract can over-read nearby date/form digits when the number crop is slightly too wide.

## Conservative continuation detection

### Changed

- The program now always tries standalone UPD recognition before testing for continuation-page status.

### Fixed

- Normal first-page documents being incorrectly named as `_2_страница` because they also had signature and stamp markers.

### Reason

First pages and continuation pages can both contain signatures, stamps, and company names. The safer rule is to detect continuation only after standalone recognition fails.

## Documentation expansion

### Added

- `docs/ARCHITECTURE.md`.
- `docs/CHANGELOG.md`.
- `docs/ROADMAP.md`.
- `AGENTS.md`.

### Changed

- README now provides a compact overview and links to detailed documentation.

### Reason

The project has accumulated enough OCR heuristics and operational rules to require dedicated documentation beyond the README.

## Test dependency documentation

### Changed

- Test instructions now explicitly use `requirements-dev.txt`.
- `requirements.txt` remains limited to runtime dependencies for ordinary document processing.
- README test-running instructions recommend `pip install -r requirements-dev.txt` followed by `python -m pytest -q`.

### Reason

The application runtime and the development/test environment should stay separate. Users who only process scans do not need `pytest`; developers who run tests should install developer dependencies.
