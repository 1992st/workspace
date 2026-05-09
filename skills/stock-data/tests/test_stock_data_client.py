from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from browser_fetch import parse_tencent_quote
from stock_client import StockDataClient


class StockDataClientTests(unittest.TestCase):
    def make_client(self) -> StockDataClient:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        workspace = Path(temp_dir.name)
        return StockDataClient(workspace=str(workspace))

    def test_normalize_skill_result_reads_nested_skill_payload(self):
        client = self.make_client()
        nested = {
            "status": "ok",
            "data": {
                "status": "degraded",
                "data": {
                    "symbol": "601211",
                    "name": "国泰海通",
                    "price": 10.5,
                    "change": 0.2,
                    "change_pct": 1.94,
                },
                "meta": {"source": "http", "fetched_at": "2026-04-25T10:00:00"},
                "quality": {"score": 82.0, "issues": ["fallback_used"]},
                "error": {"failed_sources": ["akshare"]},
            },
        }

        result = client._normalize_skill_result(nested, "601211")
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "http")
        self.assertEqual(result["data"]["price"], 10.5)
        self.assertEqual(result["failed_sources"], ["akshare"])
        self.assertEqual(result["data_status"], "degraded")

    def test_get_quote_falls_back_to_browser_and_caches(self):
        client = self.make_client()
        client._call_skill = lambda action, payload: {
            "status": "error",
            "data": {
                "status": "error",
                "data": {},
                "meta": {},
                "quality": {"issues": ["quote failed"]},
                "error": {"message": "quote failed", "failed_sources": ["akshare", "http"]},
            },
        }
        client._call_browser = lambda symbol: {
            "success": True,
            "source": "browser-tencent",
            "data": {
                "symbol": symbol,
                "name": "国泰海通",
                "price": 10.6,
                "change": 0.1,
                "change_pct": 0.95,
                "open": 10.5,
                "high": 10.7,
                "low": 10.4,
                "pre_close": 10.5,
                "volume": 1000,
                "amount": 2000,
                "timestamp": "2026-04-25T10:00:00",
            },
            "quality_score": 88,
            "is_cached": False,
            "errors": [],
            "failed_sources": [],
            "data_status": "ok",
        }

        result = client.get_quote("601211")
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "browser-tencent")
        cached = client._get_cache("601211", "quote")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["data"]["price"], 10.6)

    def test_get_quote_uses_cache_after_live_failures(self):
        client = self.make_client()
        client._save_cache(
            "601211",
            "quote",
            {
                "symbol": "601211",
                "name": "国泰海通",
                "price": 10.3,
            },
        )
        client._call_skill = lambda action, payload: {
            "status": "error",
            "data": {
                "status": "error",
                "data": {},
                "meta": {},
                "quality": {"issues": []},
                "error": {"message": "skill failed", "failed_sources": ["akshare", "http"]},
            },
        }
        client._call_browser = lambda symbol: {
            "success": False,
            "source": "browser-tencent",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "errors": ["browser failed"],
            "failed_sources": ["browser-tencent"],
            "data_status": "error",
        }

        result = client.get_quote("601211")
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "cache")
        self.assertTrue(result["is_cached"])
        self.assertIn("browser failed", result["errors"])

    def test_get_quote_does_not_refresh_local_cache_from_skill_cache_result(self):
        client = self.make_client()
        client._call_skill = lambda action, payload: {
            "status": "ok",
            "data": {
                "status": "degraded",
                "data": {"symbol": "601211", "name": "国泰海通", "price": 10.3},
                "meta": {"source": "cache"},
                "quality": {"score": 60.0, "issues": ["stale_cache_fallback"]},
                "error": {"failed_sources": ["akshare", "http"]},
            },
        }
        save_calls = []
        original_save_cache = client._save_cache

        def wrapped_save_cache(*args, **kwargs):
            save_calls.append((args, kwargs))
            return original_save_cache(*args, **kwargs)

        client._save_cache = wrapped_save_cache
        result = client.get_quote("601211")
        self.assertTrue(result["success"])
        self.assertEqual(result["source"], "cache")
        self.assertEqual(save_calls, [])

    def test_get_kline_cache_is_partitioned_by_timeframe_and_limit(self):
        client = self.make_client()
        kline_payload = {"symbol": "601211", "bars": [{"date": "2026-04-25", "close": 10.0}]}
        client._save_cache("601211", "kline", kline_payload, timeframe="1d", limit=30)
        same_request_cache = client._get_cache("601211", "kline", timeframe="1d", limit=30)
        different_timeframe_cache = client._get_cache("601211", "kline", timeframe="1w", limit=30)
        different_limit_cache = client._get_cache("601211", "kline", timeframe="1d", limit=60)
        self.assertIsNotNone(same_request_cache)
        self.assertIsNone(different_timeframe_cache)
        self.assertIsNone(different_limit_cache)

    def test_get_kline_does_not_reuse_wrong_parameter_cache_on_live_failure(self):
        client = self.make_client()
        client._save_cache(
            "601211",
            "kline",
            {"symbol": "601211", "bars": [{"date": "2026-04-25", "close": 10.0}]},
            timeframe="1d",
            limit=30,
        )
        client._call_skill = lambda action, payload: {
            "status": "error",
            "data": {
                "status": "error",
                "data": {},
                "meta": {},
                "quality": {"issues": []},
                "error": {"message": "skill failed", "failed_sources": ["akshare"]},
            },
        }
        result = client.get_kline("601211", timeframe="1w", limit=30)
        self.assertFalse(result["success"])
        self.assertIn("K线数据当前未实现 browser 降级", result["errors"])

    def test_get_analysis_payload_dispatches_to_fast_data(self):
        client = self.make_client()
        calls = []
        client._run_fast = lambda *args, **kwargs: calls.append(args) or {"success": True, "data": {"symbol": "601211"}}
        result = client.get_analysis_payload("601211")
        self.assertTrue(result["success"])
        self.assertEqual(calls[0], ("analysis", "601211"))

    def test_get_kline_period_dispatches_to_extended_fast_command(self):
        client = self.make_client()
        calls = []
        client._run_fast = lambda *args, **kwargs: calls.append(args) or {"success": True, "data": {"period": "weekly"}}
        result = client.get_kline_period("601211", "weekly", 104)
        self.assertTrue(result["success"])
        self.assertEqual(calls[0], ("klinex", "601211", "weekly", "104"))


class BrowserFetchTests(unittest.TestCase):
    def test_parse_tencent_quote_maps_expected_fields(self):
        raw = (
            'v_sh601211="1~国泰海通~601211~16.60~16.79~16.71~535335~253583~281753~16.59~686~16.58~120~16.57~90~16.56~50~16.55~30~'
            '16.60~500~16.61~800~16.62~1000~16.63~300~16.64~200~20260424115908~-0.19~-1.13~16.73~16.48~16.60/535335/887662161~535335~887662161~1.25~10.52~";'
        )
        result = parse_tencent_quote(raw, "601211")
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["symbol"], "601211")
        self.assertEqual(result["data"]["name"], "国泰海通")
        self.assertEqual(result["data"]["price"], 16.60)
        self.assertEqual(result["data"]["high"], 16.73)
        self.assertEqual(result["data"]["low"], 16.48)
        self.assertEqual(result["data"]["amount"], 887662161)


if __name__ == "__main__":
    unittest.main()
