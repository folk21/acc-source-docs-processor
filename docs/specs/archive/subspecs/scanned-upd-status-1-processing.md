---
type: Specification
title: Scanned UPD status 1 processing
description: Reconstructed change contract for the original scan-oriented UPD recognition, OCR correction, continuation, and output workflow.
document_role: subspec
spec_status: completed
---

# Scanned UPD status 1 processing

## Status

Completed and released. Reconstructed from the early pre-release milestones,
current UPD tests, and surviving package invariants.

## Feature scope

- `PROCESSING.UPD_SCANS`

## Goal

Process folders of scanned Russian UPD/invoice-transfer documents with status `1`
locally, preserve source files, correct orientation, recover document identity
from noisy OCR, attach conservative continuation pages, and emit portable output.

## Reconstructed requirements

- Recursively scan supported raster images while excluding generated output.
- Recognize UPD status `1`; do not treat every accounting-looking page as a target.
- Try 0/90/180/270 degree orientations when auto-rotation is enabled and save
  recognized output upright.
- Prefer targeted/anchored OCR for status, number, date, and shipment-row evidence
  over one unconstrained text pass.
- Normalize document-number OCR separators such as spaces, dots, and hyphens.
- Use `Документ об отгрузке` number/date as a reliable fallback when the header is
  missing or suspicious.
- Reject the static form-template date `02-04-2021` when it comes from regulation
  text rather than document identity.
- Correct suspicious header numbers with reliable shipment-row evidence, including
  short-number and trailing-digit over-read cases such as `4 -> 405`,
  `43007 -> 430`, and `4977 -> 497`.
- Test standalone UPD recognition before continuation-page classification.
- Continuation detection must remain conservative: sparse page, no normal UPD
  header, inherited metadata, and `_2_страница` naming.
- Copy recognized and unrecognized images, preserve relative subfolders, avoid
  absolute local paths in portable registry cells, and emit the detailed CSV plus
  text report.
- Keep `--debug-crops`, `--no-auto-rotate`, output selection, and duplicate-safe
  naming behavior available.

## Non-goals

This feature does not process electronic PDF/DOCX UPD files and does not define
rules for other accounting document types.

## Validation evidence

Current regression coverage protects number/date normalization, shipment-row
fallback, template-date filtering, continuation behavior, filename generation,
registered workflow behavior, and synthetic pipeline output.

## Historical basis

This reconstruction corresponds to the `Earlier pre-release milestones` section
of `docs/CHANGELOG.md` and the later focused UPD extraction refactors that
preserved behavior.
