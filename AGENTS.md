# AGENTS.md

This file contains development rules for AI coding agents working on `acc-source-docs-processor`.

## Project summary

The project is a local CLI for scanned and electronic accounting source documents. A complete document type definition selects three independent parts:

```text
document processor + processing workflow + registry definition
```

The registered document types are:

- `upd_invoices_status_1` — the default scan-oriented document type;
- `npd_receipts`;
- `incoming_purchase_documents` — incoming purchase-document tasks for 1C entry; the current implementation supports PDF/DOCX UPD status `1` only.

## Language rules

- All code comments, docstrings, tests, configuration comments, and software documentation must be in English.
- Russian accounting field names may remain in OCR patterns, registry headers, and user-facing filenames where required by the business workflow.

## Architecture rules

- Keep `main.py` minimal.
- Keep top-level feature composition in `source_docs_processor/cli.py`.
- Keep each operation's parser and command handler in its owning feature
  `command.py`; the root CLI must not import format handlers, workflows,
  registries, or concrete document types.
- Read the nearest feature or document-type `README.md` before changing that
  module. Keep its public API, dependency rules, invariants, and focused tests in
  sync with structural changes.
- Keep independent operations under `source_docs_processor/features/`.
- Keep feature-neutral technical primitives under `source_docs_processor/core/`;
  core modules must not import feature modules.
- Admit code to `core` only when all of these conditions hold:
  1. it imports nothing from `features`;
  2. its API contains no UPD, receipt, invoice, registry, workflow, or other
     feature-specific concepts;
  3. its behavior remains meaningful without knowing a document type;
  4. another feature can call it without adapting business rules.
- Keep every feature root as a readable integration map. A feature root may
  contain `__init__.py`, `README.md`, `api.py`, `command.py`, genuinely public
  result models, and explicit framework extension modules used directly by the
  feature's registered implementations. Put configuration, format handlers,
  contracts, serializers, OCR containers, and other implementation details under
  the feature's `_internal/` package.
- Treat feature `_internal/` packages as private APIs. Modules outside the owning
  feature must not import them. Concrete document types may import shared
  `document_processing._internal` modules because they belong to that feature.
- Mirror private feature unit tests under
  `tests/unit/<feature>/_internal/`; keep API, command, and catalog tests at the
  feature test root.
- Keep anonymization's public surface in `features/anonymization/api.py` and its
  CLI adapter in `command.py`. Keep configuration, models, recursive workflow,
  text analysis, and PDF/DOCX/image/editable handlers under
  `features/anonymization/_internal/`.
- Keep document processing's stable programmatic surface in `api.py`,
  `command.py`, and `models.py`. Keep framework extension contracts used by
  concrete document types at the feature root: `document_type_definition.py`,
  `processor_base.py`, `registry_base.py`, `workflow_base.py`, and
  `workflow_copy_and_register.py`.
- Keep component injection, file actions, shared OCR, strict date/decimal
  normalizers, and registry serializers under
  `features/document_processing/_internal/`. Do not recreate internal
  `processors.py`, `contracts.py`, `registry/base.py`, or `workflows/` modules.
- The public `process_folder()` API must resolve registered components from the
  document type identifier and must not expose processor/workflow/registry
  injection parameters. Internal tests may use
  `_internal/service.py::process_folder_with_components()` with fake components.
- Keep strict reusable document-value parsing in
  `document_processing/_internal/date_normalization.py` and
  `money_normalization.py`. Keep OCR aliases, source priorities, template
  filtering, and other format heuristics inside the owning concrete document
  type.
- Keep concrete document implementations under
  `features/document_processing/document_types/`.
- Use CLI subcommands for distinct operations such as `process` and `anonymize`;
  do not model operations as document types.
- Keep `DocumentTypeDefinition` in
  `document_processing/document_type_definition.py`.
- Keep processor protocols and reusable processor defaults in
  `document_processing/processor_base.py`.
- Keep the registry schema contract in `document_processing/registry_base.py`;
  keep CSV/XLSX/task-workbook serialization under `_internal/registry/`.
