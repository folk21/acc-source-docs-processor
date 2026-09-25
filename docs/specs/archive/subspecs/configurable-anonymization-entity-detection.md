---
type: Specification
title: Configurable targeted anonymization entity detection
description: Reconstructed change contract for automatic, configured, combined, and disabled entity-detection modes with receipt-safe multilingual recognition.
document_role: subspec
spec_status: completed
---

# Configurable targeted anonymization entity detection

## Status

Completed across `0.27.0` through `0.27.2`, with later focused recognition
extensions preserving the same mode contract.

## Feature scope

- `ANONYMIZATION.ENTITY_DETECTION`
- `ANONYMIZATION.CONFIGURED_RULES`

## Goal

Make entity-source selection explicit while keeping automatic recognition targeted
to privacy data and avoiding broad masking of receipt amounts, dates, totals, and
ordinary financial text.

## Reconstructed requirements

- Support `entityDetectionMode` values `automatic`, `configured`, `combined`, and
  `disabled`.
- Preserve legacy inference when the key is absent: configured literals imply
  configured-only mode; otherwise automatic mode.
- In `combined`, configured mask/replacement spans take precedence over
  overlapping automatic detections.
- `excluded` filters only automatic detections and never cancels explicit
  configured rules.
- `includedParagraphs` remains independent from entity-detection mode.
- Expose the ordered mode identifiers through the public anonymization API so CLI
  and UI do not duplicate the contract.
- Automatic mode uses both required local Russian and English spaCy models and
  must fail rather than silently degrade to one language.
- Use a deliberate privacy entity set instead of every default Presidio
  recognizer.
- Keep generic organization/location NER disabled and reject single-token PERSON
  guesses to reduce false positives.
- Keep explicit project recognizers for identifiers, bank/card data, contacts,
  and bounded international `+` phone formats.
- Do not treat short signed numbers as international phones.

## Validation evidence

Deterministic regressions cover all modes, legacy inference, precedence,
multilingual analysis, targeted recognizers, and CLI/UI analyzer selection.
