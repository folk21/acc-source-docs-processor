# Changelog

## 0.14.0 — Feature-oriented package layout

### Changed

- Grouped independent operations under `source_docs_processor/features/`.
- Moved anonymization to `source_docs_processor/features/anonymization/`.
- Moved document-processing contracts, models, OCR helpers, workflows, registry writers, and concrete document types to `source_docs_processor/features/document_types/`.
- Replaced the former document-type registry module with `features/document_types/catalog.py` and package-level re-exports.
- Added `source_docs_processor/core/paths.py` for the path relationship helper shared by anonymization and document processing.
- Updated production imports, tests, comments, and architecture documentation without changing CLI commands or registered `--document-type` values.
- Bumped the package version to `0.14.0`.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`110 passed`)

## 0.13.8 — Stable output directory cleanup

### Added

- Added `--clearOutput` for safe in-place cleanup of prior anonymized files.
- Preserved the output root and existing subdirectory inodes so terminals opened in the output directory continue to observe generated files.
- Rejected cleanup when source is nested inside output.
- Added regression coverage for open-directory inode preservation and source safety.

## 0.13.7 — Output-directory traversal fix

### Fixed

- Fixed anonymization when the output directory is an ancestor of the source directory, including runs launched from the destination directory with `--output .`.
- Limited generated-output exclusion to the case where the output directory is nested inside the source directory.
- Changed an empty effective source scan from a silent zero-file success into a clear error with resolved source, output, and working-directory diagnostics.

This changelog records project changes by functional milestone. The project is pre-release.

## 0.13.6 — Configured pseudonym replacement

### Added

- Added multiline `includedAndReplaced` rules using `source -> replacement` syntax.
- Added exact replacement for native TXT and DOCX text, including values split across DOCX runs.
- Added OCR-fuzzy replacement for PDF, raster, embedded-image, and OCR-to-DOCX paths.
- Added raster replacement rendering which covers the source region before drawing the configured target.
- Added replacement precedence when the same source also appears in `included`.
- Added regression coverage for configuration parsing, malformed rules, replacement precedence, fuzzy OCR replacement, native DOCX runs, raster output, editable layout, and dual output.

### Changed

- Standardized public multiword anonymization options on camelCase: `--outputDocumentType`, `--outputLayout`, and `--alsoOutputSourceFormat`.
- Removed the older kebab-case aliases for those three options.
- Extended configured-only mode so either `included` or `includedAndReplaced` bypasses Presidio and ignores `excluded`.
- Bumped the package version to `0.13.6`.

## 0.13.5 — Dual anonymized output

### Added

- Added `--also-output-source-format` with the requested `--alsoOutputSourceFormat` alias.
- Added generation of both anonymized source-format and requested DOCX artifacts in one run.
- Added deterministic collision handling when converted DOCX names overlap source-format files.
- Added generated-artifact counts to privacy-safe console progress and the final summary.
- Added regression coverage for dual TXT/DOCX output, matching DOCX formats, required option validation, aliases, and output-name collisions.

### Preserved

- Omitting the new flag keeps the existing single-output behavior.
- A source already matching the requested format produces one artifact instead of a redundant duplicate.
- If either requested variant fails, partial artifacts for that source file are removed.

### Changed

- Bumped the package version to `0.13.5`.

## 0.13.4 — Approximate editable layout preservation

### Added

- Added `--output-layout preserve` with the requested `--outputLayout` alias.
- Added OCR line grouping and approximate reconstruction of page size, orientation, horizontal placement, vertical spacing, and font sizes.
- Added upright layout coordinates alongside original-image redaction coordinates.
- Added regression coverage for page geometry, rotated scans, positioned masked text, CLI aliases, and the no-background-image privacy guarantee.

### Preserved

- The original scan is never embedded in editable DOCX output.
- Native DOCX input continues to retain sanitized source formatting.
- Omitting `--output-layout` keeps the simpler editable paragraph output.

### Changed

- Bumped the package version to `0.13.4`.

## 0.13.3 — Editable DOCX anonymization output

### Added

- Added `--output-document-type docx` with the requested `--outputDocumentType` alias.
- Added editable OCR-to-DOCX reconstruction for PDF and raster inputs.
- Added TXT-to-DOCX conversion and preserved sanitized DOCX output for DOCX sources.
- Added deterministic collision-safe names when different source formats share one stem.
- Added regression coverage for CLI aliases, editable text masking, scanned PDF conversion, and output-name collisions.

### Preserved

