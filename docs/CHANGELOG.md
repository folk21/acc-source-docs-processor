# Changelog

## 0.27.0 — Configurable anonymization entity detection

### Added

- Added `entityDetectionMode` with `automatic`, `configured`, `combined`, and
  `disabled` values.
- Added combined analyzer behavior in which explicit `included` and
  `includedAndReplaced` spans take priority over overlapping automatic
  Presidio/spaCy detections.
- Added deterministic regression coverage for all modes, invalid mode values,
  backward-compatible legacy inference, combined replacement precedence, and
  matching CLI/Streamlit analyzer selection.
- Added a cross-project DRY guideline to `AGENTS.md`.

### Changed

- `excluded` now has an explicit mode contract: it filters automatic detections
  in `automatic` and `combined` modes but never cancels configured rules.
- `includedParagraphs` is documented as independent from entity-detection mode.
- Updated the example anonymization configuration, CLI help, localized UI help,
  installation guidance, usage documentation, architecture notes, roadmap, and
  anonymization development guide for the new mode contract.
- Bumped the package version to `0.27.0`.

### Preserved

- Configuration files without `entityDetectionMode` retain historical behavior:
  configured rules imply configured-only detection; otherwise automatic
  detection is used.
- Existing output formats, recursive processing, fuzzy OCR matching, replacement
  syntax, fail-closed format handling, and `includedParagraphs` behavior remain
  unchanged.

### Validation

- `make test-anonymization` (`59 passed`)
- `make test-ui` (`17 passed`)
- `make test-public-api` (`18 passed`)
- `make test-architecture` (`42 passed`)
- `make check` (`188 passed`)

## 0.26.0 — Complete localized operations UI and documentation ownership

### Added

- Added `docs/INSTALLATION.md` with GitHub download/clone steps, virtual-environment setup, Tesseract language verification, dependency profiles, Streamlit launch, update instructions, and troubleshooting for Windows, Linux, and macOS.
- Added `docs/USAGE.md` as the single user-facing source for CLI commands, processing workflows, anonymization configuration, output modes, and safe cleanup.
- Added localized Streamlit operations for scanned UPD status 1, NPD receipts, and incoming PDF/DOCX purchase documents through the public document-processing API.
- Added a generic processing UI adapter with metadata-driven controls, synchronous progress rendering, relative-path result rows, and generated-artifact tables.
- Added deterministic UI tests for public API forwarding, metadata resolution, processing path validation, and privacy-conscious result mapping.

### Changed

- Reduced the root README to a compact overview, quick start, privacy notice, and documentation index.
- Refocused architecture, roadmap, root development rules, and local package README files on their owning concerns and replaced repeated explanations with links.
- Preserved application feature behavior, public APIs, CLI options, registries, and output formats while expanding the Streamlit adapter.
- Updated Russian and English UI configurations, adapter documentation, architecture guidance, roadmap, and local AI rules.
- Bumped the package version to `0.26.0`.

### Validation

- `make test-ui` (`16 passed`)
- `make test-public-api` (`18 passed`)
- `make test-architecture` (`42 passed`)
- `make check` (`179 passed`)

## 0.25.0 — Localized Streamlit anonymization UI

### Added

- Added an optional local Streamlit adapter with a detailed application header, language selector, configured operation selector, operation explanation, parameter form, progress display, and result summary.
- Added Russian and English UI configurations under `config/ui/ui_<language>.ini`; the files own static UI text and the ordered list of enabled operation identifiers.
- Added the first UI operation for local document anonymization through the public feature API, including source/output/config paths, OCR language, output variants, layout preservation, and safe output cleanup.
- Added UI path validation, relative-path result mapping, optional `requirements-ui.txt`, `scripts/run_ui.sh`, focused `make test-ui`, and deterministic unit/smoke coverage.
- Added a local UI development guide and architecture regression checks that keep Streamlit outside core and feature dependencies.

### Changed

- Extended the root README, architecture guidance, roadmap, Make targets, and AI development rules for the optional localized UI adapter.
- Bumped the package version to `0.25.0`.

