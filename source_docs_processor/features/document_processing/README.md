# Document processing feature

## Purpose

This feature implements the `process` operation. Its stable embedded API exposes
folder processing and extracted-document result models. Its feature root also
contains the framework-facing contracts used directly by registered document
types:

- `document_type_definition.py` — processor/workflow/registry composition;
- `processor_base.py` — processor protocols and reusable recognition defaults;
- `registry_base.py` — registry schema and row-mapping protocol;
- `workflow_base.py` — workflow protocol, options, results, and run helpers;
- `workflow_copy_and_register.py` — reusable image copy/register workflow.

Component injection, OCR containers, strict value normalizers,
processing-specific file actions, and registry serializers remain private under
`_internal/`.

Feature-neutral file, image, path, and whitespace primitives live in
`source_docs_processor.core`.

## Stable entry points

- `source_docs_processor.features.document_processing.process_folder`
- `source_docs_processor.features.document_processing.ExtractedDocument`
- `source_docs_processor.features.document_processing.ExtractedDocumentItem`
- `source_docs_processor.features.document_processing.command.register_process_command`

The framework-facing modules are extension points for document types owned by
this repository. They are intentionally not re-exported from the package root as
part of the stable embedded API, and the project does not currently provide an
external processor plugin SDK.

## Dependency rules

- May import feature-neutral helpers from `source_docs_processor.core`.
- Must not import `features.anonymization`.
- The feature root contains the public API/models plus explicit framework
  extension modules used directly by concrete document types.
- Processor, registry, workflow, and document-type composition contracts belong
  at the feature root, not under `_internal/`.
- Component injection, file actions, OCR support, strict normalizers, and
  registry serializers belong under `_internal/`.
- Concrete document types may import root framework modules and shared
  `document_processing._internal` implementation helpers because they belong to
  the same feature.
- Modules outside this feature must not import `document_processing._internal`.
- Shared framework and `_internal` modules must not import concrete document
  types. The internal composition service may resolve the catalog, while only
  the catalog imports complete concrete definitions.
- One concrete document type must not import another concrete document type.
- A document type root exposes only `definition.py`, `processor.py`,
  `workflow.py`, and `registry.py` as framework-facing modules.
- Document-specific OCR, readers, extraction, classification, validation, and
  other implementation details belong under the owning `_internal/` package.
- Strict date and decimal normalization stays in the feature `_internal`
  package; OCR aliases, source priorities, template filtering, and positional
  rules stay private to the document type that requires them.

## Structure

```text
document_processing/
├── README.md
├── __init__.py
├── api.py                         # stable process_folder API
├── command.py                     # process CLI adapter
├── models.py                      # public extracted-document results
├── document_type_definition.py    # registered component composition
├── processor_base.py              # processor protocols and reusable defaults
├── registry_base.py               # registry definition protocol
├── workflow_base.py               # workflow protocol and run types
├── workflow_copy_and_register.py  # reusable copy/register workflow
├── document_types/
│   ├── catalog.py                 # imports only complete definitions
│   └── <document_type>/
│       ├── README.md
│       ├── definition.py
│       ├── processor.py
│       ├── registry.py
│       ├── workflow.py
│       └── _internal/             # private OCR, readers, extraction, validation
└── _internal/
    ├── service.py                 # component composition and test injection
    ├── file_ops.py                # ExtractedDocument copy actions
    ├── ocr.py                     # shared OCR result and helpers
    ├── date_normalization.py
    ├── money_normalization.py
    └── registry/                  # private serializers and workbook helpers
```

## Adding a document type

1. Create a package under `document_types/`.
2. Add `definition.py`, `processor.py`, `workflow.py`, and `registry.py` at the
   package root.
3. Put document-specific readers, OCR, parsing, classification, and validation
   under `_internal/`.
4. Import processor contracts/defaults from `processor_base.py`, the registry
   contract from `registry_base.py`, and workflow contracts from
   `workflow_base.py`.
5. Inherit from `workflow_copy_and_register.py` when its copy/register behavior
   fits.
6. Keep format-specific folder actions in the concrete `workflow.py` and row
   mapping in `registry.py`.
7. Export `DOCUMENT_TYPE` and `DEFINITION` from `definition.py` using
   `DocumentTypeDefinition` from `document_type_definition.py`.
8. Register only that definition in `document_types/catalog.py`.
9. Mirror private unit tests under `tests/unit/<document_type>/_internal/`.

Use `document_processing._internal.service.process_folder_with_components()` only
for internal integration tests that need fake processors, workflows, or registry
definitions. Production and embedded callers should use the public
`process_folder()` API.

## Validation

```bash
python -m pytest -q \
  tests/unit/document_processing \
  tests/unit/test_package_boundaries.py \
  tests/integration/test_pipeline_with_fake_processor.py
```
