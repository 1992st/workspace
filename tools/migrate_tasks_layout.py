#!/usr/bin/env python3
import argparse
import datetime as dt
import pathlib
import re
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


STATUSES = [
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
]

ROOT = pathlib.Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
DEV_TOPICS = ROOT / "dev-topics"
REPORTS = ROOT / "reports"


@dataclass
class MoveItem:
    src: pathlib.Path
    dst: pathlib.Path


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "task"


def extract_task_id_from_text(content: str) -> Optional[str]:
    patterns = [
        r"^task_id\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})",
        r"\*\*task_id\*\*\s*[:：]\s*`?([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})`?",
        r"-\s*\*\*task_id\*\*\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})",
    ]
    for pat in patterns:
        m = re.search(pat, content, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1)
    return None


def detect_status(content: str) -> str:
    for st in STATUSES:
        if re.search(rf"\b{re.escape(st)}\b", content):
            return st
    return "DRAFTING"


def detect_title(content: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()
    m = re.search(r"title\s*:\s*\"?([^\n\"]+)\"?", content)
    if m:
        return m.group(1).strip()
    return fallback


def next_task_id(existing: set[str], date_str: str) -> str:
    max_idx = 0
    for tid in existing:
        if tid.startswith(date_str + "-"):
            try:
                max_idx = max(max_idx, int(tid.split("-")[-1]))
            except ValueError:
                pass
    new_id = f"{date_str}-{max_idx + 1:03d}"
    existing.add(new_id)
    return new_id


def collect_existing_task_ids() -> set[str]:
    ids: set[str] = set()
    for p in TASKS.iterdir():
        if p.name.startswith(".") or p.name == "_templates":
            continue
        m = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})", p.name)
        if m:
            ids.add(m.group(1))
        elif p.is_file() and p.suffix == ".md":
            content = p.read_text(encoding="utf-8", errors="ignore")
            tid = extract_task_id_from_text(content)
            if tid:
                ids.add(tid)
    return ids


def build_task_md(task_id: str, title: str, status: str, legacy_content: str, source_note: str) -> str:
    now = dt.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    safe_title = title.replace('"', "'")
    return (
        "---\n"
        f"task_id: {task_id}\n"
        f'title: "{safe_title}"\n'
        f"status: {status}\n"
        "owner: agent-radar-desk\n"
        f'created_at: "{now}"\n'
        f'updated_at: "{now}"\n'
        "---\n\n"
        "## 状态\n"
        f"- status: {status}\n\n"
        "## 迁移信息\n"
        f"- source: {source_note}\n\n"
        "## Legacy Notes\n\n"
        f"{legacy_content.strip()}\n"
    )


def ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def ensure_unique_dir(base_name: str) -> pathlib.Path:
    candidate = TASKS / base_name
    if not candidate.exists():
        return candidate
    n = 2
    while True:
        c = TASKS / f"{base_name}-{n}"
        if not c.exists():
            return c
        n += 1


