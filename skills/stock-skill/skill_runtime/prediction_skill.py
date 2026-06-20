from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict

from base import BaseSkill, SkillResult
from shared.contracts import build_error_response, build_success_response


RUNTIME_DIR = Path(__file__).resolve().parents[2] / "market-sector-prediction" / "runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from capability_probe import CapabilityProbe
from market_adapter import MarketPredictionAdapter
from review_bridge import ReviewBridge
from sector_adapter import SectorPredictionAdapter
from stock_context_bridge import StockContextBridge


class PredictionSkill(BaseSkill):
    name = "prediction"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[3]
        self.actions: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "prediction.health.check": self._health_check,
            "prediction.market.prepare": self._market_generate,
            "prediction.market.generate": self._market_generate,
            "prediction.sector.prepare": self._sector_generate,
            "prediction.sector.generate": self._sector_generate,
            "prediction.review.update": self._review_update,
            "prediction.latest.get": self._latest_get,
        }

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        action = payload.get("action")
        if action not in self.actions:
            response = build_error_response("unsupported_action", f"unsupported action: {action}", retryable=False)
            return SkillResult(status="error", data=response, errors=[f"unsupported action: {action}"])
        try:
            response = self.actions[action](payload)
            return SkillResult(status=response["status"], data=response)
        except Exception as exc:
            response = build_error_response("prediction_skill_failure", str(exc), retryable=True)
            return SkillResult(status="error", data=response, errors=[str(exc)])

    def _health_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = CapabilityProbe().probe()
        status = "ok" if data.get("vibe_available") else "degraded"
        return build_success_response(
            data,
            source="market-sector-prediction",
            source_chain=["prediction_skill", "capability_probe"],
            status=status,
            issues=data.get("missing_requirements", []),
        )

    def _market_generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = MarketPredictionAdapter(self.root).generate(payload)
        status = data.get("data_quality", {}).get("status", "blocked")
        return build_success_response(
            data,
            source="market-sector-prediction",
            source_chain=["prediction_skill", "market_adapter"],
            status="degraded" if status == "blocked" else status,
            issues=data.get("data_quality", {}).get("blocking_reasons", []),
        )

    def _sector_generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = SectorPredictionAdapter(self.root).generate(payload)
        status = data.get("data_quality", {}).get("status", "blocked")
        return build_success_response(
            data,
            source="market-sector-prediction",
            source_chain=["prediction_skill", "sector_adapter"],
            status="degraded" if status == "blocked" else status,
            issues=data.get("data_quality", {}).get("blocking_reasons", []),
        )

    def _review_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = ReviewBridge(self.root).build_review_plan()
        return build_success_response(data, source="market-sector-prediction", source_chain=["prediction_skill", "review_bridge"])

    def _latest_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = StockContextBridge(self.root).build_context(payload.get("sector"))
        return build_success_response(data, source="market-sector-prediction", source_chain=["prediction_skill", "stock_context_bridge"])
