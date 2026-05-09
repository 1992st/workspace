from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

RUNTIME_ROOT = Path(__file__).resolve().parents[1] / "skill_runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import providers.akshare_provider as akshare_provider_module
from analysis_engine import _build_rumor_check, _infer_relative_strength
from shared.cache import FileCache
from shared.utils import cache_key
from stock_skill import StockSkill
from providers.akshare_provider import AkshareProvider
from shared.failure_log import ToolFailureRecorder


ANALYSIS_PAYLOAD_FIXTURE = {
    "success": True,
    "data": {
        "symbol": "601211",
        "quote": {
            "symbol": "601211",
            "name": "国泰海通",
            "price": 10.0,
            "change": 0.2,
            "change_pct": 2.0,
            "open": 9.8,
            "high": 10.2,
            "low": 9.7,
            "pre_close": 9.8,
            "volume": 1000,
            "amount": 5000,
            "turnover_rate": 1.5,
            "volume_ratio": 1.2,
        },
        "market": {
            "indices": [
                {
                    "code": "000001",
                    "name": "上证指数",
                    "price": 3200,
                    "change_pct": 0.5,
                    "volume": 1000000,
                    "date": "2026-04-24",
                }
            ],
            "count": 1,
            "timestamp": "2026-04-24T10:00:00",
        },
        "sector": {"symbol": "601211", "industry": "证券"},
        "fund_flow": {
            "symbol": "601211",
            "date": "2026-04-24",
            "main_net_inflow": 100,
            "super_large_net": 50,
            "large_net": 20,
            "medium_net": 10,
            "small_net": 20,
        },
        "fundamental_valuation": {"symbol": "601211", "pe_ttm": 12, "pb": 1.1, "market_cap": 1000000000},
        "fundamental_trend": {
            "symbol": "601211",
            "periods": [
                {"report_date": "2025-09-30", "revenue_yoy": 8, "profit_yoy": 3, "roe": 8.5, "gross_margin": 19, "debt_ratio": 61},
                {"report_date": "2025-12-31", "revenue_yoy": 10, "profit_yoy": 5, "roe": 9, "gross_margin": 20, "debt_ratio": 60},
            ],
            "latest": {"report_date": "2025-12-31", "revenue_yoy": 10, "profit_yoy": 5, "roe": 9, "gross_margin": 20, "debt_ratio": 60},
            "count": 2,
        },
        "kline_daily": {
            "symbol": "601211",
            "period": "daily",
            "bars": [
                {"date": "2026-04-18", "open": 9.5, "high": 9.8, "low": 9.4, "close": 9.6, "volume": 100, "amount": 200},
                {"date": "2026-04-21", "open": 9.6, "high": 9.9, "low": 9.5, "close": 9.7, "volume": 120, "amount": 230},
                {"date": "2026-04-22", "open": 9.7, "high": 10.0, "low": 9.6, "close": 9.8, "volume": 140, "amount": 260},
                {"date": "2026-04-23", "open": 9.8, "high": 10.1, "low": 9.7, "close": 9.9, "volume": 160, "amount": 290},
                {"date": "2026-04-24", "open": 9.9, "high": 10.2, "low": 9.8, "close": 10.0, "volume": 180, "amount": 320},
            ],
            "count": 5,
        },
        "kline_weekly": {"symbol": "601211", "period": "weekly", "bars": [{"date": "2026-04-24", "close": 10.0}], "count": 1},
        "kline_monthly": {"symbol": "601211", "period": "monthly", "bars": [{"date": "2026-04-24", "close": 10.0}], "count": 1},
        "intraday": {"1m": {"symbol": "601211", "bars": [], "count": 0}, "5m": {"symbol": "601211", "bars": [], "count": 0}},
        "technical_indicators": {"daily": {"ma": {"ma5": 9.8}, "macd": {"dif": 0.1, "dea": 0.05, "hist": 0.1}, "rsi14": 58}},
        "quality": {
            "sections": {
                "quote": {"status": "ok", "source": "stock-data"},
                "market": {"status": "ok", "source": "stock-data"},
                "sector": {"status": "ok", "source": "stock-data"},
                "flow": {"status": "ok", "source": "stock-data"},
                "finance": {"status": "ok", "source": "stock-data"},
                "financial_trend": {"status": "ok", "source": "stock-data"},
                "kline_daily": {"status": "ok", "source": "stock-data"},
            },
            "missing_sections": [],
            "status": "ok",
        },
    },
}