### Preserved

- Preserved CLI behavior, public feature APIs, document-processing workflows, anonymization behavior, output formats, and privacy rules.
- Kept Streamlit optional; normal CLI installations continue to use `requirements.txt`.

### Validation

- `make test-ui` (`11 passed`)
- `make test-architecture` (`42 passed`)
- `make check` (`174 passed`)

## 0.24.0 — Streamlit-ready document-processing API

### Added

- Added public `ProcessingSummary` with output roots, registry/report paths, aggregate counts, generated-file discovery, and compatible legacy tuple unpacking.
- Added public synchronous `ProcessingProgress` events and callback typing for scan, file, registry, and completion lifecycle updates.
- Added public `DocumentTypeMetadata`, `DOCUMENT_TYPE_METADATA`, and `get_document_type_metadata()` so UI adapters can build selectors and capability-aware controls without constructing OCR processors.
- Added integration coverage for progress and summary behavior across shared scan, NPD receipt, and incoming electronic-document workflows.

### Changed

- `process_folder()` now returns `ProcessingSummary` and accepts an optional `progress_callback`.
- `DocumentTypeDefinition` now owns the metadata for its registered processor/workflow/registry bundle.
- Updated public API regression contracts, root and local AI rules, embedded API documentation, architecture guidance, and roadmap.
- Bumped the package version to `0.24.0`.

### Preserved

- Preserved CLI behavior, registered document-type identifiers, OCR/extraction behavior, output names, registries, reports, and existing two-value result unpacking.

### Validation

- `make test-public-api` (`18 passed`)
- `make test-document-processing` (`95 passed`)
- `make check` (`159 passed`)

## 0.23.0 — Explicit public API regression contracts

### Added

- Added anonymization public API tests for exact package exports, supported constants, function signatures, and public configuration/result dataclass fields.
- Added document-processing public API tests for exact package exports, registered document-type identifiers, the `process_folder()` signature, and public extracted-document model fields.
- Added framework API tests for processor, registry, workflow, document-type definition, and copy/register extension exports, dataclass schemas, protocol methods, and override hooks.
- Added root package and CLI API tests for the supported version export, CLI entry points, and the legacy `cli.process_folder` alias.
- Added `make test-public-api` and included the public contract suite in `make test-architecture`.

### Changed

- Added explicit `__all__` declarations to the root package and document-processing public models module.
- Updated root and local `AGENTS.md`, README, architecture ownership guidance, roadmap, Make targets, and architecture tests for deliberate public compatibility changes.
- Bumped the package version to `0.23.0`.

### Preserved

- Preserved CLI behavior, processing and anonymization behavior, registered document-type identifiers, output files, OCR heuristics, registry schemas, and existing public call semantics.

### Validation

- `make test-public-api` (`17 passed`)
- `make test-architecture` (`37 passed`)
- `make check` (`154 passed`)

## 0.22.0 — Local AI ownership and validation guides

### Added

- Added local `AGENTS.md` files for anonymization, shared document processing, and every registered document type.
- Added a root `Makefile` with focused targets for core, architecture, anonymization, shared document processing, scanned UPD, NPD receipts, incoming purchase documents, and complete validation.
- Added a change ownership map to `docs/ARCHITECTURE.md` so local tasks identify their primary scope, allowed shared dependencies, excluded areas, and focused test target.
- Added architecture regression coverage requiring local agent guides and the standardized validation targets.

### Changed

- Updated feature and document-type README validation sections to use the standardized Make targets and link to their local development guides.
- Updated root development rules, architecture/testing documentation, roadmap, and user-facing test instructions for local-first development followed by full validation.
- Corrected stale architecture references to removed private test and contract locations.
- Bumped the package version to `0.22.0`.

### Preserved

- Preserved CLI commands, public APIs, registered document-type identifiers, OCR and anonymization behavior, output names, registries, reports, and file-layout behavior.

### Validation

- `make check` (`138 passed`)

## 0.21.0 — Visible document-processing framework contracts

### Changed

