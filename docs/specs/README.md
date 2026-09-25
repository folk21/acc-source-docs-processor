---
type: Specification Guide
title: Change specifications
description: Specification hierarchy, lifecycle, feature references, reconstruction rules, and minimal metadata conventions.
---

# Change specifications

## Purpose

`docs/specs/` contains bounded specifications for significant planned,
in-progress, and historically reconstructed changes.

A specification describes intended behavior and acceptance criteria for one
change slice. It is not the permanent source of truth for behavior that has
already been accepted and implemented. Current behavior belongs in production
code, tests, [Architecture](../ARCHITECTURE.md), [Usage](../USAGE.md), and the
owning package documentation.

Stable capability names belong in [Features](../FEATURES.md).

## Source-of-truth order

Use this order when documents disagree:

1. production code and machine-readable configuration/contracts define current
   implemented behavior;
2. tests define verified behavior;
3. active specifications define intended changes for current work;
4. owning current-state documentation explains accepted architecture, usage, and
   package contracts;
5. [Roadmap](../ROADMAP.md) describes priorities and future candidates;
6. archived specifications are historical context only.

Reverse-engineered archived specs are intentionally subordinate to the current
implementation. They reconstruct the likely change contract from release history,
current tests, and surviving package invariants; they are not claimed to be the
original pre-implementation design documents.

## Feature, requirement, and specification IDs

Keep these concepts separate:

- **Feature ID** — stable capability vocabulary from `docs/FEATURES.md`, for
  example `PROCESSING.NPD_QR`.
- **Requirement ID** — normative requirement inside one specification, for
  example `N1` or `U3`.
- **Specification name** — one bounded implementation/change slice, for example
  `npd-qr-assisted-extraction`.

A feature may be refined by several specifications over time. A completed
specification is archived; its feature ID remains stable.

## Tree

Keep the active tree shallow:

```text
docs/specs/
├── README.md
├── active/
│   ├── spec-accounting-source-document-platform.md
│   └── subspecs/
│       └── <bounded-current-focus>.md
└── archive/
    └── subspecs/
        └── <completed-change>.md
```

Rules:

- the active umbrella defines the selected near-term product/system target;
- `current_focus` points to one active implementation sub-spec when there is a
  single current slice;
- additional active sub-specs should exist only for unresolved supporting
  constraints that benefit from stable acceptance criteria;
- completing one sub-spec does not automatically complete the umbrella;
- do not create deeper trees without a concrete need.

## When to create a sub-spec

Create a sub-spec when a change materially affects one or more of these areas:

- feature or document-type ownership/dependency direction;
- public CLI or Python API behavior;
- registry/workbook schemas or output contracts;
- OCR/extraction precedence with meaningful regression risk;
- privacy/fail-closed behavior;
- multi-step filesystem workflows and destructive-output safety;
- work spanning multiple implementation sessions that benefits from explicit
  acceptance criteria.

Small bugs, narrow refactors, spelling/documentation cleanup, and routine
dependency maintenance do not require a specification.

## Lifecycle

1. Keep the umbrella under `docs/specs/active/spec-*.md`.
2. Put the current bounded implementation slice under
   `docs/specs/active/subspecs/`.
3. Record `document_role`, `spec_status`, and `parent` in frontmatter.
4. Make umbrella `current_focus` and the human-readable status agree.
5. Reference existing feature IDs from `docs/FEATURES.md`.
6. Give important normative requirements stable IDs when tests or reviews need
   to refer to them.
7. Implement and validate the slice.
8. Move accepted stable knowledge into owning current-state documentation.
9. Move the completed sub-spec to `docs/specs/archive/subspecs/`.
10. Archive the umbrella only when its own selected acceptance target is complete.

A specification must exist in exactly one lifecycle location. Archival is a move,
not a duplicated copy.

## Metadata

Use minimal YAML frontmatter:

```yaml
---
type: Specification
title: Human-readable title
description: One-sentence scope summary.
document_role: umbrella | subspec
spec_status: active | verification-pending | completed
parent: ../spec-accounting-source-document-platform.md  # sub-spec only
current_focus: subspecs/example.md                      # umbrella only, when used
---
```

Do not add metadata that merely repeats Git history or the body.

## Writing structure

Use only sections that add value. A normal change specification may contain:

```text
# <Change name>

## Status
## Feature scope
## Goal
## Current state
## Requirements
## Processing sequence
## Failure semantics
## Scenarios
## Non-goals
## Design constraints
## Compatibility / migration
## Validation
## Implementation tasks
```

Use `must`, `must not`, `should`, and `may` consistently for normative
requirements. Keep processing order separate from invariants and failure
semantics.

## Current active specifications

Umbrella:

- [`active/spec-accounting-source-document-platform.md`](active/spec-accounting-source-document-platform.md)
  — selected near-term development target built on the released local processing
  platform.

Current implementation focus:

- [`active/subspecs/npd-qr-assisted-extraction.md`](active/subspecs/npd-qr-assisted-extraction.md)
  — `PROCESSING.NPD_QR`; integrate the existing local decoder/parser with NPD
  extraction and make QR/OCR conflicts explicit.

## Reconstructed archive

The archive reconstructs completed change contracts from `docs/CHANGELOG.md`,
`docs/ROADMAP.md`, current tests, and current package invariants. It deliberately
groups release notes into bounded features instead of creating one file per patch
version.

Archived change contracts:

- [`scanned-upd-status-1-processing.md`](archive/subspecs/scanned-upd-status-1-processing.md) — `PROCESSING.UPD_SCANS`; early UPD scan/OCR/continuation milestones.
- [`document-processing-framework.md`](archive/subspecs/document-processing-framework.md) — `PROCESSING.FRAMEWORK`; generic model and processor/workflow/registry composition.
- [`npd-receipt-processing.md`](archive/subspecs/npd-receipt-processing.md) — `PROCESSING.NPD_RECEIPTS`; scanned NPD receipt workflow and XLSX registry.
- [`incoming-purchase-documents.md`](archive/subspecs/incoming-purchase-documents.md) — `PROCESSING.INCOMING_PURCHASE_DOCUMENTS`; PDF/DOCX UPD task workbooks.
- [`operation-subcommands.md`](archive/subspecs/operation-subcommands.md) — `PLATFORM.CLI`; operation-oriented command structure.
- [`local-document-anonymization.md`](archive/subspecs/local-document-anonymization.md) — `ANONYMIZATION.LOCAL_REDACTION`; initial fail-closed local anonymization.
- [`anonymization-configured-rules.md`](archive/subspecs/anonymization-configured-rules.md) — `ANONYMIZATION.CONFIGURED_RULES`; configured inclusion/exclusion/section/fuzzy rules.
- [`editable-docx-anonymization.md`](archive/subspecs/editable-docx-anonymization.md) — `ANONYMIZATION.EDITABLE_DOCX`; editable layout and dual output.
- [`anonymization-pseudonym-replacement.md`](archive/subspecs/anonymization-pseudonym-replacement.md) — configured pseudonym replacement.
- [`anonymization-output-safety.md`](archive/subspecs/anonymization-output-safety.md) — safe cleanup and source/output traversal.
- [`modular-feature-architecture.md`](archive/subspecs/modular-feature-architecture.md) — `PLATFORM.ARCHITECTURE_GUARDRAILS`; feature/core/private/public boundaries and local guides.
- [`public-processing-apis.md`](archive/subspecs/public-processing-apis.md) — `PLATFORM.PUBLIC_APIS`; explicit API, progress, summary, and metadata contracts.
- [`local-streamlit-ui.md`](archive/subspecs/local-streamlit-ui.md) — `PLATFORM.STREAMLIT_UI`; localized local UI adapters.
- [`configurable-anonymization-entity-detection.md`](archive/subspecs/configurable-anonymization-entity-detection.md) — `ANONYMIZATION.ENTITY_DETECTION`; detection modes and targeted multilingual policy.
- [`xlsx-anonymization.md`](archive/subspecs/xlsx-anonymization.md) — `ANONYMIZATION.XLSX`; fail-closed spreadsheet sanitization.
- [`boarding-pass-passenger-detection.md`](archive/subspecs/boarding-pass-passenger-detection.md) — targeted passenger-name detection under `ANONYMIZATION.ENTITY_DETECTION`.
- [`expense-reconciliation.md`](archive/subspecs/expense-reconciliation.md) — `RECONCILIATION.EXPENSES`; receipt/ticket-to-statement reconciliation and UI integration.