class StubAkProvider:
    def quote_get(self, payload):
        return {
            "symbol": "601211",
            "name": "国泰海通",
            "price": 10.0,
            "change": 0.2,
            "change_pct": 2.0,
            "open": 9.8,
            "high": 10.2,
            "low": 9.7,
            "pre_close": 9.8,
            "volume": 1000,
            "amount": 5000,
            "timestamp": "2026-04-24T10:00:00",
        }

    def quotes_batch_get(self, payload):
        return {
            "items": [self.quote_get(payload)],
            "universe_size": 1,
            "timestamp": "2026-04-24T10:00:00",
            "advancers": 1,
            "decliners": 0,
            "flat_count": 0,
            "limit_up_count": 0,
            "limit_down_count": 0,
        }

    def kline_get(self, payload):
        return {
            "symbol": "601211",
            "period": "daily",
            "adjust": "none",
            "bars": [{"date": "2026-04-24", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100, "amount": 200}],
        }

    def index_get(self, payload):
        return {"index_code": "sh000001", "index_name": "上证指数", "price": 3200, "change_pct": 0.5, "timestamp": "2026-04-24T10:00:00"}

    def trading_calendar_get(self, payload):
        return {"date": "2026-04-24", "is_trading_day": True, "session": "open", "next_trading_day": "2026-04-27"}

    def market_snapshot_get(self, payload):
        data = self.quotes_batch_get(payload)
        data["market_change_pct"] = 1.1
        data["total_amount"] = 5000
        data["top_sector_list"] = [{"sector": "证券", "change_pct": 2.1}]
        return data

    def news_stock_get(self, payload):
        return {"symbol": "601211", "events": [{"title": "测试新闻", "source": "stub", "publish_time": "2026-04-24", "url": "https://example.com"}]}

    def news_market_get(self, payload):
        return {"events": [{"title": "市场新闻", "source": "stub", "publish_time": "2026-04-24"}]}

    def flow_main_get(self, payload):
        return {"symbol": "601211", "date": "2026-04-24", "main_net_inflow": 100, "super_large_net": 50, "large_net": 20, "medium_net": 10, "small_net": 20}

    def flow_order_size_get(self, payload):
        return {"date": "2026-04-24", "big_order_ratio": 0.7, "small_order_ratio": 0.2, "buy_sell_imbalance": 0.1}

    def etf_pcf_get(self, payload):
        return {
            "fund_code": "512000",
            "date": "2026-04-24",
            "pcf_items": [{"symbol": "601211", "name": "国泰海通", "quantity": 1000}],
            "cash_component": 0.0,
            "publish_time": "2026-04-24T08:30:00",
            "availability": "pre_open_available",
            "session_constraint": "盘前可获取PCF，不能代表盘中实时净申赎",
            "is_pcf_not_real_flow": True,
        }

    def margin_balance_get(self, payload):
        return {
            "symbol": "601211",
            "requested_date": "2026-04-24",
            "as_of_date": "2026-04-23",
            "is_latest_trading_day": False,
            "availability": "previous_trading_day_only",
            "session_constraint": "盘中默认上一交易日口径",
            "financing_balance": 1000.0,
            "financing_buy": 120.0,
            "financing_repay": 80.0,
            "securities_lending_balance": 50.0,
            "balance_change": 40.0,
        }

    def hsgt_top10_get(self, payload):
        return {
            "date": "2026-04-24",
            "channel": "shanghai_connect",
            "availability": "post_close_only",
            "items": [{"symbol": "601211", "name": "国泰海通", "net_buy": 300.0, "buy_amount": 500.0, "sell_amount": 200.0, "turnover": 700.0}],
        }

    def lhb_detail_get(self, payload):
        return {
            "symbol": "601211",
            "date": "2026-04-24",
            "availability": "conditional_only",
            "eligible": False,
            "reason": "未满足当日交易公开信息条件或无公开记录",
            "items": [],
            "institution_summary": {"buy_amount": 0.0, "sell_amount": 0.0},
            "northbound_seat_present": False,
        }

    def block_trade_get(self, payload):
        return {
            "symbol": "601211",
            "date": "2026-04-24",
            "availability": "post_close_only",
            "items": [{"price": 10.0, "volume": 1000, "amount": 10000.0, "discount_rate": -2.0, "buyer": "机构A", "seller": "机构B"}],
            "total_amount": 10000.0,
            "avg_discount_rate": -2.0,
            "buyer_seller_pairs": [{"buyer": "机构A", "seller": "机构B"}],
        }

    def fundamental_valuation_get(self, payload):
        return {"symbol": "601211", "pe_ttm": 12, "pb": 1.1, "market_cap": 1000000000}

    def fundamental_metrics_get(self, payload):
        return {"report_date": "2025-12-31", "revenue_yoy": 10, "profit_yoy": 5, "roe": 9, "gross_margin": 20, "debt_ratio": 60}

    def sector_map_get(self, payload):
        return {"symbol": "601211", "sectors": ["证券"], "primary_sector": "证券", "concept_tags": []}

    def sector_heat_get(self, payload):
        return {"sector": "证券", "change_pct": 1.5, "leader_symbols": ["601211"], "sector_fund_flow": 1000, "continuity_score": 0.6}


