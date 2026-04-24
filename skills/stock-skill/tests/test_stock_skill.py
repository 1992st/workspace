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
from shared.cache import FileCache
from shared.utils import cache_key
from stock_skill import StockSkill
from providers.akshare_provider import AkshareProvider


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
        return data

    def news_stock_get(self, payload):
        return {"symbol": "601211", "events": [{"title": "测试新闻", "source": "stub", "publish_time": "2026-04-24", "url": "https://example.com"}]}

    def news_market_get(self, payload):
        return {"events": [{"title": "市场新闻", "source": "stub", "publish_time": "2026-04-24"}]}

    def flow_main_get(self, payload):
        return {"symbol": "601211", "date": "2026-04-24", "main_net_inflow": 100, "super_large_net": 50, "large_net": 20, "medium_net": 10, "small_net": 20}

    def flow_order_size_get(self, payload):
        return {"date": "2026-04-24", "big_order_ratio": 0.7, "small_order_ratio": 0.2, "buy_sell_imbalance": 0.1}

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
        return StockSkill(
            cache=cache,
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

    def test_cache_key_ignores_control_flags(self):
        base = {"action": "quote.get", "symbol": "601211", "market": "CN-A"}
        forced = {"action": "quote.get", "symbol": "601211", "market": "CN-A", "force_refresh": True, "timeout_ms": 5000}
        self.assertEqual(cache_key("quote.get", base), cache_key("quote.get", forced))


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


if __name__ == "__main__":
    unittest.main()
