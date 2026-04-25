#!/bin/bash
set -e

echo "=== QMD Maintenance Check ==="

# Check qmd availability
if ! command -v qmd &> /dev/null; then
    echo "ERROR: qmd not found in PATH"
    exit 1
fi

echo "qmd found: $(qmd --version 2>&1 || echo 'version unknown')"

echo ""
echo "=== 1) Collection Check ==="
qmd collection list 2>&1 || echo "COLLECTION_CHECK_FAILED"

echo ""
echo "=== 2) QMD Update ==="
qmd update 2>&1 || echo "UPDATE_FAILED"

echo ""
echo "=== 3) QMD Embed ==="
qmd embed 2>&1 || echo "EMBED_FAILED"

echo ""
echo "=== 4) QMD Status ==="
qmd status 2>&1 || echo "STATUS_FAILED"

echo ""
echo "=== Done ==="