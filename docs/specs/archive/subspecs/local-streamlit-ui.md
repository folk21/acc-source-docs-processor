---
type: Specification
title: Localized local Streamlit adapter
description: Reconstructed change contract for the optional local browser UI over public feature APIs.
document_role: subspec
spec_status: completed
---

# Localized local Streamlit adapter

## Status

Completed across releases `0.25.0`, `0.26.0`, and the later reconciliation UI
addition in `0.28.1`.

## Feature scope

- `PLATFORM.STREAMLIT_UI`
- `PLATFORM.PUBLIC_APIS`

## Goal

Provide a local browser-based interface without moving business logic into UI code
or changing CLI-only installations.

## Reconstructed requirements

- Keep Streamlit optional through `requirements-ui.txt`.
- Call public feature APIs directly; never invoke CLI commands through subprocess
  or import feature `_internal` modules.
- Store localized static text and operation order in
  `config/ui/ui_<language>.ini` while keeping executable handler mappings in
  explicit Python code.
- Support Russian and English localization, with Russian as default.
- Use one generic processing adapter driven by public `DocumentTypeMetadata`
  capability flags for all registered processing document types.
- Render synchronous privacy-safe progress and relative-path result/artifact
  tables.
- Do not display OCR text or extracted private accounting values in generic
  progress/result views.
- Provide anonymization controls including one-run entity-detection-mode override
  without rewriting the user's INI file.
- Provide expense-reconciliation source/statement/output/OCR controls and show
  only aggregate counts plus the portable generated workbook name.
- Keep path validation in the UI adapter and source/output safety behavior in the
  owning feature.

## Validation evidence

Focused UI tests protect API forwarding, localization, path validation, metadata
use, progress/result mapping, and privacy-safe rendering.
