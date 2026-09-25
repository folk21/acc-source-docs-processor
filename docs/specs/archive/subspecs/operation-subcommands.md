---
type: Specification
title: Operation-oriented CLI subcommands
description: Reconstructed change contract for separating document processing and anonymization into explicit top-level CLI operations.
document_role: subspec
spec_status: completed
---

# Operation-oriented CLI subcommands

## Status

Completed and released in the `0.11.x` line, with `reconcile-expenses` added later
under the same operation-oriented CLI model.

## Feature scope

- `PLATFORM.CLI`

## Goal

Make independent application operations explicit at the command line instead of
extending one flat parser with unrelated flags.

## Reconstructed requirements

- Use top-level subcommands for independent features.
- Route document processing through `python main.py process ...`.
- Route anonymization through `python main.py anonymize ...` once implemented.
- Later independent multi-input features may add their own subcommand rather than
  pretending to be a document type; `reconcile-expenses` follows this rule.
- Keep top-level CLI composition small and delegate parsing/handling to the owning
  feature.
- Preserve the programmatic document-processing API separately from CLI dispatch.
- Reject the obsolete flat processing syntax after migration.
- Keep portable example scripts grouped by operation.

## Compatibility

This change intentionally changed documented CLI invocation while preserving
registered document-type identifiers and programmatic processing behavior.
