from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from prediction_thresholds import classify_return, market_threshold, support_resistance_hit


CN_TZ = timezone(timedelta(hours=8))


class ReviewBridge:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.stock_client = root / "skills" / "stock-data" / "scripts" / "stock_client.py"

    def pending_predictions(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for path in (
            self.root / "data" / "market" / "predictions" / "index.jsonl",
            self.root / "data" / "sectors" / "predictions" / "index.jsonl",
        ):
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("review_status") == "pending":
                    records.append(record)
        return records

    def build_review_plan(self) -> Dict[str, Any]:
        reviewed = [self._write_review(record) for record in self.pending_predictions()]
        self._rewrite_indexes(reviewed)
        return {
            "reviewed": reviewed,
            "reviewed_count": len(reviewed),
            "note": "review_bridge writes structural review files and marks index records reviewed",
        }

    def _write_review(self, record: Dict[str, Any]) -> Dict[str, Any]:
        prediction_payload = {}
        json_path = record.get("json_path")
        if json_path and Path(json_path).exists():
            prediction_payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        target_type = record.get("target_type")
        date = record.get("date")
        direction_threshold = market_threshold(record.get("horizon", "short")) if target_type == "market" else None
        actual = self._actual_market_result(prediction_payload) if target_type == "market" else {}
        market_context = prediction_payload.get("market_context") or {}
        direction_hit = None
        support_hit = None
        resistance_hit = None
        error_type = "actual_data_pending"
        status = "blocked_gap_review" if record.get("status") == "blocked" else "actual_data_pending"
        if actual.get("status") == "ok":
            expected = self._expected_direction(prediction_payload)
            actual_direction = actual.get("direction")
            direction_hit = expected == actual_direction
            support_hit = actual.get("support_hit")
            resistance_hit = actual.get("resistance_hit")
            status = "reviewed_with_actuals"
            error_type = "none" if direction_hit else "wrong_market_expectation"
        review = {
            "schema_version": "1.0",
            "reviewed_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
            "date": date,
            "target_type": target_type,
            "target": record.get("target"),
            "horizon": record.get("horizon"),
            "status": status,
            "direction_threshold": direction_threshold,
            "actual": actual,
            "direction_hit": direction_hit,
            "probability_calibration_error": None,
            "support_resistance_hit": {"support": support_hit, "resistance": resistance_hit},
            "regime_review": self._regime_review(market_context, actual),
            "trigger_matched": None,
            "invalidation_matched": None,
            "error_type": error_type,
            "lesson": "已根据实际行情验证方向和关键价位。" if actual.get("status") == "ok" else "已纳入复盘队列；待接入实际行情验证方向和关键价位。",
            "prediction_artifact": json_path,
            "prediction_quality": prediction_payload.get("data_quality", {}),
        }
        if target_type == "market":
            review_path = self.root / "data" / "market" / "reviews" / f"{date}_market_prediction_review.json"
        else:
            target = str(record.get("target") or "unknown").replace("/", "_")
            review_path = self.root / "data" / "sectors" / "reviews" / target / f"{date}_prediction_review.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
        return {**record, "review_path": str(review_path)}

    def _rewrite_indexes(self, reviewed: List[Dict[str, Any]]) -> None:
        reviewed_keys = {
            (item.get("target_type"), item.get("target"), item.get("date"), item.get("horizon"), item.get("json_path"))
            for item in reviewed
        }
        for path in (
            self.root / "data" / "market" / "predictions" / "index.jsonl",
            self.root / "data" / "sectors" / "predictions" / "index.jsonl",
        ):
            if not path.exists():
                continue
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for record in records:
                key = (record.get("target_type"), record.get("target"), record.get("date"), record.get("horizon"), record.get("json_path"))
                if key in reviewed_keys:
                    record["review_status"] = "reviewed"
            path.write_text("\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n", encoding="utf-8")

    def _expected_direction(self, prediction_payload: Dict[str, Any]) -> str:
        probabilities = (prediction_payload.get("prediction") or {}).get("probabilities") or {}
        if not probabilities:
            return "sideways"
        return max(("up", "sideways", "down"), key=lambda key: probabilities.get(key, 0))

    def _actual_market_result(self, prediction_payload: Dict[str, Any]) -> Dict[str, Any]:
        local = prediction_payload.get("local_snapshot") or {}
        predicted_date = str(prediction_payload.get("trading_date") or "")
        indices = local.get("indices") or []
        predicted_sh = next((item for item in indices if str(item.get("code")) == "000001"), indices[0] if indices else {})
        predicted_close = self._num(predicted_sh.get("price"))
        if not predicted_close:
            return {"status": "missing", "error": "prediction close is missing"}
        current = self._run_stock_client(["market"])
        data = current.get("data") or {}
        actual_indices = data.get("indices") or []
        actual_sh = next((item for item in actual_indices if str(item.get("code")) == "000001"), actual_indices[0] if actual_indices else {})
        actual_date = str(actual_sh.get("date") or "")
        actual_close = self._num(actual_sh.get("price"))
        if not current.get("success") or not actual_close or not actual_date or actual_date <= predicted_date:
            return {"status": "pending", "error": "next trading day market data is unavailable", "actual_date": actual_date}
        change_pct = (actual_close - predicted_close) / predicted_close * 100
        threshold = market_threshold(prediction_payload.get("horizon", "short"))
        support_levels = (prediction_payload.get("prediction") or {}).get("support") or []
        resistance_levels = (prediction_payload.get("prediction") or {}).get("resistance") or []
        actual_low = self._num(actual_sh.get("low")) or actual_close
        actual_high = self._num(actual_sh.get("high")) or actual_close
        return {
            "status": "ok",
            "actual_date": actual_date,
            "predicted_close": round(predicted_close, 3),
            "actual_close": round(actual_close, 3),
            "change_pct": round(change_pct, 3),
            "direction": classify_return(change_pct, threshold),
            "support_hit": any(support_resistance_hit(actual_low, float(level)) for level in support_levels if self._num(level) is not None),
            "resistance_hit": any(support_resistance_hit(actual_high, float(level)) for level in resistance_levels if self._num(level) is not None),
        }

    def _regime_review(self, market_context: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, Any]:
        regime = market_context.get("regime") or {}
        constraints = market_context.get("constraints") or {}
        predicted_regime = regime.get("primary_regime", "")
        risk_flags = constraints.get("risk_flags") or regime.get("risk_flags") or []
        actual_pattern = actual.get("direction") if actual.get("status") == "ok" else ""
        regime_hit = None
        if predicted_regime and actual_pattern:
            if predicted_regime in {"risk_off", "failed_rebound"}:
                regime_hit = actual_pattern != "up"
            elif predicted_regime == "trend_confirmed":
                regime_hit = actual_pattern == "up"
            elif predicted_regime in {"weak_rebound", "range_bound", "technical_rebound", "low_visibility"}:
                regime_hit = actual_pattern == "sideways"
        return {
            "predicted_regime": predicted_regime,
            "risk_flags": risk_flags,
            "actual_pattern": actual_pattern,
            "regime_hit": regime_hit,
        }

    def _run_stock_client(self, args: list[str]) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                [sys.executable, str(self.stock_client), *args],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=90,
            )
            if not completed.stdout.strip():
                return {"success": False, "error": completed.stderr.strip() or "empty stock_client output"}
            return json.loads(completed.stdout)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _num(self, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return None
