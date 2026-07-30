#!/usr/bin/env bash
set -euo pipefail

# Keep the output folder and remove the files in it
mkdir -p ../acc-work/output/npd_receipts
find ../acc-work/output/npd_receipts \
  -mindepth 1 \
  -maxdepth 1 \
  -exec rm -rf -- {} +

# Process scanned NPD receipts from the project root
python main.py process \
  --source ../acc-work/input/npd_receipts \
  --output ../acc-work/output/npd_receipts \
  --document-type npd_receipts
