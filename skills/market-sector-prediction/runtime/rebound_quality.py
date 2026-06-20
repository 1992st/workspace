from __future__ import annotations

from typing import Any, Dict


def classify_rebound(local_snapshot: Dict[str, Any], breadth_assessment: Dict[str, Any]) -> Dict[str, Any]:
    sh = _primary_index(local_snapshot)
    change = _num(sh.get("change_pct"))
    high = _num(sh.get("high"))
    close = _num(sh.get("price") or sh.get("close"))
    low = _num(sh.get("low"))
    amount = _num(sh.get("amount"))
    amount_avg = _num(sh.get("amount_avg_5d"))
    amount_ratio = amount / amount_avg if amount and amount_avg else None
    reasons: list[str] = []

    if change is None:
        return _result("none", ["缺少指数涨跌幅"], "", 72)

    if change > 0 and amount_ratio is not None and amount_ratio < 0.92:
        reasons.append("指数上涨但成交额低于5日均值")
        return _result("weak", reasons, "sideways", 50)

    if change > 0 and breadth_assessment.get("state") in {"weak", "collapse"}:
        reasons.append("指数反弹但市场宽度未修复")
        return _result("weak", reasons, "sideways", 50)

    if change > 0.8 and amount_ratio is not None and amount_ratio >= 1.08 and breadth_assessment.get("state") in {"strong", "neutral"}:
        reasons.append("放量上涨且宽度未明显拖累")
        return _result("confirmed", reasons, "", 72)

    if change > 0:
        reasons.append("指数上涨但缺少量能或宽度确认")
        return _result("technical", reasons, "sideways_up", 50)

    if high is not None and close is not None and low is not None and high > low:
        close_position = (close - low) / (high - low)
        if close_position < 0.35 and change <= 0:
            reasons.append("指数冲高回落，收盘靠近日内低位")
            return _result("failed", reasons, "sideways_down", 50)

    return _result("none", reasons, "", 72)


def _result(quality: str, reasons: list[str], direction_cap: str, confidence_cap: int) -> Dict[str, Any]:
    risk_flags = []
    if quality in {"weak", "failed", "technical"}:
        risk_flags.append(f"{quality}_rebound")
    return {
        "quality": quality,
        "reason": reasons,
        "direction_cap": direction_cap,
        "confidence_cap": confidence_cap,
        "risk_flags": risk_flags,
    }


def _primary_index(local_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    indices = local_snapshot.get("indices") or []
    return next((item for item in indices if str(item.get("code")) == "000001"), indices[0] if indices else {})


def _num(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None
