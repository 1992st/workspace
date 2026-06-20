#!/usr/bin/env python3
"""
Win_Stock 统一数据客户端 - 高速版

修正：
1. 直连 akshare（绕过冗余的 stock-skill 编排层）
2. 全量行情 120 秒缓存池 -> 后续报价查询 < 1 秒
3. 统一输出格式，兼容存量调用方
4. 降级链：fast_data -> cache -> stock-skill(遗留) -> browser_fetch(开天窗兜底)

用法：
  python3 stock_client.py quote 601211
  python3 stock_client.py quotes 601211 002241
  python3 stock_client.py kline 601211 [天数]
  python3 stock_client.py market
  python3 stock_client.py sector 601211
  python3 stock_client.py finance 601211
  python3 stock_client.py margin 601211
  python3 stock_client.py flow 601211
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class StockDataClient:
    def __init__(self, workspace: Optional[str] = None) -> None:
        self.workspace = Path(workspace) if workspace else Path(__file__).resolve().parents[3]
        self.fast_script = self.workspace / "skills/stock-data/scripts/fast_data.py"
        self.browser_script = self.workspace / "skills/stock-data/scripts/browser_fetch.py"
        self.alternative_script = self.workspace / "skills/stock-data/scripts/alternative_data_probe.py"
        self.cache_dir = self.workspace / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.health_dir = self.workspace / "data" / "health"
        self.health_dir.mkdir(parents=True, exist_ok=True)
        self.alternative_health_dir = self.health_dir / "alternative"
        self.alternative_health_dir.mkdir(parents=True, exist_ok=True)
        self.health_state_path = self.health_dir / "source_state.json"
        self.db_path = self.workspace / "data" / "win_stock.db"
        self.error_log = self.workspace / "logs" / "errors" / "data_fetch_failures.jsonl"
        self.error_log.parent.mkdir(parents=True, exist_ok=True)

    def _run_fast(self, *args: str, timeout: int = 180) -> Dict[str, Any]:
        cmd = ["python3", str(self.fast_script), *args]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(self.workspace))
            if not result.stdout.strip():
                return {"success": False, "error": "fast_data: 空输出", "stderr": result.stderr.strip()}
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"fast_data: 超时 {timeout}s"}
        except Exception as e:
            return {"success": False, "error": f"fast_data: {e}"}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        errors: List[str] = []

        skill_result = self._call_skill("quote.get", {"symbol": symbol, "market": "CN-A"})
        normalized_skill = self._normalize_skill_result(skill_result, symbol)
        if normalized_skill["success"]:
            if normalized_skill["source"] != "cache":
                self._save_cache(symbol, "quote", normalized_skill["data"])
            return normalized_skill
        errors.extend(normalized_skill["errors"])

        browser_result = self._call_browser(symbol)
        if browser_result.get("success"):
            self._save_cache(symbol, "quote", browser_result.get("data", {}))
            browser_result["errors"] = errors + browser_result.get("errors", [])
            return browser_result
        errors.extend(browser_result.get("errors", []))

        result = self._run_fast("quote", symbol)
        if result.get("success"):
            if result.get("source") != "cache":
                self._save_cache(symbol, "quote", result.get("data", {}))
            return {
                "success": True,
                "source": result.get("source", "fast_data"),
                "data": result.get("data"),
                "quality_score": 90,
                "is_cached": result.get("source") == "cache",
                "cache_age_hours": None,
                "errors": errors,
                "failed_sources": normalized_skill.get("failed_sources", []),
                "data_status": "ok",
            }
        errors.append(result.get("error", "quote failed"))

        cached = self._get_cache(symbol, "quote")
        if cached:
            cached["errors"] = errors + cached.get("errors", [])
            return cached

        return self._final_failure(symbol, "quote", errors)

    def get_quotes_batch(self, symbols: List[str]) -> Dict[str, Any]:
        return self._run_fast("quotes", *symbols)

    def get_kline(
        self,
        symbol: str,
        days: int = 60,
        timeframe: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        if timeframe is not None or limit is not None:
            tf = timeframe or "1d"
            bars_limit = limit or 30
            fast_result = self.get_kline_period(symbol, tf, bars_limit)
            if fast_result.get("success"):
                self._save_cache(symbol, "kline", fast_result.get("data", {}), timeframe=tf, limit=bars_limit)
                return {
                    "success": True,
                    "source": fast_result.get("source", "fast_data"),
                    "data": fast_result.get("data"),
                    "quality_score": 90,
                    "is_cached": fast_result.get("source") == "cache",
                    "cache_age_hours": None,
                    "errors": [],
                    "failed_sources": [],
                    "data_status": "ok",
                }
            cached = self._get_cache(symbol, "kline", timeframe=tf, limit=bars_limit)
            if cached:
                cached["errors"] = [fast_result.get("error", "kline failed")] + cached.get("errors", [])
                return cached
            return self._final_failure(symbol, "kline", [fast_result.get("error", "kline failed"), "K线数据当前未实现 browser 降级"])
        result = self._run_fast("kline", symbol, str(days))
        if result.get("success"):
            self._save_cache(symbol, "kline", result.get("data", {}), timeframe="daily", limit=days)
            return result
        browser_result = self._call_browser_kline(symbol, days)
        if browser_result.get("success"):
            self._save_cache(symbol, "kline", browser_result.get("data", {}), timeframe="daily", limit=days)
            browser_result["errors"] = [result.get("error", "kline failed")] + browser_result.get("errors", [])
            return browser_result
        cached = self._get_cache(symbol, "kline", max_age_hours=24, timeframe="daily", limit=days)
        if cached:
            cached["errors"] = [result.get("error", "kline failed")] + cached.get("errors", [])
            return cached
        return result

    def get_kline_period(self, symbol: str, period: str = "daily", days: int = 120) -> Dict[str, Any]:
        result = self._run_fast("klinex", symbol, period, str(days))
        if result.get("success"):
            self._save_cache(symbol, "kline", result.get("data", {}), timeframe=period, limit=days)
            return result
        if period in {"daily", "day", "1d"}:
            browser_result = self._call_browser_kline(symbol, days)
            if browser_result.get("success"):
                self._save_cache(symbol, "kline", browser_result.get("data", {}), timeframe=period, limit=days)
                browser_result["errors"] = [result.get("error", "kline failed")] + browser_result.get("errors", [])
                return browser_result
        cached = self._get_cache(symbol, "kline", max_age_hours=24, timeframe=period, limit=days)
        if cached:
            cached["errors"] = [result.get("error", "kline failed")] + cached.get("errors", [])
            return cached
        return result

    def get_market(self) -> Dict[str, Any]:
        result = self._run_fast("market")
        browser_result = self._call_browser_market()

        if self._market_has_valid_indices(result):
            if browser_result.get("success"):
                result = self._merge_market_result(result, browser_result)
            self._save_global_cache("market", result.get("data", {}))
            return result

        if browser_result.get("success"):
            self._save_global_cache("market", browser_result.get("data", {}))
            browser_result["errors"] = self._compact_errors([result.get("error"), *browser_result.get("errors", [])])
            return browser_result

        cached = self._get_global_cache("market", max_age_hours=6)
        if cached:
            cached["errors"] = self._compact_errors([result.get("error"), *browser_result.get("errors", []), *cached.get("errors", [])])
            return cached
        return result

    def _merge_market_result(self, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        primary_data = dict(primary.get("data") or {})
        secondary_data = secondary.get("data") or {}
        primary_indices = primary_data.get("indices") or []
        secondary_by_code = {str(item.get("code")): item for item in secondary_data.get("indices") or []}
        merged_indices = []
        for item in primary_indices:
            merged = dict(item)
            alt = secondary_by_code.get(str(item.get("code"))) or {}
            for key in ("price", "change", "change_pct", "open", "high", "low", "pre_close", "volume", "amount", "timestamp"):
                if merged.get(key) in (None, "") and alt.get(key) not in (None, ""):
                    merged[key] = alt[key]
            merged_indices.append(merged)
        if merged_indices:
            primary_data["indices"] = merged_indices
        breadth = primary_data.get("breadth") or {}
        if not self._has_valid_breadth(breadth):
            alt_breadth = secondary_data.get("breadth") or {}
            primary_data["breadth"] = alt_breadth if self._has_valid_breadth(alt_breadth) else breadth
        primary["data"] = primary_data
        primary["source"] = f"{primary.get('source', 'primary')}+{secondary.get('source', 'secondary')}"
        primary["errors"] = self._compact_errors([*primary.get("errors", []), primary.get("error"), *secondary.get("errors", [])])
        return primary

    def get_sector(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "sector", ["sector", symbol], max_age_hours=24)

    def get_finance(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "finance", ["finance", symbol], max_age_hours=48)

    def get_margin(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "margin", ["margin", symbol], max_age_hours=72)

    def get_flow(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "flow", ["flow", symbol], max_age_hours=24)

    def get_flow_hist(self, symbol: str, days: int = 10) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "flow_hist", ["flow-hist", symbol, str(days)], max_age_hours=24, days=days)

    def get_north_south(self) -> Dict[str, Any]:
        return self._run_fast_with_global_cache("north_south", "north-south", max_age_hours=6)

    def get_market_breadth(self) -> Dict[str, Any]:
        return self._run_fast_with_global_cache("market_breadth", "breadth", max_age_hours=6)

    def get_market_flow(self) -> Dict[str, Any]:
        return self._run_fast_with_global_cache("market_flow", "market-flow", max_age_hours=6)

    def get_market_proxy(self) -> Dict[str, Any]:
        return self._run_fast_with_global_cache("market_proxy", "market-proxy", max_age_hours=2)

    def get_lhb(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "lhb", ["lhb", symbol], max_age_hours=72)

    def get_intraday(self, symbol: str, interval: str = "1", days: int = 3) -> Dict[str, Any]:
        result = self._run_fast("intraday", symbol, interval, str(days))
        if result.get("success"):
            self._save_cache(symbol, "intraday", result.get("data", {}), interval=interval, days=days)
            return result
        if str(interval) in {"1", "1m"}:
            browser_result = self._call_browser_intraday(symbol)
            if browser_result.get("success"):
                self._save_cache(symbol, "intraday", browser_result.get("data", {}), interval=interval, days=days)
                browser_result["errors"] = [result.get("error", "intraday failed")] + browser_result.get("errors", [])
                return browser_result
        cached = self._get_cache(symbol, "intraday", max_age_hours=1, interval=interval, days=days)
        if cached:
            cached["errors"] = [result.get("error", "intraday failed")] + cached.get("errors", [])
            return cached
        return result

    def get_financial_trend(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast_with_symbol_cache(symbol, "finance_trend", ["finance-trend", symbol], max_age_hours=72)

    def get_alternative_data(self, symbol: str, stock_name: Optional[str] = None) -> Dict[str, Any]:
        normalized_symbol = symbol.zfill(6)
        cached_recent = self._get_latest_alternative_probe(normalized_symbol, max_age_hours=6)
        if cached_recent and self._alternative_probe_has_structured_records(cached_recent.get("data")):
            return cached_recent

        if not self.alternative_script.exists():
            return self._final_failure(normalized_symbol, "alternative_data", ["alternative_data_probe.py 不存在"])

        cmd = ["python3", str(self.alternative_script), normalized_symbol]
        if stock_name:
            cmd.append(stock_name)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=35,
                cwd=str(self.workspace),
            )
            if not result.stdout.strip():
                errors = self._compact_errors(["alternative_data_probe: 空输出", result.stderr.strip()])
                cached = self._get_latest_alternative_probe(normalized_symbol, max_age_hours=24)
                if cached:
                    cached["errors"] = errors + cached.get("errors", [])
                    return cached
                return self._final_failure(normalized_symbol, "alternative_data", errors)
            payload = json.loads(result.stdout)
            return self._normalize_alternative_probe(payload, is_cached=False)
        except subprocess.TimeoutExpired:
            errors = ["alternative_data_probe: 超时 35s"]
        except Exception as exc:
            errors = [f"alternative_data_probe: {exc}"]

        cached = self._get_latest_alternative_probe(normalized_symbol, max_age_hours=24)
        if cached:
            cached["errors"] = errors + cached.get("errors", [])
            return cached
        return self._final_failure(normalized_symbol, "alternative_data", errors)

    def get_analysis_payload(self, symbol: str) -> Dict[str, Any]:
        sections: Dict[str, Dict[str, Any]] = {
            "quote": self.get_quote(symbol),
            "market": self.get_market(),
            "sector": self._run_fast_with_symbol_cache(symbol, "sector_ctx", ["sector-ctx", symbol], max_age_hours=24),
            "finance": self.get_finance(symbol),
            "finance_trend": self.get_financial_trend(symbol),
            "flow": self.get_flow(symbol),
            "flow_hist_10": self.get_flow_hist(symbol, 10),
            "margin": self.get_margin(symbol),
            "north_south": self.get_north_south(),
            "lhb": self.get_lhb(symbol),
            "kline_daily_120": self.get_kline(symbol, 120),
            "kline_daily_60": self.get_kline(symbol, 60),
            "intraday_1m": self.get_intraday(symbol, "1", 1),
        }
        quote_data = sections["quote"].get("data") or {}
        stock_name = quote_data.get("name") or quote_data.get("股票简称") or quote_data.get("名称")
        sections["alternative_data"] = self.get_alternative_data(symbol, stock_name)
        missing_sections = []
        quality_sections = {}
        for name, response in sections.items():
            success = bool(response.get("success"))
            data = response.get("data")
            missing = not success or data in (None, {}, [])
            if missing:
                missing_sections.append({"section": name, "reason": response.get("error") or "; ".join(response.get("errors", [])) or "empty"})
            section_status = "error"
            if success:
                section_status = "degraded" if (
                    response.get("is_cached")
                    or response.get("source") == "cache"
                    or response.get("data_status") == "degraded"
                    or response.get("quality_score", 100) < 80
                ) else "ok"
            quality_sections[name] = {
                "status": section_status,
                "source": response.get("source", "unknown"),
                "fetched_at": response.get("fetched_at") or response.get("timestamp"),
                "is_cached": bool(response.get("is_cached") or response.get("source") == "cache"),
                "cache_age_hours": response.get("cache_age_hours"),
                "errors": response.get("errors", []) or ([response.get("error")] if response.get("error") else []),
            }
            if name == "market" and success and ((data or {}).get("breadth") or {}).get("status") == "missing":
                missing_sections.append({"section": "market_breadth", "reason": ((data or {}).get("breadth") or {}).get("reason", "市场广度缺失")})
        payload = {
            "symbol": symbol.zfill(6),
            "quote": sections["quote"].get("data"),
            "market": sections["market"].get("data"),
            "sector": sections["sector"].get("data"),
            "fundamental_valuation": sections["finance"].get("data"),
            "fundamental_trend": sections["finance_trend"].get("data"),
            "fund_flow": sections["flow"].get("data"),
            "fund_flow_hist_10": sections["flow_hist_10"].get("data"),
            "margin": sections["margin"].get("data"),
            "north_south_flow": sections["north_south"].get("data"),
            "lhb": sections["lhb"].get("data"),
            "kline_daily": sections["kline_daily_120"].get("data") or sections["kline_daily_60"].get("data"),
            "intraday": {"1m": sections["intraday_1m"].get("data")},
            "alternative_data_clues": sections["alternative_data"].get("data"),
            "quality": {
                "status": "ok" if not missing_sections else "degraded",
                "sections": quality_sections,
                "missing_sections": missing_sections,
                "degradation_rules": self._analysis_degradation_rules(missing_sections),
            },
        }
        return {
            "success": True,
            "source": "stock_client.analysis",
            "data": payload,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "data_status": payload["quality"]["status"],
            "missing_sections": missing_sections,
        }

    def _analysis_degradation_rules(self, missing_sections: List[Dict[str, str]]) -> List[str]:
        missing = {item["section"] for item in missing_sections}
        rules = []
        if {"kline_daily_120", "kline_daily_60"} & missing:
            rules.append("缺K线：不输出明确买卖价")
        if "intraday_1m" in missing:
            rules.append("缺分时：不输出做T计划")
        if "margin" in missing:
            rules.append("缺融资融券：资金判断降级")
        if "north_south" in missing:
            rules.append("缺北向/南向：不得判断外资流向")
        if "market_breadth" in missing:
            rules.append("缺市场广度：大盘走势只能降级判断，不得给出强市场环境结论")
        if "sector" in missing:
            rules.append("缺板块：不得判断顺应主线或板块退潮")
        if "finance" in missing:
            rules.append("缺估值：基本面判断降级")
        if "alternative_data" in missing:
            rules.append("缺非常规公开数据雷达：不得声称已排查公告/监管/舆情/招投标等弱信号")
        return rules

    def _get_latest_alternative_probe(self, symbol: str, max_age_hours: int) -> Optional[Dict[str, Any]]:
        pattern = f"alternative_probe_{symbol}_*.json"
        candidates = sorted(self.alternative_health_dir.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
        if not candidates:
            return None
        latest = candidates[0]
        age_hours = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds() / 3600
        if age_hours > max_age_hours:
            return None
        try:
            payload = json.loads(latest.read_text(encoding="utf-8"))
        except Exception:
            return None
        normalized = self._normalize_alternative_probe(payload, is_cached=True)
        normalized["cache_age_hours"] = round(age_hours, 2)
        normalized["errors"] = [f"使用 {age_hours:.1f} 小时前非常规数据探测缓存"] + normalized.get("errors", [])
        return normalized

    def _normalize_alternative_probe(self, payload: Dict[str, Any], is_cached: bool) -> Dict[str, Any]:
        success = bool(payload.get("success"))
        summary = payload.get("summary") or {}
        available = int(summary.get("available") or 0)
        failed = int(summary.get("failed") or 0)
        total = available + failed
        quality_score = int(round((available / total) * 100)) if total else (80 if success else 0)
        failed_sources = summary.get("failed_sources") or []
        errors = [f"failed_sources: {', '.join(failed_sources)}"] if failed_sources else []
        data_status = "ok" if success and failed == 0 else ("degraded" if success else "error")
        return {
            "success": success,
            "source": "alternative-probe-cache" if is_cached else payload.get("source", "alternative_data_probe"),
            "data": payload if success else None,
            "quality_score": quality_score,
            "is_cached": is_cached,
            "cache_age_hours": None,
            "errors": errors,
            "failed_sources": failed_sources,
            "data_status": data_status,
            "fetched_at": payload.get("fetched_at") or datetime.now().isoformat(timespec="seconds"),
            "symbol": payload.get("symbol"),
        }

    def _alternative_probe_has_structured_records(self, payload: Any) -> bool:
        if not isinstance(payload, dict):
            return False
        summary = payload.get("summary") or {}
        if int(summary.get("structured_sources") or 0) > 0:
            return True
        for item in payload.get("results") or []:
            if isinstance(item, dict) and item.get("structured"):
                return True
        return False

    def health_check(self, symbols: Optional[List[str]] = None, retry_delay_sec: float = 1.0) -> Dict[str, Any]:
        probe_symbols = symbols or ["601211", "002241", "600406"]
        if len(probe_symbols) < 3:
            probe_symbols = list(dict.fromkeys([*probe_symbols, "601211", "002241", "600406"]))

        probes: List[Dict[str, Any]] = [
            self._probe("market", lambda: self.get_market(), ["indices", "breadth"]),
            self._probe("north-south", lambda: self.get_north_south(), ["summary", "daily"]),
        ]

        for symbol in probe_symbols:
            symbol_probes = [
                self._probe(f"quote:{symbol}", lambda s=symbol: self.get_quote(s), ["price", "change_pct", "volume", "amount"], retry_delay_sec),
                self._probe(f"kline:{symbol}:60", lambda s=symbol: self.get_kline(s, 60), ["bars", "count"], retry_delay_sec),
                self._probe(f"sector:{symbol}", lambda s=symbol: self._run_fast("sector-ctx", s), ["industry"], retry_delay_sec),
                self._probe(f"finance:{symbol}", lambda s=symbol: self.get_finance(s), ["pe_ttm", "pb", "market_cap"], retry_delay_sec),
                self._probe(f"flow:{symbol}", lambda s=symbol: self.get_flow(s), ["main_net_inflow", "super_large_net", "large_net"], retry_delay_sec),
                self._probe(f"flow-hist:{symbol}:10", lambda s=symbol: self.get_flow_hist(s, 10), ["bars", "recent_5d"], retry_delay_sec),
                self._probe(f"margin:{symbol}", lambda s=symbol: self.get_margin(s), ["financing_balance", "financing_buy", "financing_repay"], retry_delay_sec),
                self._probe(f"lhb:{symbol}", lambda s=symbol: self.get_lhb(s), ["records", "count"], retry_delay_sec),
                self._probe(f"intraday:{symbol}", lambda s=symbol: self.get_intraday(s, "1", 1), ["bars", "count"], retry_delay_sec),
            ]
            probes.extend(symbol_probes)

        summary = {
            "healthy": sum(1 for item in probes if item["health_status"] == "healthy"),
            "degraded": sum(1 for item in probes if item["health_status"] == "degraded"),
            "unstable": sum(1 for item in probes if item["health_status"] == "unstable"),
            "failed": sum(1 for item in probes if item["health_status"] == "failed"),
            "unsupported_now": sum(1 for item in probes if item["health_status"] == "unsupported_now"),
        }
        result = {
            "success": True,
            "source": "stock_client.health",
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "data_status": "ok" if summary["failed"] == 0 else "degraded",
            "symbols": probe_symbols,
            "summary": summary,
            "interfaces": probes,
            "report_path": None,
        }
        report_path = self.health_dir / f"interface_health_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["report_path"] = str(report_path)
        self._write_health_state(result)
        return result

    def _probe(
        self,
        name: str,
        fn: Callable[[], Dict[str, Any]],
        required_fields: List[str],
        retry_delay_sec: float = 1.0,
    ) -> Dict[str, Any]:
        first = self._run_probe_once(name, fn, required_fields)
        if first["success"] and first["field_completeness"] >= 1.0 and not first["is_cached"] and not first["has_quality_gap"]:
            first["health_status"] = "healthy"
            return first
        if first["success"]:
            first["health_status"] = self._classify_success_status(first)
            return first

        if retry_delay_sec > 0:
            time.sleep(retry_delay_sec)
        second = self._run_probe_once(name, fn, required_fields)
        if second["success"]:
            second["health_status"] = "unstable"
            second["errors"] = first["errors"] + second["errors"]
            return second

        second["health_status"] = "failed"
        second["errors"] = first["errors"] + second["errors"]
        self._log_error("health", name, second["errors"])
        return second

    def _run_probe_once(self, name: str, fn: Callable[[], Dict[str, Any]], required_fields: List[str]) -> Dict[str, Any]:
        started = time.monotonic()
        try:
            response = fn()
        except Exception as exc:
            response = {"success": False, "error": str(exc), "data": None}
        elapsed_ms = round((time.monotonic() - started) * 1000, 2)
        data = response.get("data") or {}
        if isinstance(data, dict) and "availability" in data and data.get("availability") in {"post_close_only", "conditional_only"}:
            unsupported = not data.get("items") and not data.get("eligible", True)
        else:
            unsupported = False
        present = [field for field in required_fields if self._has_field(data, field)]
        completeness = round(len(present) / len(required_fields), 4) if required_fields else 1.0
        quality_gaps = self._quality_gaps(data, response)
        errors = []
        if response.get("error"):
            errors.append(str(response.get("error")))
        errors.extend(str(item) for item in response.get("errors", []) if item)
        errors.extend(gap for gap in quality_gaps if gap not in errors)
        return {
            "interface": name,
            "success": bool(response.get("success")),
            "health_status": "unsupported_now" if unsupported else "failed",
            "elapsed_ms": elapsed_ms,
            "source": response.get("source", "unknown"),
            "fetched_at": response.get("fetched_at") or response.get("timestamp") or datetime.now().isoformat(timespec="seconds"),
            "data_timestamp": self._infer_data_timestamp(data),
            "is_cached": bool(response.get("is_cached") or response.get("source") == "cache"),
            "cache_age_hours": response.get("cache_age_hours"),
            "field_completeness": completeness,
            "required_fields": required_fields,
            "present_fields": present,
            "missing_fields": [field for field in required_fields if field not in present],
            "quality_gaps": quality_gaps,
            "has_quality_gap": bool(quality_gaps),
            "usable_for_trade": bool(response.get("success")) and completeness >= 0.7 and not unsupported and not quality_gaps,
            "errors": errors,
        }

    def _classify_success_status(self, probe: Dict[str, Any]) -> str:
        if probe["is_cached"] or probe["field_completeness"] < 1.0 or probe.get("has_quality_gap"):
            return "degraded"
        return "healthy"

    def _quality_gaps(self, data: Any, response: Dict[str, Any]) -> List[str]:
        gaps: List[str] = []
        if response.get("data_status") == "degraded":
            gaps.append("接口成功但数据状态为 degraded")
        if isinstance(data, dict):
            breadth = data.get("breadth")
            if isinstance(breadth, dict) and breadth.get("status") == "missing":
                gaps.append(breadth.get("reason") or "市场广度字段存在但不可用")
        return gaps

    def _has_field(self, data: Any, field: str) -> bool:
        if not isinstance(data, dict):
            return False
        value = data.get(field)
        if value not in (None, "", [], {}):
            return True
        if field == "industry" and isinstance(data.get("sector_heat"), dict):
            return bool(data.get("industry"))
        return False

    def _infer_data_timestamp(self, data: Any) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        for key in ("timestamp", "fetched_at", "date", "latest_date", "as_of_date", "requested_date"):
            value = data.get(key)
            if value:
                return str(value)
        return None

    def _call_skill(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "error", "errors": ["stock-skill unavailable"]}

    def _run_fast_with_symbol_cache(
        self,
        symbol: str,
        data_type: str,
        args: List[str],
        max_age_hours: int,
        **cache_params: Any,
    ) -> Dict[str, Any]:
        circuit = self._circuit_status(symbol, data_type)
        if circuit.get("open"):
            cached = self._get_cache(symbol, data_type, max_age_hours=max_age_hours, **cache_params)
            if cached:
                cached["errors"] = self._compact_errors([
                    circuit.get("reason"),
                    *cached.get("errors", []),
                ])
                cached["source"] = "cache-after-circuit-breaker"
                return cached
            return self._circuit_failure(symbol, data_type, circuit)

        result = self._run_fast(*args)
        if result.get("success"):
            self._save_cache(symbol, data_type, result.get("data", {}), **cache_params)
            return result
        cached = self._get_cache(symbol, data_type, max_age_hours=max_age_hours, **cache_params)
        if cached:
            cached["errors"] = [result.get("error", f"{data_type} failed")] + cached.get("errors", [])
            return cached
        return result

    def _run_fast_with_global_cache(self, data_type: str, *args: str, max_age_hours: int) -> Dict[str, Any]:
        circuit = self._circuit_status("global", data_type)
        if circuit.get("open"):
            cached = self._get_global_cache(data_type, max_age_hours=max_age_hours)
            if cached:
                cached["errors"] = self._compact_errors([
                    circuit.get("reason"),
                    *cached.get("errors", []),
                ])
                cached["source"] = "cache-after-circuit-breaker"
                return cached
            return self._circuit_failure("global", data_type, circuit)

        result = self._run_fast(*args)
        if result.get("success"):
            self._save_global_cache(data_type, result.get("data", {}))
            return result
        cached = self._get_global_cache(data_type, max_age_hours=max_age_hours)
        if cached:
            cached["errors"] = [result.get("error", f"{data_type} failed")] + cached.get("errors", [])
            return cached
        return result

    def _call_browser(self, symbol: str) -> Dict[str, Any]:
        return self._call_browser_script(symbol, "auto")

    def _call_browser_kline(self, symbol: str, days: int) -> Dict[str, Any]:
        return self._call_browser_script(symbol, "kline", str(days))

    def _call_browser_intraday(self, symbol: str) -> Dict[str, Any]:
        return self._call_browser_script(symbol, "intraday")

    def _call_browser_market(self) -> Dict[str, Any]:
        return self._call_browser_script("000001", "market")

    def _market_has_valid_indices(self, result: Dict[str, Any]) -> bool:
        if not result.get("success"):
            return False
        data = result.get("data") or {}
        indices = data.get("indices") or []
        valid_count = 0
        for item in indices:
            if not isinstance(item, dict):
                continue
            price = item.get("price") or item.get("最新价") or item.get("close")
            error = item.get("error")
            try:
                if price is not None and float(price) > 0 and not error:
                    valid_count += 1
            except (TypeError, ValueError):
                continue
        return valid_count >= 2

    def _has_valid_breadth(self, breadth: Dict[str, Any]) -> bool:
        return breadth.get("advancers") is not None and breadth.get("decliners") is not None

    def _call_browser_script(self, symbol: str, *args: str) -> Dict[str, Any]:
        cmd = ["python3", str(self.browser_script), symbol, *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.workspace),
            )
            output = result.stdout.strip() or result.stderr.strip()
            if not output:
                return {
                    "success": False,
                    "source": "browser",
                    "data": None,
                    "quality_score": 0,
                    "is_cached": False,
                    "errors": ["browser: empty output"],
                    "failed_sources": ["browser"],
                    "data_status": "error",
                }
            payload = json.loads(output)
            payload.setdefault("errors", [])
            payload.setdefault("failed_sources", [])
            payload.setdefault("data_status", "ok" if payload.get("success") else "error")
            if not payload.get("success"):
                payload["failed_sources"] = [payload.get("source", "browser")]
                payload["errors"] = payload.get("errors", []) or [payload.get("error", "browser failed")]
            return payload
        except Exception as exc:
            return {
                "success": False,
                "source": "browser",
                "data": None,
                "quality_score": 0,
                "is_cached": False,
                "errors": [f"browser: {exc}"],
                "failed_sources": ["browser"],
                "data_status": "error",
            }

    def _compact_errors(self, errors: List[Any]) -> List[str]:
        compacted = []
        for error in errors:
            if error in (None, ""):
                continue
            text = str(error)
            if text not in compacted:
                compacted.append(text)
        return compacted

    def _write_health_state(self, health_report: Dict[str, Any], ttl_hours: int = 6) -> None:
        interfaces = {}
        for item in health_report.get("interfaces", []):
            name = item.get("interface")
            if not name:
                continue
            status = item.get("health_status")
            usable = bool(item.get("usable_for_trade"))
            open_circuit = status == "failed"
            interfaces[name] = {
                "health_status": status,
                "usable_for_trade": usable,
                "open_circuit": open_circuit,
                "source": item.get("source"),
                "fetched_at": item.get("fetched_at"),
                "errors": item.get("errors", []),
                "quality_gaps": item.get("quality_gaps", []),
            }
        state = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "ttl_hours": ttl_hours,
            "summary": health_report.get("summary", {}),
            "interfaces": interfaces,
        }
        self.health_state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_health_state(self) -> Optional[Dict[str, Any]]:
        if not self.health_state_path.exists():
            return None
        try:
            state = json.loads(self.health_state_path.read_text(encoding="utf-8"))
            generated_at = datetime.fromisoformat(str(state.get("generated_at")))
            ttl_hours = int(state.get("ttl_hours") or 6)
            if (datetime.now() - generated_at).total_seconds() > ttl_hours * 3600:
                return None
            return state
        except Exception:
            return None

    def _circuit_status(self, symbol: str, data_type: str) -> Dict[str, Any]:
        state = self._load_health_state()
        if not state:
            return {"open": False}
        interface_names = self._interface_names_for_data_type(symbol, data_type)
        interfaces = state.get("interfaces", {})
        for interface_name in interface_names:
            item = interfaces.get(interface_name)
            if item and item.get("open_circuit"):
                errors = item.get("errors") or []
                reason = errors[0] if errors else f"{interface_name} 最近健康检查失败"
                return {
                    "open": True,
                    "interface": interface_name,
                    "reason": f"熔断: {reason}",
                    "health_status": item.get("health_status"),
                    "source": item.get("source"),
                }
        return {"open": False}

    def _interface_names_for_data_type(self, symbol: str, data_type: str) -> List[str]:
        normalized = str(symbol).zfill(6) if str(symbol).isdigit() else str(symbol)
        if data_type in {"sector", "sector_ctx"}:
            return [f"sector:{normalized}"]
        if data_type == "finance":
            return [f"finance:{normalized}"]
        if data_type == "flow":
            return [f"flow:{normalized}"]
        if data_type == "flow_hist":
            return [f"flow-hist:{normalized}:10", f"flow-hist:{normalized}"]
        if data_type == "margin":
            return [f"margin:{normalized}"]
        if data_type == "north_south":
            return ["north-south"]
        if data_type == "market":
            return ["market"]
        return [f"{data_type}:{normalized}", data_type]

    def _circuit_failure(self, symbol: str, data_type: str, circuit: Dict[str, Any]) -> Dict[str, Any]:
        reason = circuit.get("reason") or "接口近期健康检查失败，已短期熔断"
        return {
            "success": False,
            "source": "health-circuit-breaker",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "cache_age_hours": None,
            "errors": [reason],
            "failed_sources": [circuit.get("interface") or data_type],
            "data_status": "error",
            "error": reason,
            "symbol": symbol,
        }

    def _normalize_skill_result(self, result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        top_status = result.get("status")
        if top_status == "error" and "data" not in result:
            return {
                "success": False,
                "source": "stock-skill",
                "data": None,
                "quality_score": 0,
                "is_cached": False,
                "errors": result.get("errors", ["stock-skill: unknown failure"]),
                "failed_sources": ["stock-skill"],
                "data_status": "error",
            }

        response = result.get("data", {})
        data_status = response.get("status", "error")
        payload = response.get("data") or {}
        meta = response.get("meta") or {}
        quality = response.get("quality") or {}
        error = response.get("error") or {}
        source = meta.get("source") or "stock-skill"
        success = data_status in {"ok", "degraded"} and bool(payload)

        normalized = {
            "success": success,
            "source": source,
            "data": payload if success else None,
            "quality_score": int(round(float(quality.get("score", 0)))),
            "is_cached": source == "cache",
            "cache_age_hours": None,
            "errors": [],
            "failed_sources": error.get("failed_sources", []),
            "data_status": data_status,
        }

        if success:
            normalized["errors"] = [
                issue for issue in quality.get("issues", []) if issue not in {"cache_hit", "fallback_used"}
            ]
            return normalized

        message = error.get("message") or "stock-skill unavailable"
        issues = quality.get("issues", [])
        normalized["errors"] = [f"stock-skill: {message}"] + [
            f"stock-skill issue: {issue}" for issue in issues if issue != message
        ]
        if not normalized["failed_sources"]:
            normalized["failed_sources"] = ["stock-skill"]
        return normalized

    def _get_cache(
        self,
        symbol: str,
        data_type: str,
        max_age_hours: int = 24,
        **cache_params: Any,
    ) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / symbol / self._cache_name(data_type, **cache_params)
        if not cache_file.exists():
            return None

        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        if age_hours > max_age_hours:
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None

        return {
            "success": True,
            "source": "cache",
            "data": data,
            "quality_score": max(40, 80 - int(age_hours * 2)),
            "is_cached": True,
            "cache_age_hours": round(age_hours, 2),
            "errors": [f"使用 {age_hours:.1f} 小时前缓存"],
            "failed_sources": [],
            "data_status": "degraded",
        }

    def _get_global_cache(self, data_type: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_dir / "_global" / f"{data_type}.json"
        if not cache_file.exists():
            return None

        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        if age_hours > max_age_hours:
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None

        return {
            "success": True,
            "source": "cache",
            "data": data,
            "quality_score": max(40, 80 - int(age_hours * 2)),
            "is_cached": True,
            "cache_age_hours": round(age_hours, 2),
            "errors": [f"使用 {age_hours:.1f} 小时前全局缓存"],
            "failed_sources": [],
            "data_status": "degraded",
        }

    def _save_cache(
        self,
        symbol: str,
        data_type: str,
        data: Dict[str, Any],
        **cache_params: Any,
    ) -> None:
        cache_dir = self.cache_dir / symbol
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / self._cache_name(data_type, **cache_params)
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _save_global_cache(self, data_type: str, data: Dict[str, Any]) -> None:
        cache_dir = self.cache_dir / "_global"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{data_type}.json"
        cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cache_name(self, data_type: str, **cache_params: Any) -> str:
        if data_type == "flow_hist":
            days = int(cache_params.get("days") or 10)
            return f"{data_type}_{days}.json"
        if data_type == "intraday":
            interval = str(cache_params.get("interval") or "1").strip()
            days = int(cache_params.get("days") or 3)
            return f"{data_type}_{interval}_{days}.json"
        if data_type != "kline":
            return f"{data_type}.json"
        timeframe = str(cache_params.get("timeframe") or "1d").strip()
        limit = int(cache_params.get("limit") or 30)
        return f"{data_type}_{timeframe}_{limit}.json"

    def _final_failure(self, symbol: str, data_type: str, errors: List[str]) -> Dict[str, Any]:
        self._log_error(symbol, data_type, errors)
        return {
            "success": False,
            "source": "unavailable",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "cache_age_hours": None,
            "errors": errors,
            "failed_sources": [],
            "data_status": "error",
        }

    def _log_error(self, symbol: str, data_type: str, errors: List[str]) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol,
            "data_type": data_type,
            "errors": errors,
            "status": "error",
        }
        with self.error_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._log_error_sqlite(entry)

    def _log_error_sqlite(self, entry: Dict[str, Any]) -> None:
        if not self.db_path.exists():
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO data_fetch_failures (
                        timestamp, stock_code, data_type, errors, context, retry_count, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["timestamp"],
                        entry.get("symbol"),
                        entry.get("data_type"),
                        json.dumps(entry.get("errors", []), ensure_ascii=False),
                        json.dumps({"source": "stock_client"}, ensure_ascii=False),
                        0,
                        entry.get("status", "error"),
                    ),
                )
                conn.commit()
        except Exception:
            return


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 stock_client.py <命令> [参数...]", file=sys.stderr)
        print("  命令: quote quotes kline klinex market breadth market-flow market-proxy sector finance finance-trend margin flow flow-hist north-south lhb intraday alternative analysis snapshot health", file=sys.stderr)
        print("  snapshot <代码1> <代码2>...  自选股快照（行情+PE/PB+市值）", file=sys.stderr)
        print("  flow-hist <代码> [天数]     个股资金流向历史", file=sys.stderr)
        print("  north-south                 北向/南向资金流向", file=sys.stderr)
        print("  lhb <代码>                  个股龙虎榜记录", file=sys.stderr)
        print("  alternative <代码> [名称]    非常规公开数据入口探测", file=sys.stderr)
        raise SystemExit(1)

    cmd = sys.argv[1]
    client = StockDataClient()

    dispatch = {
        "quote": lambda: client.get_quote(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "quotes": lambda: client.get_quotes_batch(sys.argv[2:]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "kline": lambda: client.get_kline(sys.argv[2], int(sys.argv[3]) if len(sys.argv) >= 4 else 60) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "klinex": lambda: client.get_kline_period(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "daily", int(sys.argv[4]) if len(sys.argv) >= 5 else 120) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "market": client.get_market,
        "breadth": client.get_market_breadth,
        "market-flow": client.get_market_flow,
        "market-proxy": client.get_market_proxy,
        "sector": lambda: client.get_sector(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "finance": lambda: client.get_finance(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "finance-trend": lambda: client.get_financial_trend(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "margin": lambda: client.get_margin(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "flow": lambda: client.get_flow(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "flow-hist": lambda: client.get_flow_hist(sys.argv[2], int(sys.argv[3]) if len(sys.argv) >= 4 else 10) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "north-south": client.get_north_south,
        "lhb": lambda: client.get_lhb(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "intraday": lambda: client.get_intraday(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "1", int(sys.argv[4]) if len(sys.argv) >= 5 else 3) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "alternative": lambda: client.get_alternative_data(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else None) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "analysis": lambda: client.get_analysis_payload(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "snapshot": lambda: client._run_fast("snapshot", *sys.argv[2:]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "watchlist": lambda: client._run_fast("watchlist", *sys.argv[2:]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "health": lambda: client.health_check(sys.argv[2:] or None),
    }

    handler = dispatch.get(cmd)
    if not handler:
        print(f"未知命令: {cmd}", file=sys.stderr)
        raise SystemExit(1)

    result = handler()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("success"):
        symbol = sys.argv[2] if len(sys.argv) >= 3 else "global"
        client._log_error(symbol, cmd, [result.get("error", "unknown")])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
