# Document processing feature

## Purpose

This feature implements the `process` operation. It owns shared processing
contracts, extracted-document models, OCR and image helpers, folder workflows,
registry writers, the programmatic API, CLI adaptation, and registered document
type implementations.

## Public entry points

- `source_docs_processor.features.document_processing.process_folder`
- `source_docs_processor.features.document_processing.DocumentTypeDefinition`
- `source_docs_processor.features.document_processing.get_document_type_definition`
- `source_docs_processor.features.document_processing.command.register_process_command`

Callers should use these entry points instead of importing a concrete document
type unless they are testing or extending that implementation.

## Dependency rules

- May import cross-feature helpers from `source_docs_processor.core`.
- Must not import `features.anonymization`.
- Shared modules outside `document_types/` must not import a concrete document
  type. Only the catalog composes registered definitions.
- One concrete document type must not import another concrete document type.
- A concrete document type may import shared contracts, models, workflows,
  registry writers, OCR helpers, and file helpers from this feature.

## Structure

```text
document_processing/
├── api.py                    # reusable process_folder API
├── command.py                # process CLI adapter
├── contracts.py              # DocumentTypeDefinition
├── document_processor.py     # processor protocols and base defaults
├── models.py                 # shared extracted-document models
├── file_ops.py
├── image_processing.py
├── ocr.py
├── registry/                 # document-neutral serializers and contracts
├── workflows/                # folder workflow contracts and shared workflows
└── document_types/
    ├── catalog.py            # imports only complete definitions
    ├── upd_invoices_status_1/
    ├── npd_receipts/
    └── incoming_purchase_documents/
```

## Adding a document type

1. Create a package under `document_types/`.
2. Keep file recognition and extraction in the package processor/extractor.
3. Keep folder actions in its workflow and row mapping in its registry definition.
4. Add `definition.py` which exports `DOCUMENT_TYPE` and `DEFINITION`.
5. Register only that definition in `document_types/catalog.py`.
6. Add isolated unit and integration tests under matching test folders.

## Validation

```bash
python -m pytest -q \
  tests/unit/test_document_types.py \
  tests/unit/test_models.py \
  tests/unit/test_ocr.py \
  tests/integration/test_pipeline_with_fake_processor.py
```
