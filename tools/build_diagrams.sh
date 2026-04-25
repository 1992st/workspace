#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <task_id|task_dir>"
  echo "Example: $0 2026-04-05-002"
  exit 1
fi

python3 "$SCRIPT_DIR/diagram_build.py" "$1" --root "$ROOT_DIR"
