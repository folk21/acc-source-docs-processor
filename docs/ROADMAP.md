# Roadmap

Status legend:

- `[x]` released foundation;
- `[/]` in progress or partially integrated;
- `[ ]` backlog.

Completed release history belongs in [CHANGELOG.md](CHANGELOG.md). This file
keeps only a compact foundation summary plus current and planned work.

## Released foundations

- [x] Separate `process` and `anonymize` operations.
- [x] Isolate feature-neutral helpers in `source_docs_processor/core/`.
- [x] Compose document processors, workflows, registries, and metadata through
  `DocumentTypeDefinition`.
- [x] Keep feature and concrete document implementations behind explicit public
  and `_internal` boundaries enforced by architecture tests.
- [x] Provide deterministic unit, integration, public API, and package-boundary
  regression tests.
- [x] Support scanned UPD status `1`, NPD receipts, and incoming PDF/DOCX UPD
  status `1` workflows.
- [x] Provide local fail-closed anonymization for PDF, DOCX, TXT, and raster
  images with configured masking/replacement and Presidio mode.
- [x] Provide configurable anonymization entity-detection modes for automatic,
  configured, combined, and disabled entity sources.
- [x] Provide a localized local Streamlit interface for anonymization and all
  registered document-processing workflows.
- [x] Provide platform installation and centralized usage documentation.

## Architecture and code quality

- [ ] Reuse `document_processing/_internal/registry/common.py` consistently in
  CSV and XLSX writers.
- [ ] Split large extractors only when a stable independent reason for change is
  demonstrated.
- [ ] Evaluate config-driven document definitions only after multiple processors
  share a proven configuration contract.
- [ ] Evaluate entry-point discovery only if external processor packages become
  necessary.
- [ ] Add `ruff` configuration.
- [ ] Add continuous integration.
- [ ] Add `pyproject.toml` and package the CLI.
- [ ] Evaluate a standalone executable distribution.
- [ ] Add missing English docstrings to NPD regression tests.

## Scanned UPD status 1

- [/] Continue tuning private problematic examples outside the repository.
- [ ] Add field-level confidence values.
- [ ] Add synthetic OCR image fixtures for important scan-quality regressions.

## Incoming purchase documents

- [ ] Tune PDF table extraction against private supplier layouts.
- [ ] Evaluate additional PDF table-reconstruction strategies.
- [ ] Add field-level confidence for extracted item values.
- [ ] Add workbook update mode that preserves existing `processed` values.
- [ ] Add an aggregate task summary across incoming UPD and NPD workbooks.

## NPD receipts

- [/] Integrate the existing local QR decoder and official NPD URL parser into
  receipt processing.
- [ ] Reconcile QR and OCR values and report conflicts explicitly.
- [ ] Improve clean print-view and mobile screenshot recognition.
- [ ] Add synthetic OCR image fixtures without real names or identifiers.
- [ ] Add an optional local INN-to-organization mapping for recipient names.

## Output and review

- [ ] Add a review folder for low-confidence documents.
- [ ] Add machine-readable debug JSON without private OCR content.
- [ ] Add summary counts by document type and recognition status.
- [ ] Add an optional machine-readable anonymization audit report without PII
  values.

## Performance

- [ ] Add a persistent OCR cache.
- [ ] Add optional parallel processing with `--workers`.
- [ ] Add a benchmark command.

## Configuration and usability

- [ ] Add custom organization/person dictionaries beyond literal matching.
- [ ] Add YAML processing profiles when repeated real configurations justify
  them.
- [ ] Add a Tesseract validation command.
- [ ] Evaluate secure remote deployment only with an explicit storage,
  authentication, and privacy design.
