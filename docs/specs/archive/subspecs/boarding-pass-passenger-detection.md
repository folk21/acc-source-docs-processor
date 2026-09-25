---
type: Specification
title: Boarding-pass passenger-name detection
description: Reconstructed change contract for high-confidence same-line and stacked passenger-name recognition without broadening generic NER.
document_role: subspec
spec_status: completed
---

# Boarding-pass passenger-name detection

## Status

Completed through releases `0.27.3` and `0.27.4`.

## Feature scope

- `ANONYMIZATION.ENTITY_DETECTION`

## Goal

Recover passenger names from common boarding-pass OCR layouts while preserving
route, airline, amount, date, and ordinary uppercase text that broad NER/heuristics
could mask incorrectly.

## Reconstructed requirements

- Add high-confidence same-line passenger recognition for labeled/titled layouts
  such as `SURNAME/GIVENNAME` forms.
- Recognize explicit English and Russian passenger labels, including
  `Passenger name` and `Фамилия пассажира`.
- For raster/PDF OCR, support a value on the line directly below the passenger
  label.
- Keep recognition narrow and label/layout anchored; do not replace it with a
  generic uppercase-word detector.
- Run this supplemental recognition only when automatic detection participates
  (`automatic` or `combined`).
- Preserve configured-rule precedence and exclusions under the established entity
  mode contract.
- Support Latin-script passenger values under Russian labels.

## Validation evidence

Deterministic regressions cover English/Russian labels, same-line and stacked
layouts, Latin-script names, route preservation, and configured-only isolation.
