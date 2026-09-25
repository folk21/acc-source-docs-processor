---
type: Specification
title: Safe anonymization output cleanup and path handling
description: Reconstructed change contract for stable output-directory cleanup and safe source/output traversal.
document_role: subspec
spec_status: completed
---

# Safe anonymization output cleanup and path handling

## Status

Completed and released in `0.13.7` and `0.13.8`.

## Feature scope

- `ANONYMIZATION.LOCAL_REDACTION`

## Goal

Make repeated anonymization runs safe when source/output paths overlap in allowed
ways and when another terminal has the output directory as its current working
directory.

## Reconstructed requirements

- Exclude generated output from source traversal only when output is actually
  nested inside source.
- Allow output to be an ancestor of source when traversal remains safe.
- Treat an empty effective source scan as an explicit error rather than silent
  zero-file success.
- `--clearOutput` removes existing output contents while preserving the output
  root inode and existing directory objects.
- Never implement cleanup by deleting and recreating the output root.
- Reject cleanup when source is nested inside output.
- Preserve privacy-safe diagnostics and source files.

## Validation evidence

Regression tests protect ancestor/descendant path behavior, open-directory inode
preservation, and unsafe cleanup rejection.
