from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from breadth_risk_gate import assess_breadth
from external_signal_policy import evaluate_external_signal
from market_regime_engine import assess_market_regime
from rebound_quality import classify_rebound


class MarketContextBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root

    def build(self, local_snapshot: Dict[str, Any], horizon: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        breadth = assess_breadth(local_snapshot)
        rebound = classify_rebound(local_snapshot, breadth)
        external = evaluate_external_signal(payload, breadth)
        regime = assess_market_regime(local_snapshot, breadth, rebound)
        constraints = self._merge_constraints(breadth, rebound, external, regime)
        return {
            "breadth": breadth,
            "regime": regime,
            "rebound": rebound,
            "external": external,
            "constraints": constraints,
        }

    def _merge_constraints(
        self,
        breadth: Dict[str, Any],
        rebound: Dict[str, Any],
        external: Dict[str, Any],
        regime: Dict[str, Any],
    ) -> Dict[str, Any]:
        caps = [item.get("confidence_cap") for item in (breadth, rebound, regime) if item.get("confidence_cap")]
        confidence_cap = min(caps) if caps else 72
        direction_cap = self._most_restrictive(
            [breadth.get("direction_cap"), rebound.get("direction_cap"), regime.get("direction_cap")]
        )
        position_cap = regime.get("position_cap") or ""
        risk_flags: list[str] = []
        reasons: list[str] = []
        for item in (breadth, rebound, external, regime):
            risk_flags.extend(item.get("risk_flags", []))
            reasons.extend(item.get("reason", []) or item.get("why", []))
        return {
            "direction_cap": direction_cap,
            "confidence_cap": confidence_cap,
            "position_cap": position_cap,
            "risk_flags": self._dedupe(risk_flags),
            "forced_neutral_reasons": self._dedupe(reasons),
        }

    def _most_restrictive(self, caps: list[Any]) -> str:
        order = {"": 0, None: 0, "up": 0, "sideways_up": 1, "sideways": 2, "sideways_down": 3, "down": 4}
        selected = ""
        selected_value = 0
        for cap in caps:
            value = order.get(str(cap), 0)
            if value > selected_value:
                selected = str(cap)
                selected_value = value
        return selected

    def _dedupe(self, values: list[Any]) -> list[str]:
        result = []
        for value in values:
            if value in (None, ""):
                continue
            text = str(value)
            if text not in result:
                result.append(text)
        return result
