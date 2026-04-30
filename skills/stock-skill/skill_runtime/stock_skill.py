from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from analysis_engine import build_stock_analysis_context
from analysis_resources import AnalysisResourceLoader
from analysis_validation import validate_analysis_result
from base import BaseSkill, SkillResult
from providers import AkshareProvider, HttpProvider
from shared import (
    FileCache,
    HealthTracker,
    ToolFailureRecorder,
    build_error_response,
    build_success_response,
)
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
        "etf.pcf.get": 43200,
        "margin.balance.get": 43200,
        "hsgt.top10.get": 43200,
        "lhb.detail.get": 43200,
        "block_trade.get": 43200,
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
        failure_recorder: Optional[ToolFailureRecorder] = None,
        ak_provider: Optional[Any] = None,
        http_provider: Optional[Any] = None,
        resource_loader: Optional[AnalysisResourceLoader] = None,
    ) -> None:
        root = Path(__file__).resolve().parents[3]
        skill_root = Path(__file__).resolve().parents[1]
        self.root = root
        self.skill_root = skill_root
        self.cache = cache or FileCache(root / "data" / "market" / "cache")
        self.health = health or HealthTracker()
        self.failure_recorder = failure_recorder or ToolFailureRecorder(
            skill_root / "runtime_data" / "tool_failures"
        )
        self.ak_provider = ak_provider or AkshareProvider()
        self.http_provider = http_provider or HttpProvider()
        self.resource_loader = resource_loader or AnalysisResourceLoader(skill_root)
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
            "etf.pcf.get": self._etf_pcf_get,
            "margin.balance.get": self._margin_balance_get,
            "hsgt.top10.get": self._hsgt_top10_get,
            "lhb.detail.get": self._lhb_detail_get,
            "block_trade.get": self._block_trade_get,
            "fundamental.valuation.get": self._fundamental_valuation_get,
            "fundamental.metrics.get": self._fundamental_metrics_get,
            "sector.map.get": self._sector_map_get,
            "sector.heat.get": self._sector_heat_get,
            "analysis.stock.prepare": self._analysis_stock_prepare,
            "analysis.result.validate": self._analysis_result_validate,
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

    def _etf_pcf_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "etf.pcf.get",
            payload,
            providers=[("akshare", self.ak_provider.etf_pcf_get)],
        )

    def _margin_balance_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "margin.balance.get",
            payload,
            providers=[("akshare", self.ak_provider.margin_balance_get)],
        )

    def _hsgt_top10_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "hsgt.top10.get",
            payload,
            providers=[("akshare", self.ak_provider.hsgt_top10_get)],
        )

    def _lhb_detail_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "lhb.detail.get",
            payload,
            providers=[("akshare", self.ak_provider.lhb_detail_get)],
        )

    def _block_trade_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_with_fallback(
            "block_trade.get",
            payload,
            providers=[("akshare", self.ak_provider.block_trade_get)],
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

    def _analysis_stock_prepare(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = str(payload.get("symbol") or "").strip()
        if not symbol:
            return build_error_response(
                "missing_symbol",
                "symbol is required for analysis.stock.prepare",
                retryable=False,
            )
        sector_map_response = self._sector_map_get(payload)
        primary_sector = (
            sector_map_response.get("data", {}).get("primary_sector")
            if sector_map_response.get("status") in {"ok", "degraded"}
            else ""
        )
        sector_heat_response = (
            self._sector_heat_get({"sector": primary_sector})
            if primary_sector
            else build_error_response(
                "missing_sector_for_sector_heat",
                "sector heat unavailable because primary sector could not be resolved",
                retryable=False,
            )
        )
        responses = {
            "quote.get": self._quote_get(payload),
            "kline.get": self._kline_get({**payload, "timeframe": payload.get("timeframe", "1d"), "limit": payload.get("kline_limit", 60)}),
            "index.get": self._index_get({"index_code": payload.get("index_code", "sh000001")}),
            "market.snapshot.get": self._market_snapshot_get({"limit": payload.get("market_limit", 50)}),
            "sector.map.get": sector_map_response,
            "sector.heat.get": sector_heat_response,
            "news.market.get": self._news_market_get({"limit": payload.get("market_news_limit", 10)}),
            "news.stock.get": self._news_stock_get({**payload, "limit": payload.get("news_limit", 10)}),
            "flow.main.get": self._flow_main_get(payload),
            "flow.order_size.get": self._flow_order_size_get(payload),
            "fundamental.valuation.get": self._fundamental_valuation_get(payload),
            "fundamental.metrics.get": self._fundamental_metrics_get(payload),
        }
        bundle = self.resource_loader.load_stock_analysis_bundle()
        analysis_context = build_stock_analysis_context(
            symbol=symbol,
            responses=responses,
            resource_bundle=bundle,
            selection_context={
                "action_intent": payload.get("action_intent", "observe"),
                "requested_tags": payload.get("strategy_tags", []),
            },
        )
        failed_actions = [
            action for action, response in responses.items() if response.get("status") == "error"
        ]
        status = "ok" if not failed_actions else "degraded"
        issues = ["analysis_bundle_prepared"]
        if failed_actions:
            issues.append("partial_data_available")
        return build_success_response(
            analysis_context,
            source="stock_skill",
            source_chain=["stock_skill"],
            status=status,
            issues=issues,
            failed_sources=failed_actions,
        )

    def _health_report_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_success_response(
            {"sources": self.health.snapshot()},
            source="system",
            source_chain=["system"],
        )

    def _analysis_result_validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        analysis_result = payload.get("analysis_result")
        prompt_bundle = payload.get("prompt_bundle")
        data_quality = payload.get("data_quality")
        missing = []
        if not isinstance(analysis_result, dict):
            missing.append("analysis_result")
        if not isinstance(prompt_bundle, dict):
            missing.append("prompt_bundle")
        if not isinstance(data_quality, dict):
            missing.append("data_quality")
        if missing:
            return build_error_response(
                "missing_validation_payload",
                f"analysis.result.validate requires dict fields: {', '.join(missing)}",
                retryable=False,
            )

        validation = validate_analysis_result(
            analysis_result=analysis_result,
            prompt_bundle=prompt_bundle,
            data_quality=data_quality,
        )
        issues = []
        status = "ok"
        if validation["warnings"]:
            issues.extend(validation["warnings"])
            status = "degraded"
        if not validation["valid"]:
            issues.extend(validation["errors"])
            status = "error"
        return build_success_response(
            validation,
            source="stock_skill",
            source_chain=["stock_skill"],
            status=status,
            issues=issues,
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
                self.failure_recorder.record(
                    {
                        "action": action,
                        "provider": source_name,
                        "event_type": "provider_failure",
                        "payload": {"symbol": payload.get("symbol"), "market": payload.get("market")},
                        "message": str(exc),
                    }
                )
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
            self.failure_recorder.record(
                {
                    "action": action,
                    "provider": "cache",
                    "event_type": "stale_cache_fallback",
                    "payload": {"symbol": payload.get("symbol"), "market": payload.get("market")},
                    "message": "live providers failed; returned stale cache",
                    "failed_sources": failures,
                }
            )
            return response

        self.failure_recorder.record(
            {
                "action": action,
                "provider": "system",
                "event_type": "all_sources_failed",
                "payload": {"symbol": payload.get("symbol"), "market": payload.get("market")},
                "message": f"{action} failed across all providers",
                "failed_sources": failures,
            }
        )
        return build_error_response(
            "all_sources_failed",
            f"{action} failed across all providers",
            retryable=True,
            failed_sources=failures,
            source_chain=[name for name, _ in providers],
        )
