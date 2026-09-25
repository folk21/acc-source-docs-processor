---
type: Specification
title: Accounting source document platform - current development target
description: Define the selected near-term development slices that extend the released local processing, anonymization, and reconciliation foundation.
document_role: umbrella
spec_status: active
current_focus: subspecs/npd-qr-assisted-extraction.md
---

# Accounting source document platform - current development target

## Status

Active umbrella. The current implementation focus is
[`npd-qr-assisted-extraction.md`](subspecs/npd-qr-assisted-extraction.md).

This umbrella intentionally covers only a reasonable near-term subset of the
roadmap. The full backlog remains in [Roadmap](../../ROADMAP.md).

## Feature scope

Current focus:

- `PROCESSING.NPD_QR`

Selected follow-up candidates after the current slice:

- `PROCESSING.FIELD_CONFIDENCE`
- `RECONCILIATION.REVIEW_CONFIDENCE`
- `OUTPUT.REVIEW`
- `TOOLING.CI_QUALITY`

## Goal

Extend the released application with changes that improve extraction reliability
and reviewability without weakening the existing local/privacy model or blurring
feature ownership.

The near-term sequence should prefer improvements that can be validated with
synthetic data and deterministic tests before larger packaging, parallelism, or
remote-deployment work.

## Current state

The released foundation already provides:

- three independent operations: `process`, `anonymize`, and
  `reconcile-expenses`;
- three registered processing document types;
- public feature APIs used by CLI and Streamlit adapters;
- local fail-closed anonymization for PDF, DOCX, XLSX, TXT, and raster images;
- deterministic unit/integration/public-API/architecture regression suites;
- local QR decoding and official NPD receipt URL parsing utilities that are not
  yet integrated into the NPD processor.

The roadmap also identifies field-level confidence, explicit review reasons,
low-confidence review output, lint/CI tooling, OCR caching, parallelism, and
packaging as future work. Only the selected subset above is part of this umbrella.

## Requirements

### U1 - preserve local/privacy behavior

All selected changes must remain local by default. They must not add cloud OCR,
remote document storage, telemetry, or external receipt lookups.

### U2 - preserve ownership boundaries

Document-specific extraction remains in the owning document-type package.
Cross-feature behavior must not be introduced merely because two backlog items
sound similar.

### U3 - prefer structured evidence over noisy OCR

When an owning document type has a validated structured source, such as an
official locally decoded QR payload, the implementation should use it as
higher-quality evidence than an unconstrained OCR guess for the same field.
Conflicts must be explicit and regression-tested.

### U4 - keep review information privacy-safe

Confidence/review improvements may expose flags, reasons, counts, and portable
paths, but generic progress/UI layers must not start displaying OCR text or
private extracted accounting values.

### U5 - keep validation deterministic

New behavior should be covered with prepared text, fake OCR, generated/synthetic
files, or synthetic QR fixtures. Real Tesseract remains optional.

### U6 - complete one bounded slice at a time

Do not combine NPD QR integration, field-confidence redesign, review-folder
semantics, and CI/tooling into one implementation change. Each should receive a
focused sub-spec when it becomes the current implementation slice.

## Selected sequence

1. Integrate local NPD QR evidence and explicit QR/OCR conflict handling.
2. Re-evaluate field-level confidence after the NPD change establishes one
   concrete structured-vs-OCR evidence pattern.
3. Use confidence/review reasons to define low-confidence output only after the
   field contract is stable.
4. Add repository lint/CI tooling independently from extraction behavior.

## Non-goals

This umbrella does not currently specify:

- persistent OCR caching;
- multi-worker processing;
- YAML processing profiles;
- a standalone executable;
- secure remote deployment;
- new accounting document types;
- an aggregate cross-workbook task manager.

Those remain roadmap candidates and should receive their own bounded specs if
selected for implementation.

## Validation

Each active sub-spec must define focused tests and the required broader project
checks. For repository-wide completion, `make check` remains the baseline gate.
