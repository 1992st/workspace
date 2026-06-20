from __future__ import annotations

from typing import Any, Dict


def assess_breadth(local_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    breadth = local_snapshot.get("market_breadth") or {}
    advancers = _num(breadth.get("advancers"))
    decliners = _num(breadth.get("decliners"))
    universe_size = _num(breadth.get("universe_size"))
    sampled = bool(breadth.get("sampled"))
    stale = bool(breadth.get("stale") or local_snapshot.get("stale"))
    risk_flags: list[str] = []

    if advancers is None or decliners is None:
        return {
            "quality": "invalid",
            "state": "unknown",
            "usable_for_direction": False,
            "usable_for_risk": False,
            "confidence_cap": 50,
            "direction_cap": "sideways",
            "risk_flags": ["breadth_invalid"],
            "reason": ["市场宽度缺少上涨/下跌家数字段"],
        }

    if stale:
        quality = "stale"
    elif sampled or (universe_size is not None and universe_size < 1000):
        quality = "sampled"
    elif universe_size is not None and universe_size < 4000:
        quality = "partial"
    else:
        quality = "full"

    total = advancers + decliners
    up_ratio = advancers / total if total > 0 else None
    state = "unknown"
    direction_cap = ""
    confidence_cap = 72
    reasons: list[str] = []

    if up_ratio is None:
        state = "unknown"
        confidence_cap = 50
        direction_cap = "sideways"
        risk_flags.append("breadth_invalid")
    elif up_ratio < 0.25 or decliners > 4000:
        state = "collapse"
        direction_cap = "sideways_down"
        confidence_cap = 45
        risk_flags.append("breadth_collapse")
        reasons.append("市场宽度坍塌，禁止强看多")
    elif up_ratio < 0.42 or decliners > 3500:
        state = "weak"
        direction_cap = "sideways"
        confidence_cap = 55
        risk_flags.append("breadth_weak")
        reasons.append("市场宽度偏弱，看多方向需降级")
    elif up_ratio >= 0.58:
        state = "strong"
    else:
        state = "neutral"

    if quality in {"sampled", "partial"}:
        confidence_cap = min(confidence_cap, 55 if quality == "sampled" else 62)
        risk_flags.append(f"breadth_{quality}")
        reasons.append("市场宽度不是完整全市场口径，不能单独支持强方向")
    if quality == "stale":
        confidence_cap = min(confidence_cap, 50)
        direction_cap = direction_cap or "sideways"
        risk_flags.append("breadth_stale")
        reasons.append("市场宽度过期，只能作为背景风险")

    return {
        "quality": quality,
        "state": state,
        "advancers": advancers,
        "decliners": decliners,
        "universe_size": universe_size,
        "up_ratio": round(up_ratio, 4) if up_ratio is not None else None,
        "usable_for_direction": quality in {"full", "partial"} and state != "unknown",
        "usable_for_risk": quality != "invalid" and state != "unknown",
        "confidence_cap": confidence_cap,
        "direction_cap": direction_cap,
        "risk_flags": risk_flags,
        "reason": reasons,
    }


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None
