# Roadmap

Status legend:

- `[x]` Done / implemented
- `[/]` In progress / partially implemented
- `[ ]` To do / backlog

## Generic architecture

- [x] Introduce top-level CLI subcommands for independent operations.
- [x] Keep document processing under the `process` subcommand.
- [x] Reserve an `anonymize` command without coupling it to document-type registration.
- [x] Separate shared models from document-specific OCR.
- [x] Use a document-type-neutral `ExtractedDocument` model.
- [x] Separate image-level `DocumentProcessor` behavior from folder actions.
- [x] Introduce independently selectable `ProcessingWorkflow` implementations.
- [x] Introduce document-specific `RegistryDefinition` schemas and row mapping.
- [x] Bind processor, workflow, and registry factories through `DocumentTypeDefinition`.
- [x] Keep low-level file copying independent from filename policy.
- [x] Add document-neutral CSV and XLSX writers.
- [x] Test processor, workflow, and registry separation with synthetic components.
- [ ] Reuse `registry/common.py` consistently to remove duplicated writer validation.
- [ ] Evaluate whether the existing processors share enough structure for config-driven definitions.
- [ ] Evaluate entry-point discovery only if external processor packages become necessary.

## UPD status 1

- [x] Detect UPD invoice-transfer documents with status `1`.
- [x] Extract document number and date.
- [x] Preserve `Документ об отгрузке` fallback logic.
- [x] Filter the form-template date `02-04-2021`.
- [x] Correct suspicious short and over-read numbers.
- [x] Try multiple rotations and save upright output.
- [x] Detect continuation pages conservatively.
- [x] Preserve copying, renaming, report generation, and detailed registry output.
- [x] Keep UPD filename and continuation policy in its workflow.
- [x] Keep UPD CSV shape in its registry definition.
- [/] Continue tuning private problematic examples outside the repository.
- [ ] Add field-level confidence values.

## Incoming purchase documents

- [x] Add `incoming_purchase_documents` without renaming existing document types.
- [x] Limit the initial implementation to UPD status `1`; acts remain out of scope.
- [x] Support native-text PDF and DOCX inputs.
- [x] Use OCR fallback for image-only PDF pages.
- [x] Extract document number, date, status, seller, buyer, and totals.
- [x] Add first-class goods and service item rows.
- [x] Generate one workbook with `Documents`, `Items`, `Review`, and `_metadata`.
- [x] Add binary document-level processing dropdowns.
- [x] Link to original source files without copying unchanged PDF/DOCX inputs.
- [x] Write directly into an explicitly selected output directory.
- [x] Add stable hidden task UUIDs for future task aggregation.
- [x] Ignore official UPD column-designator rows during item extraction.
- [x] Separate numeric OKEI codes from textual unit names.
- [x] Add arithmetic validation and explicit review warnings.
- [ ] Tune PDF table extraction against private supplier layouts.
- [ ] Add optional support for more PDF table reconstruction strategies.
- [ ] Add field-level confidence for each extracted item value.
- [ ] Add workbook update mode that preserves existing processed values.
- [ ] Add an aggregate task summary across UPD and NPD workbooks.

## NPD receipts

- [x] Add `source_docs_processor/npd_receipts/` as a separate processor package.
- [x] Add a copy-and-register workflow that renames recognized receipts.
- [x] Preserve relative source subfolders in copied output.
- [x] Copy unrecognized receipt images without renaming.
- [x] Write `npd_receipts_registry.xlsx` inside the target directory.
- [x] Write NPD artifacts directly into an explicit `--output` directory unless a target name is requested.
- [x] Keep the NPD output limited to copied images and the XLSX registry without a text report.
- [x] Include only recognized receipts in the workbook.
- [x] Keep the exact compact eight-column workbook contract.
- [x] Add a hyperlink only to `target_file_name`.
- [x] Extract the first INN as the self-employed payee INN.
- [x] Recognize one-line and split-line full names.
- [x] Require an explicit label before accepting a receipt number.
- [/] Integrate the existing local QR decoder and NPD URL parser into receipt processing.
- [ ] Reconcile QR values with OCR values and report conflicts.
- [ ] Improve support for clean print views and mobile screenshots.
- [ ] Add synthetic OCR image fixtures without real names or INNs.
- [ ] Add an optional local INN-to-organization mapping for recipient names.

## Output and review

- [x] Preserve source subfolders for UPD and NPD copy workflows.
- [x] Copy unrecognized files unchanged in both current workflows.
- [x] Generate UTF-8 BOM semicolon-separated CSV for UPD.
- [x] Generate formatted XLSX with portable file hyperlinks for NPD receipts.
- [x] Keep absolute paths out of current registry cells.
- [x] Generate text reports for UPD workflows where an audit report is part of the output contract.
- [x] Reuse XLSX output for electronic UPD task workbooks.
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

- [x] Move launch examples into `scripts/examples/`.
- [x] Implement local directory anonymization behind the `anonymize` subcommand.
- [x] Add Microsoft Presidio with Russian spaCy NER and accounting/identity recognizers.
- [x] Add fail-closed PDF, DOCX, TXT, and raster-image output sanitization.
- [x] Add configurable default-mode exclusions, included-only literal redaction, and section-level redaction headings.
- [ ] Add custom organization/person dictionaries beyond literal matching.
- [ ] Add an optional machine-readable anonymization audit report without PII values.
- [x] Support source, output, target name, document type, deep OCR, dry run, rotation, and debug options.
- [x] Let each workflow interpret output-related options.
- [ ] Add YAML processing profiles when repeated real configurations justify them.
- [ ] Add a Tesseract validation command.
- [ ] Add Windows-oriented setup instructions.
- [ ] Add a simple local UI.

## Code quality and packaging

- [x] Keep runtime and developer dependencies separate.
- [x] Add deterministic unit and integration tests.
- [x] Group document-specific tests by production package while keeping shared tests at the unit/integration root.
- [x] Keep comments, docstrings, and software documentation in English.
- [ ] Add missing English docstrings to NPD regression tests.
- [ ] Add `ruff` configuration.
- [ ] Add CI.
- [ ] Add `pyproject.toml` and package the CLI.
- [ ] Add a standalone executable build option.
