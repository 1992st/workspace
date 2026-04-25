#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
tasks = root / "tasks"
dev = root / "dev-topics"
errors = []

if dev.exists():
    for p in dev.iterdir():
        if p.name.startswith(".") or p.name in {"_migrated", "README.md"}:
            continue
        errors.append(f"dev-topics should be deprecated/empty, found: {p}")

status_allow = {
    "NEW",
    "SCOPING",
    "COLLECTING",
    "SYNTHESIZING",
    "DRAFTING",
    "REVIEW_READY",
    "APPROVED",
    "PACKAGED",
    "SENT",
    "ARCHIVED",
    "NEEDS_INPUT",
    "BLOCKED",
}

for d in sorted(tasks.iterdir()):
    if d.name.startswith(".") or d.name == "_templates":
        continue

    if not d.is_dir():
        errors.append(f"tasks child must be directory: {d}")
        continue

    m = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})-([a-z0-9\-]+)$", d.name)
    if not m:
        errors.append(f"invalid task dir name: {d.name}")
        continue

    task_id = m.group(1)
    task_md = d / "task.md"
    if not task_md.exists():
        errors.append(f"missing task.md: {d}")
        continue

    content = task_md.read_text(encoding="utf-8", errors="ignore")

    fm_task = re.search(r"^task_id:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})\s*$", content, flags=re.M)
    if not fm_task:
        errors.append(f"missing frontmatter task_id: {task_md}")
        continue
    if fm_task.group(1) != task_id:
        errors.append(f"task_id mismatch dir vs frontmatter: {d.name} vs {fm_task.group(1)}")

    fm_status = re.search(r"^status:\s*([A-Z_]+)\s*$", content, flags=re.M)
    if not fm_status:
        errors.append(f"missing frontmatter status: {task_md}")
        continue
    if fm_status.group(1) not in status_allow:
        errors.append(f"invalid frontmatter status: {task_md} => {fm_status.group(1)}")

    body_status = re.search(r"##\s*状态[\s\S]*?-\s*status:\s*([A-Z_]+)", content)
    if not body_status:
        errors.append(f"missing body status sync block: {task_md}")
        continue
    if body_status.group(1) != fm_status.group(1):
        errors.append(
            f"status mismatch: {task_md} frontmatter={fm_status.group(1)} body={body_status.group(1)}"
        )

if errors:
    print("TASK_LINT_FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("TASK_LINT_PASS")
PY
