#!/usr/bin/env bash
set -euo pipefail

# The target folder is created in the current working directory by default.
python main.py --source scans --target-dir-name target_scans

