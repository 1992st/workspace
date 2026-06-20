from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRED_RUNTIME = ROOT / "skills" / "market-sector-prediction" / "runtime"
STOCK_RUNTIME = ROOT / "skills" / "stock-skill" / "skill_runtime"
for path in (PRED_RUNTIME, STOCK_RUNTIME):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fact_reconciliation import reconcile_market
from breadth_risk_gate import assess_breadth
from evidence_mapper import default_market_evidence
from external_signal_policy import evaluate_external_signal
from local_signal_engine import market_local_signal
from local_snapshot import LocalSnapshotBuilder
from market_context_builder import MarketContextBuilder
from prediction_skill import PredictionSkill
from prediction_thresholds import classify_return, market_threshold, sector_threshold, support_resistance_hit
from quality_gate import QualityGate
from report_writer import ReportWriter
from stock_context_bridge import StockContextBridge
from tool_whitelist import ToolPolicy
from vibe_templates import MARKET_INDEX_CODES, build_run_dir, factor_csv_payload, market_data_payload, write_local_ohlcv


class PredictionRuntimeTests(unittest.TestCase):
    def test_tool_whitelist_blocks_forbidden_tools(self):
        policy = ToolPolicy.default()
        with self.assertRaises(ValueError):
            policy.validate("write_file")
        with self.assertRaises(ValueError):
            policy.validate("unknown_tool")
        policy.validate("get_market_data")

    def test_fact_reconciliation_blocks_trading_date_conflict(self):
        result = reconcile_market({"trading_date": "2026-05-25"}, {"trading_date": "2026-05-24"})
        self.assertEqual(result["status"], "blocked")

    def test_prediction_thresholds(self):
        self.assertEqual(market_threshold("short"), 0.8)
        self.assertEqual(sector_threshold("short", 1.2), 1.0)
        self.assertEqual(classify_return(1.2, 0.8), "up")
        self.assertTrue(support_resistance_hit(100.2, 100.0))

    def test_vibe_market_payload_matches_real_schema(self):
        payload = market_data_payload(MARKET_INDEX_CODES, "short")
        self.assertEqual(payload["codes"], MARKET_INDEX_CODES)
        self.assertIn("start_date", payload)
        self.assertIn("end_date", payload)
        self.assertEqual(payload["source"], "akshare")

    def test_vibe_factor_payload_matches_real_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = factor_csv_payload(Path(tmp), "sector", "证券", "short", ["601211.SH", "600030.SH", "000776.SZ"])
            self.assertTrue(Path(payload["factor_csv"]).exists())
            self.assertTrue(Path(payload["return_csv"]).exists())
            self.assertTrue(Path(payload["output_dir"]).exists())
            self.assertIn("n_groups", payload)

    def test_vibe_run_dir_contains_required_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = build_run_dir(Path(tmp), "market", "A股大盘", "short", MARKET_INDEX_CODES)
            self.assertTrue((run_dir / "config.json").exists())
            self.assertTrue((run_dir / "code" / "signal_engine.py").exists())

    def test_write_local_ohlcv_requires_enough_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = build_run_dir(Path(tmp), "market", "A股大盘", "short", MARKET_INDEX_CODES)
            status = write_local_ohlcv(
                run_dir,
                [{"code": "000001", "date": "2026-05-25", "price": 4152.5, "volume": 1000}],
            )
            self.assertFalse(status["written"])
            self.assertIn("000001.SH", status["insufficient"])

    def test_market_local_signal_generates_evidence(self):
        signal = market_local_signal(
            {
                "indices": [
                    {"code": "000001", "name": "上证指数", "change_pct": 1.1, "change_5d": 1.4, "low": 4100, "high": 4200},
                    {"code": "399001", "name": "深证成指", "change_pct": 1.5, "change_5d": 2.0, "low": 15000, "high": 15800},
                ],
                "market_breadth": {"advancers": 3200, "decliners": 1800},
                "capital_flow": {
                    "items": [{"name": "北向资金", "net": 12.3, "unit": "亿元", "direction": "inflow"}]
                },
            },
            "short",
        )
        self.assertIn("up", signal["probabilities"])
        self.assertGreater(signal["confidence"], 0)
        self.assertTrue(signal["bullish"])
        self.assertFalse(any("资金/成交额或外部研究不足" in item for item in signal["bearish"]))
        self.assertTrue(signal["support"])
        self.assertTrue(signal["capital_flow"])

    def test_breadth_gate_rejects_small_sample_as_full_market(self):
        result = assess_breadth(
            {"market_breadth": {"advancers": 80, "decliners": 20, "universe_size": 100, "sampled": True}}
        )
        self.assertIn(result["quality"], {"sampled", "invalid"})
        self.assertFalse(result["usable_for_direction"])
        self.assertLessEqual(result["confidence_cap"], 55)

    def test_breadth_collapse_caps_direction(self):
        result = assess_breadth(
            {"market_breadth": {"advancers": 500, "decliners": 4200, "universe_size": 4700}}
        )
        self.assertEqual(result["state"], "collapse")
        self.assertEqual(result["direction_cap"], "sideways_down")
        self.assertLessEqual(result["confidence_cap"], 45)

    def test_market_context_applies_direction_cap(self):
        signal = market_local_signal(
            {
                "indices": [
                    {"code": "000001", "name": "上证指数", "change_pct": 1.5, "change_5d": 1.8, "low": 3100, "high": 3200},
                    {"code": "399001", "name": "深证成指", "change_pct": 1.3, "change_5d": 1.6, "low": 9000, "high": 9400},
                ],
                "market_breadth": {"advancers": 3300, "decliners": 1500, "universe_size": 4800},
                "capital_flow": {"items": [{"name": "主力资金", "net": 10, "direction": "inflow", "unit": "亿元"}]},
            },
            "short",
            {"direction_cap": "sideways", "confidence_cap": 50, "position_cap": "hold", "risk_flags": ["breadth_weak"]},
        )
        self.assertEqual(signal["raw_direction"], "up")
        self.assertEqual(signal["direction"], "sideways")
        self.assertEqual(max(signal["probabilities"], key=signal["probabilities"].get), "sideways")
        self.assertLessEqual(signal["confidence"], 50)
        self.assertEqual(signal["position_environment"], "hold")

    def test_weak_rebound_does_not_emit_up(self):
        local = {
            "indices": [
                {
                    "code": "000001",
                    "name": "上证指数",
                    "change_pct": 1.2,
                    "change_5d": 1.5,
                    "amount": 90,
                    "amount_avg_5d": 120,
                    "low": 3100,
                    "high": 3200,
                    "price": 3180,
                }
            ],
            "market_breadth": {"advancers": 1800, "decliners": 3000, "universe_size": 4800},
            "capital_flow": {"items": [{"name": "主力资金", "net": 8, "direction": "inflow", "unit": "亿元"}]},
        }
        context = MarketContextBuilder(Path(tempfile.gettempdir())).build(local, "short", {})
        signal = market_local_signal(local, "short", context["constraints"])
        self.assertEqual(context["rebound"]["quality"], "weak")
        self.assertNotEqual(signal["direction"], "up")

    def test_external_positive_without_local_confirmation_is_open_only(self):
        result = evaluate_external_signal(
            {"external_signal": {"signal": "positive", "signal_type": "policy_signal"}},
            {"state": "weak", "quality": "full"},
        )
        self.assertEqual(result["local_confirmation"], "conflicted")
        self.assertEqual(result["allowed_effect"], "open_boost_only")

    def test_market_local_signal_uses_low_weight_proxy_flow(self):
        signal = market_local_signal(
            {
                "indices": [
                    {
                        "code": "000001",
                        "name": "上证指数",
                        "change_pct": 1.0,
                        "change_5d": 1.3,
                        "volume": 1000,
                    },
                    {
                        "code": "399001",
                        "name": "深证成指",
                        "change_pct": 0.8,
                        "change_5d": 1.1,
                        "volume": 900,
                    },
                ],
                "market_breadth": {"advancers": 3000, "decliners": 1900},
                "capital_flow": {"items": []},
            },
            "short",
        )
        self.assertTrue(signal["capital_flow"])
        self.assertTrue(signal["capital_flow"][0]["proxy"])
        self.assertLessEqual(signal["confidence"], 58)
        self.assertTrue(any("代理资金" in item for item in signal["neutral"]))

    def test_proxy_capital_flow_does_not_use_real_flow_confidence_ceiling(self):
        signal = market_local_signal(
            {
                "indices": [
                    {
                        "code": "000001",
                        "name": "上证指数",
                        "change_pct": 1.0,
                        "change_5d": 1.3,
                        "volume": 1000,
                    }
                ],
                "market_breadth": {"advancers": 3000, "decliners": 1900, "universe_size": 4900},
                "capital_flow": {
                    "items": [
                        {
                            "name": "全市场量价资金代理",
                            "net": 1.0,
                            "unit": "proxy_score",
                            "direction": "inflow",
                            "proxy": True,
                            "note": "代理指标，不等同真实资金",
                        }
                    ]
                },
            },
            "short",
        )
        self.assertLessEqual(signal["confidence"], 58)
        self.assertFalse(any("净流入" in item and "全市场量价资金代理" in item for item in signal["bullish"]))
        self.assertTrue(any("代理指标" in item for item in signal["bullish"] + signal["neutral"]))

    def test_real_capital_flow_keeps_full_weight(self):
        signal = market_local_signal(
            {
                "indices": [
                    {
                        "code": "000001",
                        "name": "上证指数",
                        "change_pct": 1.0,
                        "change_5d": 1.3,
                        "volume": 1000,
                    }
                ],
                "market_breadth": {"advancers": 3000, "decliners": 1900, "universe_size": 4900},
                "capital_flow": {
                    "items": [{"name": "北向资金", "net": 20.0, "unit": "亿元", "direction": "inflow", "proxy": False}]
                },
            },
            "short",
        )
        self.assertTrue(any("北向资金净流入" in item for item in signal["bullish"]))
        self.assertLessEqual(signal["confidence"], 62)

    def test_sampled_breadth_is_not_valid_breadth(self):
        builder = LocalSnapshotBuilder(Path(tempfile.gettempdir()))
        self.assertFalse(builder._has_valid_breadth({"advancers": 100, "decliners": 0, "universe_size": 100}))
        self.assertFalse(
            builder._has_valid_breadth({"advancers": 3000, "decliners": 1500, "universe_size": 4500, "sampled": True})
        )
        self.assertTrue(builder._has_valid_breadth({"advancers": 3000, "decliners": 1500, "universe_size": 4500}))

    def test_sampled_breadth_can_be_replaced_by_full_fallback(self):
        builder = LocalSnapshotBuilder(Path(tempfile.gettempdir()))
        current = {"advancers": 100, "decliners": 0, "universe_size": 100}
        candidate = {"advancers": 2600, "decliners": 2100, "universe_size": 4700}
        self.assertTrue(builder._is_better_breadth(candidate, current))

    def test_vibe_tool_limits_are_not_bearish_market_evidence(self):
        pattern_payload = {
            "results": {
                "000001.SH": {
                    "trend_slope": {"mean_slope": 1.8},
                    "support_resistance": {"support": [4130.0], "resistance": [4200.0]},
                    "patterns": {"broadening": [1], "double_tops": [], "double_bottoms": []},
                }
            }
        }
        evidence = default_market_evidence(
            {"market_breadth": {"error": "unavailable"}},
            {
                "market_data": {"status": "error", "error": "symbol unsupported", "payload": {}},
                "factor_analysis": {"status": "skipped", "error": "schema mismatch", "payload": {}},
                "backtest": {"status": "error", "error": "no index loader", "payload": {}},
                "pattern_recognition": {
                    "status": "ok",
                    "payload": {"structuredContent": {"result": json.dumps(pattern_payload)}},
                },
            },
        )
        joined_bearish = "\n".join(evidence["bearish"])
        self.assertNotIn("部分工具调用失败", joined_bearish)
        self.assertNotIn("前置数据不足", joined_bearish)
        self.assertTrue(any("趋势斜率为正" in item for item in evidence["bullish"]))
        self.assertTrue(any("get_market_data" in item for item in evidence["neutral"]))
        self.assertTrue(any("backtest" in item for item in evidence["neutral"]))

    def test_quality_gate_blocks_missing_probability(self):
        gate = QualityGate()
        result = gate.evaluate(
            target_type="market",
            mode="standard",
            local_snapshot={"indices": [{"code": "000001"}], "has_amount": True, "has_breadth": True},
            evidence={"capital_flow": [1], "bearish": ["risk"], "next_day_checks": ["check"]},
            prediction={"probabilities": {}, "invalidation_conditions": ["invalid"]},
            reconciliation={"status": "ok", "conflicts": []},
            capabilities={"vibe_available": True},
        )
        self.assertEqual(result["status"], "blocked")

    def test_quality_gate_blocks_empty_sector_members(self):
        gate = QualityGate()
        result = gate.evaluate(
            target_type="sector",
            mode="standard",
            local_snapshot={
                "has_sector_quote": True,
                "has_members": True,
                "member_count": 0,
            },
            evidence={
                "capital_flow": [1],
                "sector_stage": "start",
                "leaders": ["601211"],
                "fade_signals": ["跌破板块5日线"],
                "bearish": ["risk"],
                "next_day_checks": ["check"],
            },
            prediction={"probabilities": {"up": 1, "sideways": 98, "down": 1}, "invalidation_conditions": ["invalid"]},
            reconciliation={"status": "ok", "conflicts": []},
            capabilities={"vibe_available": True},
            taxonomy={"status": "ok"},
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("members_snapshot", result["missing_sections"])

    def test_prediction_skill_health_contract(self):
        skill = PredictionSkill(root=ROOT)
        result = skill.run({"action": "prediction.health.check"})
        self.assertIn(result.status, {"ok", "degraded"})
        data = result.data["data"]
        self.assertIn("tools_detected", data)
        self.assertIn("modes_available", data)

    def test_market_prediction_writes_blocked_report_without_vibe(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_command = os.environ.get("WIN_STOCK_VIBE_MCP_COMMAND")
            os.environ["WIN_STOCK_VIBE_MCP_COMMAND"] = "/tmp/win-stock-test-missing-vibe-mcp"
            try:
                root = Path(tmp)
                stock_client = root / "skills" / "stock-data" / "scripts"
                stock_client.mkdir(parents=True)
                (stock_client / "stock_client.py").write_text(
                    "import json\nprint(json.dumps({'success': False, 'error': 'no data'}))\n",
                    encoding="utf-8",
                )
                skill = PredictionSkill(root=root)
                result = skill.run({"action": "prediction.market.generate", "horizon": "short"})
                self.assertEqual(result.status, "degraded")
                payload = result.data["data"]
                self.assertEqual(payload["data_quality"]["status"], "blocked")
                self.assertTrue(Path(payload["artifacts"]["blocked_report_path"]).exists())
                self.assertTrue((root / "data" / "market" / "predictions" / "index.jsonl").exists())
            finally:
                if old_command is None:
                    os.environ.pop("WIN_STOCK_VIBE_MCP_COMMAND", None)
                else:
                    os.environ["WIN_STOCK_VIBE_MCP_COMMAND"] = old_command

    def test_report_contains_market_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "target_type": "market",
                "target": "A股大盘",
                "trading_date": "2026-05-25",
                "generated_at": "2026-05-25T16:00:00+08:00",
                "horizon": "short",
                "mode": "standard",
                "engine": {"vibe_run_id": ""},
                "data_quality": {"status": "degraded", "confidence_cap": 50},
                "market_context": {
                    "breadth": {"quality": "sampled", "state": "weak"},
                    "regime": {"primary_regime": "weak_rebound"},
                    "rebound": {"quality": "weak"},
                    "external": {"signal": "unknown", "allowed_effect": "none"},
                    "constraints": {
                        "direction_cap": "sideways",
                        "position_cap": "hold",
                        "risk_flags": ["breadth_weak", "weak_rebound"],
                    },
                },
                "prediction": {
                    "base_case": "震荡观察",
                    "probabilities": {"up": 25, "sideways": 55, "down": 20},
                    "confidence": 50,
                    "position_environment": "hold",
                    "invalidation_conditions": ["跌破支撑"],
                },
                "evidence": {"bullish": [], "bearish": ["反方证据"], "neutral": [], "capital_flow": [], "backtest_summary": [], "vibe_opinions": []},
                "review_plan": {"next_day_checks": []},
                "artifacts": {"json_path": "", "markdown_path": "", "vibe_raw_path": ""},
                "vibe_raw": {},
            }
            artifacts = ReportWriter(root).write_prediction(payload)
            self.assertIn("market_context", Path(artifacts["json_path"]).read_text(encoding="utf-8"))
            self.assertIn("市场状态与风险约束", Path(artifacts["markdown_path"]).read_text(encoding="utf-8"))
            index_text = (root / "data" / "market" / "predictions" / "index.jsonl").read_text(encoding="utf-8")
            self.assertIn('"regime": "weak_rebound"', index_text)
            self.assertIn('"risk_level": "medium"', index_text)

    def test_review_update_writes_review_and_marks_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "data" / "market" / "predictions" / "index.jsonl"
            prediction = root / "data" / "market" / "predictions" / "2026-05-25_market_short_prediction.json"
            prediction.parent.mkdir(parents=True)
            prediction.write_text(json.dumps({"data_quality": {"status": "degraded"}}, ensure_ascii=False), encoding="utf-8")
            index.write_text(
                json.dumps(
                    {
                        "date": "2026-05-25",
                        "target_type": "market",
                        "target": "A股大盘",
                        "horizon": "short",
                        "mode": "standard",
                        "status": "degraded",
                        "confidence": 30,
                        "json_path": str(prediction),
                        "markdown_path": "",
                        "vibe_run_id": "",
                        "review_status": "pending",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            skill = PredictionSkill(root=root)
            result = skill.run({"action": "prediction.review.update"})
            self.assertEqual(result.status, "ok")
            self.assertEqual(result.data["data"]["reviewed_count"], 1)
            self.assertIn('"review_status": "reviewed"', index.read_text(encoding="utf-8"))
            review_path = root / "data" / "market" / "reviews" / "2026-05-25_market_prediction_review.json"
            self.assertTrue(review_path.exists())
            review = json.loads(review_path.read_text(encoding="utf-8"))
            self.assertIn("regime_review", review)

    def test_stock_context_bridge_returns_new_market_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prediction = root / "data" / "market" / "predictions" / "latest.json"
            index = root / "data" / "market" / "predictions" / "index.jsonl"
            prediction.parent.mkdir(parents=True)
            payload = {
                "target_type": "market",
                "target": "A股大盘",
                "trading_date": "2026-06-01",
                "market_context": {"regime": {"primary_regime": "weak_rebound"}},
            }
            prediction.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            index.write_text(
                json.dumps(
                    {
                        "date": "2026-06-01",
                        "target_type": "market",
                        "target": "A股大盘",
                        "horizon": "short",
                        "status": "degraded",
                        "json_path": str(prediction),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            context = StockContextBridge(root).latest_market_prediction()
            self.assertEqual(context["market_context"]["regime"]["primary_regime"], "weak_rebound")


if __name__ == "__main__":
    unittest.main()
