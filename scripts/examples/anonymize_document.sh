#!/usr/bin/env bash
set -euo pipefail

# The anonymize subcommand is reserved but not implemented yet.
python main.py anonymize \
  --source "/path/to/document.pdf" \
  --output "/path/to/document_anonymized.pdf" \
  --document-type incoming_purchase_documents
