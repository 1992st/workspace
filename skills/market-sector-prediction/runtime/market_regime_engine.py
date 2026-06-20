from __future__ import annotations

from typing import Any, Dict


def assess_market_regime(
    local_snapshot: Dict[str, Any],
    breadth_assessment: Dict[str, Any],
    rebound: Dict[str, Any],
) -> Dict[str, Any]:
    risk_flags = []
    reasons = []
    confidence = 0.55
    primary = "range_bound"
    direction_cap = ""
    position_cap = ""
    confidence_cap = 72

    breadth_state = breadth_assessment.get("state")
    if breadth_assessment.get("quality") in {"invalid", "stale"}:
        primary = "low_visibility"
        direction_cap = "sideways"
        position_cap = "hold"
        confidence_cap = 50
        risk_flags.append("low_visibility")
        reasons.append("宽度数据不可用于高置信方向判断")
    elif breadth_state == "collapse":
        primary = "risk_off"
        direction_cap = "sideways_down"
        position_cap = "defense"
        confidence_cap = 45
        risk_flags.append("risk_off")
        reasons.append("市场宽度坍塌，先进入防御状态")
    elif rebound.get("quality") == "failed":
        primary = "failed_rebound"
        direction_cap = "sideways_down"
        position_cap = "defense"
        confidence_cap = 50
        risk_flags.append("failed_rebound")
        reasons.append("反弹失败或冲高回落")
    elif rebound.get("quality") == "weak":
        primary = "weak_rebound"
        direction_cap = "sideways"
        position_cap = "hold"
        confidence_cap = 50
        risk_flags.append("weak_rebound")
        reasons.append("反弹缺少宽度或量能确认")
    elif rebound.get("quality") == "technical":
        primary = "technical_rebound"
        direction_cap = "sideways_up"
        position_cap = "hold"
        confidence_cap = 50
        reasons.append("技术性修复，尚未确认趋势反转")
    elif _trend_confirmed(local_snapshot, breadth_assessment):
        primary = "trend_confirmed"
        confidence = 0.68
        reasons.append("主要指数动量与市场宽度同步改善")
    else:
        reasons.append("指数处于区间震荡或确认不足状态")

    risk_flags.extend(breadth_assessment.get("risk_flags", []))
    risk_flags.extend(rebound.get("risk_flags", []))
    return {
        "primary_regime": primary,
        "risk_flags": _dedupe(risk_flags),
        "confidence": confidence,
        "direction_cap": direction_cap,
        "position_cap": position_cap,
        "confidence_cap": confidence_cap,
        "why": reasons,
    }


def _trend_confirmed(local_snapshot: Dict[str, Any], breadth_assessment: Dict[str, Any]) -> bool:
    indices = local_snapshot.get("indices") or []
    positives = 0
    for item in indices[:3]:
        try:
            if float(item.get("change_5d") or 0) > 1.2:
                positives += 1
        except Exception:
            continue
    return positives >= 2 and breadth_assessment.get("state") == "strong"


def _dedupe(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
