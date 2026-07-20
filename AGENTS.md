# AGENTS.md

This file contains instructions for AI coding agents working on `acc-source-docs-processor`.

## Project summary

`acc-source-docs-processor` is a local Python utility for processing scanned Russian accounting source documents. The current implementation focuses on UPD transfer documents with status `1`, extracts document number/date, copies and renames files, and generates a CSV registry plus a report.

The current OCR logic is practical and heuristic-heavy because it was tuned against real scanned documents with rotation, weak contrast, punch holes, noisy headers, over-read digits, and second pages.

## Repository structure

```text
acc-source-docs-processor/
├── README.md
├── AGENTS.md
├── requirements.txt
├── main.py
├── run.sh
├── run_example.sh
├── archive.sh
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   └── ROADMAP.md
└── source_docs_processor/
    ├── __init__.py
    ├── cli.py
    ├── extractor.py
    ├── file_ops.py
    ├── image_processing.py
    ├── models.py
    └── ocr.py
```

## Language rules

- All code comments must be written in English.
- All docstrings must be written in English.
- All software documentation must be written in English.
- User-facing file names may contain Russian when this matches the business requirement, for example `УПД_426_от_09-03-2023.png` or `передаточные_документы`.
- Do not translate Russian accounting field names that must be matched in OCR text, for example `Документ об отгрузке`, `Счет-фактура`, or `Статус`.

## Coding rules

- Keep `main.py` minimal. Put application logic in `source_docs_processor`.
- Keep importable package code under `source_docs_processor`.
- Do not use hyphens in Python package or module names.
- Prefer small functions with clear docstrings.
- Add comments only when they explain non-obvious OCR or business logic.
- Preserve source files. The application must never modify input scans.
- Be careful with filesystem paths that contain Cyrillic characters.
- Preserve the source subfolder structure in output unless the user explicitly asks otherwise.
- Do not write full local paths to CSV output unless the user explicitly asks for them.

## OCR-specific rules

- Do not rely only on full-page OCR for key fields.
- Prefer targeted crop OCR for status, document number, document date, and shipment-row fields.
- The `Документ об отгрузке` row is a high-priority fallback source for document number/date.
- In rows like `№ п/п 1 № 511 от 21 марта 2023 г.`, the first `1` is only the row number. The actual document number is after the next `№`.
- Ignore the UPD form-template date `02-04-2021` when it comes from the government-decree service text.
- Continue to record heuristic corrections in the `warnings` field.
- Use `--debug-crops` when changing crop coordinates or OCR preprocessing.

## Continuation-page rules

- Always try to recognize a scan as a standalone UPD first page before treating it as a continuation page.
- Treat a page as a continuation only when standalone UPD recognition fails and continuation markers are strong.
- Continuation pages inherit the previous recognized document number/date.
- Continuation output file names must use the previous document stem plus `_2_страница` or a later page suffix if implemented.

## Documentation rules

- Keep `README.md` concise and user-oriented.
- Put detailed internal logic in `docs/ARCHITECTURE.md`.
- Record functional milestones in `docs/CHANGELOG.md`.
- Track planned work in `docs/ROADMAP.md`.
- Update documentation when changing CLI parameters, output files, registry columns, or recognition behavior.

## Validation checklist

Before returning an updated project archive:

1. Run Python compilation checks:

   ```bash
   python -m py_compile main.py source_docs_processor/*.py
   ```

2. Confirm the archive contains the project root folder, not only loose files.
3. Confirm the internal package is named `source_docs_processor`.
4. Confirm generated documentation is included in the archive.
5. Confirm README examples still match the current CLI behavior.

## Avoid

- Do not remove working OCR heuristics without replacing them with tested behavior.
- Do not simplify date extraction in a way that allows the template date `02-04-2021` to be used as a document date.
- Do not classify a scan as a continuation page before standalone document recognition has failed.
- Do not make output paths absolute in the registry by default.
- Do not add external network calls. The tool must remain local.
