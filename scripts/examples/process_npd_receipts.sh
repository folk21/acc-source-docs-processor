#!/usr/bin/env bash
set -euo pipefail

# Process scanned NPD receipts from the project root.
python main.py process \
  --source "/path/to/receipts" \
  --output "/path/to/output" \
  --document-type npd_receipts
