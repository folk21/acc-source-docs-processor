# Anonymization development guide

This file narrows the root `AGENTS.md` rules for
`source_docs_processor/features/anonymization/`.

## Scope

Use this feature for local privacy-safe redaction of supported document formats.
The preferred change scope is this feature plus its matching unit/integration
tests. Change `source_docs_processor/core/` only when the required behavior is
feature-neutral.

Do not modify document processing for an anonymization-only task.

## Public surface

- `api.py` owns the programmatic entry points and public result/configuration
  types.
- `command.py` owns argparse integration and console orchestration.
- `__init__.py` re-exports only the supported package API. Keep `api.py` and
  package `__all__` synchronized with `tests/unit/anonymization/test_api.py`.

Everything under `_internal/` is private to this feature.

## Internal ownership

- `_internal/config.py` owns configuration loading and matching rules.
- `_internal/workflow.py` owns recursive processing and output planning.
- `_internal/text.py` owns text recognition and replacement decisions.
- `_internal/image.py`, `pdf.py`, `docx.py`, and `editable.py` own format-specific
  sanitization and reconstruction.
- `_internal/models.py` owns feature-private state shared by those modules.

Modules outside anonymization must not import this `_internal/` package.

## Invariants

- Processing remains local; do not add network or cloud OCR calls.
- Unsupported or opaque content fails closed.
- Never log recognized PII values.
- `entityDetectionMode` owns entity-source selection: `automatic`, `configured`,
  `combined`, or `disabled`; legacy configurations without the key retain their
  historical inferred behavior.
- Automatic detection uses both Russian and English local spaCy NER. Do not
  silently fall back to one language when a required model is unavailable.
- Keep automatic detection targeted to privacy entities. Do not enable broad
  Presidio recognizers that can mask receipt amounts, dates, or ordinary text
  without a regression demonstrating the need.
- Keep generic organization/location NER disabled in automatic detection and
  reject single-token PERSON guesses; use explicit configured rules for known
  single-word proper names.
- Keep boarding-pass passenger-name recovery narrow and label/slash anchored; do
  not replace it with generic uppercase-word heuristics.
- Keep international `+` phone recognition language-neutral and regression-tested.
- In `combined` mode, explicit `included` and `includedAndReplaced` spans take
  priority over overlapping automatic detections; `excluded` filters only the
  automatic side.
- `includedParagraphs` remains independent from entity-detection mode.
- Preserve source names and relative paths unless deterministic conversion or
  collision handling requires a new name.
- Do not retain PDF source text layers or metadata.
- `--clearOutput` must preserve the output root inode.
- Use synthetic names, identifiers, files, images, and workbooks in tests.
- XLSX anonymization must preserve numeric values and formulas, sanitize hidden
  visible-content stores and supported embedded raster images, and fail closed on
  external links, active/embedded objects, cached external data, or detected PII
  inside formulas/structural names.

## Validation

Run the public contract tests after changing exports, signatures, constants, or
public models:

```bash
make test-public-api
```

Run the focused suite while developing:

```bash
make test-anonymization
```

Run the full project validation before completion:

```bash
make check
```
