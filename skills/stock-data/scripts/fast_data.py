#!/usr/bin/env python3
"""
Win_Stock 高速数据管道 - 绕过冗余编排，直连数据源 + 智能缓存

关键优化：
1. 缓存全量 A 股行情表到本地，后续报价查询 < 1 秒
2. K 线、板块、财务数据各自独立缓存
3. 所有接口统一 JSON 输出，直接适配上层分析
4. 不抛异常，用失败状态码 + 错误信息返回
"""

from __future__ import annotations

import json
import math
import sys
import time
import urllib.parse
import urllib.request
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


WORKSPACE = Path(__file__).resolve().parents[3]
CACHE_DIR = WORKSPACE / "data" / "cache" / "fast"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缓存有效期
SPOT_CACHE_TTL_SEC = 7200  # 全量行情表 2 小时刷新（拉取全市场约 70s，不宜频繁重刷）
QUOTE_INDIVIDUAL_TTL_SEC = 300  # 单股报价 5 分钟（盘后分析用，无需秒级刷新）
KLINE_TTL_SEC = 3600  # K 线 1 小时
FINANCE_TTL_SEC = 86400  # 财务数据 24 小时
SECTOR_TTL_SEC = 3600  # 板块数据 1 小时
MARKET_TTL_SEC = 7200  # 大盘数据 2 小时
INTRADAY_TTL_SEC = 900  # 分时数据 15 分钟
NORTH_SOUTH_TTL_SEC = 7200  # 北向南向资金 2 小时
LHB_TTL_SEC = 3600  # 龙虎榜 1 小时


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def _read_cache(key: str, ttl_sec: int) -> Optional[Any]:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        stored = payload.get("_ts", 0)
        age = time.time() - stored
        if age > ttl_sec:
            return None
        return payload.get("data")
    except Exception:
        return None


def _read_cache_stale(key: str) -> Optional[Any]:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        data = payload.get("data")
        if isinstance(data, dict):
            data = dict(data)
            data["stale"] = True
            data["cache_age_sec"] = round(time.time() - float(payload.get("_ts", 0)), 2)
        return data
    except Exception:
        return None


def _write_cache(key: str, data: Any) -> None:
    path = _cache_path(key)
    payload = {"_ts": time.time(), "data": data}
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")


def _fail(message: str, **extra: Any) -> Dict[str, Any]:
    return {
        "success": False,
        "error": message,
        "data": None,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **extra,
    }


def _ok(data: Any, source: str = "akshare", **extra: Any) -> Dict[str, Any]:
    fetched_at = datetime.now().isoformat(timespec="seconds")
    return {
        "success": True,
        "error": None,
        "data": data,
        "source": source,
        "timestamp": fetched_at,
        "fetched_at": fetched_at,
        "data_status": "ok" if source != "cache" else "degraded",
        "is_cached": source == "cache",
        **extra,
    }


# ─── 全量行情缓存 ─────────────────────────────────────────────

_full_spot_cache: Optional[Dict[str, Dict[str, Any]]] = None
_full_spot_ts: float = 0


def _load_full_spot() -> Dict[str, Dict[str, Any]]:
    """加载全量 A 股行情（缓存命中则跳过网络请求）"""
    global _full_spot_cache, _full_spot_ts
    now = time.time()

    # 进程内缓存
    if _full_spot_cache is not None and (now - _full_spot_ts) < SPOT_CACHE_TTL_SEC:
        return _full_spot_cache

    # 文件缓存
    cached = _read_cache("full_spot", SPOT_CACHE_TTL_SEC)
    if cached is not None:
        _full_spot_cache = cached
        _full_spot_ts = now
        return cached

    # 网络请求
    import akshare as ak

    try:
        frame = ak.stock_zh_a_spot_em()
        records = frame.to_dict(orient="records")
        spot_map = _normalize_spot_records(records)
    except Exception:
        spot_map = _load_full_spot_eastmoney()

    _full_spot_cache = spot_map
    _full_spot_ts = now
    _write_cache("full_spot", spot_map)
    return spot_map