- Omitting the option keeps each source file in its original format.
- Existing included-only, fuzzy OCR, includedParagraphs, metadata removal, and progress behavior remain unchanged.

### Changed

- Bumped the package version to `0.13.3`.

## 0.13.2 — OCR-tolerant included matching

### Added

- Added `includedFuzzy` to enable bounded fuzzy matching for configured `included` values in OCR-derived text.
- Added `includedFuzzyMaxErrors` with a validated range of `0` to `3` and a conservative default of `1`.
- Added normalization for punctuation, whitespace, `ё`/`е`, and common Latin/Cyrillic OCR lookalikes.
- Added regression coverage for one-character OCR substitutions, Latin/Cyrillic lookalikes, raster redaction, and invalid error limits.

### Preserved

- Native TXT and DOCX text continues to use exact literal matching.
- `includedParagraphs` remains independent from fuzzy included matching.
- Included-only mode continues to bypass Presidio and spaCy loading.

### Changed

- Updated the default configuration to enable OCR fuzzy matching with one permitted edit.
- Bumped the package version to `0.13.2`.

## 0.13.1 — Included-only anonymization mode

### Changed

- Changed a non-empty `included` list to become the only literal redaction source.
- Bypassed default Presidio detections and ignored `excluded` while included-only mode is active.
- Skipped Presidio and spaCy model loading in included-only mode.
- Kept `includedParagraphs` independent and active in both analyzer modes.
- Allowed multiword literal rules to match across spaces, tabs, and line breaks.
- Updated the default local configuration with the requested included-only values.
- Bumped the package version to `0.13.1`.

## 0.13.0 — Configurable anonymization rules and progress

### Added

- Added `config/anonymization.ini` with `excluded`, `included`, and `includedParagraphs` lists.
- Added case-insensitive literal inclusion and exclusion around default Presidio detections.
- Added section-level redaction below configured headings and across all following PDF/TIFF pages.
- Added immediate file progress plus PDF page and image-frame progress in the CLI.
- Added regression coverage for configuration parsing, literal overrides, section masking, later-page coverage, and progress callbacks.

### Changed

- Added optional `--config`, defaulting to `config/anonymization.ini`.
- Included configured headings in OCR orientation scoring.
- Bumped the package version to `0.13.0`.

## 0.12.0 — Local folder anonymization

### Added

- Implemented recursive directory-to-directory anonymization behind the `anonymize` subcommand.
- Added Microsoft Presidio configured with the Russian `ru_core_news_sm` spaCy NER pipeline.
- Added Russian accounting and identity pattern recognizers for INN, KPP, OGRN, SNILS, bank details, contacts, vehicle identifiers, and labeled document numbers.
- Added image OCR-coordinate redaction with multi-orientation Tesseract analysis.
- Added rasterized PDF rebuilding which removes source text layers and metadata.
- Added DOCX package text, metadata, relationship, custom XML, and embedded raster-image sanitization.
- Added TXT masking for UTF-8 and Windows-1251 files.
- Added deterministic unit and integration coverage without requiring real Presidio or Tesseract calls.

### Changed

- Changed `anonymize --source` and `--output` to directory-only semantics.
- Removed `--document-type` from the anonymization operation.
- Preserved relative subfolders and source file names in anonymized output.
- Bumped the package version to `0.12.0`.

### Safety

- Unsupported files are not copied unchanged into anonymized output.
- DOCX files with opaque embedded/active content or unsupported vector media fail closed.
- Per-file writes are atomic and partial outputs are removed after failures.
- Documentation requires manual review because OCR and NER detection remain heuristic.

## 0.11.2 — Compact NPD output

### Changed

- Renamed the NPD workbook to `npd_receipts_registry.xlsx`.
- Removed NPD text-report generation; the workflow now writes only copied images and the XLSX registry.
- Updated integration coverage for the new NPD output contract.

## 0.11.1 — Explicit NPD output directory

### Changed

- Changed the NPD receipt workflow so an explicit `--output` directory receives copied receipts, `реестр_чеков_нпд.xlsx`, and the text report directly.
- Preserved nested output only when `--target-dir-name` is provided or when the default output directory is used without `--output`.
- Added integration regression coverage preventing an unexpected `чеки_нпд` subdirectory below an explicit output path.

## 0.11.0 — Operation subcommands

### Added

- Added the `process` subcommand for all existing document-processing workflows.
- Added a reserved `anonymize` subcommand with source, output, and optional document-type arguments.
- Added `source_docs_processor/commands/` to separate command-specific parsing and execution from top-level CLI dispatch.
- Added `scripts/examples/` with processing examples for all registered document types and a future anonymization invocation.
- Added CLI regression tests for command selection, process options, the anonymization placeholder, and rejection of the obsolete flat syntax.

