# AGENTS.md

This file contains development rules for AI coding agents working on `acc-source-docs-processor`.

## Project summary

The project is a local CLI for scanned accounting source documents. It uses a generic folder pipeline plus factory-selected document processors.

The current released processor is `upd_invoices_status_1`. Its OCR logic is heuristic-heavy and tuned for rotation, weak contrast, noisy headers, over-read digits, template dates, and continuation pages.

## Language rules

- All code comments, docstrings, tests, configuration comments, and software documentation must be in English.
- Russian accounting field names may remain in OCR patterns and user-facing filenames where required by the business workflow.

## Generic architecture rules

- Keep `main.py` minimal.
- Keep file discovery, image loading, copying, CSV/report output, and common OCR wrappers in the top-level package.
- Keep template crops, OCR anchors, extraction rules, confidence logic, and business naming in a processor package.
- Use `ExtractedDocument` common fields for values shared across document types.
- Put document-specific values in `extra_fields` and declare their CSV keys in `registry_extra_columns`.
- Do not add invoice-, UPD-, receipt-, or act-specific fields to the generic model unless at least two real processor types need the same concept.
- Do not generate filenames in generic file operations. Each processor owns its filename policy.
- A processor should extend `BaseDocumentProcessor` unless there is a concrete reason not to.
- Register processors explicitly in `PROCESSOR_FACTORIES`.
- Do not add external network calls. Processing must remain local.

## Generic field semantics

Use these mappings consistently:

- `document_number`, `document_date`, `document_datetime` for document identity;
- `issuer_*` for the party issuing/providing the document or service;
- `recipient_*` for the receiving/buying party;
- `amount_without_tax`, `tax_amount`, `total_amount`, `currency` for money;
- `description` for the main service or goods description;
- `status` for a processor-defined document status;
- `extra_fields` only for document-specific values.

## UPD processor rules

- Keep all UPD-specific logic under `source_docs_processor/upd_invoices_status_1/`.
- Prefer targeted OCR crops over full-page OCR.
- Use `Документ об отгрузке` as a high-priority number/date fallback.
- Ignore the form-template date `02-04-2021` when it comes from regulation text.
- Preserve short-number and over-read correction heuristics.
- Recognize standalone UPD pages before checking continuation-page markers.
- Preserve auto-rotation and debug-crop support.
- Preserve the `УПД_<number>_от_<date>` and `_2_страница` filename conventions.

## Testing rules

- Use `pytest`.
- Put pure logic tests under `tests/unit/` and pipeline/filesystem tests under `tests/integration/`.
- Every test must have an English docstring explaining the verified behavior and protected risk.
- Prefer fake OCR, fake processors, and synthetic images.
- Every recognition bug fix must add a regression test.
- Do not commit real scans, company names, INNs/KPPs, addresses, or shipment data.

Run tests with:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Documentation rules

- Keep `README.md` user-oriented and reasonably compact.
- Put detailed design in `docs/ARCHITECTURE.md`.
- Record completed changes in `docs/CHANGELOG.md`.
- Track work in `docs/ROADMAP.md` using `[x]`, `[/]`, and `[ ]`.
- Update documentation when CLI behavior, registry columns, project structure, or processor contracts change.

## Validation checklist

Before returning an archive:

```bash
python -m py_compile main.py source_docs_processor/*.py source_docs_processor/*/*.py
python -m pytest -q
```

Also confirm:

1. The archive contains the root folder `acc-source-docs-processor/`.
2. The default UPD processor is still registered.
3. No real accounting scans or identifiers were added.
4. README examples match the current CLI.
5. CSV common columns remain document-type-neutral.
