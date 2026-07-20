# Changelog

This changelog describes the project evolution by functional milestones. The project is still pre-release and does not use strict semantic version tags yet.

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

The shipment row repeats the real document number and date and is often a more reliable OCR source than the top header.

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
