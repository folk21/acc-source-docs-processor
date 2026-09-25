---
type: Specification
title: Feature-oriented architecture and private implementation boundaries
description: Reconstructed change contract for feature packages, core primitives, private internals, visible framework extension points, and local development guides.
document_role: subspec
spec_status: completed
---

# Feature-oriented architecture and private implementation boundaries

## Status

Completed through the `0.14.0` to `0.22.0` architecture sequence.

## Feature scope

- `PLATFORM.ARCHITECTURE_GUARDRAILS`
- `PROCESSING.FRAMEWORK`

## Goal

Make repository ownership obvious to humans and coding agents while preserving
all user-visible processing behavior.

## Reconstructed requirements

- Group independent operations under `source_docs_processor/features/`.
- Keep feature-neutral filesystem/image/path/text helpers under
  `source_docs_processor/core/` only when their ownership is genuinely neutral.
- Keep the root CLI as a composition point; each feature owns its parser/handler.
- Keep concrete document types below document processing and prevent cross-imports
  between them.
- Expose only `definition.py`, `processor.py`, `workflow.py`, and `registry.py` at
  concrete document-type roots; keep parsing/OCR/readers/validation private under
  `_internal/`.
- Keep feature implementation private under feature `_internal/` packages while
  leaving deliberate framework extension contracts visible.
- Keep shared workflow, processor, registry, and `DocumentTypeDefinition`
  contracts at stable visible paths when they are intended extension points.
- Mirror private implementation ownership in unit-test package layout.
- Add architecture regressions for forbidden dependency directions and required
  package shape.
- Add local `AGENTS.md` files and focused Make targets so changes can be validated
  in their owning scope first.
- Preserve CLI options, registered document types, OCR heuristics, registries,
  reports, and output layout through architecture-only changes.

## Non-goals

The architecture does not introduce external plugin discovery, separate services,
or broad abstractions without at least two proven users.
