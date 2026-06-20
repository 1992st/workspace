from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class CapitalFlowBuilder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.stock_client = root / "skills" / "stock-data" / "scripts" / "stock_client.py"

    def market(self) -> Dict[str, Any]:
        errors = []
        items = []
        result = self._run(["north-south"], timeout=8)
        data = result.get("data") or {}
        summary = data.get("summary") or {}
        north_net = self._num(summary.get("north_net"))
        errors.extend(self._errors(result))
        source_parts = [result.get("source", "stock_client")]
        if north_net is not None:
            direction = "inflow" if north_net > 0 else "outflow" if north_net < 0 else "flat"
            items.append(
                {
                    "name": "北向资金",
                    "net": north_net,
                    "unit": "亿元",
                    "direction": direction,
                    "date": data.get("latest_date", ""),
                    "proxy": False,
                }
            )

        market_flow = self._run(["market-flow"], timeout=8)
        flow_data = market_flow.get("data") or {}
        errors.extend(self._errors(market_flow))
        source_parts.append(market_flow.get("source", "stock_client"))
        proxy_net = self._num(flow_data.get("net"))
        if proxy_net is not None:
            items.append(
                {
                    "name": flow_data.get("name") or "全市场量价资金代理",
                    "net": proxy_net,
                    "unit": flow_data.get("unit") or "proxy_score",
                    "direction": flow_data.get("direction") or ("inflow" if proxy_net > 0 else "outflow" if proxy_net < 0 else "flat"),
                    "date": flow_data.get("date", ""),
                    "proxy": True,
                    "sample_size": flow_data.get("sample_size"),
                    "total_amount": flow_data.get("total_amount"),
                    "note": flow_data.get("note"),
                }
            )
        if proxy_net is None:
            proxy_data = self._read_global_cache("market_proxy", max_age_hours=2) or {}
            if proxy_data:
                proxy_flow = proxy_data.get("flow") or {}
                source_parts.append("global_cache")
            else:
                proxy_result = self._run(["market-proxy"], timeout=8)
                proxy_data = proxy_result.get("data") or {}
                proxy_flow = proxy_data.get("flow") or {}
                errors.extend(self._errors(proxy_result))
                source_parts.append(proxy_result.get("source", "stock_client"))
            sample_net = self._num(proxy_flow.get("net"))
            if sample_net is not None:
                items.append(
                    {
                        "name": proxy_flow.get("name") or "抽样量价资金代理",
                        "net": sample_net,
                        "unit": proxy_flow.get("unit") or "proxy_score",
                        "direction": proxy_flow.get("direction") or ("inflow" if sample_net > 0 else "outflow" if sample_net < 0 else "flat"),
                        "date": proxy_flow.get("date", ""),
                        "proxy": True,
                        "sample_size": proxy_flow.get("sample_size"),
                        "total_amount": proxy_flow.get("total_amount"),
                        "note": proxy_flow.get("note"),
                    }
                )
        if not items:
            return {
                "status": "missing",
                "source": "+".join(part for part in source_parts if part),
                "items": [],
                "errors": errors,
            }
        return {
            "status": "ok",
            "source": "+".join(part for part in source_parts if part),
            "items": items,
            "errors": errors,
        }

    def sector(self, codes: List[str]) -> Dict[str, Any]:
        items = []
        errors = []
        for code in codes[:8]:
            normalized = str(code).split(".")[0].zfill(6)
            result = self._run(["flow", normalized], timeout=90)
            data = result.get("data") or {}
            net = self._num(data.get("main_net_inflow"))
            if net is None:
                errors.extend(self._errors(result) or [f"{normalized} 主力资金缺失"])
                continue
            items.append(
                {
                    "code": normalized,
                    "net": net,
                    "unit": "元",
                    "direction": "inflow" if net > 0 else "outflow" if net < 0 else "flat",
                    "date": data.get("date", ""),
                }
            )
        if not items:
            return {"status": "missing", "source": "stock_client", "items": [], "errors": errors}
        total = round(sum(item["net"] for item in items), 2)
        return {
            "status": "ok",
            "source": "stock_client",
            "items": items,
            "summary": {
                "sample_size": len(items),
                "main_net_total": total,
                "direction": "inflow" if total > 0 else "outflow" if total < 0 else "flat",
            },
            "errors": errors,
        }

    def _run(self, args: list[str], timeout: int) -> Dict[str, Any]:
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

    def _errors(self, result: Dict[str, Any]) -> list[str]:
        return result.get("errors", []) + ([result.get("error")] if result.get("error") else [])

    def _read_global_cache(self, data_type: str, max_age_hours: int) -> Dict[str, Any] | None:
        cache_file = self.root / "data" / "cache" / "_global" / f"{data_type}.json"
        if not cache_file.exists():
            return None
        try:
            age_hours = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() / 3600
            if age_hours > max_age_hours:
                return None
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _num(self, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return None