- Each concrete document type must expose `DOCUMENT_TYPE` and `DEFINITION` from
  its own `definition.py`.
- Keep only framework-facing modules at a concrete document type package root:
  `definition.py`, `processor.py`, `workflow.py`, and `registry.py`.
- Put document-specific OCR, readers, parsing, classification, validation,
  normalization, and other implementation details under the owning document
  type's `_internal/` package.
- Treat a document type `_internal/` package as private to that type. Shared
  processing modules and other document types must not import it.
- Private document-type modules must not import `definition.py`, `workflow.py`,
  or `registry.py`; dependencies flow from framework-facing modules into
  `_internal/`, not in the opposite direction.
- Move code out of a document type `_internal/` only after its contract is
  document-type-neutral and belongs either to shared document-processing
  internals or to `core`.
- `document_types/catalog.py` may import complete definition modules, but must not
  import concrete processor, workflow, or registry classes directly.
- Shared document-processing `_internal` modules must not import a concrete
  document type. The composition service may resolve the catalog; only the
  catalog imports complete concrete definitions.
- One concrete document type must not import another.
- An image document processor owns only image-level recognition, orientation,
  OCR, extraction, normalization, and recognition decisions.
- A source-file processor owns only one-file reading, OCR fallback, extraction,
  normalization, and recognition decisions.
- A processor must not own folder traversal, copying, output folders, filename
  policy, report generation, or registry columns.
- A processing workflow owns recursive folder behavior, file actions, output
  selection, and the document list passed to a registry writer.
- Shared processor, registry, workflow, and document-type composition
  frameworks belong at the document-processing feature root. Concrete
  processor, registry, workflow, and definition modules remain in each document
  type package. Low-level file actions and registry serialization remain under
  `_internal/`.
- A registry definition owns the tabular schema and conversion of one
  `ExtractedDocument` into one row.
- Registry writers own serialization and belong under
  `document_processing/_internal/registry/`.
- Keep generic filename collision and image I/O helpers in `core`; keep only
  `ExtractedDocument` copy actions and destination-state updates in
  `document_processing/_internal/file_ops.py`.
- Keep template crops, OCR heuristics, readers, and parsing rules in the
  corresponding concrete document type's `_internal/` package.
- Do not add document-type conditionals to `cli.py`, feature command handlers, or
  shared processing modules.
- Do not add external network calls. Processing must remain local.
- Output cleanup must preserve the output directory inode; never delete and
  recreate the output root because another terminal may have it as its current
  directory.

`RegistryDefinition` is intentionally narrower than an output processor. It
defines columns and row mapping; workflows, file operations, and CSV/XLSX writers
handle the remaining output behavior.

## Generic model rules

Use these fields consistently:

- `document_number`, `document_date`, and `document_datetime` for identity;
- `issuer_*` for the issuing or service-providing party;
- `recipient_*` for the receiving or buying party;
- `amount_without_tax`, `tax_amount`, `total_amount`, and `currency` for money;
- `description` for goods or services;
- `extra_fields` only for document-specific extracted values.

Do not put output-action state into the generic extracted model unless it is necessary to describe a produced artifact.

## UPD rules

- Keep UPD-specific code under `source_docs_processor/features/document_processing/document_types/upd_invoices_status_1/`.
- Keep `definition.py`, `processor.py`, `workflow.py`, and `registry.py` at the UPD package root.
- Keep targeted OCR, crop modules, extraction, classification, continuation, and confidence logic under `upd_invoices_status_1/_internal/`; use generic image I/O, rotation, cropping, and OCR variants from `core.images`.
- Keep `_internal/extractor.py` limited to assembling `ExtractedDocument`; detailed identity, number, date, shipment-row, continuation, party, financial, transport, classification, and confidence rules belong in focused private modules. Shared strict date/decimal parsing belongs in `document_processing/_internal/date_normalization.py` and `money_normalization.py`, while noisy month aliases, template-date filtering, crop recovery, and UPD amount-position rules remain private to UPD.
- Import focused UPD helpers from `_internal/` only inside the UPD package and its matching private unit tests.
- Keep UPD copy, naming, and continuation attachment policy in `workflow.py`.
- Keep UPD CSV columns and row mapping in `registry.py`.
- Prefer targeted OCR crops over full-page OCR.
- Preserve `Документ об отгрузке` fallback logic.
- Preserve form-template date filtering for `02-04-2021`.
- Preserve short-number and over-read corrections.
- Recognize standalone pages before continuation pages.
- Preserve auto-rotation, debug crops, `УПД_<number>_от_<date>`, and `_2_страница` output names.

