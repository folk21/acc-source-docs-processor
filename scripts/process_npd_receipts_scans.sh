#!/usr/bin/env bash
set -euo pipefail

rm -fR ../acc-work/output/npd_receipts

# Process scanned NPD receipts from the project root.
python main.py process \
  --source ../acc-work/input/npd_receipts \
  --output ../acc-work/output/npd_receipts \
  --document-type npd_receipts
