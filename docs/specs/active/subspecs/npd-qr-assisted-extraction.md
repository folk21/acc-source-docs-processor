---
type: Specification
title: NPD QR-assisted extraction
description: Integrate the existing local official NPD receipt QR decoder/parser into receipt extraction and reconcile structured QR values with OCR explicitly.
document_role: subspec
spec_status: active
parent: ../spec-accounting-source-document-platform.md
---

# NPD QR-assisted extraction

## Status

Active. The decoder and official URL parser already exist under the NPD private
implementation, but they are not yet part of normal receipt processing.

## Feature scope

- `PROCESSING.NPD_QR`
- `PROCESSING.NPD_RECEIPTS`

## Goal

Use a locally decoded official NPD receipt QR URL as structured evidence for the
issuer INN and receipt number, while preserving OCR extraction for fields not
encoded by that URL and making QR/OCR disagreements visible for review.

## Current state

`npd_receipts/_internal/qr.py` can:

- decode a QR value locally with OpenCV;
- accept only `http`/`https` URLs for `lknpd.nalog.ru`;
- parse the official `/api/v1/receipt/<inn>/<receipt-number>/print` path;
- return the issuer INN and receipt number without network access.

The NPD processor currently scores and extracts receipts from OCR only. The
package development guide already requires local QR parsing and explicit future
QR/OCR conflict reporting.

## Requirements

### N1 - local decoding only

QR integration must use the existing local image data and must not fetch the QR
URL or call a remote tax-service API.

### N2 - accept only the existing official URL contract

A QR value participates in NPD extraction only when the existing parser accepts
it as an official NPD receipt URL. Unrelated QR values must not classify a file as
an NPD receipt.

### N3 - structured values fill missing OCR fields

For fields encoded by an accepted QR payload (`issuer_inn` and
`document_number`), a valid QR value must fill the field when OCR did not extract
a value.

### N4 - structured values win only with an explicit conflict warning

When OCR and an accepted QR payload produce different values for the same encoded
field, the selected field value should use the structured QR value, and the
document must receive a stable warning describing the field conflict without
embedding raw OCR text.

The implementation must not silently replace a conflicting OCR value.

### N5 - OCR still owns non-QR fields

QR integration must not remove or weaken OCR extraction for receipt date, issuer
name, recipient data, amount, currency, description, or other fields not encoded
by the accepted URL contract.

### N6 - recognition may use valid QR evidence

A valid official NPD QR payload may strengthen receipt recognition/confidence,
but the processor must still reject unrelated QR codes and preserve the existing
copy-every-image workflow for unrecognized files.

### N7 - orientation behavior remains deterministic

QR decoding must operate on the same candidate orientation being evaluated by the
NPD processor, or otherwise preserve an equivalent deterministic orientation
contract. A successful QR from one rotation must not be attached to a different
image orientation accidentally.

### N8 - public output remains compatible

The compact `npd_receipts_registry.xlsx` schema, filename contract, source-file
copy behavior, and absence of a text report must remain unchanged unless a later
spec explicitly changes them.

## Processing sequence

For each NPD orientation candidate:

1. run the existing OCR pass;
2. decode and parse a local QR candidate;
3. extract OCR fields using current heuristics;
4. merge QR evidence into `issuer_inn` and `document_number`;
5. add conflict warnings when QR and OCR disagree;
6. score/select the strongest orientation using the combined evidence;
7. return the normal `ExtractedDocument` contract to the existing workflow.

The exact internal call ordering may differ when tests show a simpler equivalent
implementation, but QR data must remain tied to the evaluated image orientation.

## Failure semantics

- Missing or unreadable QR is not an error; OCR behavior continues unchanged.
- A non-official QR URL is ignored for NPD extraction.
- OpenCV QR decode failure must not fail the document-processing run.
- A valid QR/OCR conflict is a review warning, not a processing exception.
- No network fallback is allowed.

## Scenarios

### S1 - OCR misses issuer INN

The official QR contains a valid 12-digit issuer INN while OCR fails to read it.
The document uses the QR INN and may gain recognition confidence.

### S2 - OCR misses receipt number

The official QR contains a receipt number while OCR cannot find an explicitly
labeled number. The document uses the QR receipt number.

### S3 - QR and OCR agree

Both sources produce the same issuer INN and receipt number. The output contains
one normalized value for each field and no conflict warning.

### S4 - QR and OCR disagree

The official QR and OCR produce different values for an encoded field. The QR
value is selected and a stable conflict warning is recorded.

### S5 - unrelated QR code

An image contains a QR code for another domain. It does not contribute NPD fields
or recognition confidence.

## Non-goals

This slice does not:

- perform HTTP requests to the receipt URL;
- validate receipt authenticity with a remote service;
- add an INN-to-organization lookup;
- redesign the workbook schema;
- add field-level confidence to the shared model;
- solve all print-view/mobile-screenshot OCR issues.

## Design constraints

- Keep implementation inside `document_types/npd_receipts/` unless a helper is
  proven document-neutral.
- Keep `_internal/qr.py` private.
- Do not add a new runtime dependency for behavior OpenCV already provides.
- Warning text must be deterministic and suitable for regression assertions.
- Tests must use synthetic data and must not call public network services or real
  Tesseract.

## Validation

Acceptance requires at least:

1. unit tests for accepted official URLs and rejected unrelated QR values;
2. processor/extractor regression tests for missing OCR fields filled by QR;
3. explicit conflict regressions for issuer INN and receipt number;
4. a regression showing unreadable/missing QR preserves existing OCR behavior;
5. a regression showing unrelated QR data cannot classify a receipt;
6. `make test-npd` passing;
7. `make test-document-processing` passing when shared processing contracts are
   touched;
8. `make check` passing before completion.

## Implementation tasks

1. Thread parsed QR evidence through the private NPD processing path.
2. Add one focused merge/reconciliation helper instead of duplicating merge logic
   across processor and extractor.
3. Add stable QR/OCR conflict warning codes or messages.
4. Update NPD tests with synthetic/fake QR results.
5. Update current-state NPD documentation after acceptance, then move this spec to
   the archive.
