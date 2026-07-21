# Roadmap

Status legend:

- `[x]` Done / released in the current prototype
- `[/]` In progress / partially implemented
- `[ ]` To do / backlog

## Current document-processing scope

- [x] Recursively process image files from a source folder.
- [x] Support PNG, JPG, JPEG, TIFF, and BMP input files.
- [x] Detect UPD transfer documents with status `1`.
- [x] Extract document number.
- [x] Extract document date.
- [x] Copy recognized documents into a target folder.
- [x] Rename recognized documents using `УПД_<number>_от_<date>`.
- [x] Copy unrecognized files unchanged.
- [x] Preserve source subfolder structure in output.
- [x] Generate an Excel-friendly CSV registry.
- [x] Generate a text report.
- [x] Save debug OCR crops when requested.

## OCR reliability

- [x] Try multiple page rotations.
- [x] Save recognized sideways documents in the corrected orientation.
- [x] Use targeted OCR crops for status, document number, and document date.
- [x] Use `Документ об отгрузке` as a fallback source for number/date.
- [x] Ignore the UPD form-template date `02-04-2021` when it comes from service text.
- [x] Correct OCR over-read in document numbers.
- [x] Avoid false continuation-page detection for normal first pages.
- [/] Continue collecting private problematic examples outside the repository and tuning crop boxes.
- [ ] Add confidence levels per field instead of only one document-level score.
- [ ] Add a review folder for low-confidence documents.
- [ ] Add a machine-readable debug JSON file per processed document.

## Output and reporting

- [x] Use `--target-dir-name` for custom target folder names.
- [x] Use `--output` for custom output base directories.
- [x] Store file names in CSV instead of full local paths.
- [x] Add warnings to registry rows.
- [ ] Generate XLSX registry in addition to CSV.
- [ ] Generate a summary report with counts by year, subfolder, and recognition status.
- [ ] Generate a `not_recognized.csv` or review-only registry.
- [ ] Optionally split recognized/unrecognized/continuation files into separate folders.

## Performance

- [x] Keep full-page OCR limited by default.
- [x] Use targeted crops for high-value fields.
- [ ] Add persistent OCR cache keyed by file path, size, and modification time.
- [ ] Add optional parallel processing with `--workers`.
- [ ] Add a benchmark command for measuring OCR throughput on sample folders.
- [ ] Add a fast precheck mode that only detects likely UPD pages before deep extraction.

## Generalization

- [x] Keep the project name generic enough for source documents beyond UPD.
- [x] Keep the processing pipeline separable from UPD-specific extraction logic.
- [x] Introduce a document processor interface/protocol.
- [x] Move UPD status `1` parsing into a dedicated processor package.
- [x] Add a processor registry/factory.
- [ ] Add config-driven document type definitions for simple templates.
- [ ] Add configurable output actions: copy/rename, registry only, statistics only, review folder.
- [ ] Add support for other primary document types, for example acts, waybills, generic invoices, contracts, or payment documents.

## Configuration and usability

- [x] Provide command-line options for source, target name, output base, deep OCR, dry run, auto-rotation, debug crops, and document type.
- [ ] Add a YAML configuration file for profiles.
- [ ] Add named processing profiles, for example `tax_request_upd` and `archive_inventory`.
- [ ] Add a simple local UI for non-technical users.
- [ ] Add Windows-oriented setup instructions and run scripts.
- [ ] Add a validation command that checks Tesseract installation and language packs.

## Code quality

- [x] Use English comments and docstrings in code.
- [x] Keep the Python package name import-friendly: `source_docs_processor`.
- [x] Compile-check the project after changes.
- [x] Keep runtime dependencies in `requirements.txt` and test dependencies in `requirements-dev.txt`.
- [x] Add unit tests for number/date normalization and selection.
- [x] Add tests for shipment-row parsing.
- [x] Add tests for template-date filtering.
- [x] Add tests for continuation-page decision logic.
- [/] Add anonymized/synthetic regression fixtures for known problematic cases; current tests use OCR-text candidates, fake processors, and generated tiny PNGs.
- [x] Add processor factory tests.
- [x] Add integration tests for the generic folder pipeline with fake processor injection.
- [x] Add a testability injection point for `process_folder()`.
- [ ] Add linting and formatting configuration.
- [ ] Add CI workflow.
- [ ] Add private OCR fixture policy for local-only customer scans.

## Packaging

- [x] Provide archive script for project distribution.
- [ ] Add `pyproject.toml`.
- [ ] Package as an installable CLI.
- [ ] Add a standalone executable build option.
- [ ] Evaluate whether a future Rust CLI or Rust helper module is worth implementing after the Python logic stabilizes.
