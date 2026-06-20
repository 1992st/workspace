#!/usr/bin/env python3
"""
Win_Stock alternative public data radar probe.

The probe only checks public, legal, traceable sources. It does not decide
trades; it records whether important evidence routes are reachable and which
signals may deserve follow-up in a report.
"""

from __future__ import annotations

import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests


WORKSPACE = Path(__file__).resolve().parents[3]
OUT_DIR = WORKSPACE / "data" / "health" / "alternative"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TIMEOUT = 8


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ms_since(start: float) -> float:
    return round((time.time() - start) * 1000, 2)


def request_text(url: str, timeout: int = DEFAULT_TIMEOUT, headers: Optional[Dict[str, str]] = None) -> str:
    request_headers = {
        "User-Agent": "Mozilla/5.0 Win_Stock alternative data radar",
        "Accept": "*/*",
    }
    if headers:
        request_headers.update(headers)
    response = requests.get(url, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def request_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    request_headers = {
        "User-Agent": "Mozilla/5.0 Win_Stock alternative data radar",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://data.eastmoney.com/",
    }
    if headers:
        request_headers.update(headers)
    response = requests.get(url, params=params, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def make_result(
    name: str,
    category: str,
    signal_level: str,
    success: bool,
    elapsed_ms: float,
    url: str,
    evidence_use: str,
    note: str,
    sample: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    structured: bool = False,
    record_count: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "signal_level": signal_level,
        "success": success,
        "status": "available" if success else "failed",
        "elapsed_ms": elapsed_ms,
        "fetched_at": now_iso(),
        "url": url,
        "traceable": True,
        "evidence_use": evidence_use,
        "note": note,
        "structured": structured,
        "record_count": record_count,
        "sample": sample,
        "error": error,
    }


def probe_page(
    name: str,
    category: str,
    signal_level: str,
    url: str,
    evidence_use: str,
    note: str,
    min_bytes: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    start = time.time()
    try:
        text = request_text(url, headers=headers)
        sample = {
            "bytes": len(text),
            "title_hint": text[:160].replace("\n", " ").replace("\r", " "),
        }
        if len(text) < min_bytes:
            raise ValueError(f"response too small: {len(text)} bytes")
        return make_result(name, category, signal_level, True, ms_since(start), url, evidence_use, note, sample=sample)
    except Exception as exc:
        return make_result(name, category, signal_level, False, ms_since(start), url, evidence_use, note, error=str(exc))


def compact_record(record: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    compacted = {}
    for key in keys:
        value = record.get(key)
        if value not in (None, "", [], {}):
            compacted[key] = value
    return compacted


def to_float(value: Any) -> Optional[float]:
    if value in (None, "", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct_change(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous in (None, 0):
        return None
    return round(((current - previous) / previous) * 100, 2)


def probe_eastmoney_datacenter(
    name: str,
    category: str,
    signal_level: str,
    report_name: str,
    filter_expr: str,
    evidence_use: str,
    note: str,
    sample_keys: List[str],
    sort_columns: Optional[str] = None,
    sort_types: Optional[str] = None,
    page_size: int = 10,
) -> Dict[str, Any]:
    start = time.time()
    base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params: Dict[str, Any] = {
        "reportName": report_name,
        "columns": "ALL",
        "pageNumber": 1,
        "pageSize": page_size,
        "filter": filter_expr,
        "source": "WEB",
    }
    if sort_columns:
        params["sortColumns"] = sort_columns
    if sort_types:
        params["sortTypes"] = sort_types
    try:
        payload = request_json(base_url, params=params)
        if payload.get("success") is False:
            raise ValueError(payload.get("message") or "eastmoney api returned success=false")
        result = payload.get("result") or {}
        records = result.get("data") or []
        if not isinstance(records, list):
            raise ValueError("eastmoney api result.data is not a list")
        sample_records = [compact_record(item, sample_keys) for item in records[:3] if isinstance(item, dict)]
        sample = {
            "count": len(records),
            "pages": result.get("pages"),
            "records": sample_records,
            "query_url": requests.Request("GET", base_url, params=params).prepare().url,
        }
        return make_result(
            name,
            category,
            signal_level,
            True,
            ms_since(start),
            sample["query_url"] or base_url,
            evidence_use,
            note,
            sample=sample,
            structured=True,
            record_count=len(records),
        )
    except Exception as exc:
        query_url = requests.Request("GET", base_url, params=params).prepare().url
        return make_result(
            name,
            category,
            signal_level,
            False,
            ms_since(start),
            query_url or base_url,
            evidence_use,
            note,
            error=str(exc),
            structured=True,
            record_count=0,
        )


def probe_google_news_records(symbol: str, name: str) -> Dict[str, Any]:
    query = quote_plus(f"{symbol} {name}")
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    start = time.time()
    try:
        text = request_text(url, headers={"Accept": "application/rss+xml,application/xml,text/xml,*/*"})
        root = ET.fromstring(text)
        records = []
        for item in root.findall("./channel/item")[:10]:
            records.append({
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "published_at": (item.findtext("pubDate") or "").strip(),
                "source": ((item.find("source").text if item.find("source") is not None else "") or "").strip(),
            })
        sample = {
            "count": len(records),
            "records": records[:5],
        }
        return make_result(
            "google_news_records",
            "sentiment_attention",
            "弱线索",
            True,
            ms_since(start),
            url,
            "新闻关注度和事件线索；用于发现新增报道标题和来源",
            "新闻标题只能作为待核验线索，不能替代公告原文或成交验证。",
            sample=sample,
            structured=True,
            record_count=len(records),
        )
    except Exception as exc:
        return make_result(
            "google_news_records",
            "sentiment_attention",
            "弱线索",
            False,
            ms_since(start),
            url,
            "新闻关注度和事件线索；用于发现新增报道标题和来源",
            "新闻标题只能作为待核验线索，不能替代公告原文或成交验证。",
            error=str(exc),
            structured=True,
            record_count=0,
        )


def build_probes(symbol: str, name: str) -> List[Dict[str, str]]:
    query = quote_plus(f"{symbol} {name}")
    return [
        {
            "name": "cninfo_home",
            "category": "announcement_regulatory",
            "signal_level": "可交易事实",
            "url": "https://www.cninfo.com.cn/new/index",
            "evidence_use": "公告原文入口；重大消息必须以公告原文为准",
            "note": "入口可用不代表已获取到具体公告，后续需按代码和日期搜索。",
        },
        {
            "name": "sse_announcements",
            "category": "announcement_regulatory",
            "signal_level": "可交易事实",
            "url": "https://www.sse.com.cn/disclosure/listedinfo/announcement/",
            "evidence_use": "沪市公告入口；用于核验公告、问询、处罚、重大事项",
            "note": "沪市股票优先查此入口和巨潮。",
        },
        {
            "name": "szse_announcements",
            "category": "announcement_regulatory",
            "signal_level": "可交易事实",
            "url": "https://www.szse.cn/disclosure/listed/notice/index.html",
            "evidence_use": "深市公告入口；用于核验公告、互动易和监管信息",
            "note": "深市股票优先查此入口和巨潮。",
        },
        {
            "name": "sse_margin",
            "category": "margin_leverage",
            "signal_level": "可交易事实",
            "url": "https://www.sse.com.cn/market/othersdata/margin/",
            "evidence_use": "沪市融资融券官方入口；用于杠杆情绪和滞后资金压力",
            "note": "通常为上一交易日/盘后口径，禁止当作盘中实时资金。",
        },
        {
            "name": "szse_margin",
            "category": "margin_leverage",
            "signal_level": "可交易事实",
            "url": "https://www.szse.cn/market/product/stock/margin/index.html",
            "evidence_use": "深市融资融券官方入口；用于杠杆情绪和滞后资金压力",
            "note": "通常为上一交易日/盘后口径，禁止当作盘中实时资金。",
        },
        {
            "name": "eastmoney_lhb",
            "category": "chip_behavior",
            "signal_level": "强线索",
            "url": "https://data.eastmoney.com/stock/lhb.html",
            "evidence_use": "龙虎榜入口；盘后条件性披露，用于席位和短线资金痕迹",
            "note": "未上榜不是利空；盘中不得硬分析席位。",
        },
        {
            "name": "eastmoney_block_trade",
            "category": "chip_behavior",
            "signal_level": "强线索",
            "url": "https://data.eastmoney.com/dzjy/",
            "evidence_use": "大宗交易入口；用于折价率、连续性和潜在筹码转移",
            "note": "单笔大宗不能直接定性利好或利空。",
        },
        {
            "name": "csindex",
            "category": "etf_index_linkage",
            "signal_level": "强线索",
            "url": "https://www.csindex.com.cn/",
            "evidence_use": "指数和成分权重入口；用于 ETF/指数联动和成分股影响",
            "note": "指数/ETF 信号必须和个股相对强弱交叉验证。",
        },
        {
            "name": "gov_procurement",
            "category": "industry_weak_signal",
            "signal_level": "弱线索",
            "url": f"http://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=0&dbselect=bidx&kw={query}",
            "evidence_use": "政府采购搜索；用于订单和经营弱信号",
            "note": "单一中标/采购线索不能直接推导业绩改善。",
        },
        {
            "name": "cebpubservice",
            "category": "industry_weak_signal",
            "signal_level": "弱线索",
            "url": "https://www.cebpubservice.com/",
            "evidence_use": "招投标公共服务平台入口；用于中标和项目弱信号",
            "note": "需要后续按股票名称、子公司、产品关键词搜索。",
        },
        {
            "name": "google_news_query",
            "category": "sentiment_attention",
            "signal_level": "弱线索",
            "url": f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "evidence_use": "新闻关注度和事件线索；用于发现新增报道",
            "note": "新闻热度不是买盘，必须查一手公告和成交验证。",
        },
    ]


def build_structured_probes(symbol: str, name: str) -> List[Dict[str, Any]]:
    symbol = symbol.zfill(6)
    return [
        probe_eastmoney_datacenter(
            "eastmoney_margin_records",
            "margin_leverage",
            "可交易事实",
            "RPTA_WEB_RZRQ_GGMX",
            f'(scode="{symbol}")',
            "东方财富融资融券明细；用于补充融资余额、融资买入、偿还、融券余量等滞后杠杆情绪",
            "该数据通常滞后一交易日，禁止当作盘中实时资金。",
            [
                "DATE",
                "SCODE",
                "SECNAME",
                "RZYE",
                "RZMRE",
                "RZCHE",
                "RZJME",
                "RQYL",
                "RQYE",
                "RZRQYE",
                "SPJ",
                "ZDF",
            ],
            sort_columns="DATE",
            sort_types="-1",
        ),
        probe_eastmoney_datacenter(
            "eastmoney_lhb_records",
            "chip_behavior",
            "强线索",
            "RPT_DAILYBILLBOARD_DETAILS",
            f'(SECURITY_CODE="{symbol}")',
            "东方财富龙虎榜结构化记录；用于盘后条件性披露的短线资金痕迹",
            "未上榜不能视为利空；盘中不得硬分析游资席位。",
            [
                "TRADE_DATE",
                "SECURITY_CODE",
                "SECURITY_NAME_ABBR",
                "EXPLANATION",
                "BILLBOARD_NET_AMT",
                "BILLBOARD_BUY_AMT",
                "BILLBOARD_SELL_AMT",
                "CLOSE_PRICE",
                "CHANGE_RATE",
                "TURNOVERRATE",
            ],
            sort_columns="TRADE_DATE",
            sort_types="-1",
        ),
        probe_eastmoney_datacenter(
            "eastmoney_block_trade_records",
            "chip_behavior",
            "强线索",
            "RPT_DATA_BLOCKTRADE",
            f'(SECURITY_CODE="{symbol}")',
            "东方财富大宗交易结构化记录；用于折价率、连续性和筹码转移线索",
            "单笔大宗交易不能直接定性利好或利空，需要结合折价率、连续性和后续价格。",
            [
                "TRADE_DATE",
                "SECURITY_CODE",
                "SECURITY_NAME_ABBR",
                "DEAL_PRICE",
                "PREMIUM_RATIO",
                "DEAL_VOLUME",
                "DEAL_AMT",
                "BUYER_NAME",
                "SELLER_NAME",
                "CLOSE_PRICE",
                "CHANGE_RATE",
            ],
            sort_columns="TRADE_DATE",
            sort_types="-1",
        ),
        probe_google_news_records(symbol, name),
    ]


def records_for(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    sample = result.get("sample") or {}
    records = sample.get("records") or []
    return [record for record in records if isinstance(record, dict)]


def summarize_margin(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    latest = records[0] if records else {}
    previous = records[1] if len(records) > 1 else {}
    latest_balance = to_float(latest.get("RZYE"))
    previous_balance = to_float(previous.get("RZYE"))
    net_buy = to_float(latest.get("RZJME"))
    financing_buy = to_float(latest.get("RZMRE"))
    financing_repay = to_float(latest.get("RZCHE"))
    lending_qty = to_float(latest.get("RQYL"))
    return {
        "type": "margin_leverage",
        "signal_level": "可交易事实",
        "source": "eastmoney_margin_records",
        "source_time": latest.get("DATE"),
        "observation": {
            "financing_balance": latest_balance,
            "financing_balance_change_pct_vs_prev_record": pct_change(latest_balance, previous_balance),
            "financing_net_buy": net_buy,
            "financing_buy": financing_buy,
            "financing_repay": financing_repay,
            "securities_lending_quantity": lending_qty,
        },
        "interpretation": "融资融券为滞后口径，只能用于杠杆情绪和压力变化，不能当作盘中实时资金。",
        "impact": "仅作观察",
        "follow_up": "结合价格、成交额和下一交易日融资余额变化验证是否为融资盘加仓或被动承接。",
    }


def summarize_lhb(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    latest = records[0] if records else {}
    net_amount = to_float(latest.get("BILLBOARD_NET_AMT"))
    impact = "仅作观察"
    if net_amount is not None:
        impact = "增强" if net_amount > 0 else "削弱"
    return {
        "type": "lhb_chip_behavior",
        "signal_level": "强线索",
        "source": "eastmoney_lhb_records",
        "source_time": latest.get("TRADE_DATE"),
        "observation": {
            "latest_reason": latest.get("EXPLANATION"),
            "latest_net_amount": net_amount,
            "latest_buy_amount": to_float(latest.get("BILLBOARD_BUY_AMT")),
            "latest_sell_amount": to_float(latest.get("BILLBOARD_SELL_AMT")),
            "record_count_in_sample": len(records),
        },
        "interpretation": "龙虎榜是盘后条件性披露，样本少时只能提示短线资金痕迹，不能在盘中硬推席位行为。",
        "impact": impact,
        "follow_up": "若近期无新上榜，不应据此推断游资态度；若有新上榜，需看席位连续性和次日承接。",
    }


def summarize_block_trade(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    latest = records[0] if records else {}
    premium_ratio = to_float(latest.get("PREMIUM_RATIO"))
    impact = "仅作观察"
    if premium_ratio is not None:
        impact = "削弱" if premium_ratio < -3 else ("增强" if premium_ratio > 1 else "仅作观察")
    return {
        "type": "block_trade_chip_transfer",
        "signal_level": "强线索",
        "source": "eastmoney_block_trade_records",
        "source_time": latest.get("TRADE_DATE"),
        "observation": {
            "latest_deal_price": to_float(latest.get("DEAL_PRICE")),
            "latest_premium_ratio": premium_ratio,
            "latest_deal_amount": to_float(latest.get("DEAL_AMT")),
            "buyer": latest.get("BUYER_NAME"),
            "seller": latest.get("SELLER_NAME"),
            "record_count_in_sample": len(records),
        },
        "interpretation": "大宗交易提示潜在筹码转移；单笔折溢价不能直接定性利好利空，要看连续性和后续价格。",
        "impact": impact,
        "follow_up": "观察是否连续折价成交，以及二级市场是否放量承接或继续走弱。",
    }


def summarize_news(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    titles = [str(record.get("title") or "") for record in records]
    risk_words = ["减持", "质押", "处罚", "问询", "立案", "亏损", "下滑", "冻结", "诉讼"]
    positive_words = ["回购", "增持", "中标", "增长", "获批", "分红", "重组"]
    risk_hits = [word for word in risk_words if any(word in title for title in titles)]
    positive_hits = [word for word in positive_words if any(word in title for title in titles)]
    impact = "仅作观察"
    if risk_hits and not positive_hits:
        impact = "削弱"
    elif positive_hits and not risk_hits:
        impact = "增强"
    return {
        "type": "news_attention",
        "signal_level": "弱线索",
        "source": "google_news_records",
        "source_time": records[0].get("published_at") if records else None,
        "observation": {
            "news_count_in_sample": len(records),
            "risk_keywords": risk_hits,
            "positive_keywords": positive_hits,
            "latest_titles": titles[:3],
        },
        "interpretation": "新闻热度只代表注意力，不代表真实买盘；标题必须追溯公告原文或权威报道。",
        "impact": impact,
        "follow_up": "对包含风险词或利好词的标题，优先查公告原文和成交验证，避免标题党误导。",
    }


def build_insights(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name = {item.get("name"): item for item in results if isinstance(item, dict) and item.get("success")}
    insights: List[Dict[str, Any]] = []
    if "eastmoney_margin_records" in by_name:
        insights.append(summarize_margin(records_for(by_name["eastmoney_margin_records"])))
    if "eastmoney_lhb_records" in by_name:
        insights.append(summarize_lhb(records_for(by_name["eastmoney_lhb_records"])))
    if "eastmoney_block_trade_records" in by_name:
        insights.append(summarize_block_trade(records_for(by_name["eastmoney_block_trade_records"])))
    if "google_news_records" in by_name:
        insights.append(summarize_news(records_for(by_name["google_news_records"])))
    return insights


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    available = [item for item in results if item["success"]]
    failed = [item for item in results if not item["success"]]
    structured = [item for item in results if item.get("structured")]
    by_category: Dict[str, Dict[str, int]] = {}
    for item in results:
        bucket = by_category.setdefault(item["category"], {"available": 0, "failed": 0})
        bucket["available" if item["success"] else "failed"] += 1
    return {
        "available": len(available),
        "failed": len(failed),
        "structured_sources": len(structured),
        "structured_record_count": sum(int(item.get("record_count") or 0) for item in structured),
        "by_category": by_category,
        "usable_sources": [item["name"] for item in available],
        "failed_sources": [item["name"] for item in failed],
    }


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) >= 2 else "601211"
    stock_name = sys.argv[2] if len(sys.argv) >= 3 else symbol
    results = [
        probe_page(
            item["name"],
            item["category"],
            item["signal_level"],
            item["url"],
            item["evidence_use"],
            item["note"],
        )
        for item in build_probes(symbol, stock_name)
    ]
    results.extend(build_structured_probes(symbol, stock_name))
    insights = build_insights(results)
    report = {
        "success": True,
        "source": "alternative_data_probe",
        "fetched_at": now_iso(),
        "symbol": symbol,
        "stock_name": stock_name,
        "summary": summarize(results),
        "insights": insights,
        "results": results,
        "discipline": [
            "非常规数据只能作为线索，不能单独决定买卖。",
            "无公告原文，不得把重大消息写成确定事实。",
            "弱线索必须等待价格、成交、公告或多源验证。",
        ],
    }
    output_path = OUT_DIR / f"alternative_probe_{symbol}_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["saved_to"] = str(output_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
