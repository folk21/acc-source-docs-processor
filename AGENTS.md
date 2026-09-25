# AGENTS.md

This file contains cross-project development rules for
`acc-source-docs-processor`. Read the nearest local `AGENTS.md` before changing a
feature, UI adapter, or concrete document type; local guides own detailed
invariants and focused validation commands.

## Project summary

The project is a local Python application for accounting source documents. It
provides:

- `process` for registered document-processing workflows;
- `anonymize` for local fail-closed document redaction;
- `reconcile-expenses` for matching receipt/ticket files to an XLSX bank statement;
- an optional local Streamlit adapter that calls public feature APIs.

A processable document type combines:

```text
processor + processing workflow + registry definition + metadata
```

Registered document types are `upd_invoices_status_1`, `npd_receipts`, and
`incoming_purchase_documents`.

## Source of truth

Use this ownership order when sources disagree:

1. the current project tree, production code, machine-readable configuration, and
   output schemas define implemented behavior;
2. tests define verified behavior;
3. active specifications under `docs/specs/active/` define intended changes for
   current work;
4. owning current-state documentation defines architecture, usage, installation,
   testing, and package contracts;
5. `docs/ROADMAP.md` defines priorities and backlog candidates;
6. archived specifications are historical context only.

When a project archive or snapshot is supplied for a task, inspect that current
snapshot before relying on repository history or older documentation.

## Language and privacy

- Write code comments, docstrings, tests, configuration comments, and software
  documentation in English.
- Russian accounting field names may remain in OCR patterns, registry headers,
  localized UI text, and business-facing filenames.
- Keep processing local. Do not add external APIs, cloud OCR, telemetry, or
  remote document storage without an explicit approved design.
- Never commit real scans, company names, INNs/KPPs, addresses, shipment data,
  debug crops, or generated private output.
- Use synthetic files and fictional accounting data in tests and documentation.

## Architecture

