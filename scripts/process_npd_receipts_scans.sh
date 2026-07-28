#!/usr/bin/env bash
set -euo pipefail

rm -fR ../acc/output/receipts_dir

# Process scanned NPD receipts from the project root.
python main.py process \
  --source ../acc_work/input/npd_receipts \
  --output ../acc_work/output/receipts_dir \
  --document-type npd_receipts
