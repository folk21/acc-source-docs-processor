---
type: Testing Guide
title: Tests and validation
description: Test layers, deterministic-fixture rules, focused Make targets, and repository validation workflow.
---

# Tests and validation

## Test strategy

Use the smallest useful test layer first, then run the broader gate appropriate
to the change.

- `tests/unit/` owns pure extraction, parsing, public API, architecture, UI, and
  helper behavior.
- `tests/integration/` owns filesystem/workflow behavior across synthetic local
  inputs and generated output.
- Real OCR tests are optional and must be marked `ocr` or `slow` and skipped when
  Tesseract is unavailable.

Most tests must not call real Tesseract. Prefer prepared text, fake OCR results,
fake processors, generated images, and synthetic PDF/DOCX/XLSX files.

Every behavioral bug fix requires a regression test. Every test must have an
English docstring that explains the verified behavior and protected risk.

## Focused validation

The root `Makefile` is the command source of truth:

| Scope | Command |
|---|---|
| Core primitives | `make test-core` |
| Public API contracts | `make test-public-api` |
| CLI/dependency/package boundaries | `make test-architecture` |
| Anonymization | `make test-anonymization` |
| Shared document processing | `make test-document-processing` |
| Scanned UPD status 1 | `make test-upd` |
| NPD receipts | `make test-npd` |
| Incoming purchase documents | `make test-incoming-purchase-documents` |
| Expense reconciliation | `make test-expense-reconciliation` |
| Streamlit adapter | `make test-ui` |

Use the nearest local `AGENTS.md` to choose the focused command for a change.

## Complete validation

Run from the project root:

```bash
make check
```

`make check` compiles `main.py`, `streamlit_app.py`, `source_docs_processor`, and
`tests`, then runs the complete pytest suite.

Do not claim a command passed unless it was actually run successfully. If an
environment dependency prevents a check, report the exact command and failure.

## Privacy and fixtures

Tests and committed fixtures must not contain real scans, company names, tax
identifiers, addresses, shipment data, bank data, passenger data, or personal
information. Use generated/synthetic files and fictional values only.

## Specification validation

When a change is governed by an active specification:

- map important acceptance requirements to focused regression tests where useful;
- keep feature IDs from `docs/FEATURES.md` stable;
- move accepted current behavior into owning documentation before archiving the
  completed spec.
