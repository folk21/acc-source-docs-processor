#!/usr/bin/env bash
set -euo pipefail

# Anonymize supported files recursively while preserving names and subfolders.
python main.py anonymize \
  --source "/path/to/private-documents" \
  --output "/path/to/anonymized-documents" \
  --output-document-type docx \
  --output-layout preserve \
  --also-output-source-format \
  --config "config/anonymization.ini"
