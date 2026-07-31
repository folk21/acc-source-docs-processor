# Document-processing development guide

This file narrows the root `AGENTS.md` rules for
`source_docs_processor/features/document_processing/`.

## Scope

Use this feature for document recognition, extraction, copy/register workflows,
registry schemas, and registered document types. A shared framework change may
affect every concrete document type and therefore requires the complete feature
suite.

Do not modify anonymization for a document-processing-only task.

## Framework-facing modules

The feature root is the extension map used by concrete document types:

- `document_type_definition.py` composes processor, workflow, and registry
  factories;
- `processor_base.py` owns processor protocols and reusable defaults;
- `registry_base.py` owns the registry schema contract;
- `workflow_base.py` owns workflow protocols and run types;
- `workflow_copy_and_register.py` owns the reusable scan copy/register workflow;
- `models.py` owns public extracted-document result models;
- `api.py` and `command.py` own the embedded and CLI entry points.

Changing these files is a framework change. Keep their `__all__`, callable
signatures, protocol hooks, and dataclass fields synchronized with the public
API regression tests. Verify every registered document type and the architecture
tests.

## Private shared implementation

`_internal/` owns processing-specific file actions, OCR containers, strict date
and decimal normalization, component composition, and registry serialization.
It is shared only inside this feature and is not an external plugin SDK.

Shared framework or `_internal` modules must not import a concrete document type,
except that the composition service may resolve the central catalog. Only the
catalog imports complete document-type definitions.

## Document-type ownership

Each document type root exposes only `definition.py`, `processor.py`,
`workflow.py`, and `registry.py`. Parsing, OCR, readers, classification,
validation, and source-specific normalization belong to its `_internal/`
package. One document type must not import another.

Read the nearest document-type `AGENTS.md` before changing a concrete type.

## Invariants

- Processors own one-file recognition and extraction only.
- Workflows own recursive traversal, output policy, copying, reports, and the
  document list passed to writers.
- Registry definitions own schema and row mapping; writers own serialization.
- Keep public CLI options and registered document-type identifiers stable unless
  the task explicitly changes them.
- Add a regression test for every extraction or workflow bug.
- Use synthetic files and fictional accounting data only.

## Validation

Run the public contract tests after changing package exports, public models,
document-type identifiers, framework protocols, or base-class hooks:

```bash
make test-public-api
```

Run the complete feature suite for shared framework or `_internal` changes:

```bash
make test-document-processing
```

For a concrete document type, use its narrower target first. Run the full project
validation before completion:

```bash
make check
```
