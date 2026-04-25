#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TASKS_DIR="$ROOT_DIR/tasks"
MEMORY_DIR="$ROOT_DIR/memory"
STATE_FILE="$MEMORY_DIR/cron_guard_state.json"
OPENCLAW_CRON_RUNS_DIR="${OPENCLAW_CRON_RUNS_DIR:-$HOME/.openclaw/cron/runs}"

WINDOW_HOURS="${1:-36}"

python3 - "$TASKS_DIR" "$MEMORY_DIR" "$STATE_FILE" "$OPENCLAW_CRON_RUNS_DIR" "$WINDOW_HOURS" <<'PY'
import datetime as dt
import json
import pathlib
import re
import sys

tasks_dir = pathlib.Path(sys.argv[1])
memory_dir = pathlib.Path(sys.argv[2])
state_file = pathlib.Path(sys.argv[3])
runs_dir = pathlib.Path(sys.argv[4])
window_hours = int(sys.argv[5])

jobs = [
    "radar-daily-0800",
    "radar-daily-1900",
    "radar-weekly-friday-2000",
]

memory_dir.mkdir(parents=True, exist_ok=True)
tasks_dir.mkdir(parents=True, exist_ok=True)

if state_file.exists():
    state = json.loads(state_file.read_text())
else:
    state = {}

now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
window_ms = window_hours * 3600 * 1000

def next_task_id() -> str:
    today = dt.datetime.now().strftime("%Y-%m-%d")
    max_idx = 0
    for p in tasks_dir.glob(f"{today}-*.md"):
        m = re.match(rf"{today}-(\d{{3}})\.md$", p.name)
        if m:
            max_idx = max(max_idx, int(m.group(1)))
    return f"{today}-{max_idx + 1:03d}"

def read_last_finished_event(job_id: str):
    f = runs_dir / f"{job_id}.jsonl"
    if not f.exists():
        return None
    lines = f.read_text().splitlines()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("action") == "finished":
            return item
    return None

created = []
for job_id in jobs:
    ev = read_last_finished_event(job_id)
    if not ev:
        continue

    run_at = int(ev.get("runAtMs", 0))
    if not run_at or now_ms - run_at > window_ms:
        continue

    last_seen = int(state.get(job_id, 0))
    if run_at <= last_seen:
        continue

    status = str(ev.get("status", ""))
    delivered = ev.get("delivered")
    delivery_status = str(ev.get("deliveryStatus", ""))
    is_failed = status != "ok" or delivered is False or delivery_status == "not-delivered"

    state[job_id] = run_at
    if not is_failed:
        continue

    task_id = next_task_id()
    run_dt = dt.datetime.fromtimestamp(run_at / 1000, tz=dt.timezone.utc).astimezone()
    task_file = tasks_dir / f"{task_id}.md"
    run_file = runs_dir / f"{job_id}.jsonl"
    summary = ev.get("summary", "")
    summary_short = (summary[:800] + "...") if len(summary) > 800 else summary
    task_file.write_text(
        f"""# Task: {task_id}

## 标题
Cron 告警：{job_id} 未成功送达飞书

## 状态
NEEDS_INPUT

## 触发信息
- job_id: `{job_id}`
- run_at: `{run_dt.strftime("%Y-%m-%d %H:%M:%S %Z")}`
- status: `{status}`
- delivered: `{delivered}`
- delivery_status: `{delivery_status}`
- error: `{ev.get("error", "")}`

## 证据路径（绝对路径）
- cron 运行记录：`{run_file}`
- OpenClaw 任务配置：`/Users/zhangst/.openclaw/cron/jobs.json`
- 网关错误日志：`/Users/zhangst/.openclaw/logs/gateway.err.log`

## 摘要片段
{summary_short}

## 建议动作
1. 检查飞书配置、群目标与权限是否变更
2. 检查该任务最新 delivery 配置是否仍为 announce+feishu+chat
3. 手动补发本次摘要到飞书群，并标记该任务处理结果
""",
        encoding="utf-8",
    )
    created.append(str(task_file))

state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if created:
    print("created:")
    for p in created:
        print(p)
else:
    print("no-new-alerts")
PY
