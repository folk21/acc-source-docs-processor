# Document processing feature

## Purpose

This feature implements the `process` operation. It owns shared processing
contracts, extracted-document models, OCR containers, strict document-value
normalizers, folder workflows, registry writers, the programmatic API, CLI
adaptation, and registered document type implementations. Feature-neutral file,
image, path, and whitespace primitives live in `source_docs_processor.core`.

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
  registry writers, OCR containers, and strict value normalizers from this
  feature, plus feature-neutral primitives from `source_docs_processor.core`.
- Shared normalization must remain strict and format-neutral. OCR aliases,
  template filtering, source priorities, and positional extraction rules belong
  to the concrete document type that needs them.

## Structure

```text
document_processing/
├── api.py                    # reusable process_folder API
├── command.py                # process CLI adapter
├── contracts.py              # DocumentTypeDefinition
├── document_processor.py     # processor protocols and base defaults
├── models.py                 # shared extracted-document models
├── file_ops.py              # ExtractedDocument copy actions
├── normalization/          # strict shared date and decimal parsing
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
2. Keep file recognition in the package processor and document assembly in `extractor.py`.
3. Split stable parsing responsibilities into focused local modules when one extractor gains unrelated reasons to change.
4. Keep folder actions in its workflow and row mapping in its registry definition.
5. Add `definition.py` which exports `DOCUMENT_TYPE` and `DEFINITION`.
6. Register only that definition in `document_types/catalog.py`.
7. Add isolated unit and integration tests under matching test folders.

## Validation

```bash
python -m pytest -q \
  tests/unit/test_document_types.py \
  tests/unit/test_models.py \
  tests/unit/test_ocr.py \
  tests/integration/test_pipeline_with_fake_processor.py
```
