---
type: Feature Catalog
title: Stable feature vocabulary
description: Stable capability identifiers used across specifications, tests, documentation, and implementation entry points.
---

# Stable feature vocabulary

## Purpose

This file defines stable capability identifiers for `acc-source-docs-processor`.
Feature IDs are navigation vocabulary, not implementation-stage names and not
specification identifiers. A capability may be refined by several specifications
over time while its feature ID remains stable.

Use a feature ID when a specification, regression test, or important design note
benefits from a durable cross-reference that is independent from Python module
names.

## Rules

- Add a feature ID here before using it in a new specification.
- Reuse an existing feature ID when work changes an existing capability.
- Do not create a feature ID for a release number, refactor, temporary task, or
  individual bug fix.
- Do not rename or remove a published ID in isolation. Treat that as a vocabulary
  migration and update all references together.
- Current implementation truth remains in code, tests, and owning documentation.
  This catalog names capabilities; it does not replace those sources.

Status values in this catalog are informational:

- **released** — the capability exists in the current project;
- **partial** — a useful subset exists and planned work extends the same capability;
- **planned** — the capability is named for current roadmap/specification work but
  is not yet part of the released behavior.

## Catalog

| Feature ID | Status | Capability | Primary owner |
|---|---|---|---|
| `PLATFORM.LOCAL_EXECUTION` | released | Keep accounting-document processing local and source-preserving, without cloud document storage or telemetry. | project-wide |
| `PLATFORM.CLI` | released | Expose independent `process`, `anonymize`, and `reconcile-expenses` CLI operations. | `source_docs_processor/cli.py`, feature `command.py` modules |
| `PLATFORM.PUBLIC_APIS` | released | Expose small public Python APIs and regression-test their exports, signatures, models, and identifiers. | public feature packages |
| `PLATFORM.STREAMLIT_UI` | released | Provide an optional localized local Streamlit adapter that calls public feature APIs directly. | `source_docs_processor/ui/` |
| `PLATFORM.ARCHITECTURE_GUARDRAILS` | released | Enforce feature, core, UI, public/private, and document-type dependency boundaries with tests and local guides. | architecture tests and `AGENTS.md` files |
| `PROCESSING.FRAMEWORK` | released | Compose a document processor, workflow, registry definition, and metadata through `DocumentTypeDefinition`. | `features/document_processing/` |
| `PROCESSING.UPD_SCANS` | released | Recognize scanned UPD status `1`, correct orientation, extract identity, attach continuations, copy/rename images, and emit CSV/report output. | `document_types/upd_invoices_status_1/` |
| `PROCESSING.NPD_RECEIPTS` | released | Recognize scanned NPD receipts, copy/rename images, and emit the linked compact XLSX registry. | `document_types/npd_receipts/` |
| `PROCESSING.NPD_QR` | partial | Use locally decoded official NPD receipt QR data as structured extraction evidence and reconcile it with OCR. | `document_types/npd_receipts/_internal/` |
| `PROCESSING.INCOMING_PURCHASE_DOCUMENTS` | released | Read incoming UPD status `1` from PDF/DOCX, extract document/item data, validate arithmetic, and create the task workbook/report. | `document_types/incoming_purchase_documents/` |
| `PROCESSING.FIELD_CONFIDENCE` | planned | Expose field-level confidence/review information for extracted accounting values. | owning document types and shared model only when proven common |
| `ANONYMIZATION.LOCAL_REDACTION` | released | Recursively anonymize supported local document formats with fail-closed format handling and atomic output. | `features/anonymization/` |
| `ANONYMIZATION.CONFIGURED_RULES` | released | Support configured masks, replacements, exclusions, section redaction, and OCR-tolerant configured matching. | `features/anonymization/` |
| `ANONYMIZATION.EDITABLE_DOCX` | released | Reconstruct editable anonymized DOCX output, optionally preserving approximate layout and emitting source-format output too. | `features/anonymization/` |
| `ANONYMIZATION.ENTITY_DETECTION` | released | Select automatic/configured/combined/disabled entity sources with targeted Russian/English privacy recognition. | `features/anonymization/` |
| `ANONYMIZATION.XLSX` | released | Sanitize XLSX visible/hidden content and supported embedded raster images while failing closed on unsafe opaque structures. | `features/anonymization/` |
| `RECONCILIATION.EXPENSES` | released | Reconcile receipt/ticket files with supported 1C-style XLSX statement rows using exact amount matching and an XLSX review workbook. | `features/expense_reconciliation/` |
| `RECONCILIATION.REVIEW_CONFIDENCE` | planned | Explain ambiguous equal-amount alternatives and expose review reasons without changing exact-amount safety. | `features/expense_reconciliation/` |
| `OUTPUT.REVIEW` | planned | Collect low-confidence or review-required processing results into an explicit review workflow/folder. | owning workflows; shared only when behavior is proven common |
| `OUTPUT.MACHINE_READABLE_DIAGNOSTICS` | planned | Emit privacy-safe machine-readable run/debug summaries without OCR text or private accounting values. | shared output/reporting boundary |
| `PERFORMANCE.OCR_CACHE` | planned | Reuse deterministic OCR results across compatible local runs. | OCR-owning features/document types |
| `PERFORMANCE.PARALLELISM` | planned | Add bounded optional parallel document processing with explicit worker control. | workflow/orchestration owners |
| `CONFIGURATION.PROFILES` | planned | Add reusable processing profiles only after repeated real configurations establish a stable contract. | CLI/public configuration boundary |
| `TOOLING.CI_QUALITY` | planned | Add formatter/linter configuration and continuous integration around the existing deterministic checks. | repository tooling |
| `TOOLING.PACKAGING` | planned | Add `pyproject.toml`, installable CLI packaging, and evaluate standalone distribution. | repository tooling |

## Feature-to-document map

The primary current-state owners remain:

- architecture and dependency rules — [Architecture](ARCHITECTURE.md);
- commands and output behavior — [Usage](USAGE.md);
- active/planned priorities — [Roadmap](ROADMAP.md);
- completed release history — [Changelog](CHANGELOG.md);
- change specifications and their lifecycle — [Specification guide](specs/README.md);
- package contracts and protected behavior — local `README.md` and `AGENTS.md`
  files next to the owning code.

Completed specifications under `docs/specs/archive/` are historical evidence of
how a capability was introduced. They are not the current source of truth.
