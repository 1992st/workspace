from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, DefaultDict, Dict, List


class HealthTracker:
    def __init__(self) -> None:
        self._stats: DefaultDict[str, Dict[str, Any]] = defaultdict(
            lambda: {"success": 0, "failure": 0, "latencies": [], "last_error": None}
        )

    def record_success(self, source: str, latency_ms: float) -> None:
        stats = self._stats[source]
        stats["success"] += 1
        stats["latencies"].append(float(latency_ms))
        stats["latencies"] = stats["latencies"][-200:]

    def record_failure(self, source: str, error: str | None = None) -> None:
        stats = self._stats[source]
        stats["failure"] += 1
        stats["last_error"] = error

    def snapshot(self) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        for source, stats in self._stats.items():
            total = stats["success"] + stats["failure"]
            report[source] = {
                "success": stats["success"],
                "failure": stats["failure"],
                "success_rate": round(stats["success"] / total, 4) if total else 1.0,
                "avg_latency_ms": round(mean(stats["latencies"]), 2) if stats["latencies"] else 0.0,
                "p95_latency_ms": _percentile(stats["latencies"], 95),
                "last_error": stats["last_error"],
            }
        return report


def _percentile(values: List[float], pct: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((pct / 100) * (len(ordered) - 1))))
    return round(ordered[index], 2)
