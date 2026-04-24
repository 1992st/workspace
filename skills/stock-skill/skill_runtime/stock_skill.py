from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from base import BaseSkill, SkillResult
from providers import AkshareProvider, HttpProvider
from shared import FileCache, HealthTracker, build_error_response, build_success_response
from shared.utils import cache_key


class StockSkill(BaseSkill):
    name = "stock"

    TTL_MAP = {
        "quote.get": 300,
        "quotes.batch.get": 300,
        "market.snapshot.get": 300,
        "index.get": 900,
        "trading.calendar.get": 43200,
        "kline.get": 86400,
        "news.stock.get": 1800,
        "news.market.get": 900,
        "flow.main.get": 1800,
        "flow.order_size.get": 1800,
        "fundamental.valuation.get": 86400,
        "fundamental.metrics.get": 86400,
        "sector.map.get": 86400,
        "sector.heat.get": 1800,
    }

    def __init__(
        self,
        *,
        cache: Optional[FileCache] = None,
        health: Optional[HealthTracker] = None,
        ak_provider: Optional[Any] = None,
        http_provider: Optional[Any] = None,
    ) -> None:
        root = Path(__file__).resolve().parents[3]
        self.cache = cache or FileCache(root / "data" / "market" / "cache")
        self.health = health or HealthTracker()
        self.ak_provider = ak_provider or AkshareProvider()
        self.http_provider = http_provider or HttpProvider()
        self.actions: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "quote.get": self._quote_get,
            "quotes.batch.get": self._quotes_batch_get,
            "kline.get": self._kline_get,
            "index.get": self._index_get,
            "trading.calendar.get": self._trading_calendar_get,
            "market.snapshot.get": self._market_snapshot_get,
            "news.stock.get": self._news_stock_get,
            "news.market.get": self._news_market_get,
            "flow.main.get": self._flow_main_get,
            "flow.order_size.get": self._flow_order_size_get,
            "fundamental.valuation.get": self._fundamental_valuation_get,
            "fundamental.metrics.get": self._fundamental_metrics_get,
            "sector.map.get": self._sector_map_get,
            "sector.heat.get": self._sector_heat_get,
            "health.report.get": self._health_report_get,
        }

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        action = payload.get("action")
        if action not in self.actions:
            return SkillResult(
                status="error",
                data=build_error_response(
                    "unsupported_action",
                    f"unsupported action: {action}",
                    retryable=False,
                ),
                errors=[f"unsupported action: {action}"],
            )
        try:
            response = self.actions[action](payload)
            return SkillResult(status=response["status"], data=response)
        except Exception as exc:
            response = build_error_response(
                "stock_skill_failure",
                str(exc),
                retryable=True,
            )
            return SkillResult(status="error", data=response, errors=[str(exc)])

    def _quote_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "quote.get",
            payload,
            providers=[
                ("akshare", self.ak_provider.quote_get),
                ("http", self.http_provider.quote_get),
            ],
        )

    def _quotes_batch_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "quotes.batch.get",
            payload,
            providers=[
                ("akshare", self.ak_provider.quotes_batch_get),
                ("http", self.http_provider.quotes_batch_get),
            ],
        )

    def _kline_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback("kline.get", payload, providers=[("akshare", self.ak_provider.kline_get)])

    def _index_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback("index.get", payload, providers=[("akshare", self.ak_provider.index_get)])

    def _trading_calendar_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "trading.calendar.get",
            payload,
            providers=[("akshare", self.ak_provider.trading_calendar_get)],
        )

    def _market_snapshot_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "market.snapshot.get",
            payload,
            providers=[("akshare", self.ak_provider.market_snapshot_get)],
        )

    def _news_stock_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback("news.stock.get", payload, providers=[("akshare", self.ak_provider.news_stock_get)])

    def _news_market_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "news.market.get",
            payload,
            providers=[
                ("akshare", self.ak_provider.news_market_get),
                ("http", self.http_provider.news_market_get),
            ],
        )

    def _flow_main_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback("flow.main.get", payload, providers=[("akshare", self.ak_provider.flow_main_get)])

    def _flow_order_size_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "flow.order_size.get",
            payload,
            providers=[("akshare", self.ak_provider.flow_order_size_get)],
        )

    def _fundamental_valuation_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "fundamental.valuation.get",
            payload,
            providers=[("akshare", self.ak_provider.fundamental_valuation_get)],
        )

    def _fundamental_metrics_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "fundamental.metrics.get",
            payload,
            providers=[("akshare", self.ak_provider.fundamental_metrics_get)],
        )

    def _sector_map_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback("sector.map.get", payload, providers=[("akshare", self.ak_provider.sector_map_get)])

    def _sector_heat_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback("sector.heat.get", payload, providers=[("akshare", self.ak_provider.sector_heat_get)])

    def _health_report_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_success_response(
            {"sources": self.health.snapshot()},
            source="system",
            source_chain=["system"],
        )

    def _call_with_fallback(
        self,
        action: str,
        payload: Dict[str, Any],
        *,
        providers: Sequence[Tuple[str, Callable[[Dict[str, Any]], Dict[str, Any]]]],
    ) -> Dict[str, Any]:
        ttl = self.TTL_MAP.get(action, 900)
        key = cache_key(action, payload)
        if not payload.get("force_refresh"):
            cached = self.cache.get(key, ttl)
            if cached:
                response = cached["response"]
                response["meta"]["source"] = "cache"
                response["meta"]["source_chain"] = ["cache"] + response["meta"].get("source_chain", [])
                response["status"] = "degraded"
                response["quality"]["freshness"] = 0.45
                response["quality"]["score"] = min(response["quality"]["score"], 79.0)
                response["quality"]["issues"] = sorted(set(response["quality"].get("issues", []) + ["cache_hit"]))
                return response

        failures: List[str] = []
        for source_name, provider in providers:
            start = time.perf_counter()
            try:
                data = provider(payload)
                latency_ms = (time.perf_counter() - start) * 1000
                self.health.record_success(source_name, latency_ms)
                status = "ok" if not failures else "degraded"
                response = build_success_response(
                    data,
                    source=source_name,
                    source_chain=[name for name, _ in providers],
                    latency_ms=latency_ms,
                    status=status,
                    issues=["fallback_used"] if failures else [],
                    failed_sources=failures,
                )
                self.cache.set(key, response)
                return response
            except Exception as exc:
                self.health.record_failure(source_name, str(exc))
                failures.append(source_name)

        stale = self.cache.get_any(key)
        if stale:
            response = stale["response"]
            response["status"] = "degraded"
            response["meta"]["source"] = "cache"
            response["meta"]["source_chain"] = [name for name, _ in providers] + ["cache"]
            response["quality"]["issues"] = sorted(
                set(response["quality"].get("issues", []) + ["stale_cache_fallback", "live_source_failed"])
            )
            response["error"]["failed_sources"] = failures
            return response

        return build_error_response(
            "all_sources_failed",
            f"{action} failed across all providers",
            retryable=True,
            failed_sources=failures,
            source_chain=[name for name, _ in providers],
        )
