#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <doc_path>" >&2
  exit 2
fi

DOC="$1"
if [[ ! -f "$DOC" ]]; then
  echo "BLOCKED: doc not found: $DOC"
  exit 1
fi

BASE_DIR="$(cd "$(dirname "$DOC")" && pwd)"
FAIL=0

echo "[LUMI_REVIEW] doc=$DOC"

# G1.1 Markdown image path existence
while IFS= read -r src; do
  [[ -z "$src" ]] && continue
  if [[ "$src" =~ ^https?:// ]]; then
    continue
  fi
  if [[ "$src" =~ ^data: ]]; then
    continue
  fi
  img="$BASE_DIR/$src"
  if [[ ! -f "$img" ]]; then
    echo "ISSUE G1 IMG_NOT_FOUND $src"
    FAIL=1
  fi
done < <(rg -o '!\[[^]]*\]\(([^)]+)\)' "$DOC" -r '$1' || true)

# G1.1 HTML img src non-empty + local existence
while IFS= read -r src; do
  [[ -z "$src" ]] && continue
  if [[ "$src" =~ ^https?://|^data: ]]; then
    continue
  fi
  img="$BASE_DIR/$src"
  if [[ ! -f "$img" ]]; then
    echo "ISSUE G1 HTML_IMG_NOT_FOUND $src"
    FAIL=1
  fi
done < <(rg -o '<img[^>]*src="([^"]+)"' "$DOC" -r '$1' || true)

# G1.2 risky box drawing table chars
if rg -n '[┌┬┐├┼┤└┴┘│]' "$DOC" >/dev/null 2>&1; then
  echo "ISSUE G1 BOX_DRAWING_RENDER_RISK detected"
  FAIL=1
fi

# G2 heuristic guard: uncertain claims should carry boundary hints when window claims appear
if rg -n '窗口期|必然|一定会|注定' "$DOC" >/dev/null 2>&1; then
  if ! rg -n '可能|不确定|边界|因行业而异|主观判断|风险' "$DOC" >/dev/null 2>&1; then
    echo "ISSUE G2 MISSING_UNCERTAINTY_BOUNDARY"
    FAIL=1
  fi
fi

# G2 tone guard (business default)
if rg -n '姐妹们|家人们|宝子们' "$DOC" >/dev/null 2>&1; then
  echo "ISSUE G2 PERSONA_DRIFT_STRONG"
  FAIL=1
fi

# G3 readability: too many ultra-short lines can indicate over-fragmentation
short_lines=$(awk 'length($0)>0 && length($0)<8 {c++} END{print c+0}' "$DOC")
if [[ "$short_lines" -gt 40 ]]; then
  echo "ISSUE G3 OVER_FRAGMENTED short_lines=$short_lines"
  FAIL=1
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "PASS"
  exit 0
fi

echo "REVISION_REQUIRED"
exit 1
