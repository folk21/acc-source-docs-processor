#!/usr/bin/env bash
set -euo pipefail

# Reconcile local receipt and ticket files with an XLSX bank statement.
python main.py reconcile-expenses \
  --source "/path/to/receipts-and-tickets" \
  --statement "/path/to/payments.xlsx" \
  --output "/path/to/output"
