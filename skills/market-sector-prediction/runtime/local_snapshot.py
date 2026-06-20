from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

from capital_flow import CapitalFlowBuilder
from data_cache import PredictionDataCache


CN_TZ = timezone(timedelta(hours=8))


class LocalSnapshotBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.stock_client = root / "skills" / "stock-data" / "scripts" / "stock_client.py"
        self.fast_data = root / "skills" / "stock-data" / "scripts" / "fast_data.py"
        self.cache = PredictionDataCache(root)
        self.capital_flow = CapitalFlowBuilder(root)

    def market(self) -> Dict[str, Any]:
        result = self._run_stock_client(["market"], timeout=18)
        if not result.get("success"):
            result = self._run_browser_market()
        data = result.get("data") or {}
        breadth = data.get("breadth") or {}
        fallback_breadth = dict(breadth) if self._has_any_breadth(breadth) else {}
        if not self._has_valid_breadth(breadth):
            proxy_data = self._read_global_cache("market_proxy", max_age_hours=2) or {}
            if not proxy_data:
                proxy_result = self._run_stock_client(["market-proxy"], timeout=8)
                proxy_data = proxy_result.get("data") or {}
            proxy_breadth = proxy_data.get("breadth") or {}
            if self._is_better_breadth(proxy_breadth, fallback_breadth):
                fallback_breadth = proxy_breadth
            if self._has_valid_breadth(proxy_breadth):
                breadth = proxy_breadth
        if not self._has_valid_breadth(breadth):
            breadth_result = self._run_stock_client(["breadth"], timeout=8)
            breadth_data = breadth_result.get("data") or {}
            if self._is_better_breadth(breadth_data, fallback_breadth):
                fallback_breadth = breadth_data
            if self._has_valid_breadth(breadth_data):
                breadth = breadth_data
        if not self._has_valid_breadth(breadth) and fallback_breadth:
            breadth = fallback_breadth
        indices = data.get("indices") or []
        indices = self._attach_index_ohlcv(indices)
        payload = {
            "status": "ok" if result.get("success") and indices else "degraded",
            "trading_date": self._latest_date(indices),
            "indices": indices,
            "market_breadth": breadth,
            "has_amount": any(item.get("amount") is not None or item.get("volume") is not None for item in indices)
            or breadth.get("total_amount") is not None,
            "has_breadth": breadth.get("advancers") is not None and breadth.get("decliners") is not None,
            "capital_flow": self.capital_flow.market(),
            "source": result.get("source", "stock_client"),
            "errors": result.get("errors", []) + ([result.get("error")] if result.get("error") else []),
        }
        if indices:
            payload["cache_path"] = self.cache.write("market_snapshot_latest", payload)
            return payload
        cached = self.cache.read("market_snapshot_latest", max_age_sec=7200, allow_stale=True)
        if cached and cached.get("data"):
            stale_payload = dict(cached["data"])
            stale_payload["status"] = "degraded"
            stale_payload["source"] = "prediction_cache"
            stale_payload["stale"] = cached["stale"]
            stale_payload["cache_age_sec"] = cached["age_sec"]
            stale_payload["errors"] = payload["errors"] + [f"使用预测缓存: {cached['path']}"]
            return stale_payload
        return payload

    def _has_valid_breadth(self, breadth: Dict[str, Any]) -> bool:
        if not self._has_any_breadth(breadth):
            return False
        if breadth.get("stale"):
            return False
        universe_size = self._num(breadth.get("universe_size"))
        if bool(breadth.get("sampled")):
            return False
        if universe_size is not None and universe_size < 1000:
            return False
        advancers = self._num(breadth.get("advancers"))
        decliners = self._num(breadth.get("decliners"))
        if advancers is None or decliners is None:
            return False
        if advancers < 0 or decliners < 0:
            return False
        if advancers + decliners <= 0:
            return False
        return True

    def _has_any_breadth(self, breadth: Dict[str, Any]) -> bool:
        return breadth.get("advancers") is not None and breadth.get("decliners") is not None

    def _is_better_breadth(self, candidate: Dict[str, Any], current: Dict[str, Any]) -> bool:
        if not self._has_any_breadth(candidate):
            return False
        if not current:
            return True
        if self._has_valid_breadth(candidate) and not self._has_valid_breadth(current):
            return True
        candidate_size = self._num(candidate.get("universe_size")) or 0
        current_size = self._num(current.get("universe_size")) or 0
        if candidate_size and candidate_size > current_size:
            return True
        return False

    def _read_global_cache(self, data_type: str, max_age_hours: int) -> Dict[str, Any] | None:
        cache_file = self.root / "data" / "cache" / "_global" / f"{data_type}.json"
        if not cache_file.exists():
            return None
        try:
            age_hours = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() / 3600
            if age_hours > max_age_hours:
                return None
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data = dict(data)
                data["cache_age_hours"] = round(age_hours, 2)
                data["source"] = data.get("source") or "global_cache"
                data["is_cached"] = True
                return data
        except Exception:
            return None
        return None

    def _num(self, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return None

    def sector(self, sector: str, taxonomy_payload: Dict[str, Any]) -> Dict[str, Any]:
        heat = self._run_fast_data(["heat", sector], timeout=120)
        heat_data = heat.get("data") or {}
        members = heat_data.get("members") or []
        member_codes = [str(item.get("code", "")).zfill(6) for item in members if item.get("code")]
        if taxonomy_payload.get("status") == "ok":
            from sector_taxonomy import SectorTaxonomyResolver

            taxonomy_payload = SectorTaxonomyResolver(self.root).resolve(
                sector,
                taxonomy_payload.get("sector_taxonomy"),
                members=members,
            )
        payload = {
            "status": "ok" if taxonomy_payload.get("status") == "ok" and members else "blocked",
            "trading_date": datetime.now(CN_TZ).strftime("%Y-%m-%d"),
            "sector": sector,
            "sector_taxonomy": taxonomy_payload.get("sector_taxonomy"),
            "member_count": len(members),
            "members_snapshot_path": taxonomy_payload.get("members_snapshot_path"),
            "member_codes": member_codes,
            "sector_heat": heat_data,
            "has_sector_quote": bool(heat.get("success") and heat_data),
            "has_members": bool(members),
            "capital_flow": self.capital_flow.sector(member_codes),
            "errors": heat.get("errors", []) + ([heat.get("error")] if heat.get("error") else []),
        }
        cache_key = f"sector_snapshot_{taxonomy_payload.get('sector_taxonomy', 'unknown')}_{sector}"
        if members:
            payload["cache_path"] = self.cache.write(cache_key, payload)
            return payload
        cached = self.cache.read(cache_key, max_age_sec=7200, allow_stale=True)
        if cached and cached.get("data"):
            stale_payload = dict(cached["data"])
            stale_payload["status"] = "degraded"
            stale_payload["source"] = "prediction_cache"
            stale_payload["stale"] = cached["stale"]
            stale_payload["cache_age_sec"] = cached["age_sec"]
            stale_payload["errors"] = payload["errors"] + [f"使用预测缓存: {cached['path']}"]
            return stale_payload
        return payload

    def _run_stock_client(self, args: list[str], timeout: int) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                [sys.executable, str(self.stock_client), *args],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if not completed.stdout.strip():
                return {"success": False, "error": completed.stderr.strip() or "empty stock_client output"}
            return json.loads(completed.stdout)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _run_fast_data(self, args: list[str], timeout: int) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                [sys.executable, str(self.fast_data), *args],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if not completed.stdout.strip():
                return {"success": False, "error": completed.stderr.strip() or "empty fast_data output"}
            return json.loads(completed.stdout)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _run_browser_market(self) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                [sys.executable, str(self.root / "skills" / "stock-data" / "scripts" / "browser_fetch.py"), "000001", "market"],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if not completed.stdout.strip():
                return {"success": False, "error": completed.stderr.strip() or "empty browser market output"}
            return json.loads(completed.stdout)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _attach_index_ohlcv(self, indices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        aliases = {"000001": "sh000001", "399001": "sz399001", "399006": "sz399006"}
        enriched = []
        for item in indices:
            payload = dict(item)
            code = str(item.get("code") or "")
            alias = aliases.get(code, code)
            kline_result = self._run_browser_kline(alias, 60) or {}
            kline_data = kline_result.get("data") or {}
            bars = kline_data.get("bars") or []
            if bars:
                payload["ohlcv"] = bars
            enriched.append(payload)
        return enriched

    def _run_browser_kline(self, symbol: str, days: int) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                [sys.executable, str(self.root / "skills" / "stock-data" / "scripts" / "browser_fetch.py"), symbol, "kline", str(days)],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=20,
            )
            if not completed.stdout.strip():
                return {"success": False, "error": completed.stderr.strip() or "empty browser_fetch output"}
            return json.loads(completed.stdout)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _latest_date(self, indices: list[dict[str, Any]]) -> str:
        dates = [str(item.get("date")) for item in indices if item.get("date")]
        return max(dates) if dates else datetime.now(CN_TZ).strftime("%Y-%m-%d")
