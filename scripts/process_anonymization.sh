#!/usr/bin/env bash
set -euo pipefail

# Anonymize documents
python main.py anonymize \
  --source ../acc-work/input/anonymization \
  --output ../acc-work/output/anonymization \
  --outputDocumentType docx \
  --outputLayout preserve \
  --clearOutput \
  --alsoOutputSourceFormat