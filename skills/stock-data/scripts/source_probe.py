#!/usr/bin/env python3
"""
Win_Stock public data source probe.

This script verifies practical, low-cost data routes without depending on
premium accounts. It is intentionally small and explicit: each probe has its
own timeout, field check, and suggested fallback.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode

import requests


WORKSPACE = Path(__file__).resolve().parents[3]
OUT_DIR = WORKSPACE / "data" / "health" / "sources"
OUT_DIR.mkdir(parents=True, exist_ok=True)


DEFAULT_SYMBOLS = ["601211", "002241", "600406"]
DEFAULT_TIMEOUT = 8


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ms_since(start: float) -> float:
    return round((time.time() - start) * 1000, 2)


def safe_float(value: Any) -> Optional[float]:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except Exception:
        return None


def market_prefix(symbol: str) -> str:
    return "1" if symbol.startswith(("6", "9")) else "0"


def request_text(url: str, timeout: int = DEFAULT_TIMEOUT, headers: Optional[Dict[str, str]] = None) -> str:
    default_headers = {
        "User-Agent": "Mozilla/5.0 Win_Stock source probe",
        "Accept": "*/*",
    }
    if headers:
        default_headers.update(headers)
    resp = requests.get(url, timeout=timeout, headers=default_headers)
    resp.raise_for_status()
    return resp.text


def ok(
    name: str,
    source_type: str,
    elapsed_ms: float,
    data: Any,
    required_fields: List[str],
    present_fields: List[str],
    note: str = "",
) -> Dict[str, Any]:
    missing = [field for field in required_fields if field not in present_fields]
    completeness = 1.0 if not required_fields else round((len(required_fields) - len(missing)) / len(required_fields), 3)
    status = "healthy" if completeness == 1.0 else "degraded"
    return {
        "name": name,
        "source_type": source_type,
        "status": status,
        "success": True,
        "elapsed_ms": elapsed_ms,
        "fetched_at": now_iso(),
        "field_completeness": completeness,
        "required_fields": required_fields,
        "present_fields": present_fields,
        "missing_fields": missing,
        "sample": data,
        "error": None,
        "note": note,
    }


def fail(name: str, source_type: str, elapsed_ms: float, error: str, note: str = "") -> Dict[str, Any]:
    return {
        "name": name,
        "source_type": source_type,
        "status": "failed",
        "success": False,
        "elapsed_ms": elapsed_ms,
        "fetched_at": now_iso(),
        "field_completeness": 0.0,
        "required_fields": [],
        "present_fields": [],
        "missing_fields": [],
        "sample": None,
        "error": error,
        "note": note,
    }


def probe_tencent_quote(symbol: str) -> Dict[str, Any]:
    name = f"tencent_quote:{symbol}"
    start = time.time()
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        text = request_text(f"https://qt.gtimg.cn/q={prefix}{symbol}")
        if "~" not in text:
            raise ValueError("unexpected response")
        payload = text.split('"')[1]
        parts = payload.split("~")
        data = {
            "name": parts[1] if len(parts) > 1 else None,
            "code": symbol,
            "price": safe_float(parts[3] if len(parts) > 3 else None),
            "pre_close": safe_float(parts[4] if len(parts) > 4 else None),
            "open": safe_float(parts[5] if len(parts) > 5 else None),
            "volume": safe_float(parts[6] if len(parts) > 6 else None),
        }
        present = [key for key, value in data.items() if value not in (None, "")]
        return ok(name, "http_quote", ms_since(start), data, ["price", "pre_close", "open", "volume"], present)
    except Exception as exc:
        return fail(name, "http_quote", ms_since(start), str(exc), "Fallback for AkShare quote/full spot.")


def probe_tencent_kline(symbol: str) -> Dict[str, Any]:
    name = f"tencent_kline:{symbol}"
    start = time.time()
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        text = request_text(f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix}{symbol},day,,,20,qfq")
        parsed = json.loads(text)
        rows = (((parsed.get("data") or {}).get(f"{prefix}{symbol}") or {}).get("qfqday") or [])
        bars = []
        for row in rows[-20:]:
            if len(row) >= 6:
                bars.append({
                    "date": row[0],
                    "open": safe_float(row[1]),
                    "close": safe_float(row[2]),
                    "high": safe_float(row[3]),
                    "low": safe_float(row[4]),
                    "volume": safe_float(row[5]),
                })
        present = ["bars", "count"] if bars else []
        return ok(name, "http_kline", ms_since(start), {"count": len(bars), "latest": bars[-1] if bars else None}, ["bars", "count"], present, "Primary K-line fallback when AkShare/Eastmoney fail.")
    except Exception as exc:
        return fail(name, "http_kline", ms_since(start), str(exc), "Use local cache if Tencent K-line fails.")


def probe_tencent_intraday(symbol: str) -> Dict[str, Any]:
    name = f"tencent_intraday:{symbol}"
    start = time.time()
    try:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        text = request_text(f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?code={prefix}{symbol}")
        parsed = json.loads(text)
        rows = ((((parsed.get("data") or {}).get(f"{prefix}{symbol}") or {}).get("data") or {}).get("data") or [])
        sample = rows[-1] if rows else None
        present = ["bars", "count"] if rows else []
        return ok(name, "http_intraday", ms_since(start), {"count": len(rows), "latest": sample}, ["bars", "count"], present, "Primary intraday fallback; enables do-T only when fresh.")
    except Exception as exc:
        return fail(name, "http_intraday", ms_since(start), str(exc), "No intraday means no do-T plan.")


def probe_tencent_market() -> Dict[str, Any]:
    name = "tencent_market_indices"
    start = time.time()
    try:
        text = request_text(
            "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006",
            headers={"Referer": "https://stock.finance.qq.com/"},
        )
        expected = ["sh000001", "sz399001", "sz399006"]
        indices = []
        for code in expected:
            if f"v_{code}" not in text:
                continue
            line = next((item for item in text.split(";") if f"v_{code}" in item), "")
            parts = line.split('"')[1].split("~") if '"' in line else []
            if len(parts) > 33:
                indices.append({
                    "code": code,
                    "price": safe_float(parts[3]),
                    "pre_close": safe_float(parts[4]),
                    "open": safe_float(parts[5]),
                    "change": safe_float(parts[31]),
                    "change_pct": safe_float(parts[32]),
                    "high": safe_float(parts[33]),
                    "low": safe_float(parts[34]),
                })
        present = ["indices", "count"] if len(indices) >= 2 else []
        return ok(
            name,
            "http_market",
            ms_since(start),
            {"count": len(indices), "indices": indices},
            ["indices", "count"],
            present,
            "Index fallback only; market breadth still requires Eastmoney/AkShare.",
        )
    except Exception as exc:
        return fail(name, "http_market", ms_since(start), str(exc), "Use cache and mark market judgment degraded.")


def probe_eastmoney_quote(symbol: str) -> Dict[str, Any]:
    name = f"eastmoney_quote:{symbol}"
    start = time.time()
    try:
        secid = f"{market_prefix(symbol)}.{symbol}"
        params = {
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "2",
            "invt": "2",
            "fields": "f43,f57,f58,f60,f46,f44,f45,f47,f48,f169,f170",
            "secid": secid,
        }
        text = request_text(f"https://push2.eastmoney.com/api/qt/stock/get?{urlencode(params)}")
        parsed = json.loads(text)
        raw = parsed.get("data") or {}
        data = {
            "code": raw.get("f57"),
            "name": raw.get("f58"),
            "price": safe_float(raw.get("f43")),
            "pre_close": safe_float(raw.get("f60")),
            "open": safe_float(raw.get("f46")),
            "high": safe_float(raw.get("f44")),
            "low": safe_float(raw.get("f45")),
            "volume": safe_float(raw.get("f47")),
            "amount": safe_float(raw.get("f48")),
            "change_pct": safe_float(raw.get("f170")),
        }
        if data["price"] is not None and data["price"] > 1000:
            for key in ("price", "pre_close", "open", "high", "low"):
                if data[key] is not None:
                    data[key] = round(data[key] / 100, 4)
        present = [key for key, value in data.items() if value not in (None, "")]
        return ok(name, "http_quote", ms_since(start), data, ["price", "pre_close", "open", "volume", "amount"], present)
    except Exception as exc:
        return fail(name, "http_quote", ms_since(start), str(exc), "Fallback for quote and sector mapping.")


def probe_eastmoney_kline(symbol: str) -> Dict[str, Any]:
    name = f"eastmoney_kline:{symbol}"
    start = time.time()
    try:
        secid = f"{market_prefix(symbol)}.{symbol}"
        params = {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "secid": secid,
            "beg": "20250101",
            "end": "20500101",
            "lmt": "5",
        }
        text = request_text(f"https://push2his.eastmoney.com/api/qt/stock/kline/get?{urlencode(params)}")
        parsed = json.loads(text)
        rows = ((parsed.get("data") or {}).get("klines") or [])[-5:]
        bars = []
        for row in rows:
            parts = row.split(",")
            if len(parts) >= 6:
                bars.append({
                    "date": parts[0],
                    "open": safe_float(parts[1]),
                    "close": safe_float(parts[2]),
                    "high": safe_float(parts[3]),
                    "low": safe_float(parts[4]),
                    "volume": safe_float(parts[5]),
                })
        present = ["bars", "count"] if bars else []
        return ok(name, "http_kline", ms_since(start), {"count": len(bars), "bars": bars}, ["bars", "count"], present)
    except Exception as exc:
        return fail(name, "http_kline", ms_since(start), str(exc), "Fallback for AkShare daily K line.")


def probe_akshare(symbol: str) -> List[Dict[str, Any]]:
    probes: List[Dict[str, Any]] = []
    if importlib.util.find_spec("akshare") is None:
        return [fail("akshare_import", "python_package", 0, "akshare not installed")]
    import akshare as ak

    start = time.time()
    try:
        frame = ak.stock_zh_a_spot_em()
        records = frame.head(3).to_dict(orient="records")
        present = list(records[0].keys()) if records else []
        probes.append(ok("akshare_spot_em", "akshare", ms_since(start), {"rows": len(frame), "sample": records}, ["代码", "名称", "最新价", "涨跌幅"], present))
    except Exception as exc:
        probes.append(fail("akshare_spot_em", "akshare", ms_since(start), str(exc), "Use Tencent/Eastmoney quote fallback."))

    start = time.time()
    try:
        frame = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20250101", end_date="20500101", adjust="qfq")
        records = frame.tail(5).to_dict(orient="records")
        present = list(records[0].keys()) if records else []
        probes.append(ok(f"akshare_kline:{symbol}", "akshare", ms_since(start), {"rows": len(frame), "sample": records}, ["日期", "开盘", "收盘", "最高", "最低", "成交量"], present))
    except Exception as exc:
        probes.append(fail(f"akshare_kline:{symbol}", "akshare", ms_since(start), str(exc), "Use Eastmoney HTTP K-line fallback."))

    return probes


def probe_official_pages() -> List[Dict[str, Any]]:
    targets = [
        ("cninfo_home", "official_disclosure", "https://www.cninfo.com.cn/new/index", "公告原文入口"),
        ("sse_announcements", "official_disclosure", "https://www.sse.com.cn/disclosure/listedinfo/announcement/", "沪市公告入口"),
        ("szse_home", "official_disclosure", "https://www.szse.cn/", "深市公告/互动入口"),
        ("sse_margin", "official_margin", "https://www.sse.com.cn/market/othersdata/margin/sum/", "沪市融资融券入口"),
        ("eastmoney_data", "public_data_center", "https://data.eastmoney.com/", "东方财富数据中心入口"),
    ]
    results = []
    for name, source_type, url, note in targets:
        start = time.time()
        try:
            text = request_text(url, timeout=DEFAULT_TIMEOUT)
            sample = {"url": url, "bytes": len(text), "title_hint": text[:120].replace("\n", " ")}
            present = ["bytes"] if len(text) > 100 else []
            results.append(ok(name, source_type, ms_since(start), sample, ["bytes"], present, note))
        except Exception as exc:
            results.append(fail(name, source_type, ms_since(start), str(exc), note))
    return results


def probe_optional_packages() -> List[Dict[str, Any]]:
    results = []
    for pkg, env_name, note in [
        ("baostock", "", "Install to add a free historical quote fallback."),
        ("tushare", "TUSHARE_TOKEN", "Install and set TUSHARE_TOKEN to add standardized Pro data."),
    ]:
        start = time.time()
        installed = importlib.util.find_spec(pkg) is not None
        token_ok = True if not env_name else bool(os.environ.get(env_name))
        data = {"package": pkg, "installed": installed, "env": env_name or None, "env_configured": token_ok}
        if installed and token_ok:
            results.append(ok(f"{pkg}_ready", "optional_package", ms_since(start), data, ["installed", "env_configured"], ["installed", "env_configured"], note))
        else:
            missing = []
            if not installed:
                missing.append("package not installed")
            if installed and not token_ok:
                missing.append(f"{env_name} not configured")
            results.append(fail(f"{pkg}_ready", "optional_package", ms_since(start), "; ".join(missing), note))
    return results


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {"healthy": 0, "degraded": 0, "failed": 0}
    for item in results:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    usable = [item["name"] for item in results if item["success"]]
    failed = [item["name"] for item in results if not item["success"]]
    return {"counts": summary, "usable_sources": usable, "failed_sources": failed}


def main() -> None:
    symbols = sys.argv[1:] or DEFAULT_SYMBOLS
    first_symbol = symbols[0]
    results: List[Dict[str, Any]] = []
    results.extend(probe_optional_packages())
    results.extend(probe_akshare(first_symbol))
    for symbol in symbols:
        results.append(probe_tencent_quote(symbol))
        results.append(probe_eastmoney_quote(symbol))
    results.append(probe_tencent_market())
    results.append(probe_tencent_kline(first_symbol))
    results.append(probe_eastmoney_kline(first_symbol))
    results.append(probe_tencent_intraday(first_symbol))
    results.extend(probe_official_pages())

    report = {
        "success": True,
        "source": "source_probe",
        "fetched_at": now_iso(),
        "symbols": symbols,
        "summary": summarize(results),
        "results": results,
        "routing_recommendation": {
            "quote": ["tencent_quote", "eastmoney_quote", "akshare_spot_em", "local_cache"],
            "market": ["akshare_market_with_breadth", "tencent_market_indices", "local_cache"],
            "kline": ["tencent_kline", "akshare_kline", "eastmoney_kline", "local_cache"],
            "intraday": ["tencent_intraday", "local_cache"],
            "announcements": ["cninfo_home", "sse_announcements", "szse_home"],
            "margin": ["sse_margin", "akshare_margin", "local_cache_previous_trade_day"],
            "optional_next": ["install baostock for historical fallback", "install tushare and configure TUSHARE_TOKEN if needed"],
        },
    }
    output_path = OUT_DIR / f"source_probe_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    report["saved_to"] = str(output_path)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
