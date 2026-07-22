# AGENTS.md

This file contains development rules for AI coding agents working on `acc-source-docs-processor`.

## Project summary

The project is a local CLI for scanned accounting source documents. A complete document type definition selects three independent parts:

```text
document processor + folder workflow + registry definition
```

The current released type is `upd_invoices_status_1`.

## Language rules

- All code comments, docstrings, tests, configuration comments, and software documentation must be in English.
- Russian accounting field names may remain in OCR patterns and user-facing filenames where required by the business workflow.

## Architecture rules

- Keep `main.py` minimal.
- A document processor owns only image-level recognition, orientation, OCR, extraction, and recognition decisions.
- A processor must not own copying, output folders, filename policy, report generation, or CSV columns.
- A processing workflow owns recursive folder behavior and file actions.
- A registry definition owns columns and row mapping.
- `source_docs_processor/document_types.py` binds processor, workflow, and registry factories into one CLI-selectable definition.
- Keep low-level file operations in `file_ops.py` and generic CSV serialization in `registry/csv_writer.py`.
- Keep template crops and OCR heuristics in the corresponding processor package.
- Do not add document-type conditionals to `cli.py`.
- Do not add external network calls. Processing must remain local.

## Generic model rules

Use these fields consistently:

- `document_number`, `document_date`, and `document_datetime` for identity;
- `issuer_*` for the issuing or service-providing party;
- `recipient_*` for the receiving or buying party;
- `amount_without_tax`, `tax_amount`, `total_amount`, and `currency` for money;
- `description` for goods or services;
- `extra_fields` only for document-specific extracted values.

Do not put output-action state into the generic extracted model unless it is necessary to describe a produced artifact.

## UPD rules

- Keep UPD-specific code under `source_docs_processor/upd_invoices_status_1/`.
- Keep OCR and extraction in `processor.py`, `ocr.py`, `extractor.py`, and `image_processing.py`.
- Keep UPD copy/naming/continuation policy in `workflow.py`.
- Keep UPD CSV columns and row mapping in `registry.py`.
- Prefer targeted OCR crops over full-page OCR.
- Preserve `Документ об отгрузке` fallback logic.
- Preserve form-template date filtering for `02-04-2021`.
- Preserve short-number and over-read corrections.
- Recognize standalone pages before continuation pages.
- Preserve auto-rotation, debug crops, `УПД_<number>_от_<date>`, and `_2_страница` output names.

## Testing rules

- Use `pytest`.
- Put pure logic tests under `tests/unit/` and pipeline/filesystem tests under `tests/integration/`.
- Every test must have an English docstring explaining the verified behavior and protected risk.
- Test processors, workflows, and registry definitions independently where useful.
- Prefer fake OCR, fake processors, synthetic workflows, and generated images.
- Every OCR or extraction bug fix must add a regression test.
- Do not commit real scans, names, INNs/KPPs, addresses, or shipment data.

Run validation with:

```bash
python -m py_compile main.py source_docs_processor/*.py source_docs_processor/*/*.py
python -m pytest -q
```

## Documentation rules

- Keep `README.md` user-oriented.
- Put detailed design in `docs/ARCHITECTURE.md`.
- Record completed changes in `docs/CHANGELOG.md`.
- Track work in `docs/ROADMAP.md` using `[x]`, `[/]`, and `[ ]`.
- Update documentation when CLI behavior, registry columns, project structure, or component contracts change.

## Archive checklist

1. Preserve the root folder `acc-source-docs-processor/`.
2. Keep the default UPD document type registered.
3. Include no private accounting fixtures.
4. Confirm README examples match current behavior.
5. Confirm processors do not contain workflow or registry policy.
