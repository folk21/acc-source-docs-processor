#!/usr/bin/env bash
set -euo pipefail

# Run the local Streamlit UI in Russian unless another language is provided.
UI_LANGUAGE="${1:-ru}"
python -m streamlit run streamlit_app.py -- --lang "$UI_LANGUAGE"
