from __future__ import annotations

from typing import Any, Dict


def evaluate_external_signal(payload: Dict[str, Any], breadth_assessment: Dict[str, Any]) -> Dict[str, Any]:
    external = payload.get("external_signal")
    if not isinstance(external, dict):
        return {
            "signal": "unknown",
            "signal_type": "unknown",
            "local_confirmation": "missing",
            "allowed_effect": "none",
            "risk_flags": [],
            "reason": ["未提供结构化外部信号"],
        }

    signal = str(external.get("signal") or "unknown")
    signal_type = str(external.get("signal_type") or "unknown")
    local_state = breadth_assessment.get("state")
    if signal == "positive" and local_state in {"weak", "collapse"}:
        return {
            "signal": signal,
            "signal_type": signal_type,
            "local_confirmation": "conflicted",
            "allowed_effect": "open_boost_only",
            "risk_flags": ["external_local_conflict"],
            "reason": ["外部利好与本地市场宽度冲突，只允许影响开盘修复预期"],
        }
    if signal == "positive" and local_state in {"strong", "neutral"}:
        return {
            "signal": signal,
            "signal_type": signal_type,
            "local_confirmation": "confirmed",
            "allowed_effect": "market_support" if signal_type in {"macro_risk", "policy_signal"} else "sector_only",
            "risk_flags": [],
            "reason": ["外部信号获得本地宽度确认"],
        }
    if signal == "negative":
        return {
            "signal": signal,
            "signal_type": signal_type,
            "local_confirmation": "weak" if local_state in {"strong", "neutral"} else "confirmed",
            "allowed_effect": "risk_warning",
            "risk_flags": ["external_risk"],
            "reason": ["外部负面信号作为风险提示"],
        }
    return {
        "signal": signal,
        "signal_type": signal_type,
        "local_confirmation": "missing",
        "allowed_effect": "none",
        "risk_flags": [],
        "reason": ["外部信号未形成可用方向约束"],
    }
