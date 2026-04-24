from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


CN_TZ = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(CN_TZ).isoformat(timespec="seconds")


def normalize_symbol(symbol: str) -> str:
    raw = str(symbol or "").strip().upper()
    if not raw:
        raise ValueError("symbol is required")
    raw = raw.replace("SHSE.", "").replace("SZSE.", "")
    if "." in raw:
        raw = raw.split(".", 1)[0]
    raw = re.sub(r"^(SH|SZ|BJ)", "", raw)
    raw = re.sub(r"\D", "", raw)
    if not raw:
        raise ValueError(f"invalid symbol: {symbol}")
    return raw.zfill(6)


def infer_exchange(symbol: str) -> str:
    code = normalize_symbol(symbol)
    if code.startswith(("6", "9")):
        return "SH"
    if code.startswith(("4", "8")):
        return "BJ"
    return "SZ"


def pick_number(record: Dict[str, Any], keys: Iterable[str], default: float = 0.0) -> float:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            try:
                return float(str(record[key]).replace(",", ""))
            except (TypeError, ValueError):
                continue
    return float(default)


def pick_text(record: Dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def to_records(frame: Any) -> List[Dict[str, Any]]:
    if frame is None:
        return []
    if hasattr(frame, "to_dict"):
        try:
            return frame.to_dict(orient="records")
        except TypeError:
            pass
    if isinstance(frame, list):
        return frame
    return []


def compact_payload(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def cache_key(action: str, payload: Dict[str, Any]) -> str:
    sanitized = sanitize_cache_payload(payload)
    raw = f"{action}:{compact_payload(sanitized)}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return digest


def sanitize_cache_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    control_fields = {"action", "force_refresh", "timeout_ms"}
    sanitized = deepcopy(payload)
    for field in control_fields:
        sanitized.pop(field, None)
    return sanitized


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def normalize_timeframe(timeframe: Optional[str]) -> str:
    value = str(timeframe or "1d").lower()
    mapping = {
        "1d": "daily",
        "1w": "weekly",
        "1m": "monthly",
        "1mo": "monthly",
        "daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly",
    }
    return mapping.get(value, value)


def limit_items(items: List[Dict[str, Any]], limit: Optional[int]) -> List[Dict[str, Any]]:
    if not limit or limit <= 0:
        return items
    return items[:limit]
