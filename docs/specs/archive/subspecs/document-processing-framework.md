---
type: Specification
title: Independent document-processing framework
description: Reconstructed change contract for document-neutral models and independently composed processors, workflows, registries, and metadata.
document_role: subspec
spec_status: completed
---

# Independent document-processing framework

## Status

Completed and released. Reconstructed primarily from releases `0.8.0`, `0.9.0`,
and later compatibility-preserving framework refinements.

## Feature scope

- `PROCESSING.FRAMEWORK`
- `PLATFORM.PUBLIC_APIS`

## Goal

Allow multiple document types to share folder-processing infrastructure without
putting one document type's OCR, filename, registry, or output rules into generic
code.

## Reconstructed requirements

- Use document-neutral `ExtractedDocument` fields for identity, parties, amounts,
  currency, description, continuation metadata, and document-specific scalar
  extras.
- Keep repeating goods/service rows in `ExtractedDocumentItem`, not
  `extra_fields`.
- A processor owns recognition and extraction for one input file only.
- A workflow owns recursive traversal, output-directory policy, copy/link actions,
  naming, continuation attachment, report generation, and registry row selection.
- A registry definition owns columns and row mapping; generic writers own CSV/XLSX
  serialization.
- `DocumentTypeDefinition` binds processor, workflow, registry definition, and
  UI-facing metadata.
- The central catalog imports complete definitions rather than concrete internal
  processor/workflow classes.
- Generic/shared modules must not import concrete document-type internals.
- Preserve registered identifiers and existing output contracts while framework
  internals evolve.
- Keep deterministic fake-component integration tests for composition behavior.

## Compatibility

The scanned UPD workflow remained the default document type while NPD and incoming
purchase-document processors were added independently.

## Historical basis

`0.8.0` introduced the generic model; `0.9.0` established independent processor,
workflow, and registry composition. Releases `0.14.0` through `0.24.0` later
refined package/public boundaries without changing this core contract.
