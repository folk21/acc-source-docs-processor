# Local Streamlit UI

## Purpose

This package is an optional local adapter for non-technical users. It presents
supported operations in a browser while calling the existing public Python APIs
in the same local process.

```text
Streamlit UI -> public feature API -> existing workflow
CLI          -> public feature API -> existing workflow
```

The first released UI operation is document anonymization.

## Structure

```text
streamlit_app.py
source_docs_processor/ui/
├── AGENTS.md
├── README.md
├── app.py
├── anonymization.py
├── config.py
└── path_validation.py
config/ui/
├── ui_ru.ini
└── ui_en.ini
```

## Localization

The operation list, titles, descriptions, labels, help text, progress messages,
result-table headings, and validation messages are loaded from
`config/ui/ui_<language>.ini`.

Russian is the default language. English can be selected in the interface or at
launch:

```bash
python -m streamlit run streamlit_app.py -- --lang en
```

The language configuration controls only known operation identifiers. It cannot
load arbitrary Python handlers.

## Dependencies and launch

Install the optional UI environment:

```bash
pip install -r requirements-ui.txt
```

Run from the project root:

```bash
python -m streamlit run streamlit_app.py -- --lang ru
```

The application is intended for localhost use on the same machine that contains
the source and output folders. No browser upload or remote storage is included.

## Validation

```bash
make test-ui
make check
```
