---
type: Specification
title: Editable DOCX anonymization output
description: Reconstructed change contract for OCR-to-DOCX conversion, approximate layout preservation, and dual anonymized output.
document_role: subspec
spec_status: completed
---

# Editable DOCX anonymization output

## Status

Completed and released across `0.13.3` through `0.13.5`.

## Feature scope

- `ANONYMIZATION.EDITABLE_DOCX`

## Goal

Offer editable anonymized DOCX output for raster/PDF/TXT inputs without embedding
the original scan and without changing default source-format behavior.

## Reconstructed requirements

- `--outputDocumentType docx` converts supported sources to editable DOCX.
- Raster and scanned PDF inputs use OCR-derived text reconstruction.
- TXT converts to DOCX; DOCX input retains sanitized native formatting where
  possible.
- Converted filenames must be deterministic and collision-safe.
- `--outputLayout preserve` approximates page size, orientation, line placement,
  vertical spacing, and font size.
- Approximate-layout DOCX must not embed the source scan as a background image.
- Omitting output-layout selection keeps the simpler paragraph reconstruction.
- `--alsoOutputSourceFormat` may emit both source-format and requested DOCX
  artifacts in one run.
- A source already matching the requested format produces one artifact rather than
  a redundant duplicate.
- If one requested output variant fails, remove partial artifacts for that source.
- Final progress/summary includes generated-artifact counts without exposing PII.

## Compatibility

Omitting the new options preserves prior source-format anonymization behavior.
