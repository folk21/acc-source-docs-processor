# Roadmap

Status legend:

- `[x]` Done / released
- `[/]` In progress / partially implemented
- `[ ]` To do / backlog

## Generic architecture

- [x] Separate shared models from document-specific OCR.
- [x] Use a document-type-neutral `ExtractedDocument` model.
- [x] Separate image-level `DocumentProcessor` behavior from folder actions.
- [x] Introduce independently selectable `ProcessingWorkflow` implementations.
- [x] Introduce document-specific `RegistryDefinition` schemas and row mapping.
- [x] Bind processor, workflow, and registry factories through `DocumentTypeDefinition`.
- [x] Move generic CSV serialization into a document-neutral writer.
- [x] Keep low-level file copying independent from filename policy.
- [x] Test processor, workflow, and registry separation with synthetic components.
- [ ] Add config-driven processors only after at least two real processors need the same extension point.
- [ ] Evaluate entry-point discovery only if external processor packages become necessary.

## Current UPD document type

- [x] Detect UPD invoice-transfer documents with status `1`.
- [x] Extract document number and date.
- [x] Preserve `Документ об отгрузке` fallback logic.
- [x] Filter the form-template date `02-04-2021`.
- [x] Correct suspicious short and over-read numbers.
- [x] Try multiple rotations and save upright output.
- [x] Detect continuation pages conservatively.
- [x] Preserve copying, renaming, report generation, and detailed registry output.
- [x] Move UPD filename and continuation policy into its workflow.
- [x] Move UPD CSV shape into its registry definition.
- [/] Continue tuning private problematic examples outside the repository.
- [ ] Add field-level confidence values.

## NPD receipts

- [ ] Add `source_docs_processor/npd_receipts/` as a separate processor package.
- [ ] Add a registry-only workflow that does not copy or rename files.
- [ ] Write the receipt CSV directly in the source folder.
- [ ] Include only recognized receipts in the registry.
- [ ] Add portable hyperlink file cells.
- [ ] Use receipt columns: file, document number/date, recipient, amount, and issuer.
- [ ] Decode receipt QR codes locally.
- [ ] Reconcile QR values with OCR values and report conflicts.
- [ ] Support clean print views and mobile screenshots.
- [ ] Add synthetic fixtures without real names or INNs.
- [ ] Add an optional local INN-to-organization mapping for recipient names.

## Output and review

- [x] Preserve source subfolders for the UPD copy workflow.
- [x] Copy unrecognized files unchanged in the UPD workflow.
- [x] Generate UTF-8 BOM semicolon-separated CSV.
- [x] Keep absolute paths out of current registries.
- [x] Generate a text report for the UPD workflow.
- [ ] Generate XLSX where native hyperlinks are preferable.
- [ ] Add a review folder for low-confidence documents.
- [ ] Add machine-readable debug JSON.
- [ ] Add summary counts by document type and recognition status.

## Performance

- [x] Keep full-page OCR optional for UPD.
- [x] Prefer targeted crop OCR for high-value fields.
- [ ] Add a persistent OCR cache.
- [ ] Add optional parallel processing with `--workers`.
- [ ] Add a benchmark command.

## Configuration and usability

- [x] Support source, output, target name, document type, deep OCR, dry run, rotation, and debug crops.
- [x] Let each workflow interpret output-related options.
- [ ] Add YAML processing profiles.
- [ ] Add a Tesseract validation command.
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
