#!/usr/bin/env bash
set -euo pipefail

# Process incoming PDF/DOCX UPD status 1 documents from the project root.
python main.py process \
  --source "/path/to/upd-input" \
  --output "/path/to/output" \
  --document-type incoming_purchase_documents
