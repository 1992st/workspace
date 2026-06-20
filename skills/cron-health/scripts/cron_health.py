#!/usr/bin/env python3
"""Read-only health check for Win_Stock OpenClaw cron jobs."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[3]
CRON_DIR = Path.home() / ".openclaw" / "cron"
JOBS_PATH_CANDIDATES = [CRON_DIR / "jobs.json", CRON_DIR / "jobs.json.migrated"]
STATE_PATH_CANDIDATES = [CRON_DIR / "jobs-state.json", CRON_DIR / "jobs-state.json.migrated"]
ENV_FILES = [
    ROOT / "config" / ".env",
    Path.home() / ".openclaw" / "workspace" / ".env",
    Path.home() / ".openclaw" / "workspace" / "skills" / "feishu" / ".env",
]

MORNING_JOB_ID = "5183d2f0-ab69-4462-b637-1cef41203e91"
AFTERMARKET_JOB_ID = "win-stock-aftermarket-analysis"
NANYA_JOB_ID = "700ac814-3a8f-40e8-af6b-4ed260730649"
RUNS_DIR = CRON_DIR / "runs"
LOCAL_GATEWAY_URL = os.getenv("WIN_STOCK_OPENCLAW_GATEWAY_URL") or "ws://192.168.150.103:18789"
LOCALHOST_GATEWAY_URL = "ws://127.0.0.1:18789"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def existing_path(candidates: List[Path]) -> Path:
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def run_log_path(job_id: str) -> Path:
    return existing_path([
        RUNS_DIR / f"{job_id}.jsonl",
        RUNS_DIR / f"{job_id}.jsonl.migrated",
    ])


def load_jsonl_tail(path: Path, limit: int = 20) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    rows = []
    for line in lines:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def latest_file(directory: Path, patterns: Iterable[str]) -> Optional[Path]:
    matches = []
    for pattern in patterns:
        matches.extend(directory.glob(pattern))
    return max(matches, key=lambda item: item.stat().st_mtime) if matches else None


def job_by_id(jobs: Dict[str, Any], job_id: str) -> Optional[Dict[str, Any]]:
    for job in jobs.get("jobs", []):
        if job.get("id") == job_id:
            return job
    return None


def delivery_status(report_path: Optional[Path]) -> Dict[str, Any]:
    if not report_path:
        return {"exists": False, "path": None}
    path = report_path.with_suffix(".delivery.json")
    if not path.exists():
        return {"exists": False, "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"exists": True, "path": str(path), "success": False, "error": str(exc)}
    return {
        "exists": True,
        "path": str(path),
        "success": bool(data.get("success")),
        "chunk_count": data.get("chunk_count"),
        "delivery_mode": data.get("delivery_mode"),
        "file_key_present": bool(data.get("file_key")),
        "error": data.get("error"),
    }


def session_artifacts(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"session_id": None, "exists": False}
    session_dir = Path.home() / ".openclaw" / "agents" / "win_stock" / "sessions"
    trajectory_path = session_dir / f"{session_id}.trajectory.jsonl"
    result = {
        "session_id": session_id,
        "trajectory_path": str(trajectory_path),
        "exists": trajectory_path.exists(),
        "aborted": None,
        "final_status": None,
        "prompt_error": None,
        "prompt_error_source": None,
        "item_started_count": None,
        "item_completed_count": None,
        "tool_count": None,
        "last_tool_error": None,
        "last_tool_name": None,
        "last_tool_meta": None,
        "last_tool_mutating_action": None,
        "did_send_via_messaging_tool": None,
    }
    if not trajectory_path.exists():
        return result
    for row in load_jsonl_tail(trajectory_path, limit=10):
        if row.get("type") == "trace.artifacts":
            data = row.get("data", {})
            result["aborted"] = data.get("aborted")
            result["final_status"] = data.get("finalStatus")
            result["prompt_error"] = data.get("promptError")
            result["prompt_error_source"] = data.get("promptErrorSource")
            lifecycle = data.get("itemLifecycle") or {}
            result["item_started_count"] = lifecycle.get("startedCount")
            result["item_completed_count"] = lifecycle.get("completedCount")
            result["tool_count"] = len(data.get("toolMetas") or [])
            last_tool_error = data.get("lastToolError") or {}
            if last_tool_error:
                result["last_tool_error"] = last_tool_error.get("error")
                result["last_tool_name"] = last_tool_error.get("toolName")
                result["last_tool_meta"] = last_tool_error.get("meta")
                result["last_tool_mutating_action"] = last_tool_error.get("mutatingAction")
            result["did_send_via_messaging_tool"] = data.get("didSendViaMessagingTool")
    return result


def latest_aftermarket_run() -> Dict[str, Any]:
    rows = load_jsonl_tail(run_log_path(AFTERMARKET_JOB_ID), limit=1)
    if not rows:
        return {"exists": False}
    row = rows[-1]
    return describe_run(row)


def runs_for_job(job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    return [describe_run(row) for row in load_jsonl_tail(run_log_path(job_id), limit=limit)]


def describe_run(row: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = session_artifacts(row.get("sessionId"))
    effective = run_effective_status(row, artifacts)
    return {
        "exists": True,
        "run_id": row.get("runId"),
        "manual": str(row.get("runId") or "").startswith("manual:"),
        "status": row.get("status"),
        "delivery_status": row.get("deliveryStatus"),
        "delivered": row.get("delivered"),
        "error": row.get("error"),
        "session_id": row.get("sessionId"),
        "run_at_ms": row.get("runAtMs"),
        "duration_ms": row.get("durationMs"),
        "session_artifacts": artifacts,
        "effective_status": effective,
    }


def run_effective_status(row: Dict[str, Any], artifacts: Dict[str, Any]) -> Dict[str, Any]:
    if artifacts.get("aborted") or artifacts.get("final_status") == "error":
        if artifacts.get("prompt_error") and artifacts.get("item_started_count") == 0:
            return {
                "ok": False,
                "reason": "prompt_aborted_before_tools",
                "prompt_error": artifacts.get("prompt_error"),
                "prompt_error_source": artifacts.get("prompt_error_source"),
            }
        if artifacts.get("last_tool_error"):
            return {
                "ok": False,
                "reason": "tool_error_then_prompt_abort",
                "prompt_error": artifacts.get("prompt_error"),
                "last_tool_error": artifacts.get("last_tool_error"),
                "last_tool_meta": artifacts.get("last_tool_meta"),
            }
        return {
            "ok": False,
            "reason": "session_trajectory_error",
            "prompt_error": artifacts.get("prompt_error"),
        }
    if row.get("status") != "ok":
        return {"ok": False, "reason": "cron_run_not_ok", "error": row.get("error")}
    return {"ok": True, "reason": "ok"}


def expected_daily_report_for_today() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return ROOT / "reviews" / "daily" / f"{today}_复盘报告.md"


def expected_morning_report_for_today() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return ROOT / "reviews" / "morning" / f"{today}_早盘分析.md"


def today_scheduled_runs(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    today = datetime.now().strftime("%Y-%m-%d")
    result = []
    for run in runs:
        if run.get("manual"):
            continue
        run_at_ms = run.get("run_at_ms")
        if not run_at_ms:
            continue
        run_date = datetime.fromtimestamp(run_at_ms / 1000).strftime("%Y-%m-%d")
        if run_date == today:
            result.append(run)
    return result


def runs_for_date(runs: List[Dict[str, Any]], date_text: str) -> List[Dict[str, Any]]:
    result = []
    for run in runs:
        run_at_ms = run.get("run_at_ms")
        if not run_at_ms:
            continue
        run_date = datetime.fromtimestamp(run_at_ms / 1000).strftime("%Y-%m-%d")
        if run_date == date_text:
            result.append(run)
    return result


def read_env_keys() -> Dict[str, str]:
    values: Dict[str, str] = {}
    for path in ENV_FILES:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return values


def describe_job(jobs: Dict[str, Any], states: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    job = job_by_id(jobs, job_id)
    state = states.get("jobs", {}).get(job_id, {}).get("state", {})
    return {
        "id": job_id,
        "exists": job is not None,
        "name": job.get("name") if job else None,
        "enabled": job.get("enabled") if job else None,
        "schedule": job.get("schedule") if job else None,
        "delivery": job.get("delivery") if job else None,
        "last_status": state.get("lastRunStatus") or state.get("lastStatus"),
        "last_error": state.get("lastError"),
        "last_delivery_status": state.get("lastDeliveryStatus"),
        "consecutive_errors": state.get("consecutiveErrors"),
        "next_run_at_ms": state.get("nextRunAtMs"),
    }


def cron_minute(schedule: Optional[Dict[str, Any]]) -> Optional[str]:
    expr = (schedule or {}).get("expr")
    if not expr:
        return None
    parts = str(expr).split()
    if len(parts) < 2:
        return None
    return f"{parts[1].zfill(2)}:{parts[0].zfill(2)}"


def schedule_conflicts(jobs: Dict[str, Any], target_job_id: str) -> List[Dict[str, Any]]:
    target = job_by_id(jobs, target_job_id)
    target_minute = cron_minute(target.get("schedule") if target else None)
    if not target_minute:
        return []
    conflicts = []
    for job in jobs.get("jobs", []):
        if job.get("id") == target_job_id or not job.get("enabled"):
            continue
        minute = cron_minute(job.get("schedule"))
        if minute == target_minute:
            conflicts.append(
                {
                    "id": job.get("id"),
                    "name": job.get("name"),
                    "agent_id": job.get("agentId"),
                    "schedule": job.get("schedule"),
                }
            )
    return conflicts


def local_agent_dirs() -> List[str]:
    agents_dir = Path.home() / ".openclaw" / "agents"
    if not agents_dir.exists():
        return []
    return sorted(path.name for path in agents_dir.iterdir() if path.is_dir())


def gateway_diagnostics() -> Dict[str, Any]:
    return {
        "recommended_url": LOCAL_GATEWAY_URL,
        "localhost_url": LOCALHOST_GATEWAY_URL,
        "localhost_warning": (
            "Do not use 127.0.0.1:18789 for win_stock diagnostics; it may point to a different OpenClaw gateway."
        ),
        "local_agent_dirs": local_agent_dirs(),
        "expected_agent": "win_stock",
        "expected_agent_present": "win_stock" in local_agent_dirs(),
    }


def report_effective_status(report_path: Path) -> Dict[str, Any]:
    delivery = delivery_status(report_path)
    if not report_path.exists():
        return {"ok": False, "reason": "report_missing", "delivery": delivery}
    if not delivery.get("exists"):
        return {"ok": False, "reason": "delivery_json_missing", "delivery": delivery}
    if not delivery.get("success"):
        return {"ok": False, "reason": "delivery_failed", "delivery": delivery}
    return {"ok": True, "reason": "ok", "delivery": delivery}


def latest_successful_run(runs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for run in reversed(runs):
        if run.get("effective_status", {}).get("ok"):
            return run
    return None


def manual_success_after_failed_scheduled(runs: List[Dict[str, Any]], expected_report: Path) -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    today_runs = runs_for_date(runs, today)
    scheduled_failures = [
        run for run in today_runs
        if not run.get("manual") and not run.get("effective_status", {}).get("ok")
    ]
    manual_successes = [
        run for run in today_runs
        if run.get("manual") and run.get("effective_status", {}).get("ok")
    ]
    report_status = report_effective_status(expected_report)
    return {
        "ok": bool(scheduled_failures and manual_successes and report_status.get("ok")),
        "reason": manual_success_reason(scheduled_failures, manual_successes, report_status),
        "scheduled_failure_count": len(scheduled_failures),
        "manual_success_count": len(manual_successes),
        "latest_manual_success": manual_successes[-1] if manual_successes else None,
    }


def manual_success_reason(
    scheduled_failures: List[Dict[str, Any]],
    manual_successes: List[Dict[str, Any]],
    report_status: Dict[str, Any],
) -> str:
    if not scheduled_failures:
        return "no_scheduled_failure_today"
    if not manual_successes:
        return "no_manual_success_after_scheduled_failure"
    if not report_status.get("ok"):
        return str(report_status.get("reason") or "report_or_delivery_not_successful")
    return "manual_rerun_success"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Win_Stock cron and Feishu report delivery health.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args()

    jobs_path = existing_path(JOBS_PATH_CANDIDATES)
    state_path = existing_path(STATE_PATH_CANDIDATES)
    jobs = load_json(jobs_path)
    states = load_json(state_path)
    latest_morning = latest_file(ROOT / "reviews" / "morning", ["*_早盘分析.md"])
    latest_daily = latest_file(ROOT / "reviews" / "daily", ["*_复盘报告.md", "*_盘后综合分析报告.md"])
    env_values = read_env_keys()
    expected_daily = expected_daily_report_for_today()
    expected_morning = expected_morning_report_for_today()
    latest_aftermarket = latest_aftermarket_run()
    morning_runs = runs_for_job(MORNING_JOB_ID, limit=10)
    aftermarket_runs = runs_for_job(AFTERMARKET_JOB_ID, limit=10)
    today_morning_scheduled_runs = today_scheduled_runs(morning_runs)
    latest_today_morning_scheduled = today_morning_scheduled_runs[-1] if today_morning_scheduled_runs else None
    latest_morning_success = latest_successful_run(morning_runs)
    expected_morning_report_status = report_effective_status(expected_morning)
    expected_daily_report_status = report_effective_status(expected_daily)

    result = {
        "cron_store": {
            "jobs_path": str(jobs_path),
            "jobs_exists": jobs_path.exists(),
            "jobs_path_candidates": [str(path) for path in JOBS_PATH_CANDIDATES],
            "state_path": str(state_path),
            "state_exists": state_path.exists(),
            "state_path_candidates": [str(path) for path in STATE_PATH_CANDIDATES],
            "morning_run_log_path": str(run_log_path(MORNING_JOB_ID)),
            "aftermarket_run_log_path": str(run_log_path(AFTERMARKET_JOB_ID)),
        },
        "gateway": gateway_diagnostics(),
        "jobs": {
            "morning": describe_job(jobs, states, MORNING_JOB_ID),
            "aftermarket": describe_job(jobs, states, AFTERMARKET_JOB_ID),
            "nanya": describe_job(jobs, states, NANYA_JOB_ID),
        },
        "schedule_conflicts": {
            "morning_same_minute": schedule_conflicts(jobs, MORNING_JOB_ID),
        },
        "reports": {
            "latest_morning": str(latest_morning) if latest_morning else None,
            "latest_morning_delivery": delivery_status(latest_morning),
            "latest_daily": str(latest_daily) if latest_daily else None,
            "latest_daily_delivery": delivery_status(latest_daily),
            "expected_today_morning": str(expected_morning),
            "expected_today_morning_exists": expected_morning.exists(),
            "expected_today_morning_delivery": expected_morning_report_status.get("delivery"),
            "expected_today_daily": str(expected_daily),
            "expected_today_daily_exists": expected_daily.exists(),
            "expected_today_daily_delivery": expected_daily_report_status.get("delivery"),
        },
        "recent_runs": {
            "morning": morning_runs,
            "aftermarket": aftermarket_runs,
        },
        "today_scheduled_morning_status": {
            "ok": bool(
                latest_today_morning_scheduled
                and latest_today_morning_scheduled.get("effective_status", {}).get("ok")
            ),
            "reason": effective_scheduled_morning_status_reason(latest_today_morning_scheduled),
            "run": latest_today_morning_scheduled,
        },
        "morning_effective_status": {
            "ok": bool(
                latest_morning_success
                and expected_morning_report_status.get("ok")
            ),
            "reason": effective_morning_status_reason(morning_runs, expected_morning_report_status),
            "latest_successful_run": latest_morning_success,
        },
        "manual_rerun_status": {
            "morning": manual_success_after_failed_scheduled(morning_runs, expected_morning),
        },
        "latest_aftermarket_run": latest_aftermarket,
        "aftermarket_effective_status": {
            "ok": bool(
                latest_aftermarket.get("effective_status", {}).get("ok")
                and expected_daily_report_status.get("ok")
            ),
            "reason": effective_status_reason(latest_aftermarket, expected_daily_report_status),
        },
        "feishu_env": {
            "has_app_id": bool(os.getenv("FEISHU_APP_ID") or env_values.get("FEISHU_APP_ID")),
            "has_app_secret": bool(os.getenv("FEISHU_APP_SECRET") or env_values.get("FEISHU_APP_SECRET")),
            "chat_id": os.getenv("FEISHU_CHAT_ID") or env_values.get("FEISHU_CHAT_ID") or "default",
            "env_files_checked": [str(path) for path in ENV_FILES],
        },
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def effective_status_reason(latest_aftermarket: Dict[str, Any], expected_daily: Path) -> str:
    if isinstance(expected_daily, dict):
        report_status = expected_daily
    else:
        report_status = report_effective_status(expected_daily)
    if not latest_aftermarket.get("exists"):
        return "no_aftermarket_run_log"
    if not latest_aftermarket.get("effective_status", {}).get("ok"):
        return str(latest_aftermarket.get("effective_status", {}).get("reason") or "latest_aftermarket_not_effectively_ok")
    if not report_status.get("ok"):
        return str(report_status.get("reason") or "expected_daily_report_or_delivery_missing")
    return "ok"


def effective_morning_status_reason(morning_runs: List[Dict[str, Any]], expected_morning: Any) -> str:
    if isinstance(expected_morning, dict):
        report_status = expected_morning
    else:
        report_status = report_effective_status(expected_morning)
    if not morning_runs:
        return "no_morning_run_log"
    if not latest_successful_run(morning_runs):
        latest = morning_runs[-1]
        return str(latest.get("effective_status", {}).get("reason") or "latest_morning_not_effectively_ok")
    if not report_status.get("ok"):
        return str(report_status.get("reason") or "expected_morning_report_or_delivery_missing")
    return "ok"


def effective_scheduled_morning_status_reason(latest_scheduled: Optional[Dict[str, Any]]) -> str:
    if not latest_scheduled:
        return "no_scheduled_morning_run_today"
    effective = latest_scheduled.get("effective_status", {})
    if not effective.get("ok"):
        return str(effective.get("reason") or "scheduled_morning_not_effectively_ok")
    return "ok"


if __name__ == "__main__":
    raise SystemExit(main())
