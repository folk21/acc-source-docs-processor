---
type: Quality Guide
title: Code quality and repository gates
description: Current quality gates, architecture checks, and ownership of planned lint, CI, and packaging improvements.
---

# Code quality and repository gates

## Current gate

The current repository-wide gate is:

```bash
make check
```

It combines Python compilation and the full pytest suite. Architecture and public
API regressions are ordinary tests, so boundary drift fails the same validation
workflow as behavioral regressions.

Focused commands and test-layer policy are documented in [Tests](TESTS.md).

## Current quality invariants

- Keep feature ownership and dependency direction explicit.
- Keep public APIs small and regression-tested.
- Prefer deterministic synthetic tests over external services or real private
  documents.
- Avoid adding dependencies without a concrete need.
- Avoid broad refactors unrelated to the current task.
- Keep comments/docstrings useful and in English.
- Preserve privacy-safe logging and output behavior.

## Planned tooling

The roadmap currently includes:

- `TOOLING.CI_QUALITY` — add `ruff` configuration and continuous integration;
- `TOOLING.PACKAGING` — add `pyproject.toml`, package the CLI, and evaluate a
  standalone executable distribution.

Those items are not implemented yet. Do not document lint, CI, packaging, or
coverage gates as active until the repository actually contains and validates
them.

## Ownership

- `Makefile` owns runnable repository validation commands.
- `docs/TESTS.md` owns test strategy and command selection.
- this file owns quality-tool policy and the distinction between active and
  planned quality gates.
- `docs/ROADMAP.md` owns prioritization of future tooling work.
