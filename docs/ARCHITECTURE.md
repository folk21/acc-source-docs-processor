# Architecture

`acc-source-docs-processor` is a local application with two independent
operations and two outer adapters:

```text
CLI ----------> public feature API ----------> feature implementation
Streamlit ----> public feature API ----------> feature implementation
```

The UI and CLI select operations. Document types belong only to the `process`
operation.

```text
process
  -> DocumentTypeDefinition
      -> Processor
      -> ProcessingWorkflow
      -> RegistryDefinition

anonymize
  -> recursive folder workflow
      -> text analyzer
      -> format-specific sanitizer
```

## Architectural goals

- keep processing local and privacy-conscious;
- keep the CLI and Streamlit adapter thin;
- separate generic technical primitives from feature behavior;
- separate one-file recognition from folder workflows and registry schemas;
- keep document-type rules isolated;
- expose small public APIs while keeping implementation packages private;
- prefer explicit registration over plugin discovery while all implementations
  live in this repository.

## Project structure

```text
main.py                         # CLI entry point
streamlit_app.py                # local Streamlit entry point
config/
├── examples/                   # portable user configuration examples
└── ui/                         # localized UI text and operation order
docs/
├── INSTALLATION.md             # platform installation and launch
├── USAGE.md                    # commands, configuration, and outputs
├── ARCHITECTURE.md             # this document
├── ROADMAP.md                  # active and planned work
└── CHANGELOG.md                # release history
source_docs_processor/
├── cli.py                      # feature command composition
├── ui/                         # optional Streamlit adapter
├── core/                       # feature-neutral technical primitives
└── features/
    ├── anonymization/
    │   ├── api.py
    │   ├── command.py
    │   └── _internal/
    └── document_processing/
        ├── api.py
        ├── command.py
        ├── models.py
        ├── document_type_definition.py
        ├── processor_base.py
        ├── registry_base.py
        ├── workflow_base.py
        ├── workflow_copy_and_register.py
        ├── _internal/
        └── document_types/
            ├── catalog.py
            ├── upd_invoices_status_1/
            ├── npd_receipts/
            └── incoming_purchase_documents/
```

## Dependency direction

```text
cli -> feature command -> public feature API -> feature _internal -> core
ui  -> public feature API

document-processing API -> internal composition service -> catalog
catalog -> complete document type definition
complete definition -> processor + workflow + registry -> type _internal
```

Forbidden directions:

```text
core -X-> features or ui
features -X-> ui
ui -X-> feature _internal
one feature -X-> another feature's _internal
shared document processing -X-> concrete type _internal
one concrete document type -X-> another concrete document type
```

Architecture regression tests enforce these boundaries.

## Core

`source_docs_processor/core/` contains feature-neutral filesystem, image, path,
and text primitives. A core helper must remain meaningful without knowing an
operation, document type, processor, workflow, registry, UPD, receipt, or invoice
concept.

Core currently owns:

- safe filename and collision handling;
- non-ASCII OpenCV image I/O;
- image discovery, rotation, cropping, and neutral OCR preprocessing;
- path relationship checks;
- whitespace normalization.

## Feature boundaries

A feature root is a public integration map. Stable public entry points and the
CLI adapter remain visible; implementation details live under `_internal/`.
Modules outside a feature must not import its `_internal` package.

Detailed feature contracts are documented next to the code:

- [Anonymization feature](../source_docs_processor/features/anonymization/README.md)
- [Document-processing feature](../source_docs_processor/features/document_processing/README.md)
- [Local Streamlit adapter](../source_docs_processor/ui/README.md)

The nearest `AGENTS.md` contains development invariants and focused validation
commands. This architecture document intentionally does not duplicate those
rules.

## Document-processing framework

A complete `DocumentTypeDefinition` binds three independent components and its
UI-facing metadata:

```text
DocumentTypeDefinition
├── processor factory
├── workflow factory
├── registry-definition factory
└── DocumentTypeMetadata
```

### Processor

A processor owns one input file:

- image orientation and OCR for scan processors;
- native text, table reading, and OCR fallback for source-file processors;
- field extraction, normalization, confidence, warnings, and recognition state.

A processor does not own recursive traversal, output folders, copying, filenames,
reports, or registry columns.

### Processing workflow

A workflow owns run-level behavior:

- recursive source selection;
- output-directory policy;
- copying, linking, and filename policy;
- continuation attachment where applicable;
- selection of rows passed to registry writers;
- report generation;
- standard synchronous progress events.

Every registered workflow emits `scan_started`, paired
`file_started`/`file_finished`, `registry_written` when applicable, and
`run_finished`. Events contain paths, counts, recognition/error state, and
artifact paths, but no OCR text or extracted accounting values.

### Registry definition and writer

A registry definition owns columns and conversion of extracted documents into
rows. Document-neutral writers own CSV/XLSX serialization and task-workbook
mechanics.

The task-workbook writer supports `Documents`, `Items`, `Review`, and hidden
`_metadata` sheets without containing document-specific parsing rules.

### Composition

The public `process_folder()` function accepts runtime options, a registered
document-type identifier, and an optional progress callback. It resolves the
complete definition through the catalog and returns `ProcessingSummary`.

Internal integration tests may use
`document_processing._internal.service.process_folder_with_components()` for
fake-component injection. Production and adapter code use the public API.

