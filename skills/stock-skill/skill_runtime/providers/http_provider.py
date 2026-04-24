from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import requests

from shared.utils import infer_exchange, limit_items, normalize_symbol


class HttpProvider:
    name = "http"

    def __init__(self, timeout_sec: float = 6.0) -> None:
        self.timeout_sec = timeout_sec

    def quote_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        market = infer_exchange(symbol).lower()
        secid = f"{1 if market == 'sh' else 0}.{symbol}"
        response = requests.get(
            "https://push2.eastmoney.com/api/qt/stock/get",
            params={
                "secid": secid,
                "fields": "f57,f58,f43,f44,f45,f46,f60,f47,f48,f169,f170,f168",
            },
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        data = response.json()["data"]
        price = float(data["f43"]) / 100
        pre_close = float(data["f60"]) / 100
        change = float(data["f169"]) / 100
        return {
            "symbol": symbol,
            "name": data["f58"],
            "price": price,
            "change": change,
            "change_pct": float(data["f170"]) / 100,
            "open": float(data["f46"]) / 100,
            "high": float(data["f44"]) / 100,
            "low": float(data["f45"]) / 100,
            "pre_close": pre_close,
            "volume": int(data["f47"]),
            "amount": float(data["f48"]),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "turnover_rate": float(data.get("f168") or 0) / 100,
        }

    def quotes_batch_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbols = payload.get("symbols") or []
        items = [self.quote_get({"symbol": symbol}) for symbol in symbols]
        advancers = sum(1 for item in items if item["change_pct"] > 0)
        decliners = sum(1 for item in items if item["change_pct"] < 0)
        return {
            "items": limit_items(items, payload.get("limit")),
            "universe_size": len(items),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "advancers": advancers,
            "decliners": decliners,
            "flat_count": len(items) - advancers - decliners,
            "limit_up_count": sum(1 for item in items if item["change_pct"] >= 9.5),
            "limit_down_count": sum(1 for item in items if item["change_pct"] <= -9.5),
        }

    def news_market_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.get(
            "https://np-listapi.eastmoney.com/comm/web/getFastNewsList",
            params={"client": "web", "biz": "web_724", "pageSize": payload.get("limit", 20)},
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        data = response.json().get("data", {}).get("fastNewsList", [])
        events: List[Dict[str, Any]] = []
        for item in data:
            events.append(
                {
                    "title": item.get("title", ""),
                    "source": item.get("mediaName", "eastmoney"),
                    "publish_time": item.get("showTime", ""),
                }
            )
        return {"events": events}
