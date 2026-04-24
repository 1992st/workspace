from __future__ import annotations

from typing import Any, Dict, List, Optional

from .utils import now_iso


def build_success_response(
    data: Dict[str, Any],
    *,
    source: str,
    source_chain: List[str],
    fetched_at: Optional[str] = None,
    latency_ms: float = 0.0,
    status: str = "ok",
    issues: Optional[List[str]] = None,
    failed_sources: Optional[List[str]] = None,
) -> Dict[str, Any]:
    issues = issues or []
    completeness = _completeness(data)
    freshness = 1.0 if source != "cache" else 0.45
    consistency = 0.85 if not issues else 0.65
    score = round(((completeness * 0.45) + (freshness * 0.25) + (consistency * 0.30)) * 100, 2)
    return {
        "status": status,
        "data": data,
        "meta": {
            "source": source,
            "source_chain": source_chain,
            "fetched_at": fetched_at or now_iso(),
            "latency_ms": round(float(latency_ms), 2),
        },
        "quality": {
            "completeness": round(completeness, 4),
            "freshness": round(freshness, 4),
            "consistency": round(consistency, 4),
            "score": score,
            "issues": issues,
        },
        "error": {
            "code": None,
            "message": None,
            "retryable": False,
            "failed_sources": failed_sources or [],
        },
    }


def build_error_response(
    code: str,
    message: str,
    *,
    retryable: bool,
    failed_sources: Optional[List[str]] = None,
    source_chain: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "status": "error",
        "data": {},
        "meta": {
            "source": None,
            "source_chain": source_chain or [],
            "fetched_at": now_iso(),
            "latency_ms": 0.0,
        },
        "quality": {
            "completeness": 0.0,
            "freshness": 0.0,
            "consistency": 0.0,
            "score": 0.0,
            "issues": [message],
        },
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "failed_sources": failed_sources or [],
        },
    }


def _completeness(data: Dict[str, Any]) -> float:
    if not data:
        return 0.0
    non_empty = 0
    total = 0
    for value in data.values():
        total += 1
        if value not in (None, "", [], {}):
            non_empty += 1
    if total == 0:
        return 0.0
    return non_empty / total
