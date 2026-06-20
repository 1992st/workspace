#!/usr/bin/env python3
"""
Browser 辅助数据获取脚本
当前只承诺为 quote 提供 browser 降级：
1. 腾讯财经
2. 东方财富
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, List, Optional


def normalize_symbol(symbol: str) -> str:
    raw = re.sub(r"\D", "", str(symbol or "").strip())
    if not raw:
        raise ValueError("symbol is required")
    return raw.zfill(6)


def normalize_tencent_code(symbol: str, *, default_index: bool = False) -> tuple[str, str]:
    raw = str(symbol or "").strip().lower()
    if raw.startswith(("sh", "sz")) and len(raw) >= 8:
        return raw[:2], normalize_symbol(raw[2:])
    code = normalize_symbol(raw)
    if default_index and code == "000001":
        return "sh", code
    market = "sh" if code.startswith(("5", "6", "9")) else "sz"
    return market, code


def _make_failure(source: str, error: str, category: str) -> Dict[str, Any]:
    return {
        "success": False,
        "source": source,
        "data": None,
        "quality_score": 0,
        "is_cached": False,
        "error": error,
        "error_category": category,
        "errors": [error],
    }


def _request_text(url: str, *, headers: Dict[str, str], encoding: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode(encoding, errors="ignore")


def _classify_error(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        reason = getattr(exc, "reason", None)
        text = str(reason or exc)
        if "nodename nor servname provided" in text or "Name or service not known" in text:
            return "dns_failure"
        if "timed out" in text.lower():
            return "timeout"
        return "network_error"
    return "unknown_error"


def parse_tencent_quote(raw: str, symbol: str) -> Dict[str, Any]:
    prefix = "sh" if symbol.startswith("6") else "sz"
    expected_prefix = f"v_{prefix}{symbol}"
    if not raw.startswith(expected_prefix):
        raise ValueError("invalid response format")

    start = raw.find('"') + 1
    end = raw.rfind('"')
    if start <= 0 or end <= start:
        raise ValueError("invalid quoted payload")
    parts = raw[start:end].split("~")
    if len(parts) < 38:
        raise ValueError(f"incomplete data: {len(parts)} fields")

    def get_text(idx: int) -> Optional[str]:
        if idx >= len(parts):
            return None
        value = parts[idx].strip()
        return value or None

    def get_float(idx: int) -> Optional[float]:
        value = get_text(idx)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def get_int(idx: int) -> Optional[int]:
        value = get_text(idx)
        if value is None:
            return None
        try:
            return int(float(value))
        except ValueError:
            return None

    price = get_float(3)
    pre_close = get_float(4)
    open_price = get_float(5)
    volume_hands = get_int(6)

    timestamp_idx = next(
        (idx for idx, value in enumerate(parts) if re.fullmatch(r"\d{14}", value.strip() if value else "")),
        None,
    )
    if timestamp_idx is None:
        raise ValueError("timestamp field not found")

    timestamp_raw = get_text(timestamp_idx)
    change = get_float(timestamp_idx + 1)
    change_pct = get_float(timestamp_idx + 2)
    high = get_float(timestamp_idx + 3)
    low = get_float(timestamp_idx + 4)
    combo_value = get_text(timestamp_idx + 5) or ""
    amount = get_int(timestamp_idx + 7)
    turnover_rate = get_float(timestamp_idx + 8)
    pe_ttm = get_float(timestamp_idx + 9)

    if price is None or price <= 0:
        raise ValueError("invalid price data")
    if pre_close is not None and change is None:
        change = round(price - pre_close, 4)
    if pre_close not in (None, 0) and change_pct is None:
        change_pct = round((price - pre_close) / pre_close * 100, 4)

    # 腾讯返回 YYYYMMDDHHMMSS，统一转 ISO；失败时保留原始值。
    if combo_value and "/" in combo_value:
        combo_parts = combo_value.split("/")
        if len(combo_parts) >= 3:
            try:
                amount = int(combo_parts[2])
            except ValueError:
                pass

    timestamp = timestamp_raw
    if timestamp_raw and re.fullmatch(r"\d{14}", timestamp_raw):
        try:
            timestamp = datetime.strptime(timestamp_raw, "%Y%m%d%H%M%S").isoformat()
        except ValueError:
            timestamp = timestamp_raw

    return {
        "success": True,
        "source": "browser-tencent",
        "data": {
            "symbol": symbol,
            "name": get_text(1) or symbol,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "open": open_price,
            "high": high,
            "low": low,
            "pre_close": pre_close,
            "volume": volume_hands * 100 if volume_hands is not None else None,
            "amount": amount,
            "turnover_rate": turnover_rate,
            "pe_ttm": pe_ttm,
            "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
        },
        "quality_score": 88,
        "is_cached": False,
        "errors": [],
    }


def fetch_tencent_quote(symbol: str) -> Dict[str, Any]:
    symbol = normalize_symbol(symbol)
    prefix = "sh" if symbol.startswith("6") else "sz"
    url = f"http://qt.gtimg.cn/q={prefix}{symbol}"
    try:
        raw = _request_text(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://stock.finance.qq.com/",
            },
            encoding="gbk",
        )
        return parse_tencent_quote(raw, symbol)
    except Exception as exc:
        return _make_failure(
            "browser-tencent",
            f"Tencent fetch failed: {exc}",
            _classify_error(exc),
        )


def parse_tencent_kline(raw: str, symbol: str, days: int, adjust: str) -> Dict[str, Any]:
    payload = json.loads(raw)
    market, symbol = normalize_tencent_code(symbol, default_index=True)
    key = f"{market}{symbol}"
    data = ((payload.get("data") or {}).get(key) or {})
    field = f"{adjust}day" if adjust in {"qfq", "hfq"} else "day"
    rows = data.get(field) or data.get("day") or data.get("qfqday") or []
    bars: List[Dict[str, Any]] = []
    for row in rows[-days:]:
        if len(row) < 6:
            continue
        bars.append({
            "date": row[0],
            "open": float(row[1]),
            "close": float(row[2]),
            "high": float(row[3]),
            "low": float(row[4]),
            "volume": int(float(row[5]) * 100),
        })
    if not bars:
        raise ValueError("no kline bars")
    return {
        "success": True,
        "source": "browser-tencent-kline",
        "data": {
            "symbol": symbol,
            "period": "daily",
            "adjust": adjust,
            "bars": bars,
            "count": len(bars),
            "latest_date": bars[-1]["date"],
        },
        "quality_score": 86,
        "is_cached": False,
        "errors": [],
    }


def fetch_tencent_kline(symbol: str, days: int = 120, adjust: str = "qfq") -> Dict[str, Any]:
    market, symbol = normalize_tencent_code(symbol, default_index=True)
    days = max(1, min(int(days), 800))
    adjust = adjust if adjust in {"qfq", "hfq", "none"} else "qfq"
    if adjust == "none":
        endpoint = "https://web.ifzq.gtimg.cn/appstock/app/kline/kline"
        param = f"{market}{symbol},day,,,{days}"
    else:
        endpoint = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        param = f"{market}{symbol},day,,,{days},{adjust}"
    url = f"{endpoint}?param={param}"
    try:
        raw = _request_text(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://gu.qq.com/",
            },
            encoding="utf-8",
        )
        return parse_tencent_kline(raw, symbol, days, adjust)
    except Exception as exc:
        return _make_failure(
            "browser-tencent-kline",
            f"Tencent kline fetch failed: {exc}",
            _classify_error(exc),
        )


def parse_tencent_intraday(raw: str, symbol: str) -> Dict[str, Any]:
    payload = json.loads(raw)
    market = "sh" if symbol.startswith("6") else "sz"
    key = f"{market}{symbol}"
    node = (((payload.get("data") or {}).get(key) or {}).get("data") or {})
    rows = node.get("data") or []
    bars: List[Dict[str, Any]] = []
    trade_date = node.get("date") or datetime.now().strftime("%Y%m%d")
    for row in rows:
        parts = str(row).split()
        if len(parts) < 4:
            continue
        time_text = parts[0]
        bars.append({
            "time": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]} {time_text[:2]}:{time_text[2:]}",
            "price": float(parts[1]),
            "volume": int(float(parts[2]) * 100),
            "amount": float(parts[3]),
        })
    if not bars:
        raise ValueError("no intraday bars")
    return {
        "success": True,
        "source": "browser-tencent-intraday",
        "data": {
            "symbol": symbol,
            "interval": "1m",
            "date": trade_date,
            "bars": bars,
            "count": len(bars),
            "latest_time": bars[-1]["time"],
        },
        "quality_score": 82,
        "is_cached": False,
        "errors": [],
    }


def fetch_tencent_intraday(symbol: str) -> Dict[str, Any]:
    symbol = normalize_symbol(symbol)
    market = "sh" if symbol.startswith("6") else "sz"
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?code={market}{symbol}"
    try:
        raw = _request_text(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://gu.qq.com/",
            },
            encoding="utf-8",
        )
        return parse_tencent_intraday(raw, symbol)
    except Exception as exc:
        return _make_failure(
            "browser-tencent-intraday",
            f"Tencent intraday fetch failed: {exc}",
            _classify_error(exc),
        )


def parse_tencent_market(raw: str) -> Dict[str, Any]:
    index_names = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
    }
    indices: List[Dict[str, Any]] = []
    for line in raw.split(";"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        code_match = re.match(r"v_([a-z]{2}\d{6})=", line)
        if not code_match:
            continue
        full_code = code_match.group(1)
        start = line.find('"') + 1
        end = line.rfind('"')
        if start <= 0 or end <= start:
            continue
        parts = line[start:end].split("~")
        if len(parts) < 35:
            continue

        def get_text(idx: int) -> Optional[str]:
            if idx >= len(parts):
                return None
            value = parts[idx].strip()
            return value or None

        def get_float(idx: int) -> Optional[float]:
            value = get_text(idx)
            if value is None:
                return None
            try:
                return float(value)
            except ValueError:
                return None

        def get_int(idx: int) -> Optional[int]:
            value = get_text(idx)
            if value is None:
                return None
            try:
                return int(float(value))
            except ValueError:
                return None

        timestamp_idx = next(
            (idx for idx, value in enumerate(parts) if re.fullmatch(r"\d{14}", value.strip() if value else "")),
            None,
        )
        timestamp_raw = get_text(timestamp_idx) if timestamp_idx is not None else None
        timestamp = timestamp_raw
        if timestamp_raw and re.fullmatch(r"\d{14}", timestamp_raw):
            try:
                timestamp = datetime.strptime(timestamp_raw, "%Y%m%d%H%M%S").isoformat()
            except ValueError:
                timestamp = timestamp_raw

        price = get_float(3)
        pre_close = get_float(4)
        if price is None or price <= 0:
            continue
        change = get_float(timestamp_idx + 1) if timestamp_idx is not None else None
        change_pct = get_float(timestamp_idx + 2) if timestamp_idx is not None else None
        high = get_float(timestamp_idx + 3) if timestamp_idx is not None else get_float(33)
        low = get_float(timestamp_idx + 4) if timestamp_idx is not None else get_float(34)
        combo = get_text(timestamp_idx + 5) if timestamp_idx is not None else None
        amount = get_int(timestamp_idx + 7) if timestamp_idx is not None else None
        if combo and "/" in combo:
            combo_parts = combo.split("/")
            if len(combo_parts) >= 3:
                try:
                    amount = int(float(combo_parts[2]))
                except ValueError:
                    pass
        if pre_close not in (None, 0) and change is None:
            change = round(price - pre_close, 4)
        if pre_close not in (None, 0) and change_pct is None:
            change_pct = round((price - pre_close) / pre_close * 100, 4)

        indices.append({
            "code": full_code[2:],
            "market_code": full_code,
            "name": index_names.get(full_code) or get_text(1) or full_code,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "open": get_float(5),
            "high": high,
            "low": low,
            "pre_close": pre_close,
            "volume": get_int(6),
            "amount": amount,
            "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
        })
    if not indices:
        raise ValueError("no valid market indices")
    return {
        "success": True,
        "source": "browser-tencent-market",
        "data": {
            "indices": indices,
            "count": len(indices),
            "breadth": {
                "status": "missing",
                "reason": "Tencent index fallback does not provide market breadth",
            },
        },
        "quality_score": 74,
        "is_cached": False,
        "data_status": "degraded",
        "errors": ["市场广度缺失：只能用于指数走势降级判断"],
    }


def fetch_tencent_market() -> Dict[str, Any]:
    url = "http://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
    try:
        raw = _request_text(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://stock.finance.qq.com/",
            },
            encoding="gbk",
        )
        return parse_tencent_market(raw)
    except Exception as exc:
        return _make_failure(
            "browser-tencent-market",
            f"Tencent market fetch failed: {exc}",
            _classify_error(exc),
        )


def fetch_eastmoney_quote(symbol: str) -> Dict[str, Any]:
    symbol = normalize_symbol(symbol)
    market = "1" if symbol.startswith("6") else "0"
    url = (
        "https://push2.eastmoney.com/api/qt/stock/get"
        f"?secid={market}.{symbol}"
        "&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f169,f170,f168"
    )
    try:
        raw = _request_text(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://quote.eastmoney.com/",
            },
            encoding="utf-8",
        )
        payload = json.loads(raw)
        data = payload.get("data") or {}
        if not data:
            raise ValueError("no data in response")

        def em_float(field: str) -> Optional[float]:
            value = data.get(field)
            if value in (None, ""):
                return None
            return float(value) / 100

        price = em_float("f43")
        pre_close = em_float("f60")
        change = em_float("f169")
        change_pct = em_float("f170")
        if price is None or price <= 0:
            raise ValueError("invalid price data")
        if pre_close not in (None, 0) and change is None:
            change = round(price - pre_close, 4)
        if pre_close not in (None, 0) and change_pct is None:
            change_pct = round((price - pre_close) / pre_close * 100, 4)

        return {
            "success": True,
            "source": "browser-eastmoney",
            "data": {
                "symbol": data.get("f57") or symbol,
                "name": data.get("f58") or symbol,
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "open": em_float("f46"),
                "high": em_float("f44"),
                "low": em_float("f45"),
                "pre_close": pre_close,
                "volume": data.get("f47"),
                "amount": data.get("f48"),
                "turnover_rate": em_float("f168"),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            },
            "quality_score": 84,
            "is_cached": False,
            "errors": [],
        }
    except Exception as exc:
        return _make_failure(
            "browser-eastmoney",
            f"Eastmoney fetch failed: {exc}",
            _classify_error(exc),
        )


def fetch_quote(symbol: str, source: str = "auto") -> Dict[str, Any]:
    if source == "tencent":
        return fetch_tencent_quote(symbol)
    if source == "eastmoney":
        return fetch_eastmoney_quote(symbol)

    primary = fetch_tencent_quote(symbol)
    if primary["success"]:
        return primary
    secondary = fetch_eastmoney_quote(symbol)
    if secondary["success"]:
        secondary["errors"] = primary.get("errors", [])
        return secondary
    secondary["errors"] = primary.get("errors", []) + secondary.get("errors", [])
    return secondary


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 browser_fetch.py <symbol> [tencent|eastmoney|auto|kline|intraday|market] [days]", file=sys.stderr)
        raise SystemExit(1)

    symbol = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else "auto"
    if source == "market":
        result = fetch_tencent_market()
    elif source == "kline":
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 120
        result = fetch_tencent_kline(symbol, days)
    elif source == "intraday":
        result = fetch_tencent_intraday(symbol)
    else:
        result = fetch_quote(symbol, source)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
