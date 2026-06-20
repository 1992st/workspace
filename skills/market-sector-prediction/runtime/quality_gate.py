from __future__ import annotations

from typing import Any, Dict, List

from confidence_policy import confidence_cap


MARKET_REQUIRED = {
    "indices": "主要指数数据",
    "amount": "成交额/量能",
    "market_breadth": "市场宽度或情绪替代指标",
    "fund_flow": "至少一个资金维度",
    "probabilities": "概率分布",
    "bearish_evidence": "反方证据",
    "invalidation_conditions": "失效条件",
    "next_day_checks": "下一交易日验证点",
}

SECTOR_REQUIRED = {
    "sector_quote": "板块行情",
    "sector_taxonomy": "板块 taxonomy",
    "members_snapshot": "成分股快照",
    "fund_flow_or_relative_strength": "板块资金或相对强弱",
    "sector_stage": "板块阶段判断",
    "leaders": "龙头/跟风/掉队判断",
    "bearish_evidence": "反方证据",
    "fade_signals": "退潮信号",
    "next_day_checks": "下一交易日验证点",
}


class QualityGate:
    def evaluate(
        self,
        *,
        target_type: str,
        mode: str,
        local_snapshot: Dict[str, Any],
        evidence: Dict[str, Any],
        prediction: Dict[str, Any],
        reconciliation: Dict[str, Any],
        capabilities: Dict[str, Any],
        taxonomy: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        missing: List[str] = []
        stale: List[str] = []
        required = MARKET_REQUIRED if target_type == "market" else SECTOR_REQUIRED

        vibe_unavailable = not capabilities.get("vibe_available", False)
        local_insufficient = local_snapshot.get("status") not in {"ok", "degraded"} or (
            target_type == "market" and not local_snapshot.get("indices")
        )
        if vibe_unavailable and local_insufficient:
            return self._blocked(["Vibe MCP 不可用且本地数据不足"], missing, stale, 0)

        if reconciliation.get("status") == "blocked":
            return self._blocked(["关键事实冲突"], missing, stale, 0)

        if target_type == "market":
            if not local_snapshot.get("indices"):
                missing.append("indices")
            if not local_snapshot.get("has_amount"):
                missing.append("amount")
            if not local_snapshot.get("has_breadth"):
                missing.append("market_breadth")
            if not evidence.get("capital_flow"):
                missing.append("fund_flow")
        else:
            if not local_snapshot.get("has_sector_quote"):
                missing.append("sector_quote")
            if not taxonomy or taxonomy.get("status") != "ok":
                missing.append("sector_taxonomy")
            if not local_snapshot.get("has_members") or int(local_snapshot.get("member_count") or 0) <= 0:
                missing.append("members_snapshot")
            if not evidence.get("capital_flow") and not evidence.get("relative_strength"):
                missing.append("fund_flow_or_relative_strength")
            if not evidence.get("sector_stage"):
                missing.append("sector_stage")
            if not evidence.get("leaders"):
                missing.append("leaders")
            if not evidence.get("fade_signals"):
                missing.append("fade_signals")

        probabilities = prediction.get("probabilities") or {}
        if not all(key in probabilities for key in ("up", "sideways", "down")):
            missing.append("probabilities")
        if not evidence.get("bearish"):
            missing.append("bearish_evidence")
        if not prediction.get("invalidation_conditions"):
            missing.append("invalidation_conditions")
        if not evidence.get("next_day_checks"):
            missing.append("next_day_checks")

        blocked_keys = {"probabilities", "bearish_evidence", "invalidation_conditions"}
        if target_type == "sector":
            blocked_keys |= {"sector_taxonomy", "members_snapshot"}
        if any(key in missing for key in blocked_keys):
            return self._blocked([required.get(key, key) for key in missing if key in blocked_keys], missing, stale, 0)

        taxonomy_conflict = any(item.get("field") == "sector_members" for item in reconciliation.get("conflicts", []))
        has_backtest = bool(evidence.get("backtest_summary"))
        has_swarm = bool(evidence.get("vibe_opinions"))
        cap = confidence_cap(
            mode=mode,
            complete_data=not missing,
            has_backtest=has_backtest,
            has_swarm=has_swarm,
            missing_sections=missing,
            taxonomy_conflict=taxonomy_conflict,
            local_only=not capabilities.get("vibe_available", False),
        )
        status = "ok" if not missing and reconciliation.get("status") == "ok" else "degraded"
        return {
            "status": status,
            "score": max(0, min(100, 100 - len(missing) * 12 - len(stale) * 5)),
            "missing_sections": missing,
            "stale_sections": stale,
            "confidence_cap": cap,
            "blocking_reasons": [],
        }

    def _blocked(self, reasons: List[str], missing: List[str], stale: List[str], cap: int) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "score": 0,
            "missing_sections": missing,
            "stale_sections": stale,
            "confidence_cap": cap,
            "blocking_reasons": reasons,
        }