- Renamed and moved processor protocols and reusable defaults from `_internal/processors.py` to `processor_base.py` at the document-processing feature root.
- Moved the registry schema protocol from `_internal/registry/base.py` to the visible `registry_base.py` framework module while keeping writers and workbook helpers private.
- Moved `DocumentTypeDefinition` from `_internal/contracts.py` to `document_type_definition.py` at the feature root.
- Updated concrete processors, workflows, registries, definitions, the catalog, composition service, integration tests, and registry writers to use the visible framework contracts.
- Moved processor-base unit coverage to `tests/unit/document_processing/test_processor_base.py` and updated architecture tests for the new public/private boundary.
- Updated feature guidance, AI development rules, architecture documentation, roadmap, and package comments.
- Bumped the package version to `0.21.0`.

### Preserved

- Preserved CLI commands, public `process_folder()` behavior, registered document-type identifiers, OCR and anonymization behavior, output names, registries, reports, and file-layout behavior.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`136 passed`)

## 0.20.0 — Visible shared workflow framework

### Changed

- Renamed the shared workflow modules to `workflow_base.py` and `workflow_copy_and_register.py`.
- Moved both workflow framework modules from `document_processing/_internal/workflows/` to the document-processing feature root.
- Removed the now-empty `_internal/workflows/` package and updated all concrete workflows, definitions, composition services, and synthetic integration tests to use the new paths.
- Moved shared workflow unit coverage to `tests/unit/document_processing/test_workflows.py` while retaining processor and registry implementation tests under `_internal/`.
- Updated architecture tests, feature guidance, AI development rules, architecture documentation, and roadmap for the visible workflow extension boundary.
- Bumped the package version to `0.20.0`.

### Preserved

- Preserved CLI commands, public `process_folder()` behavior, registered document-type identifiers, OCR and anonymization behavior, output names, registries, reports, and file-layout behavior.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`136 passed`)

## 0.19.0 — Feature-private implementation packages

### Changed

- Reduced the anonymization feature root to package exports, `api.py`, and `command.py`; moved configuration, result contracts, recursive workflow, text analysis, and format handlers under `anonymization/_internal/`.
- Reduced the document-processing feature root to package exports, `api.py`, `command.py`, public extracted-document models, and the visible document-type catalog.
- Moved `DocumentTypeDefinition`, processor protocols and defaults, component composition, processing-specific file actions, shared OCR, registry writers, and workflow infrastructure under `document_processing/_internal/`.
- Replaced the two-file `normalization/` package with focused internal `date_normalization.py` and `money_normalization.py` modules.
- Removed the legacy processor-only compatibility factory; processor creation remains owned by complete document-type definitions.
- Simplified the public `process_folder()` signature so component injection is available only through the internal composition service used by deterministic integration tests.
- Mirrored feature-private tests under `tests/unit/anonymization/_internal/` and `tests/unit/document_processing/_internal/`.
- Updated feature guides, architecture documentation, roadmap, AI development rules, and package comments for the feature-level private API boundary.
- Bumped the package version to `0.19.0`.

### Added

- Added architecture regression checks for minimal feature roots, grouped document-processing infrastructure, private shared normalizers, and mirrored feature-private test packages.

### Preserved

- Preserved CLI commands, registered document-type identifiers, OCR and anonymization behavior, output names, registries, reports, and file-layout behavior.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`136 passed`)

## 0.18.0 — Private document-type implementation packages

### Changed

- Kept only `definition.py`, `processor.py`, `workflow.py`, and `registry.py` as framework-facing modules at each concrete document type root.
- Moved UPD OCR, crop, extraction, classification, continuation, confidence, and field-specific modules under `upd_invoices_status_1/_internal/`.
- Moved NPD receipt OCR, extraction, and QR parsing under `npd_receipts/_internal/`.
- Moved incoming purchase-document readers and extraction under `incoming_purchase_documents/_internal/`.
- Mirrored private implementation tests under `tests/unit/<document_type>/_internal/` while keeping framework and integration tests at the document-type test root.
- Removed top-level compatibility helper modules so the package root remains an explicit framework integration map.
- Updated feature guides, architecture documentation, AI development rules, and package comments for the private API boundary.
- Bumped the package version to `0.18.0`.

