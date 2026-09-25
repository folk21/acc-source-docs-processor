---
type: Specification
title: Explicit public APIs, progress, and metadata contracts
description: Reconstructed change contract for regression-tested public exports and UI-ready document-processing progress/summary metadata.
document_role: subspec
spec_status: completed
---

# Explicit public APIs, progress, and metadata contracts

## Status

Completed in releases `0.23.0` and `0.24.0`.

## Feature scope

- `PLATFORM.PUBLIC_APIS`
- `PROCESSING.FRAMEWORK`

## Goal

Make supported Python integration points explicit and safe for adapters such as a
local UI without exposing feature-private implementation packages.

## Reconstructed requirements

- Regression-test exact package exports, signatures, dataclass fields, protocol
  hooks, registered identifiers, and package version exposure.
- Keep explicit `__all__` declarations synchronized with public contract tests.
- Expose `ProcessingSummary` with output roots, registry/report paths, aggregate
  counts, recognized/complete documents, and generated artifacts.
- Preserve legacy two-value result unpacking for compatibility.
- Expose synchronous `ProcessingProgress` events and optional callback support for
  scan/file/registry/completion lifecycle updates.
- Progress events may contain paths, counts, recognition/error state, and artifact
  paths but must not expose OCR text or extracted accounting values.
- Expose `DocumentTypeMetadata` and registered metadata so adapters can render
  selectors/capability-aware controls without constructing OCR processors.
- Bind metadata into the complete `DocumentTypeDefinition`.
- Keep fake-component injection internal to deterministic tests; production and
  adapters use the public API.

## Validation evidence

`make test-public-api` and cross-workflow integration tests protect these
contracts.