- When adding code, follow DRY (Don't Repeat Yourself) where practical. Reuse
  existing logic when the behavior is genuinely shared, without introducing
  premature abstractions for unrelated cases.
- Keep `main.py` and `streamlit_app.py` minimal entry points.
- Keep CLI composition in `source_docs_processor/cli.py`; each feature owns its
  parser and command handler in `command.py`.
- Keep independent operations under `source_docs_processor/features/`.
- Keep feature-neutral technical primitives under `source_docs_processor/core/`.
  Core must not import features or the UI.
- Keep the optional Streamlit adapter under `source_docs_processor/ui/`. Features
  and core must not import the UI or Streamlit.
- UI code may import only public feature package APIs, never feature `_internal`
  modules or CLI commands through `subprocess`.
- Treat every feature `_internal/` and concrete document-type `_internal/` as a
  private API owned by that scope.
- One feature must not import another feature's `_internal` package.
- Expense reconciliation is an independent feature, not a document type: it owns
  two-input orchestration and cross-document matching under
  `features/expense_reconciliation/`.
- Shared document-processing modules must not import concrete document-type
  internals. One concrete document type must not import another.
- Use explicit document-type registration through complete definitions. Do not
  add document-type conditionals to the root CLI, feature command handlers, or
  shared processing modules.

See [Architecture](docs/ARCHITECTURE.md) for the current dependency map and
change ownership table.

## Document-processing contracts

- A processor owns recognition and extraction for one input file only.
- A workflow owns recursive traversal, output policy, copying/linking, filenames,
  reports, and the document list passed to writers.
- A registry definition owns columns and row mapping; writers own serialization.
- `DocumentTypeDefinition` binds processor, workflow, registry, and metadata.
- Concrete document-type roots expose only `definition.py`, `processor.py`,
  `workflow.py`, and `registry.py`; readers, OCR, parsing, classification, and
  validation stay under the owning `_internal/` package.
- The public `process_folder()` API resolves registered components, returns
  `ProcessingSummary`, and accepts an optional synchronous progress callback.
- Internal fake-component integration tests may use
  `_internal/service.py::process_folder_with_components()`.
- Every workflow emits the standard progress lifecycle without OCR text or
  extracted accounting field values.
- Keep public `__all__`, signatures, protocol hooks, dataclass fields, document
  type identifiers, and metadata capability flags synchronized with public API
  regression tests.

## Generic models

Use the shared accounting field names consistently:

- `document_number`, `document_date`, and `document_datetime`;
- `issuer_*` and `recipient_*`;
- `amount_without_tax`, `tax_amount`, `total_amount`, and `currency`;
- `description`;
- `items` for repeating goods or service rows;
- `extra_fields` only for document-specific scalar values.

Do not place output-action state or repeating item data into `extra_fields`.

## Output safety

- Preserve source files; processing workflows copy or link according to their
  documented contract.
- Keep absolute local paths out of portable registry cells unless the format
  explicitly requires them.
- Output cleanup must preserve the output root inode. Never delete and recreate
  the root because another terminal may have it as its current directory.
- Anonymization must fail closed for unsupported formats or opaque content.
- Never log or display detected PII values.

## UI configuration

- Store localized text and enabled operation order in
  `config/ui/ui_<language>.ini`.
- Keep operation identifiers and configuration keys language-neutral.
- Configuration may select only known explicit Python handlers; it must not
  contain arbitrary executable import paths.
- Russian remains the default UI language and may be overridden with Streamlit
  script arguments such as `-- --lang en`.
- Prefer relative paths and privacy-safe counts in UI progress and result tables.

## Testing

- Use `pytest`.
- Put pure logic under `tests/unit/` and filesystem/pipeline coverage under
  `tests/integration/`.
- Mirror feature and document-type `_internal/` packages in their private unit
  test folders.
- Keep cross-feature CLI, architecture, and root public API tests at the unit
  root.
- Prefer fake OCR, prepared text, fake processors, generated images, and
  synthetic PDF/DOCX files.
- Every extraction, OCR, workflow, or privacy bug fix requires a regression test.
- Every test must have an English docstring explaining verified behavior and the
  protected risk.
- Real OCR tests must be optional, marked `ocr` or `slow`, and skipped when
  Tesseract is unavailable.
- Run `make test-public-api` after changing exports, public models, signatures,
  framework protocols, or registered identifiers.
- Run `make test-ui` after changing Streamlit logic, localization, UI path
  validation, or UI result mapping.
- Use the nearest local guide and `docs/TESTS.md` to select a focused target.
- Run `make check` before completing a change unless the environment prevents it;
  report any check that could not be run.

## Specifications and feature vocabulary

- Stable capability identifiers live in `docs/FEATURES.md`. Reuse an existing
  feature ID when a change refines an existing capability.
- Significant intended changes live under `docs/specs/active/`; completed specs
  move to `docs/specs/archive/` after stable behavior is documented by its
  current-state owner.
- A spec is a change contract, not a permanent second copy of architecture or
  usage documentation.
- A specification must exist in exactly one lifecycle location. Archival is a
  move, not a duplicated copy.
- Keep umbrella `current_focus`, `docs/specs/README.md`, and the active spec tree
  consistent.
- Reverse-engineered archive specs are historical reconstructions. Do not use
  them to override current code/tests.
- Do not create a new feature ID for a release number, refactor, temporary task,
  or individual bug fix.

Read `docs/specs/README.md` before creating or moving specifications.

## Documentation ownership

Avoid copying the same explanation between documents. Use one owning document
and links from the others:

- `README.md` — compact project overview and entry points;
- `docs/INSTALLATION.md` — Windows, Linux, macOS, dependency installation, and
  launch;
- `docs/USAGE.md` — commands, options, configuration, and output behavior;
- `docs/ARCHITECTURE.md` — boundaries, composition, and ownership;
- `docs/FEATURES.md` — stable feature vocabulary for specs/tests/docs;
- `docs/specs/README.md` — specification workflow and lifecycle;
- `docs/specs/active/` — intended significant changes currently selected for work;
- `docs/specs/archive/` — completed historical change contracts;
- `docs/TESTS.md` — test strategy and validation command ownership;
- `docs/QUALITY.md` — active quality gates and planned tooling policy;
- `docs/CHANGELOG.md` — completed release history;
- `docs/ROADMAP.md` — active and planned work with a compact released-foundation
  summary;
- local `README.md` files — package contracts close to code;
- local `AGENTS.md` files — protected behavior and development rules.

Update documentation when CLI behavior, supported document types, installation,
registry schemas, output files, public APIs, or architecture changes.

## Local guides

- `source_docs_processor/features/anonymization/AGENTS.md`
- `source_docs_processor/features/document_processing/AGENTS.md`
- `source_docs_processor/features/expense_reconciliation/AGENTS.md`
- `source_docs_processor/features/document_processing/document_types/*/AGENTS.md`
- `source_docs_processor/ui/AGENTS.md`

## Working style

1. Identify the owning feature/document type and read the nearest local
   `AGENTS.md`.
2. Inspect implementation, tests, and any active specification for that scope.
3. Make the smallest coherent change and preserve unrelated behavior.
4. Run the focused validation for the owning scope, then broader checks when
   contracts or boundaries changed.
5. Update only the owning current-state documentation and specification lifecycle
   records that actually changed.
6. Report changed files, validation performed, and anything left unverified.

## Progressive disclosure

Read detailed guidance only when relevant:

- `docs/FEATURES.md` — stable capability IDs;
- `docs/specs/README.md` — specification workflow;
- `docs/ARCHITECTURE.md` — dependency direction and ownership;
- `docs/TESTS.md` — test layers and commands;
- `docs/QUALITY.md` — repository quality gates;
- the nearest feature/document-type/UI `AGENTS.md` — protected local behavior.

## Archive checklist

1. Preserve the root folder `acc-source-docs-processor/`.
2. Include no private scans, identifiers, configurations, or generated output.
3. Keep documented commands, requirements files, and actual behavior aligned.
4. Keep all registered document types and the default selection intact.
5. Confirm processors, workflows, registries, features, core, and UI preserve
   their dependency boundaries.
6. Confirm local guides and focused Make targets match the package layout.
7. Run `make check`.
