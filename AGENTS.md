# AGENTS.md

This file contains development rules for AI coding agents working on `acc-source-docs-processor`.

## Project summary

The project is a local CLI for scanned and electronic accounting source documents. A complete document type definition selects three independent parts:

```text
document processor + processing workflow + registry definition
```

The registered document types are:

- `upd_invoices_status_1` — the default scan-oriented document type;
- `npd_receipts`;
- `incoming_purchase_documents` — incoming purchase-document tasks for 1C entry; the current implementation supports PDF/DOCX UPD status `1` only.

## Language rules

- All code comments, docstrings, tests, configuration comments, and software documentation must be in English.
- Russian accounting field names may remain in OCR patterns, registry headers, and user-facing filenames where required by the business workflow.

## Architecture rules

- Keep `main.py` minimal.
- Keep top-level operation selection in `source_docs_processor/cli.py`.
- Keep command-specific parsing and execution in `source_docs_processor/commands/`.
- Use CLI subcommands for distinct operations such as `process` and `anonymize`; do not model operations as document types.
- An image document processor owns only image-level recognition, orientation, OCR, extraction, normalization, and recognition decisions.
- A source-file processor owns only one-file reading, OCR fallback, extraction, normalization, and recognition decisions.
- A processor must not own folder traversal, copying, output folders, filename policy, report generation, or registry columns.
- A processing workflow owns recursive folder behavior, file actions, output selection, and the document list passed to a registry writer.
- A registry definition owns the tabular schema and conversion of one `ExtractedDocument` into one row.
- Registry writers own serialization. Keep generic CSV and XLSX output in `source_docs_processor/registry/`.
- `source_docs_processor/document_types.py` binds processor, workflow, and registry factories into one CLI-selectable definition.
- Keep low-level file operations in `file_ops.py`.
- Keep template crops and OCR heuristics in the corresponding processor package.
- Do not add document-type conditionals to `cli.py` or command handlers.
- Do not add external network calls. Processing must remain local.

`RegistryDefinition` is intentionally narrower than an output processor. It defines columns and row mapping; workflows, file operations, and CSV/XLSX writers handle the remaining output behavior.

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
- Keep UPD copy, naming, and continuation policy in `workflow.py`.
- Keep UPD CSV columns and row mapping in `registry.py`.
- Prefer targeted OCR crops over full-page OCR.
- Preserve `Документ об отгрузке` fallback logic.
- Preserve form-template date filtering for `02-04-2021`.
- Preserve short-number and over-read corrections.
- Recognize standalone pages before continuation pages.
- Preserve auto-rotation, debug crops, `УПД_<number>_от_<date>`, and `_2_страница` output names.

## Incoming purchase document rules

- Keep incoming purchase-document logic under `source_docs_processor/incoming_purchase_documents/`.
- Keep native file reading in `readers.py`, extraction in `extractor.py`, file recognition in `processor.py`, folder behavior in `workflow.py`, and workbook rows in `registry.py`.
- Support UPD status `1` in `.pdf` and `.docx`; do not claim act or native `.doc` support.
- Prefer native PDF text and table extraction before OCR.
- OCR only PDF pages without a useful text layer unless `--deep-ocr` is enabled.
- Preserve one task per complete UPD and keep item rows linked through `task_id`.
- Keep `processed` binary and document-level as a `Нет`/`Да` dropdown; do not add editable item-level processing state.
- Link directly to source PDF/DOCX files; do not copy unchanged source files by default.
- Write directly into an explicit `--output` directory unless `--target-dir-name` is also provided.
- Keep `task_id` columns hidden and document their internal linking purpose.
- Keep unrecognized or incomplete files visible in `Documents` and `Review`.
- Reject explicit UPD status `2`.
- Keep workbook sheets `Documents`, `Items`, `Review`, and hidden `_metadata`.
- Reject the official UPD column-designator row (`1`, `1а`, `1б`, `2`, `2а`, and similar values) as item data.
- Keep numeric OKEI codes separate from textual unit names; never export a numeric code as `unit`.
- Validate item arithmetic and document totals without silently replacing conflicting values.

## NPD receipt rules

- Keep NPD-specific code under `source_docs_processor/npd_receipts/`.
- Keep receipt OCR and extraction inside the NPD package.
- Keep copy, rename, output-folder, and workbook selection policy in `workflow.py`.
- Keep the compact XLSX schema and row mapping in `registry.py`.
- Preserve copying of every source image and relative subfolder structure.
- Rename only recognized receipts; copy unrecognized images without renaming.
- Include only recognized receipts in `реестр_чеков_нпд.xlsx`.
- Preserve the filename pattern `<date>_<amount>_<surnameFirstNamePatronymic>_<receiptNumber>`.
- Preserve the exact eight-column workbook contract documented in `README.md`.
- Keep the hyperlink only in `target_file_name`; `source_file_name` must remain plain text.
- Treat the first INN in receipt order as the self-employed payee INN unless stronger verified data is introduced.
- Accept receipt numbers only after an explicit receipt-number label.
- Preserve one-line and split-line full-name recognition.
- QR decoding and official NPD URL parsing must remain local. When integrated, reconcile QR and OCR values explicitly and report conflicts instead of silently replacing data.

## Testing rules

- Use `pytest`.
- Put pure logic tests under `tests/unit/` and pipeline/filesystem tests under `tests/integration/`.
- Group document-specific tests under folders matching the production package name, such as `tests/unit/npd_receipts/` and `tests/integration/incoming_purchase_documents/`.
- Keep generic model, factory, writer, and synthetic cross-component tests directly under `tests/unit/` or `tests/integration/`.
- Every test must have an English docstring explaining the verified behavior and protected risk.
- Test processors, workflows, registry definitions, and writers independently where useful.
- Prefer fake OCR, fake processors, synthetic workflows, prepared text, and generated images.
- Every OCR or extraction bug fix must add a regression test.
- Real OCR tests must be optional, marked `ocr` or `slow`, and skipped when Tesseract is unavailable.
- Do not commit real scans, names, INNs/KPPs, addresses, shipment data, or debug crops from private documents.

Example launch scripts belong under `scripts/examples/`. They must use placeholder paths, run from the project root, and contain English comments only.

Run validation from the project root:

```bash
python -m compileall -q main.py source_docs_processor tests
python -m pytest -q
```

## Documentation rules

- Keep `README.md` user-oriented and compact.
- Put detailed design and component contracts in `docs/ARCHITECTURE.md`.
- Record completed changes in `docs/CHANGELOG.md`.
- Track planned and partially completed work in `docs/ROADMAP.md` using `[x]`, `[/]`, and `[ ]`.
- Update documentation when CLI behavior, supported document types, registry columns, output files, project structure, or component contracts change.
- Avoid changelog-style wording such as “now” or “previously” in documents that describe the current architecture.

## Archive checklist

1. Preserve the root folder `acc-source-docs-processor/`.
2. Keep all registered document types and the default scan UPD selection intact.
3. Include no private accounting fixtures or generated private output.
4. Confirm README commands, subcommands, example scripts, and output descriptions match current behavior.
5. Confirm processors contain no workflow or registry policy.
6. Confirm registry writers remain document-type-neutral.
7. Run compile and test validation.