def plan_migration() -> Tuple[List[MoveItem], List[Tuple[pathlib.Path, str]], List[str]]:
    moves: List[MoveItem] = []
    writes: List[Tuple[pathlib.Path, str]] = []
    logs: List[str] = []

    existing_ids = collect_existing_task_ids()
    today = dt.date.today().strftime("%Y-%m-%d")

    for p in sorted(TASKS.glob("*.md")):
        if p.name.startswith("."):
            continue
        stem = p.stem
        content = p.read_text(encoding="utf-8", errors="ignore")

        task_id = None
        m = re.match(r"^TASK-([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})$", stem)
        if m:
            task_id = m.group(1)
        m = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})$", stem)
        if m:
            task_id = m.group(1)
        if not task_id:
            task_id = extract_task_id_from_text(content)
        if not task_id:
            task_id = next_task_id(existing_ids, today)

        slug = "task"
        if "-" in stem and not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$", stem):
            possible = re.sub(r"^(TASK-)?[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}-?", "", stem)
            if possible:
                slug = slugify(possible)
        if slug == "task":
            slug = slugify(detect_title(content, fallback=stem))

        target_dir = ensure_unique_dir(f"{task_id}-{slug}")
        status = detect_status(content)
        title = detect_title(content, fallback=stem)
        writes.append((target_dir / "task.md", build_task_md(task_id, title, status, content, str(p))))
        moves.append(MoveItem(src=p, dst=target_dir / "legacy" / p.name))
        logs.append(f"top-file {p} -> {target_dir / 'task.md'}")

    for d in sorted(TASKS.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name == "_templates":
            continue

        canonical_name = re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}-", d.name)
        if canonical_name:
            task_md = d / "task.md"
            if task_md.exists():
                content = task_md.read_text(encoding="utf-8", errors="ignore")
                if "## 状态" not in content:
                    status = detect_status(content)
                    writes.append((task_md, content.rstrip() + f"\n\n## 状态\n- status: {status}\n"))
                continue

        m = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})(?:-(.*))?$", d.name)
        if m:
            task_id = m.group(1)
            suffix = m.group(2) or "task"
            slug = slugify(suffix)
        else:
            task_id = next_task_id(existing_ids, today)
            slug = slugify(d.name)

        target_dir = d if canonical_name else ensure_unique_dir(f"{task_id}-{slug}")
        if target_dir != d:
            moves.append(MoveItem(src=d, dst=target_dir))
            logs.append(f"dir {d} -> {target_dir}")

    # Build task.md for directories missing it (uses current names after planned rename)
    for item in list(moves):
        if not item.src.is_dir():
            continue
        d = item.dst
        if not d.exists():
            # planned destination; create from source snapshot
            src_dir = item.src
        else:
            src_dir = d

        task_md = d / "task.md"
        if task_md.exists():
            continue

        chosen = None
        for name in ["task.md", "STATUS.md", "inventory.md"]:
            c = src_dir / name
            if c.exists():
                chosen = c
                break

        if chosen:
            content = chosen.read_text(encoding="utf-8", errors="ignore")
            tid_match = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3})-", d.name)
            task_id = tid_match.group(1) if tid_match else next_task_id(existing_ids, today)
            title = detect_title(content, fallback=d.name)
            status = detect_status(content)
            writes.append((task_md, build_task_md(task_id, title, status, content, str(chosen))))
            if chosen.name != "task.md":
                moves.append(MoveItem(src=chosen, dst=d / "legacy" / chosen.name))

    if DEV_TOPICS.exists():
        migrated_dir = DEV_TOPICS / "_migrated"
        for td in sorted(DEV_TOPICS.iterdir()):
            if td.name.startswith(".") or not td.is_dir() or td.name == "_migrated":
                continue
            task_id = next_task_id(existing_ids, today)
            slug = slugify(td.name)
            target_dir = ensure_unique_dir(f"{task_id}-{slug}")
            drafts_dir = target_dir / "drafts"
            title = f"{td.name} 专题迁移"
            writes.append((target_dir / "task.md", build_task_md(task_id, title, "DRAFTING", "由 dev-topics 迁移", str(td))))
            for p in sorted(td.iterdir()):
                if p.name.startswith("."):
                    continue
                moves.append(MoveItem(src=p, dst=drafts_dir / p.name))
            moves.append(MoveItem(src=td, dst=migrated_dir / td.name))
            logs.append(f"dev-topic {td} -> {target_dir}/drafts")

    return moves, writes, logs


def apply_moves(moves: List[MoveItem]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for item in moves:
        src = item.src
        dst = item.dst
        if not src.exists():
            continue
        ensure_parent(dst)
        if src.resolve() == dst.resolve():
            continue
        shutil.move(str(src), str(dst))
        mapping[str(src.resolve())] = str(dst.resolve())
    return mapping


def apply_writes(writes: List[Tuple[pathlib.Path, str]]) -> None:
    for path, content in writes:
        ensure_parent(path)
        path.write_text(content, encoding="utf-8")


def replace_refs(mapping: Dict[str, str]) -> int:
    count = 0
    for f in ROOT.rglob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        orig = text
        for old, new in mapping.items():
            text = text.replace(old, new)
            if old.startswith(str(ROOT)) and new.startswith(str(ROOT)):
                old_rel = str(pathlib.Path(old).relative_to(ROOT))
                new_rel = str(pathlib.Path(new).relative_to(ROOT))
                text = text.replace(old_rel, new_rel)
        if text != orig:
            f.write_text(text, encoding="utf-8")
            count += 1
    return count


def write_report(logs: List[str], mapping: Dict[str, str], touched_md: int) -> pathlib.Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y-%m-%d")
    report = REPORTS / f"tasks-migration-{ts}.md"
    lines = [
        f"# Tasks Migration Report - {ts}",
        "",
        "## Summary",
        f"- moved_items: {len(mapping)}",
        f"- updated_markdown_refs: {touched_md}",
        "",
        "## Mappings",
    ]
    for old, new in sorted(mapping.items()):
        lines.append(f"- `{old}` -> `{new}`")
    lines.append("")
    lines.append("## Logs")
    for l in logs:
        lines.append(f"- {l}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate tasks layout to canonical directories")
    parser.add_argument("--apply", action="store_true", help="Apply migration")
    args = parser.parse_args()

    moves, writes, logs = plan_migration()
    print(f"planned_moves={len(moves)}")
    print(f"planned_writes={len(writes)}")

    if not args.apply:
        print("dry_run=true")
        for m in moves[:20]:
            print(f"MOVE {m.src} -> {m.dst}")
        for w, _ in writes[:20]:
            print(f"WRITE {w}")
        return

    mapping = apply_moves(moves)
    apply_writes(writes)
    touched = replace_refs(mapping)
    report = write_report(logs, mapping, touched)

    print("dry_run=false")
    print(f"applied_moves={len(mapping)}")
    print(f"updated_markdown_refs={touched}")
    print(f"report={report}")


if __name__ == "__main__":
    main()