### Added

- Added architecture regression checks for framework-only document type roots, private-module dependency direction, and mirrored private unit-test layout.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`132 passed`)

## 0.17.0 — Core technical primitives and strict document normalization

### Changed

- Moved safe filename generation and duplicate-safe path selection into `source_docs_processor/core/files.py`.
- Parameterized `safe_filename()` with a caller-selected fallback while preserving `document` for processed-document copy actions.
- Moved document-neutral image discovery, non-ASCII image I/O, rotation, relative cropping, and OCR preprocessing variants into `source_docs_processor/core/images.py`.
- Moved inline and line-preserving whitespace normalization into `source_docs_processor/core/text.py`.
- Reduced `document_processing/file_ops.py` to `ExtractedDocument` copy actions and destination-state updates.
- Added strict shared Russian date and decimal normalization under `features/document_processing/normalization/`.
- Reused the shared strict normalizers from scanned UPD extraction while preserving noisy month aliases, crop recovery, template filtering, and table-position amount rules; other document types retain their existing format contracts until a behavior-neutral migration is justified.
- Updated architecture documentation, local feature guidance, and AI development rules with explicit admission criteria for `core`.
- Bumped the package version to `0.17.0`.

### Added

- Added unit coverage for generic filename, path, image, and whitespace helpers.
- Added unit coverage for strict shared date and decimal normalization.
- Added architecture regression coverage requiring generic technical primitives to remain in `core` and shared normalizers to remain concrete-type-neutral.

### Preserved

- Preserved CLI behavior, document type identifiers, OCR heuristics, warning codes, output names, registries, and anonymization behavior.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`129 passed`)

## 0.16.0 — Focused scanned-UPD extraction modules

### Changed

- Reduced `upd_invoices_status_1/extractor.py` to document assembly and warning orchestration.
- Split number normalization and reliability corrections, date parsing and template filtering, shipment-row parsing, continuation detection, page classification, party fields, amounts, transport details, confidence scoring, and OCR whitespace normalization into focused local modules.
- Added `identity_extraction.py` to coordinate header, targeted-crop, and shipment-row number/date sources without exposing those decisions to the document assembler.
- Updated UPD unit tests to import focused helpers from their owning modules while retaining legacy helper re-exports from `extractor.py` for compatibility.
- Updated package guidance, architecture documentation, and AI development rules for the decomposed extraction boundary.
- Bumped the package version to `0.16.0`.

### Added

- Added structural regression coverage requiring `extractor.py` to define only `extract_document()` and preserving the focused extraction module set.

### Preserved

- Preserved CLI behavior, registered document type identifiers, OCR heuristics, warning codes, recognition confidence, filenames, registry output, and continuation behavior.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`118 passed`)

## 0.15.0 — Explicit module boundaries

### Changed

- Renamed the processing feature package to `source_docs_processor/features/document_processing/` and nested concrete implementations under `document_processing/document_types/`.
- Moved the `process` and `anonymize` CLI adapters into the features that own those operations; `source_docs_processor/cli.py` remains only the composition root.
- Moved the reusable `process_folder()` entry point into `document_processing/api.py`.
- Separated the common `DocumentTypeDefinition` contract into `document_processing/contracts.py`.
- Added one lightweight `definition.py` to every concrete document type and limited the central catalog to importing those complete definitions.
- Kept document-processing infrastructure outside the concrete type packages and preserved all existing CLI commands and `--document-type` identifiers.
- Bumped the package version to `0.15.0`.

### Added

- Added technical README files for anonymization, document processing, and every concrete document type with public APIs, dependency rules, invariants, and focused test commands.
- Expanded architecture regression tests to prevent cross-feature imports, concrete-type cross-imports, shared-module knowledge of concrete implementations, catalog knowledge of internal classes, and top-level CLI imports of feature internals.

### Validation

- `python -m compileall -q main.py source_docs_processor tests`
- `python -m pytest -q` (`115 passed`)

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
