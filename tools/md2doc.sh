#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <markdown_file> [output_dir]" >&2
  exit 2
fi

MD_PATH="$1"
if [[ ! -f "$MD_PATH" ]]; then
  echo "Input markdown not found: $MD_PATH" >&2
  exit 1
fi

MD_ABS="$(cd "$(dirname "$MD_PATH")" && pwd)/$(basename "$MD_PATH")"
BASE_NAME="$(basename "$MD_ABS")"
BASE_STEM="${BASE_NAME%.*}"
OUT_DIR="${2:-$(dirname "$MD_ABS")/build-docx}"
ASSETS_DIR="$OUT_DIR/assets"
WORK_MD="$OUT_DIR/${BASE_STEM}.publish.md"
OUT_DOCX="$OUT_DIR/${BASE_STEM}.docx"
TMP_DIR="$OUT_DIR/.tmp"

mkdir -p "$OUT_DIR" "$ASSETS_DIR" "$TMP_DIR"

node "$(dirname "$0")/preprocess_html_blocks.mjs" "$MD_ABS" "$TMP_DIR" "$WORK_MD"

render_ok=1
shopt -s nullglob
for html in "$TMP_DIR"/*.html; do
  id="$(basename "$html" .html)"
  png="$ASSETS_DIR/${id}.png"
  if node "$(dirname "$0")/render_html_to_png.mjs" "$html" "$png" 1242; then
    perl -0777 -i -pe "s/__HTML2PNG_BLOCK__${id}__/![${id}](assets\\/${id}.png)/g" "$WORK_MD"
  else
    echo "[WARN] render failed for $id" >&2
    render_ok=0
  fi
done

perl -0777 -i -pe 's/__HTML2PNG_BLOCK__([^_]+)__/<!-- HTML2PNG unresolved: $1 -->/g' "$WORK_MD"

if command -v pandoc >/dev/null 2>&1; then
  pandoc "$WORK_MD" -o "$OUT_DOCX" --resource-path="$OUT_DIR:$(dirname "$MD_ABS")"
  echo "[OK] docx: $OUT_DOCX"
else
  echo "[WARN] pandoc not found, skipped docx export" >&2
fi

echo "[OK] publish markdown: $WORK_MD"
if [[ "$render_ok" -eq 0 ]]; then
  echo "[WARN] some html blocks failed to render" >&2
  exit 1
fi
