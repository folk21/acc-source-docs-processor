# Roadmap

Status legend:

- `[x]` Done / released
- `[/]` In progress / partially implemented
- `[ ]` To do / backlog

## Generic architecture

- [x] Separate generic folder processing from document-specific OCR.
- [x] Select processors through an explicit factory registry.
- [x] Introduce a document-type-neutral `ExtractedDocument` model.
- [x] Use common issuer/recipient, date, amount, and description fields.
- [x] Support processor-specific values through `extra_fields`.
- [x] Let processors declare additional CSV columns.
- [x] Let processors control default output folders and filename conventions.
- [x] Provide reusable single-page and continuation behavior in `BaseDocumentProcessor`.
- [x] Test the generic pipeline with a synthetic non-UPD processor.
- [ ] Add config-driven processors for simple layouts after at least one more real processor exists.
- [ ] Evaluate entry-point plugin discovery only if external processor packages become necessary.

## Current UPD processor

- [x] Detect UPD invoice-transfer documents with status `1`.
- [x] Extract document number and date.
- [x] Preserve `Документ об отгрузке` fallback logic.
- [x] Filter the form-template date `02-04-2021`.
- [x] Correct suspicious short and over-read numbers.
- [x] Try multiple rotations and save upright output.
- [x] Detect continuation pages conservatively.
- [x] Preserve established UPD filenames after model generalization.
- [/] Continue tuning private problematic examples outside the repository.
- [ ] Add field-level confidence values.

## NPD receipts

- [ ] Add `source_docs_processor/npd_receipts/` as a separate processor package.
- [ ] Decode receipt QR codes locally.
- [ ] Extract receipt number, datetime, issuer, recipient INN, service description, and total amount.
- [ ] Reconcile QR values with OCR values and report conflicts.
- [ ] Support both clean print views and mobile screenshots.
- [ ] Add synthetic receipt fixtures without real names or INNs.
- [ ] Add an optional local INN-to-organization mapping file for recipient names.

## Output and review

- [x] Preserve source subfolder structure.
- [x] Copy unrecognized files unchanged.
- [x] Generate UTF-8 BOM semicolon-separated CSV.
- [x] Keep absolute paths out of the registry.
- [x] Generate a text report.
- [ ] Generate XLSX in addition to CSV.
- [ ] Add a review folder for low-confidence documents.
- [ ] Add a machine-readable debug JSON result per document.
- [ ] Add summary counts by document type, year, and recognition status.

## Performance

- [x] Keep full-page OCR optional for the UPD processor.
- [x] Prefer targeted crop OCR for high-value fields.
- [ ] Add a persistent OCR cache.
- [ ] Add optional parallel processing with `--workers`.
- [ ] Add a benchmark command.

## Configuration and usability

- [x] Support source, output, target name, document type, deep OCR, dry run, rotation, and debug crops.
- [x] Use processor-specific default target directory names.
- [ ] Add YAML processing profiles.
- [ ] Add a validation command for Tesseract and language packs.
- [ ] Add Windows-oriented setup instructions.
- [ ] Add a simple local UI.

## Code quality and packaging

- [x] Keep runtime and developer dependencies separate.
- [x] Add deterministic unit and integration tests.
- [x] Keep comments, docstrings, and software documentation in English.
- [ ] Add `ruff` configuration.
- [ ] Add CI.
- [ ] Add `pyproject.toml` and package the CLI.
- [ ] Add a standalone executable build option.
