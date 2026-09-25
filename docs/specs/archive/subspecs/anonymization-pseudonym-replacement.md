---
type: Specification
title: Configured pseudonym replacement
description: Reconstructed change contract for replacing configured sensitive literals with user-provided privacy-safe values.
document_role: subspec
spec_status: completed
---

# Configured pseudonym replacement

## Status

Completed and released in `0.13.6`.

## Feature scope

- `ANONYMIZATION.CONFIGURED_RULES`

## Goal

Allow configured sensitive values to be replaced with explicit pseudonyms instead
of always being masked.

## Reconstructed requirements

- Support multiline `includedAndReplaced` rules using `source -> replacement`.
- Validate malformed or conflicting replacement rules.
- Give replacement precedence when the same source is also configured for masking.
- Apply exact replacement to native TXT and DOCX text, including values split
  across DOCX runs.
- Apply configured OCR-fuzzy matching to OCR-derived PDF/raster/editable-DOCX
  paths when enabled.
- For raster replacement, cover the source region before drawing replacement text.
- Treat either `included` or `includedAndReplaced` as configured detection input
  under the legacy configured-only behavior.
- Keep replacement processing local and preserve all fail-closed format rules.

## Validation evidence

Regression coverage protects parsing, precedence, fuzzy replacement, native DOCX
runs, raster replacement, editable output, and dual-output behavior.
