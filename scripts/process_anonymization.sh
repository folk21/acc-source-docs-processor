#!/usr/bin/env bash
set -euo pipefail

rm -fR ../acc-work/output/anonymization

# Anonymize documents
python main.py anonymize \
  --source ../acc-work/input/anonymization \
  --output ../acc-work/output/anonymization \
  --output-document-type docx \
  --outputLayout preserve \
  --alsoOutputSourceFormat