## Incoming purchase document rules

- Keep incoming purchase-document logic under `source_docs_processor/features/document_processing/document_types/incoming_purchase_documents/`.
- Keep native file reading in `_internal/readers.py`, extraction in `_internal/extractor.py`, file recognition in `processor.py`, folder behavior in `workflow.py`, and workbook rows in `registry.py`.
- Support UPD status `1` in `.pdf` and `.docx`; do not claim act or native `.doc` support.
- Prefer native PDF text and table extraction before OCR.
- OCR only PDF pages without a useful text layer unless `--deep-ocr` is enabled.
- Preserve one task per complete UPD and keep item rows linked through `task_id`.
- Keep `processed` binary and document-level as a `Нет`/`Да` dropdown; do not add editable item-level processing state.
- Link directly to source PDF/DOCX files; do not copy unchanged source files by default.
- Write directly into an explicit `--output` directory unless `--target-dir-name` is also provided.
- Keep `task_id` columns hidden and document their internal linking purpose.
- Keep unrecognized or incomplete files visible in `Documents` and `Review`.
- Reject explicit UPD status `2`.
- Keep workbook sheets `Documents`, `Items`, `Review`, and hidden `_metadata`.
- Reject the official UPD column-designator row (`1`, `1а`, `1б`, `2`, `2а`, and similar values) as item data.
- Keep numeric OKEI codes separate from textual unit names; never export a numeric code as `unit`.
- Validate item arithmetic and document totals without silently replacing conflicting values.

## NPD receipt rules

- Keep NPD-specific code under `source_docs_processor/features/document_processing/document_types/npd_receipts/`.
- Keep receipt OCR, extraction, and QR parsing under `npd_receipts/_internal/`.
- Keep copy, rename, output-folder, and workbook selection policy in `workflow.py`.
- Write directly into an explicit `--output` directory unless `--target-dir-name` is also provided.
- Keep the compact XLSX schema and row mapping in `registry.py`.
- Preserve copying of every source image and relative subfolder structure.
- Rename only recognized receipts; copy unrecognized images without renaming.
- Include only recognized receipts in `npd_receipts_registry.xlsx`.
- Do not generate a text report for the NPD receipt workflow.
- Preserve the filename pattern `<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>`.
- Preserve the exact eight-column workbook contract documented in `README.md`.
- Keep the hyperlink only in `target_file_name`; `source_file_name` must remain plain text.
- Treat the first INN in receipt order as the self-employed payee INN unless stronger verified data is introduced.
- Accept receipt numbers only after an explicit receipt-number label.
- Preserve one-line and split-line full-name recognition.
- QR decoding and official NPD URL parsing must remain local. When integrated, reconcile QR and OCR values explicitly and report conflicts instead of silently replacing data.

## Anonymization rules

