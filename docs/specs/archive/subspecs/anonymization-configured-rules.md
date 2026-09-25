---
type: Specification
title: Configured anonymization rules and OCR-tolerant matching
description: Reconstructed change contract for included, excluded, section, and bounded fuzzy configured anonymization rules.
document_role: subspec
spec_status: completed
---

# Configured anonymization rules and OCR-tolerant matching

## Status

Completed and released across `0.13.0` through `0.13.2`.

## Feature scope

- `ANONYMIZATION.CONFIGURED_RULES`

## Goal

Allow users to define local deterministic anonymization rules that can override or
replace generic entity detection where exact domain knowledge is available.

## Reconstructed requirements

- Load rules from an INI `[anonymization]` section.
- Support `excluded`, `included`, and `includedParagraphs` lists.
- Match configured multiword literals case-insensitively across ordinary
  whitespace differences.
- When configured-only behavior is selected by legacy rules, bypass Presidio and
  spaCy and ignore `excluded` for configured matches.
- Keep `includedParagraphs` independent from entity-detection source selection.
- Support section-level redaction after configured headings, including following
  PDF/TIFF pages where applicable.
- Support OCR-only bounded fuzzy matching for configured values via
  `includedFuzzy` and `includedFuzzyMaxErrors`.
- Keep native TXT/DOCX configured matching exact.
- Normalize common OCR punctuation/whitespace, `ё`/`е`, and Latin/Cyrillic
  lookalikes for fuzzy matching.
- Validate fuzzy error bounds conservatively (`0..3`).
- Include immediate privacy-safe progress callbacks without exposing detected PII
  values.

## Validation evidence

Deterministic tests protect configuration parsing, override precedence, section
redaction, fuzzy OCR matching, and the no-Presidio configured-only path.