def _normalize_spot_records(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    spot_map: Dict[str, Dict[str, Any]] = {}
    for row in records:
        code = str(row.get("代码", row.get("f12", ""))).strip()
        if not code:
            continue
        spot_map[code.zfill(6)] = {
            "code": code,
            "name": row.get("名称", row.get("f14", "")),
            "price": _n(row.get("最新价", row.get("f2"))),
            "change_pct": _n(row.get("涨跌幅", row.get("f3"))),
            "change": _n(row.get("涨跌额", row.get("f4"))),
            "volume": _n(row.get("成交量", row.get("f5"))),
            "amount": _n(row.get("成交额", row.get("f6"))),
            "amplitude": _n(row.get("振幅", row.get("f7"))),
            "high": _n(row.get("最高", row.get("f15"))),
            "low": _n(row.get("最低", row.get("f16"))),
            "open": _n(row.get("今开", row.get("f17"))),
            "pre_close": _n(row.get("昨收", row.get("f18"))),
            "volume_ratio": _n(row.get("量比", row.get("f10"))),
            "turnover_rate": _n(row.get("换手率", row.get("f8"))),
            "pe": _n(row.get("市盈率-动态", row.get("f9"))),
            "pb": _n(row.get("市净率", row.get("f23"))),
            "market_cap": _n(row.get("总市值", row.get("f20"))),
            "circulating_cap": _n(row.get("流通市值", row.get("f21"))),
        }
    return spot_map


def _load_full_spot_eastmoney() -> Dict[str, Dict[str, Any]]:
    fields = "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23"
    params = {
        "pn": "1",
        "pz": "6000",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": fields,
        "_": str(int(time.time() * 1000)),
    }
    url = "https://push2.eastmoney.com/api/qt/clist/get?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    records = ((payload.get("data") or {}).get("diff") or [])
    spot_map = _normalize_spot_records(records)
    if not spot_map:
        raise ValueError("eastmoney full spot returned empty")
    return spot_map


def _build_market_breadth_from_spot(spot: Dict[str, Dict[str, Any]], source: str = "akshare_full_spot") -> Dict[str, Any]:
    changes = [row.get("change_pct") for row in spot.values() if isinstance(row.get("change_pct"), (int, float))]
    amounts = [row.get("amount") for row in spot.values() if isinstance(row.get("amount"), (int, float))]
    if not changes:
        raise ValueError("full spot change_pct is empty")
    advancers = sum(1 for value in changes if value > 0)
    decliners = sum(1 for value in changes if value < 0)
    flat_count = sum(1 for value in changes if value == 0)
    universe_size = len(changes)
    up_ratio = advancers / universe_size if universe_size else None
    down_ratio = decliners / universe_size if universe_size else None
    return {
        "advancers": advancers,
        "decliners": decliners,
        "flat_count": flat_count,
        "limit_up_count": sum(1 for value in changes if value >= 9.5),
        "limit_down_count": sum(1 for value in changes if value <= -9.5),
        "total_amount": round(sum(amounts), 2) if amounts else None,
        "universe_size": universe_size,
        "up_ratio": round(up_ratio, 4) if up_ratio is not None else None,
        "down_ratio": round(down_ratio, 4) if down_ratio is not None else None,
        "赚钱效应": "强" if up_ratio and up_ratio >= 0.58 else "弱" if up_ratio is not None and up_ratio <= 0.42 else "中性",
        "source": source,
    }


def market_breadth_get() -> Dict[str, Any]:
    cache_key = "market_breadth"
    cached = _read_cache(cache_key, MARKET_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache")
    try:
        breadth = _build_market_breadth_from_spot(_load_full_spot())
        _write_cache(cache_key, breadth)
        return _ok(breadth, source="akshare")
    except Exception as exc:
        stale = _read_cache_stale(cache_key)
        if stale is not None:
            stale["error"] = f"使用过期市场宽度缓存: {exc}"
            return _ok(stale, source="cache-stale")
        return _fail(f"市场宽度获取异常: {exc}")


def market_money_flow_get() -> Dict[str, Any]:
    cache_key = "market_money_flow"
    cached = _read_cache(cache_key, MARKET_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache")
    try:
        spot = _load_full_spot()
        rows = list(spot.values())
        amount_rows = [row for row in rows if isinstance(row.get("amount"), (int, float)) and row.get("amount") > 0]
        signed_amount = 0.0
        total_amount = 0.0
        for row in amount_rows:
            change = row.get("change_pct")
            amount = row.get("amount")
            if not isinstance(change, (int, float)) or not isinstance(amount, (int, float)):
                continue
            direction = 1 if change > 0 else -1 if change < 0 else 0
            strength = min(abs(change) / 5.0, 1.0)
            signed_amount += direction * strength * amount
            total_amount += amount
        proxy_score = signed_amount / total_amount if total_amount else 0.0
        top_inflow = sorted(
            [row for row in amount_rows if isinstance(row.get("change_pct"), (int, float)) and row.get("change_pct") > 0],
            key=lambda row: row.get("amount") or 0,
            reverse=True,
        )[:10]
        top_outflow = sorted(
            [row for row in amount_rows if isinstance(row.get("change_pct"), (int, float)) and row.get("change_pct") < 0],
            key=lambda row: row.get("amount") or 0,
            reverse=True,
        )[:10]
        result = {
            "name": "全市场量价资金代理",
            "net": round(proxy_score, 4),
            "unit": "proxy_score",
            "direction": "inflow" if proxy_score > 0.03 else "outflow" if proxy_score < -0.03 else "flat",
            "total_amount": round(total_amount, 2) if total_amount else None,
            "sample_size": len(amount_rows),
            "source": "akshare_full_spot",
            "note": "由全市场成交额按涨跌幅方向加权构造，代表风险偏好代理，不等同真实主力净流入。",
            "top_amount_risers": [{"code": r.get("code"), "name": r.get("name"), "change_pct": r.get("change_pct"), "amount": r.get("amount")} for r in top_inflow],
            "top_amount_fallers": [{"code": r.get("code"), "name": r.get("name"), "change_pct": r.get("change_pct"), "amount": r.get("amount")} for r in top_outflow],
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare")
    except Exception as exc:
        stale = _read_cache_stale(cache_key)
        if stale is not None:
            stale["error"] = f"使用过期全市场资金代理缓存: {exc}"
            return _ok(stale, source="cache-stale")
        return _fail(f"全市场资金代理获取异常: {exc}")


MARKET_PROXY_BASKET = [
    "601211",
    "002241",
    "002414",
    "002008",
    "600118",
    "302132",
    "603218",
    "600458",
    "600549",
    "000822",
    "000737",
    "600031",
    "603063",
    "002815",
    "600406",
    "688519",
    "600519",
    "300750",
    "000858",
    "601318",
    "600036",
    "000333",
]


def sampled_market_proxy_get(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    sample_symbols = symbols or MARKET_PROXY_BASKET
    items = []
    errors = []
    for symbol in sample_symbols:
        result = _sample_quote_get(symbol)
        data = result.get("data") or {}
        change = _n(data.get("change_pct"))
        amount = _n(data.get("amount"))
        if change is None:
            errors.append(f"{symbol} quote missing change_pct")
            continue
        items.append(
            {
                "code": symbol,
                "name": data.get("name"),
                "change_pct": change,
                "amount": amount,
            }
        )
    if len(items) < 8:
        return _fail(f"抽样市场代理样本不足: {len(items)}", errors=errors)
    advancers = sum(1 for item in items if item["change_pct"] > 0)
    decliners = sum(1 for item in items if item["change_pct"] < 0)
    flat_count = sum(1 for item in items if item["change_pct"] == 0)
    total_amount = sum(item.get("amount") or 0 for item in items)
    signed_amount = 0.0
    amount_used = 0.0
    for item in items:
        amount = item.get("amount")
        if not isinstance(amount, (int, float)) or amount <= 0:
            continue
        direction = 1 if item["change_pct"] > 0 else -1 if item["change_pct"] < 0 else 0
        strength = min(abs(item["change_pct"]) / 5.0, 1.0)
        signed_amount += direction * strength * amount
        amount_used += amount
    flow_score = signed_amount / amount_used if amount_used else 0.0
    return _ok(
        {
            "breadth": {
                "advancers": advancers,
                "decliners": decliners,
                "flat_count": flat_count,
                "universe_size": len(items),
                "up_ratio": round(advancers / len(items), 4),
                "down_ratio": round(decliners / len(items), 4),
                "total_amount": round(total_amount, 2) if total_amount else None,
                "source": "sampled_watchlist_plus_core",
                "sampled": True,
                "sample_codes": [item["code"] for item in items],
            },
            "flow": {
                "name": "抽样量价资金代理",
                "net": round(flow_score, 4),
                "unit": "proxy_score",
                "direction": "inflow" if flow_score > 0.03 else "outflow" if flow_score < -0.03 else "flat",
                "sample_size": len(items),
                "total_amount": round(total_amount, 2) if total_amount else None,
                "source": "sampled_watchlist_plus_core",
                "proxy": True,
                "note": "由自选股和核心权重样本构造，只代表抽样赚钱效应，不等同全市场宽度。",
            },
            "items": items,
            "errors": errors,
        },
        source="sampled-quotes",
    )


def _sample_quote_get(symbol: str) -> Dict[str, Any]:
    symbol = symbol.zfill(6)
    try:
        return quote_get(symbol)
    except Exception:
        pass
    browser_script = WORKSPACE / "skills" / "stock-data" / "scripts" / "browser_fetch.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(browser_script), symbol, "auto"],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if completed.stdout.strip():
            return json.loads(completed.stdout)
        return {"success": False, "error": completed.stderr.strip() or "empty browser quote"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _n(val: Any) -> Optional[float]:
    """安全转浮点"""
    if val is None or val == "" or val == "-":
        return None
    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None


def _round_or_none(val: Optional[float], digits: int = 4) -> Optional[float]:
    if val is None:
        return None
    return round(float(val), digits)


def _ema(values: List[Optional[float]], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    multiplier = 2 / (period + 1)
    ema: Optional[float] = None
    for value in values:
        if value is None:
            result.append(ema)
            continue
        if ema is None:
            ema = value
        else:
            ema = (value - ema) * multiplier + ema
        result.append(ema)
    return result


def _simple_moving_average(values: List[Optional[float]], period: int) -> Optional[float]:
    valid = [value for value in values[-period:] if isinstance(value, (int, float))]
    if len(valid) < period:
        return None
    return sum(valid) / period


def _stddev(values: List[Optional[float]], period: int) -> Optional[float]:
    valid = [value for value in values[-period:] if isinstance(value, (int, float))]
    if len(valid) < period:
        return None
    mean = sum(valid) / period
    variance = sum((value - mean) ** 2 for value in valid) / period
    return math.sqrt(variance)


def _rsi(values: List[Optional[float]], period: int = 14) -> Optional[float]:
    closes = [value for value in values if isinstance(value, (int, float))]
    if len(closes) <= period:
        return None
    gains: List[float] = []
    losses: List[float] = []
    for idx in range(1, len(closes)):
        change = closes[idx] - closes[idx - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for idx in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[idx]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[idx]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(values: List[Optional[float]]) -> Dict[str, Optional[float]]:
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    dif_series: List[Optional[float]] = []
    for fast, slow in zip(ema12, ema26):
        if fast is None or slow is None:
            dif_series.append(None)
        else:
            dif_series.append(fast - slow)
    dea_series = _ema(dif_series, 9)
    dif = dif_series[-1] if dif_series else None
    dea = dea_series[-1] if dea_series else None
    hist = None
    if dif is not None and dea is not None:
        hist = (dif - dea) * 2
    return {
        "dif": _round_or_none(dif),
        "dea": _round_or_none(dea),
        "hist": _round_or_none(hist),
    }


def _calc_pct_change(bars: List[Dict[str, Any]], lookback: int) -> Optional[float]:
    if len(bars) <= lookback:
        return None
    current = bars[-1].get("close")
    prev = bars[-1 - lookback].get("close")
    if not isinstance(current, (int, float)) or not isinstance(prev, (int, float)) or prev == 0:
        return None
    return round(((current - prev) / prev) * 100, 2)


def _summarize_indicators(bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    closes = [bar.get("close") for bar in bars]
    volumes = [bar.get("volume") for bar in bars]
    ma5 = _simple_moving_average(closes, 5)
    ma10 = _simple_moving_average(closes, 10)
    ma20 = _simple_moving_average(closes, 20)
    ma60 = _simple_moving_average(closes, 60)
    avg_volume_20 = _simple_moving_average(volumes, 20)
    boll_mid = ma20
    std20 = _stddev(closes, 20)
    boll_upper = boll_mid + (2 * std20) if boll_mid is not None and std20 is not None else None
    boll_lower = boll_mid - (2 * std20) if boll_mid is not None and std20 is not None else None
    latest_close = closes[-1] if closes else None
    return {
        "latest_close": _round_or_none(latest_close),
        "change_5d": _calc_pct_change(bars, 5),
        "change_10d": _calc_pct_change(bars, 10),
        "change_20d": _calc_pct_change(bars, 20),
        "change_60d": _calc_pct_change(bars, 60),
        "ma": {
            "ma5": _round_or_none(ma5),
            "ma10": _round_or_none(ma10),
            "ma20": _round_or_none(ma20),
            "ma60": _round_or_none(ma60),
        },
        "macd": _macd(closes),
        "rsi14": _round_or_none(_rsi(closes, 14), 2),
        "boll": {
            "upper": _round_or_none(boll_upper),
            "mid": _round_or_none(boll_mid),
            "lower": _round_or_none(boll_lower),
        },
        "avg_volume_20": _round_or_none(avg_volume_20),
    }


def _build_quality_section(*, source: str, success: bool, warning: Optional[str] = None) -> Dict[str, Any]:
    quality = {
        "status": "ok" if success else "error",
        "source": source,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }
    if warning:
        quality["warning"] = warning
        quality["status"] = "degraded"
    return quality


# ─── 公开接口 ──────────────────────────────────────────────────


def quote_get(symbol: str) -> Dict[str, Any]:
    """获取单只股票实时行情"""
    symbol = symbol.zfill(6)
    spot = _load_full_spot()
    row = spot.get(symbol)
    if row is None:
        return _fail(f"未找到股票 {symbol} 的行情数据", symbol=symbol)

    # 实时价格从快照拿，但量/额等可能有更精确的数据
    return _ok(
        {
            "symbol": symbol,
            "name": row.get("name", ""),
            "price": row.get("price"),
            "change": row.get("change"),
            "change_pct": row.get("change_pct"),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "pre_close": row.get("pre_close"),
            "volume": row.get("volume"),
            "amount": row.get("amount"),
            "turnover_rate": row.get("turnover_rate"),
            "amplitude": row.get("amplitude"),
            "volume_ratio": row.get("volume_ratio"),
            "pe": row.get("pe"),
            "pb": row.get("pb"),
            "market_cap": row.get("market_cap"),
            "circulating_cap": row.get("circulating_cap"),
        },
        source="akshare+spot_cache",
        symbol=symbol,
    )


def quotes_batch_get(symbols: List[str]) -> Dict[str, Any]:
    """批量获取多只股票行情"""
    spot = _load_full_spot()
    items = []
    for raw in symbols:
        s = raw.zfill(6)
        row = spot.get(s)
        if row:
            items.append(
                {
                    "symbol": s,
                    "name": row.get("name", ""),
                    "price": row.get("price"),
                    "change_pct": row.get("change_pct"),
                    "change": row.get("change"),
                    "volume": row.get("volume"),
                    "amount": row.get("amount"),
                    "turnover_rate": row.get("turnover_rate"),
                    "market_cap": row.get("market_cap"),
                }
            )
    return _ok(
        {
            "items": items,
            "total": len(items),
            "requested": len(symbols),
        },
        source="akshare+spot_cache",
    )


def kline_get(symbol: str, days: int = 60, period: str = "daily") -> Dict[str, Any]:
    """获取 K 线数据"""
    symbol = symbol.zfill(6)
    period = period.lower()
    cache_key = f"kline_{symbol}_{period}_{days}"
    cached = _read_cache(cache_key, KLINE_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol, days=days, period=period)

    import akshare as ak
    import pandas as pd

    try:
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        frame = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start,
            end_date=end,
            adjust="qfq",
        )
        if frame is None or frame.empty:
            return _fail(f"未能获取 {symbol} K 线数据", symbol=symbol)

        records: List[Dict[str, Any]] = []
        for _, row in frame.iterrows():
            records.append(
                {
                    "date": str(row.get("日期", "")),
                    "open": _n(row.get("开盘")),
                    "close": _n(row.get("收盘")),
                    "high": _n(row.get("最高")),
                    "low": _n(row.get("最低")),
                    "volume": _n(row.get("成交量")),
                    "amount": _n(row.get("成交额")),
                    "turnover_rate": _n(row.get("换手率")),
                }
            )

        # 按日期排序（升序）
        records.sort(key=lambda x: x["date"])
        # 只保留最新 days 天
        if len(records) > days:
            records = records[-days:]

        result = {
            "symbol": symbol,
            "period": period,
            "bars": records,
            "count": len(records),
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol, days=days, period=period)

    except Exception as e:
        return _fail(f"K 线获取异常: {e}", symbol=symbol)


def market_index_get() -> Dict[str, Any]:
    """获取大盘指数行情"""
    cache_key = "market_index"
    cached = _read_cache(cache_key, MARKET_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache")

    import akshare as ak

    try:
        indices: List[Dict[str, Any]] = []
        # 使用 stock_zh_index_daily 获取上证指数的日线数据（含涨跌幅、成交额）
        # SH 代码需要带 sh 前缀
        index_configs = [
            ("000001", "上证指数", "sh000001"),
            ("399001", "深证成指", "sz399001"),
            ("399006", "创业板指", "sz399006"),
        ]
        for code, name, api_code in index_configs:
            try:
                frame = ak.stock_zh_index_daily(symbol=api_code)
                if frame is not None and len(frame) > 0:
                    last = frame.iloc[-1]
                    # 计算涨跌幅
                    close = _n(last.get("close", last.get("收盘")))
                    pre_close = None
                    if len(frame) > 1:
                        prev = frame.iloc[-2]
                        pre_close = _n(prev.get("close", prev.get("收盘")))
                    change_pct = round((close - pre_close) / pre_close * 100, 2) if close and pre_close and pre_close != 0 else None
                    closes = [_n(v) for v in frame["close"].tail(21).tolist()] if "close" in frame else []
                    amounts = [_n(v) for v in frame["amount"].tail(6).tolist()] if "amount" in frame else []
                    change_5d = None
                    change_20d = None
                    amount_latest = amounts[-1] if amounts else _n(last.get("amount", last.get("成交额")))
                    amount_avg_5d = None
                    if close and len(closes) >= 6 and closes[-6]:
                        change_5d = round((close - closes[-6]) / closes[-6] * 100, 2)
                    if close and len(closes) >= 21 and closes[-21]:
                        change_20d = round((close - closes[-21]) / closes[-21] * 100, 2)
                    if len(amounts) >= 5:
                        amount_avg_5d = round(sum(v or 0 for v in amounts[-5:]) / 5, 2)
                    indices.append(
                        {
                            "code": code,
                            "name": name,
                            "price": close,
                            "change_pct": change_pct,
                            "change_5d": change_5d,
                            "change_20d": change_20d,
                            "volume": _n(last.get("volume", last.get("成交量"))),
                            "amount": amount_latest,
                            "amount_avg_5d": amount_avg_5d,
                            "high": _n(last.get("high", last.get("最高"))),
                            "low": _n(last.get("low", last.get("最低"))),
                            "date": str(last.get("date", "")),
                        }
                    )
                else:
                    indices.append({"code": code, "name": name, "error": "数据为空"})
            except Exception as e:
                indices.append({"code": code, "name": name, "error": str(e)})

        breadth: Dict[str, Any] = {}
        try:
            breadth = _build_market_breadth_from_spot(_load_full_spot())
            _write_cache("market_breadth", breadth)
        except Exception as exc:
            stale_breadth = _read_cache_stale("market_breadth")
            breadth = stale_breadth if isinstance(stale_breadth, dict) else {"error": f"市场广度获取失败: {exc}"}
            if isinstance(breadth, dict) and "error" not in breadth:
                breadth["error"] = f"使用过期市场宽度缓存: {exc}"

        result = {"indices": indices, "count": len(indices), "breadth": breadth}
        _write_cache(cache_key, result)
        return _ok(result, source="akshare")

    except Exception as e:
        return _fail(f"大盘数据获取异常: {e}")


def sector_get(symbol: str) -> Dict[str, Any]:
    """获取股票所属行业板块"""
    symbol = symbol.zfill(6)
    cache_key = f"sector_{symbol}"
    cached = _read_cache(cache_key, SECTOR_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    import akshare as ak

    try:
        info = ak.stock_individual_info_em(symbol=symbol)
        if info is None or info.empty:
            return _fail(f"无法获取 {symbol} 信息", symbol=symbol)

        industry = ""
        for _, row in info.iterrows():
            if str(row.get("item", "")).strip() == "行业":
                industry = str(row.get("value", "") or "").strip()
                break

        result = {"symbol": symbol, "industry": industry}
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol)

    except Exception as e:
        return _fail(f"板块获取异常: {e}", symbol=symbol)


def sector_context_get(symbol: str) -> Dict[str, Any]:
    """获取行业上下文：板块热度 + 同行对比 + 个股行业排名"""
    symbol = symbol.zfill(6)
    cache_key = f"sector_ctx_{symbol}"
    cached = _read_cache(cache_key, SECTOR_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    # 1. 先获取行业名称
    sector_result = sector_get(symbol)
    if not sector_result.get("success"):
        return sector_result

    industry = sector_result["data"]["industry"]
    if not industry:
        return _fail(f"无法确定 {symbol} 行业", symbol=symbol)

    import akshare as ak

    try:
        # 2. 获取行业板块热度 + 成分股
        heat = sector_heat_get(industry)
        if not heat.get("success"):
            return heat

        heat_data = heat["data"]
        members = heat_data.get("members", [])

        # 3. 找个股在行业中的排名
        stock_rank = None
        stock_info = None
        for i, m in enumerate(members):
            if m.get("code", "").zfill(6) == symbol:
                # 按涨跌幅排序
                sorted_members = sorted(members, key=lambda x: x.get("change_pct") or -999, reverse=True)
                for j, sm in enumerate(sorted_members):
                    if sm.get("code", "").zfill(6) == symbol:
                        stock_rank = j + 1
                        break
                stock_info = m
                break

        # 如果没有找到自己的股票，用行情接口补
        if stock_info is None:
            spot = _load_full_spot()
            row = spot.get(symbol)
            if row:
                stock_info = {
                    "code": symbol,
                    "name": row.get("name", ""),
                    "price": row.get("price"),
                    "change_pct": row.get("change_pct"),
                }

        # 4. 计算行业内部相对强弱
        peer_changes = [m.get("change_pct") for m in members if m.get("change_pct") is not None]
        if peer_changes and stock_info and stock_info.get("change_pct") is not None:
            avg_peer = sum(peer_changes) / len(peer_changes)
            relative_strength = round(stock_info["change_pct"] - avg_peer, 2)
            peer_rank_pct = round(stock_rank / len(members) * 100, 1) if stock_rank and members else None
        else:
            relative_strength = None
            peer_rank_pct = None

        result = {
            "symbol": symbol,
            "industry": industry,
            "sector_heat": {
                "name": heat_data.get("name", industry),
                "change_pct": heat_data.get("change_pct"),
                "up_count": heat_data.get("up_count"),
                "down_count": heat_data.get("down_count"),
                "main_flow": heat_data.get("main_flow"),
                "amount": heat_data.get("amount"),
            },
            "peers": members[:10],  # 前10只同业股票
            "stock_position": {
                "rank": stock_rank,
                "total": len(members),
                "rank_pct": peer_rank_pct,
                "relative_strength": relative_strength,  # 正=强于行业, 负=弱于行业
                "change_pct": stock_info.get("change_pct") if stock_info else None,
            },
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol)

    except Exception as e:
        # 降级：至少返回行业名称
        return _ok({"symbol": symbol, "industry": industry, "note": f"行业上下文获取部分失败: {e}"},
                  source="akshare", symbol=symbol)


def sector_heat_get(sector_name: str) -> Dict[str, Any]:
    """获取行业板块热度"""
    cache_key = f"sector_heat_{sector_name}"
    cached = _read_cache(cache_key, SECTOR_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache")

    import akshare as ak

    try:
        frame = ak.stock_board_industry_name_em()
        if frame is None or frame.empty:
            return _fail("无法获取板块数据")

        records = frame.to_dict(orient="records")
        matched = None
        for row in records:
            if str(row.get("板块名称", "")).strip() == sector_name:
                matched = {
                    "name": row.get("板块名称", ""),
                    "change_pct": _n(row.get("涨跌幅")),
                    "up_count": _n(row.get("上涨家数")),
                    "down_count": _n(row.get("下跌家数")),
                    "main_flow": _n(row.get("主力净流入")),
                    "amount": _n(row.get("成交额")),
                }
                break

        if not matched:
            return _fail(f"未找到板块: {sector_name}")

        # 获取板块成分股
        members = []
        try:
            cons = ak.stock_board_industry_cons_em(symbol=sector_name)
            if cons is not None and not cons.empty:
                for _, row in cons.head(10).iterrows():
                    members.append(
                        {
                            "code": str(row.get("代码", "")).strip(),
                            "name": str(row.get("名称", "")).strip(),
                            "price": _n(row.get("最新价")),
                            "change_pct": _n(row.get("涨跌幅")),
                        }
                    )
        except Exception:
            pass

        matched["members"] = members
        _write_cache(cache_key, matched)
        return _ok(matched, source="akshare")

    except Exception as e:
        return _fail(f"板块热度获取异常: {e}")


def financial_get(symbol: str) -> Dict[str, Any]:
    """获取财务指标摘要（优先从行情缓存取 PE/PB，更快更可靠）"""
    symbol = symbol.zfill(6)
    cache_key = f"finance_{symbol}"
    cached = _read_cache(cache_key, FINANCE_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    # 从行情缓存提取 PE/PB（已在 spot 表中）
    spot = _load_full_spot()
    row = spot.get(symbol)
    if row and row.get("pe") is not None:
        result = {
            "symbol": symbol,
            "pe_ttm": row.get("pe"),
            "pb": row.get("pb"),
            "market_cap": row.get("market_cap"),
            "circulating_cap": row.get("circulating_cap"),
        }
        _write_cache(cache_key, result)
        return _ok(result, source="spot_cache", symbol=symbol)

    # 兜底：独立估值 API
    import akshare as ak
    try:
        valuation = ak.stock_zh_valuation_baidu(symbol=symbol)
        pe = pb = market_cap = None
        if valuation is not None and not valuation.empty:
            last = valuation.iloc[-1]
            pe = _n(last.get("pe", last.get("市盈率TTM", last.get("市盈率(TTM)"))))
            pb = _n(last.get("pb", last.get("市净率")))
            market_cap = _n(last.get("market_cap", last.get("总市值", last.get("总市值(元)"))))
        result = {"symbol": symbol, "pe_ttm": pe, "pb": pb, "market_cap": market_cap}
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol)
    except Exception as e:
        return _fail(f"财务数据获取异常: {e}", symbol=symbol)


def margin_get(symbol: str) -> Dict[str, Any]:
    """获取融资融券余额"""
    symbol = symbol.zfill(6)
    cache_key = f"margin_{symbol}"
    cached = _read_cache(cache_key, FINANCE_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    import akshare as ak

    try:
        # 尝试获取融资余额
        margin = ak.stock_margin_detail_sse(date=datetime.now().strftime("%Y%m%d"))
        if margin is None or margin.empty:
            return _fail("融资融券数据今日未更新", symbol=symbol)

        records = margin.to_dict(orient="records")
        matched = None
        for row in records:
            code = str(row.get("标的证券代码", row.get("证券代码", ""))).strip()
            if code.zfill(6) == symbol:
                matched = {
                    "financing_balance": _n(row.get("融资余额", row.get("融资余额(元)"))),
                    "financing_buy": _n(row.get("融资买入额", row.get("融资买入额(元)"))),
                    "financing_repay": _n(row.get("融资偿还额", row.get("融资偿还额(元)"))),
                    "securities_lending_balance": _n(row.get("融券余额", row.get("融券余额(元)"))),
                }
                break

        if matched is None:
            return _fail(f"{symbol} 今日未纳入融资融券统计", symbol=symbol)

        _write_cache(cache_key, matched)
        return _ok(matched, source="akshare", symbol=symbol)

    except Exception as e:
        return _fail(f"融资融券数据获取异常: {e}", symbol=symbol)


def fund_flow_get(symbol: str) -> Dict[str, Any]:
    symbol = symbol.zfill(6)
    cache_key = f"flow_{symbol}"
    cached = _read_cache(cache_key, SECTOR_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    import akshare as ak

    try:
        # 判断代码前缀
        market = "sh" if symbol.startswith(("6", "9")) else "sz"
        frame = ak.stock_individual_fund_flow(stock=symbol, market=market)
        if frame is None or frame.empty:
            return _fail(f"无法获取 {symbol} 资金流向", symbol=symbol)

        last = frame.iloc[-1]
        result = {
            "symbol": symbol,
            "date": str(last.get("日期", "")),
            "main_net_inflow": _n(last.get("主力净流入-净额", last.get("主力净流入"))),
            "super_large_net": _n(last.get("超大单净流入-净额")),
            "large_net": _n(last.get("大单净流入-净额")),
            "medium_net": _n(last.get("中单净流入-净额")),
            "small_net": _n(last.get("小单净流入-净额")),
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol)

    except Exception as e:
        return _fail(f"资金流向获取异常: {e}", symbol=symbol)


def intraday_get(symbol: str, interval: str = "1", days: int = 3) -> Dict[str, Any]:
    """获取分钟级分时数据"""
    symbol = symbol.zfill(6)
    interval = str(interval or "1")
    cache_key = f"intraday_{symbol}_{interval}_{days}"
    cached = _read_cache(cache_key, INTRADAY_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol, interval=interval, days=days)

    import akshare as ak

    try:
        frame = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period=interval,
            adjust="qfq",
        )
        if frame is None or frame.empty:
            return _fail(f"未能获取 {symbol} 分时数据", symbol=symbol)

        records: List[Dict[str, Any]] = []
        for _, row in frame.iterrows():
            dt_text = str(row.get("时间", row.get("日期", "")))
            records.append(
                {
                    "datetime": dt_text,
                    "open": _n(row.get("开盘")),
                    "close": _n(row.get("收盘")),
                    "high": _n(row.get("最高")),
                    "low": _n(row.get("最低")),
                    "volume": _n(row.get("成交量")),
                    "amount": _n(row.get("成交额")),
                    "avg_price": _n(row.get("均价")),
                }
            )
        records.sort(key=lambda x: x["datetime"])
        if days > 0:
            daily_buckets: Dict[str, List[Dict[str, Any]]] = {}
            for row in records:
                trade_date = row["datetime"][:10]
                daily_buckets.setdefault(trade_date, []).append(row)
            trade_dates = sorted(daily_buckets.keys())[-days:]
            records = [row for trade_date in trade_dates for row in daily_buckets[trade_date]]

        latest_avg_price = None
        valid_avg = [row.get("avg_price") for row in records if isinstance(row.get("avg_price"), (int, float))]
        if valid_avg:
            latest_avg_price = round(valid_avg[-1], 4)
        elif records:
            amounts = [row.get("amount") for row in records if isinstance(row.get("amount"), (int, float))]
            volumes = [row.get("volume") for row in records if isinstance(row.get("volume"), (int, float)) and row.get("volume")]
            if amounts and volumes and sum(volumes) > 0:
                latest_avg_price = round(sum(amounts) / sum(volumes), 4)

        result = {
            "symbol": symbol,
            "interval": f"{interval}m",
            "bars": records,
            "count": len(records),
            "latest_avg_price": latest_avg_price,
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol, interval=interval, days=days)
    except Exception as e:
        return _fail(f"分时数据获取异常: {e}", symbol=symbol)


def financial_trend_get(symbol: str, periods: int = 8) -> Dict[str, Any]:
    """获取最近几个季度的财务趋势"""
    symbol = symbol.zfill(6)
    cache_key = f"finance_trend_{symbol}_{periods}"
    cached = _read_cache(cache_key, FINANCE_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol, periods=periods)

    import akshare as ak

    try:
        frame = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        if frame is None or frame.empty:
            return _fail(f"未能获取 {symbol} 财务趋势数据", symbol=symbol)
        records: List[Dict[str, Any]] = []
        for _, row in frame.tail(periods).iterrows():
            records.append(
                {
                    "report_date": str(row.get("报告期", "")),
                    "revenue_yoy": _n(row.get("营业总收入同比增长率")),
                    "profit_yoy": _n(row.get("净利润同比增长率")),
                    "roe": _n(row.get("净资产收益率")),
                    "gross_margin": _n(row.get("销售毛利率")),
                    "debt_ratio": _n(row.get("资产负债率")),
                }
            )
        latest = records[-1] if records else {}
        result = {
            "symbol": symbol,
            "periods": records,
            "latest": latest,
            "count": len(records),
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol, periods=periods)
    except Exception as e:
        return _fail(f"财务趋势获取异常: {e}", symbol=symbol)


def north_south_flow_get() -> Dict[str, Any]:
    """获取北向/南向资金流向汇总"""
    cache_key = "north_south_flow"
    cached = _read_cache(cache_key, NORTH_SOUTH_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache")

    import akshare as ak

    try:
        frame = ak.stock_hsgt_fund_flow_summary_em()
        if frame is None or frame.empty:
            return _fail("北向南向资金数据为空")

        records: List[Dict[str, Any]] = []
        for _, row in frame.iterrows():
            records.append({
                "date": str(row.get("交易日", "")),
                "type": str(row.get("类型", "")),          # 沪港通/深港通
                "board": str(row.get("板块", "")),         # 沪股通/深股通/港股通
                "direction": str(row.get("资金方向", "")), # 北向/南向
                "net_buy": _n(row.get("成交净买额")),      # 亿元
                "net_inflow": _n(row.get("资金净流入")),    # 亿元
                "quota_remaining": _n(row.get("当日资金余额")),
                "up_count": int(row.get("上涨数", 0)),
                "down_count": int(row.get("下跌数", 0)),
                "index_change": _n(row.get("指数涨跌幅")),
            })

        # 按日期分组
        by_date: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            by_date.setdefault(r["date"], []).append(r)

        latest_date = max(by_date.keys()) if by_date else ""
        latest = by_date.get(latest_date, [])

        result = {
            "latest_date": latest_date,
            "daily": latest,
            "summary": _summarize_north_south(latest),
            "count": len(records),
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare")
    except Exception as e:
        return _fail(f"北向南向资金异常: {e}")


def _summarize_north_south(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    north = [r for r in rows if r["direction"] == "北向"]
    south = [r for r in rows if r["direction"] == "南向"]
    return {
        "north_net": round(sum(r.get("net_buy") or 0 for r in north), 2),
        "south_net": round(sum(r.get("net_buy") or 0 for r in south), 2),
        "north_detail": north,
        "south_detail": south,
    }


def stock_fund_flow_hist_get(symbol: str, days: int = 20) -> Dict[str, Any]:
    """获取个股资金流向历史（主力/超大单/大单/中单/小单）"""
    symbol = symbol.zfill(6)
    cache_key = f"fund_flow_hist_{symbol}_{days}"
    cached = _read_cache(cache_key, SECTOR_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    import akshare as ak

    try:
        frame = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith(("6", "9")) else "sz")
        if frame is None or frame.empty:
            return _fail(f"无法获取 {symbol} 资金流向历史", symbol=symbol)

        records: List[Dict[str, Any]] = []
        for _, row in frame.tail(days).iterrows():
            records.append({
                "date": str(row.get("日期", "")),
                "close": _n(row.get("收盘价")),
                "change_pct": _n(row.get("涨跌幅")),
                "main_net": _n(row.get("主力净流入-净额")),
                "main_pct": _n(row.get("主力净流入-净占比")),
                "super_large_net": _n(row.get("超大单净流入-净额")),
                "super_large_pct": _n(row.get("超大单净流入-净占比")),
                "large_net": _n(row.get("大单净流入-净额")),
                "large_pct": _n(row.get("大单净流入-净占比")),
                "medium_net": _n(row.get("中单净流入-净额")),
                "medium_pct": _n(row.get("中单净流入-净占比")),
                "small_net": _n(row.get("小单净流入-净额")),
                "small_pct": _n(row.get("小单净流入-净占比")),
            })

        # 计算近期指标
        recent_main = [r.get("main_net") or 0 for r in records[-5:]]
        recent_super = [r.get("super_large_net") or 0 for r in records[-5:]]

        result = {
            "symbol": symbol,
            "bars": records,
            "count": len(records),
            "recent_5d": {
                "main_net_sum": round(sum(recent_main), 0),
                "main_net_avg": round(sum(recent_main) / len(recent_main), 0) if recent_main else 0,
                "super_large_net_sum": round(sum(recent_super), 0),
            },
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol)
    except Exception as e:
        return _fail(f"资金流向历史异常: {e}", symbol=symbol)


def lhb_stock_get(symbol: str) -> Dict[str, Any]:
    """获取个股龙虎榜记录（营业部操作明细）"""
    symbol = symbol.zfill(6)
    cache_key = f"lhb_{symbol}"
    cached = _read_cache(cache_key, LHB_TTL_SEC)
    if cached is not None:
        return _ok(cached, source="cache", symbol=symbol)

    import akshare as ak
    from datetime import datetime, timedelta

    try:
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

        # 用 stock_lhb_detail_em 获取全量再过滤
        frame = ak.stock_lhb_detail_em(start_date=start, end_date=end)
        if frame is None or frame.empty:
            return _ok({"symbol": symbol, "records": [], "count": 0, "note": "近期无龙虎榜数据"},
                      source="akshare", symbol=symbol)

        # 过滤该股票
        mask = frame['代码'].astype(str).str.zfill(6) == symbol
        stock_frame = frame[mask]

        if stock_frame.empty:
            return _ok({"symbol": symbol, "records": [], "count": 0, "note": "近期未上榜"},
                      source="akshare", symbol=symbol)

        records: List[Dict[str, Any]] = []
        for _, row in stock_frame.iterrows():
            records.append({
                "date": str(row.get("上榜日", "")),
                "name": str(row.get("名称", "")),
                "reason": str(row.get("上榜原因", "")),
                "interpretation": str(row.get("解读", "")),
                "close": _n(row.get("收盘价")),
                "change_pct": _n(row.get("涨跌幅")),
                "net_amount": _n(row.get("龙虎榜净买额")),
                "buy_amount": _n(row.get("龙虎榜买入额")),
                "sell_amount": _n(row.get("龙虎榜卖出额")),
                "total_amount": _n(row.get("龙虎榜成交额")),
                "market_amount": _n(row.get("市场总成交额")),
                "net_pct": _n(row.get("净买额占总成交比")),
                "turnover": _n(row.get("换手率")),
                "float_cap": _n(row.get("流通市值")),
                "after_1d": _n(row.get("上榜后1日")),
                "after_2d": _n(row.get("上榜后2日")),
                "after_5d": _n(row.get("上榜后5日")),
                "after_10d": _n(row.get("上榜后10日")),
            })

        result = {
            "symbol": symbol,
            "records": records,
            "count": len(records),
            "latest": records[0] if records else None,
        }
        _write_cache(cache_key, result)
        return _ok(result, source="akshare", symbol=symbol)
    except Exception as e:
        return _ok({"symbol": symbol, "records": [], "count": 0, "note": str(e)[:100]},
                  source="akshare", symbol=symbol)


def analysis_payload_get(symbol: str) -> Dict[str, Any]:
    """聚合正式分析所需证据包"""
    symbol = symbol.zfill(6)
    sections: Dict[str, Dict[str, Any]] = {
        "quote": quote_get(symbol),
        "market": market_index_get(),
        "sector": sector_context_get(symbol),  # 含板块热度+同行排名+相对强弱
        "finance": financial_get(symbol),
        "flow": fund_flow_get(symbol),
        "flow_hist_10": stock_fund_flow_hist_get(symbol, 10),
        "margin": margin_get(symbol),
        "north_south": north_south_flow_get(),
        "lhb": lhb_stock_get(symbol),
        "kline_daily": kline_get(symbol, 120, "daily"),
        "kline_weekly": kline_get(symbol, 104, "weekly"),
        "kline_monthly": kline_get(symbol, 60, "monthly"),
        "intraday_1m": intraday_get(symbol, "1", 3),
        "intraday_5m": intraday_get(symbol, "5", 5),
        "financial_trend": financial_trend_get(symbol, 8),
    }

    missing_sections: List[Dict[str, str]] = []
    quality_map: Dict[str, Dict[str, Any]] = {}
    for name, response in sections.items():
        success = bool(response.get("success"))
        warning = None if success else response.get("error")
        if not success:
            missing_sections.append({"section": name, "reason": response.get("error", "unknown")})
        quality_map[name] = _build_quality_section(
            source=response.get("source", "unknown"),
            success=success,
            warning=warning,
        )

    daily_bars = sections["kline_daily"].get("data", {}).get("bars", []) if sections["kline_daily"].get("success") else []
    weekly_bars = sections["kline_weekly"].get("data", {}).get("bars", []) if sections["kline_weekly"].get("success") else []
    monthly_bars = sections["kline_monthly"].get("data", {}).get("bars", []) if sections["kline_monthly"].get("success") else []

    payload = {
        "symbol": symbol,
        "quote": sections["quote"].get("data"),
        "market": sections["market"].get("data"),
        "sector": sections["sector"].get("data"),
        "market_context": _market_context_summary(sections),  # 大盘+行业联动分析
        "fund_flow": sections["flow"].get("data"),
        "fund_flow_hist_10": sections["flow_hist_10"].get("data"),
        "margin": sections["margin"].get("data"),
        "north_south_flow": sections["north_south"].get("data"),
        "lhb": sections["lhb"].get("data"),
        "fundamental_valuation": sections["finance"].get("data"),
        "fundamental_trend": sections["financial_trend"].get("data"),
        "kline_daily": sections["kline_daily"].get("data"),
        "kline_weekly": sections["kline_weekly"].get("data"),
        "kline_monthly": sections["kline_monthly"].get("data"),
        "intraday": {
            "1m": sections["intraday_1m"].get("data"),
            "5m": sections["intraday_5m"].get("data"),
        },
        "technical_indicators": {
            "daily": _summarize_indicators(daily_bars) if daily_bars else {},
            "weekly": _summarize_indicators(weekly_bars) if weekly_bars else {},
            "monthly": _summarize_indicators(monthly_bars) if monthly_bars else {},
        },
        "quality": {
            "sections": quality_map,
            "missing_sections": missing_sections,
            "status": "ok" if not missing_sections else "degraded",
        },
    }
    return _ok(payload, source="stock-data", symbol=symbol, missing_sections=missing_sections)


def watchlist_snapshot(symbols: List[str]) -> Dict[str, Any]:
    """自选股快照 - 一次获取所有自选股的行情 + 行业 + 估值"""
    spot = _load_full_spot()
    items = []
    for raw in symbols:
        s = raw.zfill(6)
        row = spot.get(s)
        if row:
            items.append(
                {
                    "symbol": s,
                    "name": row.get("name", ""),
                    "price": row.get("price"),
                    "change_pct": row.get("change_pct"),
                    "change": row.get("change"),
                    "volume": row.get("volume"),
                    "amount": row.get("amount"),
                    "turnover_rate": row.get("turnover_rate"),
                    "amplitude": row.get("amplitude"),
                    "volume_ratio": row.get("volume_ratio"),
                    "pe": row.get("pe"),
                    "pb": row.get("pb"),
                    "market_cap": row.get("market_cap"),
                    "circulating_cap": row.get("circulating_cap"),
                }
            )
    return _ok(
        {
            "items": items,
            "total": len(items),
            "requested": len(symbols),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        },
        source="akshare+spot_cache",
    )


# ─── CLI 入口 ────────────────────────────────────────────────

def print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python3 fast_data.py <命令> [参数...]", file=sys.stderr)
        print("", file=sys.stderr)
        print("命令:", file=sys.stderr)
        print("  quote <代码>             获取实时行情", file=sys.stderr)
        print("  quotes <代码1> <代码2>... 批量获取行情", file=sys.stderr)
        print("  kline <代码> [天数=60]   获取日线 K 线", file=sys.stderr)
        print("  klinex <代码> [周期] [条数] 获取指定周期 K 线", file=sys.stderr)
        print("  market                  获取大盘指数", file=sys.stderr)
        print("  breadth                 获取市场宽度/赚钱效应", file=sys.stderr)
        print("  market-flow             获取全市场量价资金代理", file=sys.stderr)
        print("  market-proxy [代码...]  抽样市场宽度和资金代理", file=sys.stderr)
        print("  sector <代码>           获取所属行业", file=sys.stderr)
        print("  sector-ctx <代码>        获取行业上下文（板块热度+同行排名+相对强弱）", file=sys.stderr)
        print("  heat <板块名>           获取板块热度", file=sys.stderr)
        print("  finance <代码>          获取财务指标", file=sys.stderr)
        print("  finance-trend <代码>    获取季度财务趋势", file=sys.stderr)
        print("  margin <代码>           获取融资融券", file=sys.stderr)
        print("  flow <代码>             获取资金流向", file=sys.stderr)
        print("  flow-hist <代码> [天数]  获取个股资金流向历史", file=sys.stderr)
        print("  north-south             获取北向/南向资金", file=sys.stderr)
        print("  lhb <代码>              获取个股龙虎榜记录", file=sys.stderr)
        print("  intraday <代码> [1|5] [天数] 获取分时数据", file=sys.stderr)
        print("  analysis <代码>         获取正式分析证据包", file=sys.stderr)
        print("  snapshot <代码1>...     自选股快照（含行业、PE/PB）", file=sys.stderr)
        print("  watchlist <代码1>...    snapshot 别名", file=sys.stderr)
        print("", file=sys.stderr)
        raise SystemExit(1)

    cmd = sys.argv[1]
    exit_code = 0

    try:
        if cmd == "quote" and len(sys.argv) >= 3:
            result = quote_get(sys.argv[2])
        elif cmd == "quotes" and len(sys.argv) >= 3:
            result = quotes_batch_get(sys.argv[2:])
        elif cmd == "kline" and len(sys.argv) >= 3:
            days = int(sys.argv[3]) if len(sys.argv) >= 4 else 60
            result = kline_get(sys.argv[2], days)
        elif cmd == "klinex" and len(sys.argv) >= 3:
            period = sys.argv[3] if len(sys.argv) >= 4 else "daily"
            days = int(sys.argv[4]) if len(sys.argv) >= 5 else 120
            result = kline_get(sys.argv[2], days, period)
        elif cmd == "market":
            result = market_index_get()
        elif cmd == "breadth":
            result = market_breadth_get()
        elif cmd == "market-flow":
            result = market_money_flow_get()
        elif cmd == "market-proxy":
            result = sampled_market_proxy_get(sys.argv[2:] or None)
        elif cmd == "sector" and len(sys.argv) >= 3:
            result = sector_get(sys.argv[2])
        elif cmd == "sector-ctx" and len(sys.argv) >= 3:
            result = sector_context_get(sys.argv[2])
        elif cmd == "heat" and len(sys.argv) >= 3:
            result = sector_heat_get(sys.argv[2])
        elif cmd == "finance" and len(sys.argv) >= 3:
            result = financial_get(sys.argv[2])
        elif cmd == "finance-trend" and len(sys.argv) >= 3:
            result = financial_trend_get(sys.argv[2])
        elif cmd == "margin" and len(sys.argv) >= 3:
            result = margin_get(sys.argv[2])
        elif cmd == "flow" and len(sys.argv) >= 3:
            result = fund_flow_get(sys.argv[2])
        elif cmd == "flow-hist" and len(sys.argv) >= 3:
            days = int(sys.argv[3]) if len(sys.argv) >= 4 else 20
            result = stock_fund_flow_hist_get(sys.argv[2], days)
        elif cmd == "north-south":
            result = north_south_flow_get()
        elif cmd == "lhb" and len(sys.argv) >= 3:
            result = lhb_stock_get(sys.argv[2])
        elif cmd == "intraday" and len(sys.argv) >= 3:
            interval = sys.argv[3] if len(sys.argv) >= 4 else "1"
            days = int(sys.argv[4]) if len(sys.argv) >= 5 else 3
            result = intraday_get(sys.argv[2], interval, days)
        elif cmd == "analysis" and len(sys.argv) >= 3:
            result = analysis_payload_get(sys.argv[2])
        elif cmd in ("snapshot", "watchlist") and len(sys.argv) >= 3:
            result = watchlist_snapshot(sys.argv[2:])
        else:
            print(f"未知命令或参数不足: {cmd}", file=sys.stderr)
            raise SystemExit(1)

        exit_code = 0 if result.get("success") else 1
        print_json(result)

    except Exception as e:
        print_json(_fail(f"执行异常: {e}"))
        exit_code = 1

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