- Keep anonymization as an operation under `source_docs_processor/features/anonymization/`; do not register it as a document type.
- Require source and output directories and preserve relative subfolders plus source file names.
- Keep all detection and redaction local. Do not add external APIs or cloud OCR.
- Use Microsoft Presidio with the Russian spaCy pipeline and explicit Russian accounting/identity pattern recognizers.
- Treat anonymization as fail-closed: unsupported source formats or opaque embedded content must not be copied unchanged into the anonymized output.
- Rebuild PDF files from redacted raster pages so hidden source text and metadata are removed.
- Strip image metadata and sanitize DOCX metadata, external relationships, custom XML, and supported embedded raster images.
- Reject DOCX macros, OLE/ActiveX objects, embedded workbooks, and unsupported vector media until a reliable sanitizer exists.
- Never log recognized PII values. Logs may contain only relative file paths, counts, and errors.
- Keep user configuration under `config/anonymization.ini` with `excluded`, `included`, `includedAndReplaced`, and `includedParagraphs` rules.
- Treat a non-empty `included` or `includedAndReplaced` list as configured-only mode: do not run the default analyzer and ignore `excluded`.
- Use `excluded` only to refine default detections when both configured include lists are empty.
- Treat `includedParagraphs` as an independent, stronger section-level rule once its heading has matched.
- Give `includedAndReplaced` precedence over `included` for identical spans and preserve the configured replacement value in editable and raster outputs.
- Preserve immediate privacy-safe progress output for long OCR runs.
- Exclude the output subtree during source traversal only when the output directory is nested inside the source directory; an output directory that contains the source must not suppress input discovery.
- Treat a zero-file effective scan as an error and include resolved path diagnostics without logging recognized content.
- Keep editable layout reconstruction image-free: approximate page geometry and OCR text positions, but never embed the original scan as a background.
- Keep public multiword anonymization options in camelCase: `--outputDocumentType`, `--outputLayout`, and `--alsoOutputSourceFormat`.
- When dual output is requested, write one anonymized source-format artifact and one requested-format artifact, avoid duplicate output when the formats already match, and resolve converted-name collisions deterministically.
- Document that OCR and NER are heuristic and that output requires manual review before external sharing.

## Testing rules

- Use `pytest`.
- Put pure logic tests under `tests/unit/` and pipeline/filesystem tests under `tests/integration/`.
- Group feature tests under folders matching the production feature, such as `tests/unit/anonymization/` and `tests/unit/document_processing/`. Mirror feature-private tests under `tests/unit/<feature>/_internal/`; keep command, API, public model, and catalog tests at the feature test root.
- Group document-specific tests under folders matching the production package name, such as `tests/unit/npd_receipts/` and `tests/integration/incoming_purchase_documents/`. Mirror document-private tests under `tests/unit/<document_type>/_internal/`; keep processor, workflow, registry, filename, and integration tests at the document-type test root.
- Keep only cross-feature architecture and CLI tests directly under `tests/unit/`; keep synthetic cross-component integration tests under `tests/integration/`.
- Every test must have an English docstring explaining the verified behavior and protected risk.
- Test processors, workflows, registry definitions, and writers independently where useful.
- Prefer fake OCR, fake processors, synthetic workflows, prepared text, and generated images.
- Every OCR or extraction bug fix must add a regression test.
- Real OCR tests must be optional, marked `ocr` or `slow`, and skipped when Tesseract is unavailable.
- Do not commit real scans, names, INNs/KPPs, addresses, shipment data, or debug crops from private documents.

Example launch scripts belong under `scripts/examples/`. They must use placeholder paths, run from the project root, and contain English comments only.

Run validation from the project root:

```bash
python -m compileall -q main.py source_docs_processor tests
python -m pytest -q
```

## Documentation rules

- Keep `README.md` user-oriented and compact.
- Put detailed design and component contracts in `docs/ARCHITECTURE.md`.
- Record completed changes in `docs/CHANGELOG.md`.
- Track planned and partially completed work in `docs/ROADMAP.md` using `[x]`, `[/]`, and `[ ]`.
- Update documentation when CLI behavior, supported document types, registry columns, output files, project structure, or component contracts change.
- Avoid changelog-style wording such as “now” or “previously” in documents that describe the current architecture.

## Archive checklist

1. Preserve the root folder `acc-source-docs-processor/`.
2. Keep all registered document types and the default scan UPD selection intact.
3. Include no private accounting fixtures or generated private output.
4. Confirm README commands, subcommands, example scripts, and output descriptions match current behavior.
5. Confirm processors contain no workflow or registry policy.
6. Confirm registry writers remain document-type-neutral.
7. Confirm architectural dependency tests pass for core, features, shared processing modules, the catalog, concrete document types, and `_internal/` ownership rules.
8. Run compile and test validation.
