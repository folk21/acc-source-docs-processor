#!/usr/bin/env bash
set -euo pipefail

# Process scanned UPD status 1 documents from the project root.
python main.py process \
  --source "/path/to/upd-scans" \
  --output "/path/to/output" \
  --document-type upd_invoices_status_1