### Changed

- Changed all documented processing commands from `python main.py --source ...` to `python main.py process --source ...`.
- Kept `process_folder()` available through `source_docs_processor.cli` for existing programmatic and integration-test imports.
- Removed root-level `run.sh` and `run_example.sh` in favor of explicit examples grouped by operation and document type.

### Pending

- The `anonymize` command does not yet run Microsoft Presidio or create output; it exits with code `2` and a clear message.

## 0.10.3 — Test package organization

### Changed

- Grouped document-specific unit and integration tests under folders matching `incoming_purchase_documents`, `npd_receipts`, and `upd_invoices_status_1`.
- Kept generic model, OCR, document-type factory, and synthetic cross-component tests at the unit or integration root.
- Shortened document-specific test filenames because their package folder now provides the document-type context.
- Added package markers to nested test folders to prevent duplicate module-name import conflicts.

## 0.10.2 — Incoming UPD workbook usability and table fixes

### Changed

- Explicit `--output` directories receive the workbook and report directly instead of an additional default subfolder.
- Incoming PDF/DOCX source files are referenced through workbook links and are no longer copied unchanged.
- Replaced the document processing checkbox with a compatible `Нет`/`Да` dropdown.
- Hid `task_id` columns and added an English header comment explaining their internal purpose.
- Bumped the task workbook metadata schema to version `2`.

### Fixed

- Excluded the official UPD column-designator row (`1`, `1а`, `1б`, `2`, `2а`, and similar values) from extracted item rows.
- Separated numeric OKEI codes from textual unit names and prevented numeric values from being exported as units.
- Added regression coverage for the output layout, source-link behavior, dropdown validation, hidden task identifiers, header-row filtering, and unit normalization.

## 0.10.1 — Incoming purchase document identifier

### Changed

- Renamed the newly added CLI document type from `upd_invoices_status_1_files` to `incoming_purchase_documents`.
- Renamed its package, processor, workflow, registry definition, tests, and workbook metadata schema consistently.
- Kept the implementation scope limited to PDF/DOCX UPD status `1`; acts are not supported.

### Preserved

- Existing `upd_invoices_status_1` and `npd_receipts` identifiers and behavior remain unchanged.

## 0.10.0 — Electronic UPD task workbooks

### Added

- Added the separate `upd_invoices_status_1_files` document type without renaming or changing existing document types.
- Added local native-text and table reading for PDF files through PyMuPDF.
- Added OCR fallback for PDF pages without a useful text layer.
- Added direct DOCX paragraph and table reading through `python-docx`.
- Added `ExtractedDocumentItem` for repeating goods and service rows.
- Added extraction of UPD number, date, status, seller/buyer identifiers, item rows, net amount, VAT, and total amount.
- Added line and document arithmetic validation with explicit review warnings.
- Added a generic task workbook writer with `Documents`, `Items`, `Review`, and hidden `_metadata` sheets.
- Added binary document-level processing checkboxes and stable task UUIDs.
- Added duplicate-safe workbook naming so repeated runs do not overwrite accountant checkbox state.
- Added synthetic PDF/DOCX and workbook integration regression tests.

### Changed

- Generalized processor identity so workflows can select either image processors or source-file processors.
- Updated package dependencies with PyMuPDF and `python-docx`.
- Updated documentation for three independently registered document types.

### Preserved

- `upd_invoices_status_1` remains the default scan-oriented document type.
- Existing UPD scan filenames, rotation, continuation, CSV, and report behavior remain unchanged.
- Existing NPD receipt workbook and copy/rename behavior remain unchanged.

## 0.9.1 — NPD receipts

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

- Added `source_docs_processor/features/document_types/catalog.py` with `DocumentTypeDefinition`.
- Added `source_docs_processor/features/document_types/workflows/` with workflow contracts, runtime options, results, logging helpers, and reusable `CopyAndRegisterWorkflow`.
- Added `source_docs_processor/features/document_types/registry/` with a registry definition protocol and generic validated CSV writer.
- Added `features/document_types/upd_invoices_status_1/workflow.py` for UPD copy, rename, continuation, and output-folder behavior.
- Added `features/document_types/upd_invoices_status_1/registry.py` for the detailed UPD CSV schema and row mapping.
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
- Added the `source_docs_processor/features/document_types/upd_invoices_status_1/` package.
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
