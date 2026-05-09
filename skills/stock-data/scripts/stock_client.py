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
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StockDataClient:
    def __init__(self, workspace: Optional[str] = None) -> None:
        self.workspace = Path(workspace) if workspace else Path(__file__).resolve().parents[3]
        self.fast_script = self.workspace / "skills/stock-data/scripts/fast_data.py"
        self.browser_script = self.workspace / "skills/stock-data/scripts/browser_fetch.py"
        self.cache_dir = self.workspace / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
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

        browser_result = self._call_browser(symbol)
        if browser_result.get("success"):
            self._save_cache(symbol, "quote", browser_result.get("data", {}))
            browser_result["errors"] = errors + browser_result.get("errors", [])
            return browser_result
        errors.extend(browser_result.get("errors", []))

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
        return self._run_fast("kline", symbol, str(days))

    def get_kline_period(self, symbol: str, period: str = "daily", days: int = 120) -> Dict[str, Any]:
        return self._run_fast("klinex", symbol, period, str(days))

    def get_market(self) -> Dict[str, Any]:
        return self._run_fast("market")

    def get_sector(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast("sector", symbol)

    def get_finance(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast("finance", symbol)

    def get_margin(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast("margin", symbol)

    def get_flow(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast("flow", symbol)

    def get_intraday(self, symbol: str, interval: str = "1", days: int = 3) -> Dict[str, Any]:
        return self._run_fast("intraday", symbol, interval, str(days))

    def get_financial_trend(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast("finance-trend", symbol)

    def get_analysis_payload(self, symbol: str) -> Dict[str, Any]:
        return self._run_fast("analysis", symbol)

    def _call_skill(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "error", "errors": ["stock-skill unavailable"]}

    def _call_browser(self, symbol: str) -> Dict[str, Any]:
        cmd = ["python3", str(self.browser_script), symbol, "auto"]
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

    def _cache_name(self, data_type: str, **cache_params: Any) -> str:
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


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 stock_client.py <命令> [参数...]", file=sys.stderr)
        print("  命令: quote quotes kline klinex market sector finance finance-trend margin flow intraday analysis snapshot", file=sys.stderr)
        print("  snapshot <代码1> <代码2>...  自选股快照（行情+PE/PB+市值）", file=sys.stderr)
        raise SystemExit(1)

    cmd = sys.argv[1]
    client = StockDataClient()

    dispatch = {
        "quote": lambda: client.get_quote(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "quotes": lambda: client.get_quotes_batch(sys.argv[2:]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "kline": lambda: client.get_kline(sys.argv[2], int(sys.argv[3]) if len(sys.argv) >= 4 else 60) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "klinex": lambda: client.get_kline_period(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "daily", int(sys.argv[4]) if len(sys.argv) >= 5 else 120) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "market": client.get_market,
        "sector": lambda: client.get_sector(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "finance": lambda: client.get_finance(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "finance-trend": lambda: client.get_financial_trend(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "margin": lambda: client.get_margin(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "flow": lambda: client.get_flow(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "intraday": lambda: client.get_intraday(sys.argv[2], sys.argv[3] if len(sys.argv) >= 4 else "1", int(sys.argv[4]) if len(sys.argv) >= 5 else 3) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "analysis": lambda: client.get_analysis_payload(sys.argv[2]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "snapshot": lambda: client._run_fast("snapshot", *sys.argv[2:]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
        "watchlist": lambda: client._run_fast("watchlist", *sys.argv[2:]) if len(sys.argv) >= 3 else {"success": False, "error": "缺少代码参数"},
    }

    handler = dispatch.get(cmd)
    if not handler:
        print(f"未知命令: {cmd}", file=sys.stderr)
        raise SystemExit(1)

    result = handler()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("success"):
        symbol = sys.argv[2] if len(sys.argv) >= 2 else "unknown"
        client._log_error(symbol, cmd, [result.get("error", "unknown")])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
