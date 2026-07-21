#!/usr/bin/env bash
set -euo pipefail

# Example usage. Replace the source path with your scan archive path.
# The target folder is created in the current working directory by default.
python main.py --source "/path/to/scans" --document-type upd_invoices_status_1 --target-dir-name "передаточные_документы"
