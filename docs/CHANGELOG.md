# Changelog

This changelog records project changes by functional milestone. The project is pre-release; only milestones with an established package version are grouped under a version heading.

## Unreleased

### Added

- Added the `npd_receipts` document type with a dedicated processor, workflow, and registry definition.
- Added local QR decoding and official NPD receipt URL parsing utilities. They are not yet integrated into receipt processing.
- Added a generic XLSX registry writer with formatted columns and portable external file hyperlinks.
- Added regression coverage for NPD extraction, filename generation, exact workbook columns, copied files, and hyperlink placement.

### Changed

- NPD receipt images are copied into a workflow-owned target directory while preserving relative source subfolders.
- Recognized receipts use `<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>` filenames.
- The NPD workbook uses the requested compact eight-column layout.
- Only `target_file_name` is a hyperlink; `source_file_name` remains plain text.
- Only recognized NPD receipts are included in the workbook; unrecognized images are still copied without renaming.
- Documentation describes both registered document types and distinguishes registry schemas from output workflows and writers.

### Fixed

- Restored copying and renaming of recognized NPD receipt images.
- Corrected workbook hyperlinks so they target copied files through relative external links.
- Receipt numbers are accepted only after an explicit `Чек №`, `N`, `No`, or receipt-number label.
- Full names can be recognized on one line or as a surname line followed by a first-name/patronymic line.
- The first INN in receipt order is treated as the self-employed payee INN; the second INN remains available as recipient data.

## 0.9.0 — Independent processors, workflows, and registry definitions

### Added

- Added `source_docs_processor/document_types.py` with `DocumentTypeDefinition`.
- Added `source_docs_processor/workflows/` with workflow contracts, runtime options, results, logging helpers, and reusable `CopyAndRegisterWorkflow`.
- Added `source_docs_processor/registry/` with a registry definition protocol and generic validated CSV writer.
- Added `upd_invoices_status_1/workflow.py` for UPD copy, rename, continuation, and output-folder behavior.
- Added `upd_invoices_status_1/registry.py` for the detailed UPD CSV schema and row mapping.
- Added integration tests that inject a fake processor, workflow, and registry definition independently.

### Changed

- `DocumentProcessor` owns only image-level recognition and extraction.
- Folder processing moved from `cli.py` into the selected workflow.
- Target-directory, filename, continuation-preparation, and registry policy were removed from `BaseDocumentProcessor` and the UPD processor.
- `file_ops.py` was reduced to low-level copy and image-output mechanics.
- The CLI resolves one complete document type definition and runs its selected workflow.
- The package version was set to `0.9.0`.

### Preserved

- Existing UPD output-directory behavior.
- Copying and renaming recognized UPD files.
- Copying unrecognized files unchanged.
- Relative subfolder preservation.
- Detailed UPD CSV and text report generation.
- Established UPD filenames, continuation suffixes, and OCR heuristics.

## 0.8.0 — Generic document model and initial output-policy generalization

This milestone was superseded by the independent workflow and registry architecture in `0.9.0`.

### Added

- Added `DocumentProcessor`, `BaseDocumentProcessor`, and a document-neutral `ExtractedDocument` model.
- Added `OcrResult.targeted_fields` for processor-specific anchored OCR values.
- Added generic document identity, party, amount, currency, description, continuation, and `extra_fields` support.
- Added initial processor-controlled output naming and registry extension points.
- Added synthetic non-UPD integration coverage and continuation metadata tests.

### Changed

- Removed invoice-specific field names from shared models and common pipeline code.
- Mapped UPD seller/buyer and VAT values to generic issuer/recipient and tax fields.
- Moved UPD filename generation behind a document-specific boundary.
- Replaced the initial factory switch with an explicit processor registry.

## Earlier pre-release milestones

### Initial UPD processor

- Added recursive image scanning.
- Added detection of Russian UPD invoice-transfer documents with status `1`.
- Added document number and date extraction.
- Added the default `передаточные_документы` output directory.
- Added copied and renamed recognized scans plus CSV registry generation.

### Rotation support

- Added recognition attempts for 0°, 90°, 180°, and 270° orientations.
- Added corrected-orientation output for sideways scans.
- Added `--no-auto-rotate` and `rotation_degrees` registry output.

### Output behavior

- Added copying of unrecognized files unchanged.
- Added minimal registry rows for unrecognized files.
- Added source-subfolder preservation, text reports, and output-folder exclusion.
- Removed absolute local paths from registry rows.
- Added `--output` and `--target-dir-name`.

### Processor factory and package separation

- Added `--document-type` and a processor factory.
- Added the `source_docs_processor/upd_invoices_status_1/` package.
- Moved UPD extraction, targeted OCR, and crop coordinates out of shared modules.
- Renamed the repository to `acc-source-docs-processor` and the import package to `source_docs_processor`.

### Targeted UPD OCR

- Added targeted crops for status, document number, and document date.
- Added debug crop output with `--debug-crops`.
- Added number normalization for OCR values such as `2 548`, `2.548`, and `2-548`.

### `Документ об отгрузке` fallback

- Added number and date extraction from the shipment row.
- Added correct handling of rows such as `№ п/п 1 № 511 от 21 марта 2023 г.`.
- Added fallback selection when the UPD header is obscured or incomplete.

### Continuation pages

- Added conservative second-page detection.
- Added inherited document metadata and `_2_страница` naming.
- Changed recognition order so standalone UPD pages are tested before continuation-page heuristics.
- Fixed first pages incorrectly classified as continuations because of signature or stamp markers.

### Template-date filtering

- Added rejection of the static UPD form date `02-04-2021` when it comes from regulation text.
- Added shipment-row date priority and diagnostic warnings.
- Fixed output names that incorrectly used the form-template date.

### Document-number correction

- Added comparison of header, crop, and shipment-row candidates.
- Added short-number replacement and trailing-digit over-read correction.
- Fixed examples such as `4 -> 405`, `43007 -> 430`, and `4977 -> 497` when a reliable fallback exists.

### Testing and privacy

- Added `pytest.ini`, `requirements-dev.txt`, deterministic unit tests, and fake-processor integration tests.
- Separated runtime and development dependencies.
- Replaced private names and scans with fictional or generated test data.
- Added regression coverage for OCR decisions, factory selection, filenames, continuation behavior, and registry output.

### Documentation

- Added `README.md`, `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, and `docs/ROADMAP.md` responsibilities.
- Kept detailed architecture and history outside the user-oriented README.