class StubHttpProvider:
    def quote_get(self, payload):
        raise RuntimeError("http not used")

    def quotes_batch_get(self, payload):
        raise RuntimeError("http not used")

    def news_market_get(self, payload):
        return {"events": [{"title": "http 市场新闻", "source": "http", "publish_time": "2026-04-24"}]}


class FailingAkProvider(StubAkProvider):
    def quote_get(self, payload):
        raise RuntimeError("ak failed")


class WorkingHttpProvider(StubHttpProvider):
    def quote_get(self, payload):
        return {
            "symbol": "601211",
            "name": "国泰海通",
            "price": 11.0,
            "change": 0.1,
            "change_pct": 0.9,
            "open": 10.8,
            "high": 11.1,
            "low": 10.6,
            "pre_close": 10.9,
            "volume": 2000,
            "amount": 6000,
            "timestamp": "2026-04-24T10:01:00",
        }

    def quotes_batch_get(self, payload):
        return {
            "items": [self.quote_get(payload)],
            "universe_size": 1,
            "timestamp": "2026-04-24T10:01:00",
            "advancers": 1,
            "decliners": 0,
            "flat_count": 0,
            "limit_up_count": 0,
            "limit_down_count": 0,
        }


class StockSkillTests(unittest.TestCase):
    def make_skill(self, ak_provider=None, http_provider=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        cache = FileCache(Path(temp_dir.name))
        failure_recorder = ToolFailureRecorder(Path(temp_dir.name) / "tool_failures")
        return StockSkill(
            cache=cache,
            failure_recorder=failure_recorder,
            ak_provider=ak_provider or StubAkProvider(),
            http_provider=http_provider or StubHttpProvider(),
        )

    def test_quote_contract(self):
        skill = self.make_skill()
        result = skill.run({"action": "quote.get", "symbol": "601211"})
        self.assertEqual(result.status, "ok")
        body = result.data
        self.assertEqual(body["status"], "ok")
        self.assertIn("meta", body)
        self.assertIn("quality", body)
        self.assertEqual(body["data"]["symbol"], "601211")

    def test_fallback_to_http(self):
        skill = self.make_skill(ak_provider=FailingAkProvider(), http_provider=WorkingHttpProvider())
        result = skill.run({"action": "quote.get", "symbol": "601211", "force_refresh": True})
        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.data["meta"]["source"], "http")
        self.assertEqual(result.data["error"]["failed_sources"], ["akshare"])

    def test_cache_fallback_after_live_failure(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        cache = FileCache(Path(temp_dir.name))
        healthy = StockSkill(cache=cache, ak_provider=StubAkProvider(), http_provider=StubHttpProvider())
        healthy.run({"action": "quote.get", "symbol": "601211", "force_refresh": True})

        failing = StockSkill(cache=cache, ak_provider=FailingAkProvider(), http_provider=StubHttpProvider())
        result = failing.run({"action": "quote.get", "symbol": "601211", "force_refresh": True})
        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.data["meta"]["source"], "cache")
        self.assertIn("akshare", result.data["error"]["failed_sources"])

    def test_health_report(self):
        skill = self.make_skill()
        skill.run({"action": "quote.get", "symbol": "601211", "force_refresh": True})
        result = skill.run({"action": "health.report.get"})
        self.assertEqual(result.status, "ok")
        self.assertIn("sources", result.data["data"])

    def test_runtime_contract_json_serializable(self):
        skill = self.make_skill()
        result = skill.run({"action": "fundamental.metrics.get", "symbol": "601211"})
        json.dumps(result.to_dict(), ensure_ascii=False)

    def test_extended_data_actions_return_expected_contracts(self):
        skill = self.make_skill()
        etf_result = skill.run({"action": "etf.pcf.get", "fund_code": "512000"})
        margin_result = skill.run({"action": "margin.balance.get", "symbol": "601211", "date": "2026-04-24"})
        hsgt_result = skill.run({"action": "hsgt.top10.get", "date": "2026-04-24"})
        lhb_result = skill.run({"action": "lhb.detail.get", "symbol": "601211", "date": "2026-04-24"})
        block_result = skill.run({"action": "block_trade.get", "symbol": "601211", "date": "2026-04-24"})
        self.assertEqual(etf_result.status, "ok")
        self.assertEqual(etf_result.data["data"]["availability"], "pre_open_available")
        self.assertEqual(margin_result.status, "ok")
        self.assertEqual(margin_result.data["data"]["availability"], "previous_trading_day_only")
        self.assertEqual(hsgt_result.status, "ok")
        self.assertEqual(hsgt_result.data["data"]["availability"], "post_close_only")
        self.assertEqual(lhb_result.status, "ok")
        self.assertFalse(lhb_result.data["data"]["eligible"])
        self.assertEqual(block_result.status, "ok")
        self.assertEqual(block_result.data["data"]["avg_discount_rate"], -2.0)

    def test_cache_key_ignores_control_flags(self):
        base = {"action": "quote.get", "symbol": "601211", "market": "CN-A"}
        forced = {"action": "quote.get", "symbol": "601211", "market": "CN-A", "force_refresh": True, "timeout_ms": 5000}
        self.assertEqual(cache_key("quote.get", base), cache_key("quote.get", forced))

    def test_analysis_stock_prepare_returns_prompt_bundle(self):
        skill = self.make_skill()
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        result = skill.run({"action": "analysis.stock.prepare", "symbol": "601211"})
        self.assertEqual(result.status, "ok")
        body = result.data
        self.assertEqual(body["data"]["symbol"], "601211")
        self.assertEqual(body["data"]["prompt_bundle"]["version"], "v1")
        self.assertTrue(body["data"]["prompt_bundle"]["compiled_prompt"])
        self.assertEqual(body["data"]["prompt_bundle"]["bundle_version"], "current")
        self.assertEqual(body["data"]["prompt_bundle"]["activation_source"], "current")
        self.assertIn("REM-R001", body["data"]["prompt_bundle"]["injected_strategy_ids"])
        self.assertIn("REM-R004", body["data"]["prompt_bundle"]["candidate_strategy_ids"])
        self.assertIn("evidence_threshold", body["data"]["data_quality"])
        self.assertIn("market_context", body["data"])
        self.assertIn("capital_context", body["data"])
        self.assertIn("expectation_context", body["data"])
        self.assertTrue(body["data"]["news_signal_board"])

    def test_analysis_stock_prepare_selects_sell_side_strategies(self):
        skill = self.make_skill()
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        result = skill.run(
            {"action": "analysis.stock.prepare", "symbol": "601211", "action_intent": "sell"}
        )
        self.assertEqual(result.status, "ok")
        injected = result.data["data"]["prompt_bundle"]["injected_strategy_ids"]
        self.assertIn("REM-R007", injected)
        self.assertIn("REM-R009", injected)
        self.assertNotIn("REM-R004", injected)

    def _valid_analysis_result(self, prepared_data):
        injected = prepared_data["prompt_bundle"]["injected_strategy_ids"]
        cited = injected[:2] if len(injected) >= 2 else injected
        return {
            "market_regime": {
                "current_regime": "theme_rotation",
                "risk_appetite": "high",
                "main_themes": ["证券"],
                "incremental_capital_direction": "券商",
                "next_verification_events": ["次日竞价资金承接"],
            },
            "sector_positioning": {
                "sector": "证券",
                "theme_role": "main_theme",
                "leader_status": "confirmed",
                "continuity": "good",
            },
            "expectation_analysis": {
                "market_expectation": "risk-on",
                "stock_expectation": "券商弹性延续",
                "priced_in": "partially_priced_in",
                "expectation_gap": "若量能继续放大仍有补涨空间",
                "catalyst_path": ["market", "sector", "stock"],
                "supporting_evidence": [
                    {"category": "market", "detail": "风险偏好抬升"},
                    {"category": "sector", "detail": "券商板块领涨"},
                    {"category": "capital", "detail": "主力净流入为正"},
                ],
            },
            "capital_confirmation": {
                "verdict": "confirmed",
                "main_flow": "positive",
                "order_structure": "big_order_dominant",
                "price_volume_fit": "yes",
                "relative_strength": "stronger_than_index",
                "notes": "放量且强于指数。",
            },
            "scenario_plan": {
                "bull_case": "放量突破后加速",
                "base_case": "维持强势震荡",
                "bear_case": "冲高回落失守均线",
            },
            "trigger_and_invalidation": {
                "entry_triggers": ["放量站稳前高"],
                "hold_triggers": ["主力持续净流入"],
                "invalidation_signals": ["跌破前一日低点"],
                "exit_triggers": ["放量滞涨且资金转负"],
            },
            "source_reliability": {
                "primary_sources": ["巨潮资讯", "Reuters"],
                "tradeable_signal_threshold": "S or A+capital confirmation",
            },
            "rumor_check": {
                "final_verdict": "official_confirmed",
            },
            "recommendation": {"action": "SELL", "confidence": 72, "position_size": "MODERATE"},
            "reasoning": {"primary_factors": ["trend broken"]},
            "summary": "减仓或退出，等待结构修复。",
            "strategy_usage": {
                "bundle_version": prepared_data["prompt_bundle"]["bundle_version"],
                "injected_strategy_ids": prepared_data["prompt_bundle"]["injected_strategy_ids"],
                "cited_strategy_ids": cited,
                "violated_strategy_ids": [],
                "selection_reason": prepared_data["prompt_bundle"]["selection_reason"],
                "strategy_notes": "卖出结论主要受纪律止损和反弹减仓策略约束。",
            },
        }

    def test_analysis_result_validate_accepts_consistent_strategy_usage(self):
        skill = self.make_skill()
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        prepared = skill.run({"action": "analysis.stock.prepare", "symbol": "601211", "action_intent": "sell"})
        data = prepared.data["data"]
        payload = {
            "action": "analysis.result.validate",
            "analysis_result": self._valid_analysis_result(data),
            "prompt_bundle": data["prompt_bundle"],
            "data_quality": data["data_quality"],
        }
        result = skill.run(payload)
        self.assertEqual(result.status, "ok")
        self.assertTrue(result.data["data"]["valid"])

    def test_analysis_result_validate_rejects_non_injected_strategy_ids(self):
        skill = self.make_skill()
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        prepared = skill.run({"action": "analysis.stock.prepare", "symbol": "601211"})
        data = prepared.data["data"]
        payload = {
            "action": "analysis.result.validate",
            "analysis_result": {
                **self._valid_analysis_result(data),
                "recommendation": {"action": "BUY", "confidence": 75, "position_size": "MODERATE"},
                "strategy_usage": {
                    "bundle_version": data["prompt_bundle"]["bundle_version"],
                    "injected_strategy_ids": data["prompt_bundle"]["injected_strategy_ids"],
                    "cited_strategy_ids": ["FAKE-R999", "REM-R001"],
                    "violated_strategy_ids": [],
                    "selection_reason": data["prompt_bundle"]["selection_reason"],
                    "strategy_notes": "引用了错误策略，应该被拦截。",
                },
            },
            "prompt_bundle": data["prompt_bundle"],
            "data_quality": data["data_quality"],
        }
        result = skill.run(payload)
        self.assertEqual(result.status, "error")
        self.assertIn("non-injected strategies", " ".join(result.data["data"]["errors"]))

    def test_analysis_result_validate_rejects_missing_expectation_and_trigger_blocks(self):
        skill = self.make_skill()
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        prepared = skill.run({"action": "analysis.stock.prepare", "symbol": "601211"})
        data = prepared.data["data"]
        analysis_result = self._valid_analysis_result(data)
        analysis_result.pop("expectation_analysis")
        analysis_result["trigger_and_invalidation"] = {}
        payload = {
            "action": "analysis.result.validate",
            "analysis_result": analysis_result,
            "prompt_bundle": data["prompt_bundle"],
            "data_quality": data["data_quality"],
        }
        result = skill.run(payload)
        self.assertEqual(result.status, "error")
        joined = " ".join(result.data["data"]["errors"])
        self.assertIn("expectation_analysis", joined)
        self.assertIn("trigger_and_invalidation", joined)

    def test_tool_failure_is_recorded(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        cache = FileCache(Path(temp_dir.name) / "cache")
        failure_root = Path(temp_dir.name) / "tool_failures"
        skill = StockSkill(
            cache=cache,
            failure_recorder=ToolFailureRecorder(failure_root),
            ak_provider=FailingAkProvider(),
            http_provider=WorkingHttpProvider(),
        )
        result = skill.run({"action": "quote.get", "symbol": "601211", "force_refresh": True})
        self.assertEqual(result.status, "degraded")
        files = sorted(failure_root.glob("*.jsonl"))
        self.assertTrue(files)
        content = files[0].read_text(encoding="utf-8")
        self.assertIn('"event_type": "provider_failure"', content)
        self.assertIn('"provider": "akshare"', content)

    def test_analysis_stock_prepare_rumor_check_ignores_market_only_official_news(self):
        class MixedNewsProvider(StubAkProvider):
            def kline_get(self, payload):
                return {
                    "symbol": "601211",
                    "period": "daily",
                    "adjust": "none",
                    "bars": [
                        {"date": "2026-04-23", "close": 10.0},
                        {"date": "2026-04-24", "close": 10.1},
                    ],
                }

            def news_market_get(self, payload):
                return {
                    "events": [
                        {"title": "国务院部署稳市场政策", "source": "国务院", "publish_time": "2026-04-24"},
                    ]
                }

            def news_stock_get(self, payload):
                return {
                    "symbol": "601211",
                    "events": [
                        {"title": "市场传闻公司将获重大订单", "source": "某论坛", "publish_time": "2026-04-24", "url": "https://example.com"},
                    ],
                }

        skill = self.make_skill(ak_provider=MixedNewsProvider())
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        result = skill.run({"action": "analysis.stock.prepare", "symbol": "601211"})
        self.assertEqual(result.status, "ok")
        rumor_check = result.data["data"]["rumor_check"]
        self.assertEqual(rumor_check["final_verdict"], "rumor_only")

    def test_analysis_stock_prepare_uses_aggregated_stock_data_payload(self):
        skill = self.make_skill()
        skill._load_analysis_payload = lambda symbol: ANALYSIS_PAYLOAD_FIXTURE
        result = skill.run({"action": "analysis.stock.prepare", "symbol": "601211"})
        self.assertEqual(result.status, "ok")
        stock_context = result.data["data"]["stock_context"]
        self.assertEqual(stock_context["quote"]["price"], 10.0)
        self.assertEqual(stock_context["fundamentals"]["report_date"], "2025-12-31")
        self.assertEqual(result.data["data"]["sector_context"]["primary_sector"], "证券")


class ProviderBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.original_ak = akshare_provider_module.ak

    def tearDown(self):
        akshare_provider_module.ak = self.original_ak

    def test_index_get_uses_previous_close(self):
        class StubAk:
            @staticmethod
            def stock_zh_index_daily_em(symbol):
                return pd.DataFrame(
                    [
                        {"收盘": 3000},
                        {"开盘": 3100, "收盘": 3150},
                    ]
                )

        akshare_provider_module.ak = StubAk()
        provider = AkshareProvider()
        result = provider.index_get({"index_code": "sh000001"})
        self.assertAlmostEqual(result["change_pct"], 5.0)

    def test_trading_calendar_uses_exchange_dates(self):
        class StubAk:
            @staticmethod
            def tool_trade_date_hist_sina():
                return pd.DataFrame({"trade_date": [dt.date(2026, 2, 16), dt.date(2026, 2, 17)]})

        akshare_provider_module.ak = StubAk()
        provider = AkshareProvider()
        result = provider.trading_calendar_get({"date": "2026-02-10"})
        self.assertFalse(result["is_trading_day"])
        self.assertEqual(result["next_trading_day"], "2026-02-16")

    def test_sector_map_uses_individual_info_industry(self):
        class StubAk:
            @staticmethod
            def stock_individual_info_em(symbol):
                return pd.DataFrame([{"item": "行业", "value": "半导体"}])

            @staticmethod
            def stock_board_concept_name_em():
                return pd.DataFrame([{"板块名称": "AI芯片"}, {"板块名称": "机器人"}])

            @staticmethod
            def stock_board_concept_cons_em(symbol):
                if symbol == "AI芯片":
                    return pd.DataFrame([{"代码": "688001"}])
                return pd.DataFrame([{"代码": "000001"}])

        akshare_provider_module.ak = StubAk()
        provider = AkshareProvider()
        result = provider.sector_map_get({"symbol": "688001"})
        self.assertEqual(result["primary_sector"], "半导体")
        self.assertEqual(result["concept_tags"], ["AI芯片"])

    def test_infer_relative_strength_uses_same_day_horizon(self):
        kline = [
            {"date": "2026-04-21", "close": 10.0},
            {"date": "2026-04-22", "close": 10.0},
            {"date": "2026-04-23", "close": 10.0},
            {"date": "2026-04-24", "close": 9.5},
        ]
        result = _infer_relative_strength(kline, {"change_pct": -0.2})
        self.assertEqual(result, "weaker_than_index")

    def test_build_rumor_check_only_uses_stock_scope_news(self):
        news_signal_board = [
            {
                "scope": "market",
                "source_grade": "S",
                "headline": "国务院稳市场",
            },
            {
                "scope": "stock",
                "source_grade": "C",
                "headline": "公司将获重大订单传闻",
            },
        ]
        result = _build_rumor_check(news_signal_board, {"capital_verdict": "confirmed"})
        self.assertEqual(result["final_verdict"], "rumor_only")
        self.assertFalse(result["has_official_source"])


if __name__ == "__main__":
    unittest.main()
