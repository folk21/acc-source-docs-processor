# Document-processing feature

This feature implements the `process` operation and the reusable framework used
by registered document types.

## Stable embedded API

The package facade exports:

- `process_folder`;
- `ExtractedDocument` and `ExtractedDocumentItem`;
- `ProcessingSummary` and `ProcessingProgress`;
- `DOCUMENT_TYPE_METADATA` and `get_document_type_metadata`.

`process_folder()` returns a structured summary and accepts an optional
synchronous progress callback. Progress events expose paths, counts,
recognition/error state, and generated artifacts, but no OCR text or extracted
accounting values.

## Framework-facing modules

Concrete document types use the visible feature-root contracts:

- `document_type_definition.py` — complete component composition and metadata;
- `processor_base.py` — processor protocols and reusable defaults;
- `registry_base.py` — registry schema and row mapping;
- `workflow_base.py` — workflow protocol, options, results, and progress helpers;
- `workflow_copy_and_register.py` — reusable image copy/register workflow.

Composition services, processing-specific file actions, OCR containers, strict
value normalizers, and registry serializers remain private under `_internal/`.

## Adding a document type

1. Create a package under `document_types/`.
2. Expose `definition.py`, `processor.py`, `workflow.py`, and `registry.py` at the
   package root.
3. Put readers, OCR, parsing, classification, validation, and format-specific
   normalization under `_internal/`.
4. Export `DOCUMENT_TYPE` and a complete `DEFINITION`.
5. Register only the definition in `document_types/catalog.py`.
6. Add matching unit and integration coverage.

Production and adapter code use the public `process_folder()` API. Internal tests
may use `_internal/service.py::process_folder_with_components()` for fake
component injection.

## Registered types

- [Scanned UPD status 1](document_types/upd_invoices_status_1/README.md)
- [NPD receipts](document_types/npd_receipts/README.md)
- [Incoming purchase documents](document_types/incoming_purchase_documents/README.md)

## Related documentation

- [Processing usage](../../../docs/USAGE.md#process-accounting-documents)
- [Architecture](../../../docs/ARCHITECTURE.md#document-processing-framework)
- [Development invariants](AGENTS.md)

## Validation

```bash
make test-document-processing
make check
```
