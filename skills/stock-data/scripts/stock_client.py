#!/usr/bin/env python3
"""
Win_Stock 统一数据客户端
正式入口：stock-skill -> browser_fetch -> cache -> 失败记录
本轮重点：彻底修好 quote 链路；其他类型诚实返回当前能力。
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
        self.workspace = Path(workspace or "/Volumes/zhangstExtern/openclaw/workspace/win_stock")
        self.skill_script = self.workspace / "skills/stock-skill/scripts/run.py"
        self.browser_script = self.workspace / "skills/stock-data/scripts/browser_fetch.py"
        self.cache_dir = self.workspace / "data" / "cache"
        self.error_log = self.workspace / "logs" / "errors" / "data_fetch_failures.jsonl"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.error_log.parent.mkdir(parents=True, exist_ok=True)

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
        if browser_result["success"]:
            self._save_cache(symbol, "quote", browser_result["data"])
            browser_result["errors"] = errors + browser_result.get("errors", [])
            return browser_result
        errors.extend(browser_result["errors"])

        cached = self._get_cache(symbol, "quote")
        if cached:
            cached["errors"] = errors + cached.get("errors", [])
            return cached

        return self._final_failure(symbol, "quote", errors)

    def get_kline(self, symbol: str, timeframe: str = "1d", limit: int = 30) -> Dict[str, Any]:
        skill_result = self._call_skill(
            "kline.get",
            {
                "symbol": symbol,
                "market": "CN-A",
                "timeframe": timeframe,
                "limit": limit,
            },
        )
        normalized = self._normalize_skill_result(skill_result, symbol)
        if normalized["success"]:
            if normalized["source"] != "cache":
                self._save_cache(
                    symbol,
                    "kline",
                    normalized["data"],
                    timeframe=timeframe,
                    limit=limit,
                )
            return normalized

        cached = self._get_cache(symbol, "kline", timeframe=timeframe, limit=limit)
        if cached:
            cached["errors"] = normalized["errors"] + cached.get("errors", [])
            return cached

        errors = normalized["errors"] + ["K线数据当前未实现 browser 降级"]
        return self._final_failure(symbol, "kline", errors)

    def _call_skill(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        cmd = [
            "python3",
            str(self.skill_script),
            "run",
            "--skill",
            "stock",
            "--action",
            action,
            "--input",
            json.dumps(input_data, ensure_ascii=False),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace),
            )
            output = result.stdout.strip() or result.stderr.strip()
            if not output:
                return {"status": "error", "errors": ["stock-skill: empty output"]}
            return json.loads(output)
        except Exception as exc:
            return {"status": "error", "errors": [f"stock-skill: {exc}"]}

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
        log_entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol,
            "data_type": data_type,
            "errors": errors,
            "status": "pending",
        }
        with self.error_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 stock_client.py <symbol>", file=sys.stderr)
        raise SystemExit(1)

    symbol = sys.argv[1]
    client = StockDataClient()
    result = client.get_quote(symbol)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
