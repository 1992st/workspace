#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Standard path script for HTML -> PNG with Chrome headless.
Use direct Chrome command when custom flags are required.

Usage:
  render_html_to_png.sh --html <html_path_or_file_url> --out <png_path> [--window-size <width,height>] [--chrome <chrome_bin>]

Options:
  --html         HTML file path or file:// URL.
  --out          Output PNG absolute/relative path.
  --window-size  Screenshot viewport, default 1080,1920.
  --chrome       Optional Chrome binary path override.

Examples:
  render_html_to_png.sh --html ./assets/demo.html --out ./assets/demo.png
  render_html_to_png.sh --html file:///tmp/demo.html --out /tmp/demo.png --window-size 1290,2796
USAGE
}

HTML_INPUT=""
OUT_PNG=""
WINDOW_SIZE="1080,1920"
CHROME_BIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --html)
      HTML_INPUT="${2:-}"
      shift 2
      ;;
    --out)
      OUT_PNG="${2:-}"
      shift 2
      ;;
    --window-size|--windows-size)
      WINDOW_SIZE="${2:-}"
      shift 2
      ;;
    --chrome)
      CHROME_BIN="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$HTML_INPUT" || -z "$OUT_PNG" ]]; then
  echo "Both --html and --out are required." >&2
  usage
  exit 2
fi

if [[ "$HTML_INPUT" =~ ^file:// ]]; then
  HTML_URL="$HTML_INPUT"
else
  if [[ ! -f "$HTML_INPUT" ]]; then
    echo "HTML file does not exist: $HTML_INPUT" >&2
    exit 2
  fi
  ABS_HTML="$(cd "$(dirname "$HTML_INPUT")" && pwd)/$(basename "$HTML_INPUT")"
  HTML_URL="file://$ABS_HTML"
fi

if [[ ! "$WINDOW_SIZE" =~ ^[0-9]+,[0-9]+$ ]]; then
  echo "Invalid --window-size value: $WINDOW_SIZE (expected width,height)" >&2
  exit 2
fi

if [[ -z "$CHROME_BIN" ]]; then
  if [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]; then
    CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  elif command -v google-chrome >/dev/null 2>&1; then
    CHROME_BIN="$(command -v google-chrome)"
  elif command -v chromium >/dev/null 2>&1; then
    CHROME_BIN="$(command -v chromium)"
  elif command -v chromium-browser >/dev/null 2>&1; then
    CHROME_BIN="$(command -v chromium-browser)"
  else
    echo "Chrome binary not found. Pass --chrome <path>." >&2
    exit 2
  fi
fi

mkdir -p "$(dirname "$OUT_PNG")"

USER_DATA_DIR="$(mktemp -d /tmp/chrome-headless-profile.XXXXXX)"
cleanup() {
  rm -rf "$USER_DATA_DIR"
}
trap cleanup EXIT

"$CHROME_BIN" \
  --headless=new \
  --disable-gpu \
  --hide-scrollbars \
  --no-first-run \
  --no-default-browser-check \
  --disable-background-networking \
  --user-data-dir="$USER_DATA_DIR" \
  --window-size="$WINDOW_SIZE" \
  --screenshot="$OUT_PNG" \
  "$HTML_URL"

echo "PNG generated: $OUT_PNG"