## Concrete document types

Each concrete document type exposes only framework-facing integration modules at
its package root:

```text
<document_type>/
├── definition.py
├── processor.py
├── workflow.py
├── registry.py
└── _internal/
```

Private OCR, parsing, source readers, classification, validation, and
format-specific normalization live under the owning `_internal/` package.

Current contracts are documented here:

- [Scanned UPD status 1](../source_docs_processor/features/document_processing/document_types/upd_invoices_status_1/README.md)
- [NPD receipts](../source_docs_processor/features/document_processing/document_types/npd_receipts/README.md)
- [Incoming purchase documents](../source_docs_processor/features/document_processing/document_types/incoming_purchase_documents/README.md)

## Anonymization

Anonymization is independent from document-type registration:

```text
source directory
  -> supported-file discovery
      -> configured analyzer or Presidio analyzer
          -> PDF / DOCX / TXT / raster sanitizer
              -> atomic output below the matching relative folder
```

The public API owns configuration and summary contracts. Private modules own
configuration parsing, text transformation, recursive planning, raster OCR,
PDF rebuilding, DOCX package sanitization, and editable DOCX reconstruction.

The operation is fail-closed. Unsupported formats and opaque active or embedded
content are not copied unchanged. Progress and logs do not expose detected PII
values.

Operational configuration and output behavior are documented in
[Usage](USAGE.md), while implementation invariants remain in the local feature
guide.

## Local Streamlit adapter

The optional UI is an outer adapter, not a feature implementation:

```text
streamlit_app.py -> source_docs_processor.ui -> public feature package API
```

It owns localized presentation, input validation, session state, progress
rendering, and privacy-safe result tables. One generic processing adapter calls
`process_folder()` for all registered document types and uses public
`DocumentTypeMetadata` capability flags to decide which controls to render. OCR,
redaction, document extraction, registry generation, and output policy remain in
features.

Localized text and enabled operation order are stored in
`config/ui/ui_<language>.ini`. Configuration may select only known
language-neutral operation identifiers; executable handlers remain an explicit
Python mapping. The UI currently maps anonymization and the three registered
processing workflows to those public APIs.

Streamlit remains an optional dependency. CLI-only installations use
`requirements.txt`; UI installations use `requirements-ui.txt`.

## Public models

`ExtractedDocument` contains document identity, recognition state, parties,
amounts, description, warnings, errors, continuation metadata, repeating items,
and document-specific scalar `extra_fields`.

`ExtractedDocumentItem` contains repeating goods or service row values.
Repeating rows must not be encoded into `extra_fields`.

`ProcessingSummary` provides source/output roots, recognized and complete
documents, registry/report paths, aggregate counts, and generated artifacts. Its
iterator preserves legacy two-value unpacking.

`DocumentTypeMetadata` lets adapters build selectors and capability-aware
controls without constructing OCR processors.

## Change ownership

| Change | Primary scope | Focused validation |
|---|---|---|
| Neutral files, paths, images, or whitespace | `source_docs_processor/core/` | `make test-core` |
| Anonymization behavior or formats | `features/anonymization/` | `make test-anonymization` |
| Shared processing framework or serializers | `features/document_processing/` | `make test-document-processing` |
| Scanned UPD behavior | `document_types/upd_invoices_status_1/` | `make test-upd` |
| NPD receipt behavior | `document_types/npd_receipts/` | `make test-npd` |
| Incoming PDF/DOCX behavior | `document_types/incoming_purchase_documents/` | `make test-incoming-purchase-documents` |
| Local UI, localization, or UI validation | `streamlit_app.py`, `source_docs_processor/ui/`, `config/ui/` | `make test-ui` |
| Public APIs or framework contracts | affected public modules and API tests | `make test-public-api` |
| CLI composition or dependency boundaries | `cli.py`, feature commands, architecture tests | `make test-architecture` |

Run `make check` before completing every change.

## Testing layout

Tests mirror production ownership:

```text
tests/
├── unit/
│   ├── core/
│   ├── anonymization/
│   │   └── _internal/
│   ├── document_processing/
│   │   └── _internal/
│   ├── ui/
│   ├── upd_invoices_status_1/
│   │   └── _internal/
│   ├── npd_receipts/
│   │   └── _internal/
│   └── incoming_purchase_documents/
│       └── _internal/
└── integration/
    ├── anonymization/
    ├── upd_invoices_status_1/
    ├── npd_receipts/
    └── incoming_purchase_documents/
```

Most tests use prepared text, fake processors, generated images, and synthetic
PDF/DOCX files. Real OCR tests are optional and must use synthetic or confirmed
anonymized fixtures.

## Documentation ownership

Documentation has one primary purpose per file:

- `README.md` — compact project overview and entry points;
- `docs/INSTALLATION.md` — platform setup and launch;
- `docs/USAGE.md` — user commands, configuration, and outputs;
- `docs/ARCHITECTURE.md` — system boundaries and ownership;
- `docs/ROADMAP.md` — active and planned work;
- `docs/CHANGELOG.md` — historical completed changes;
- local `README.md` files — package contracts close to code;
- `AGENTS.md` files — engineering rules and protected invariants.

A topic should be explained in its owning document and linked elsewhere instead
of being copied into multiple files.
