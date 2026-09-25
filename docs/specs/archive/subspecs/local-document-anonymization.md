---
type: Specification
title: Local fail-closed document anonymization
description: Reconstructed change contract for recursive local anonymization across text, office, PDF, and raster formats.
document_role: subspec
spec_status: completed
---

# Local fail-closed document anonymization

## Status

Completed and released starting in `0.12.0`.

## Feature scope

- `ANONYMIZATION.LOCAL_REDACTION`
- `PLATFORM.LOCAL_EXECUTION`

## Goal

Create privacy-safe local copies of supported documents while preserving source
files and failing closed when content cannot be sanitized safely.

## Reconstructed requirements

- Process source and output directories recursively while preserving relative
  subfolders.
- Support PDF, DOCX, TXT, and common raster images in the initial feature; later
  XLSX support extends the same fail-closed capability.
- Use local Presidio/spaCy and local Tesseract; do not upload documents.
- Provide OCR-coordinate redaction for raster content and multi-orientation OCR.
- Rebuild PDFs without retaining the original text layer or metadata.
- Sanitize supported DOCX text/package content and embedded raster images.
- Sanitize UTF-8 and Windows-1251 TXT text.
- Do not copy unsupported or opaque content unchanged into anonymized output.
- Fail closed on unsupported active/embedded DOCX content.
- Use atomic per-file output and remove partial artifacts after failure.
- Preserve source filenames unless later output conversion requires deterministic
  collision handling.
- Return a non-zero operation result when source files fail.
- Require manual review because OCR/NER remain heuristic.

## Non-goals

The feature does not anonymize file or directory names and does not provide cloud
storage or remote review.
