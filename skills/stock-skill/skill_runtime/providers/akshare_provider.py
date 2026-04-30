from __future__ import annotations

import datetime as dt
from bisect import bisect_right
from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.utils import (
    infer_exchange,
    limit_items,
    normalize_symbol,
    normalize_timeframe,
    pick_number,
    pick_text,
    to_records,
)

try:
    import akshare as ak
except Exception:  # pragma: no cover
    ak = None


class AkshareProvider:
    name = "akshare"

    def __init__(self) -> None:
        if ak is None:
            raise RuntimeError("akshare is required")

    def quote_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        records = to_records(ak.stock_zh_a_spot_em())
        row = next((item for item in records if normalize_symbol(item.get("代码", "")) == symbol), None)
        if not row:
            raise LookupError(f"quote not found for {symbol}")
        price = pick_number(row, ["最新价", "price"])
        pre_close = pick_number(row, ["昨收", "pre_close"])
        change = price - pre_close if pre_close else pick_number(row, ["涨跌额"])
        change_pct = (change / pre_close * 100) if pre_close else pick_number(row, ["涨跌幅"])
        return {
            "symbol": symbol,
            "name": pick_text(row, ["名称", "name"], symbol),
            "price": price,
            "change": round(change, 4),
            "change_pct": round(change_pct, 4),
            "open": pick_number(row, ["今开", "开盘"]),
            "high": pick_number(row, ["最高"]),
            "low": pick_number(row, ["最低"]),
            "pre_close": pre_close,
            "volume": int(pick_number(row, ["成交量"])),
            "amount": pick_number(row, ["成交额"]),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "turnover_rate": pick_number(row, ["换手率"]),
            "amplitude": pick_number(row, ["振幅"]),
        }

    def quotes_batch_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbols = [normalize_symbol(item) for item in payload.get("symbols", [])]
        records = to_records(ak.stock_zh_a_spot_em())
        selected = [item for item in records if normalize_symbol(item.get("代码", "")) in symbols] if symbols else records
        items = [self._normalize_quote_row(item) for item in selected]
        advancers = sum(1 for item in items if item["change_pct"] > 0)
        decliners = sum(1 for item in items if item["change_pct"] < 0)
        flat_count = len(items) - advancers - decliners
        return {
            "items": limit_items(items, payload.get("limit")),
            "universe_size": len(items),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "advancers": advancers,
            "decliners": decliners,
            "flat_count": flat_count,
            "limit_up_count": sum(1 for item in items if item["change_pct"] >= 9.5),
            "limit_down_count": sum(1 for item in items if item["change_pct"] <= -9.5),
        }

    def kline_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        period = normalize_timeframe(payload.get("timeframe"))
        adjust = payload.get("adjust", "none")
        start_date = str(payload.get("start_time") or "").replace("-", "")[:8]
        end_date = str(payload.get("end_time") or "").replace("-", "")[:8]
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = "20200101"
        frame = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust="" if adjust == "none" else adjust,
        )
        records = to_records(
            frame.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "换手率": "turnover_rate",
                }
            )
        )
        bars = [
            {
                "date": str(item["date"]),
                "open": pick_number(item, ["open"]),
                "high": pick_number(item, ["high"]),
                "low": pick_number(item, ["low"]),
                "close": pick_number(item, ["close"]),
                "volume": pick_number(item, ["volume"]),
                "amount": pick_number(item, ["amount"]),
                "turnover_rate": pick_number(item, ["turnover_rate"]),
            }
            for item in records
        ]
        return {"symbol": symbol, "period": period, "adjust": adjust, "bars": limit_items(bars, payload.get("limit"))}

    def index_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        code = str(payload.get("index_code") or "sh000001").lower()
        index_code = {
            "sh000001": "000001",
            "sz399001": "399001",
            "sz399006": "399006",
        }.get(code, code.replace("sh", "").replace("sz", ""))
        frame = ak.stock_zh_index_daily_em(symbol=index_code)
        records = to_records(frame.tail(2))
        latest = records[-1]
        price = pick_number(latest, ["收盘", "close"])
        change_pct = None
        for key in ["涨跌幅", "change_pct"]:
            if latest.get(key) not in (None, ""):
                try:
                    change_pct = float(latest[key])
                    break
                except (TypeError, ValueError):
                    pass
        pre_close = pick_number(latest, ["昨收", "前收盘"], default=0.0)
        if pre_close <= 0 and len(records) > 1:
            pre_close = pick_number(records[-2], ["收盘", "close"])
        if change_pct is None:
            change_pct = ((price - pre_close) / pre_close * 100) if pre_close else 0.0
        return {
            "index_code": code,
            "index_name": pick_text({"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指"}, [code], code),
            "price": price,
            "change_pct": round(change_pct, 4),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "volume": pick_number(latest, ["成交量"]),
            "amount": pick_number(latest, ["成交额"]),
        }

    def trading_calendar_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_date = str(payload.get("date") or datetime.now().date().isoformat())
        dt = datetime.fromisoformat(raw_date)
        trade_dates = self._get_trade_dates()
        is_trading_day = dt.date() in trade_dates
        next_day = self._next_trade_date(trade_dates, dt.date())
        session = self._infer_session(dt.date())
        return {
            "date": dt.date().isoformat(),
            "is_trading_day": is_trading_day,
            "session": session,
            "next_trading_day": next_day.isoformat(),
        }

    def market_snapshot_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = self.quotes_batch_get(payload)
        total_amount = sum(item["amount"] for item in data["items"])
        avg_change = sum(item["change_pct"] for item in data["items"]) / len(data["items"]) if data["items"] else 0.0
        top_sector_list = []
        try:
            boards = to_records(ak.stock_board_industry_name_em())
            top_sector_list = [
                {
                    "sector": pick_text(item, ["板块名称"]),
                    "change_pct": pick_number(item, ["涨跌幅"]),
                }
                for item in boards[:5]
            ]
        except Exception:
            top_sector_list = []
        data.update(
            {
                "market_change_pct": round(avg_change, 4),
                "total_amount": round(total_amount, 2),
                "top_sector_list": top_sector_list,
            }
        )
        return data

    def news_stock_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        frame = ak.stock_news_em(symbol=symbol)
        events = []
        for item in to_records(frame):
            events.append(
                {
                    "title": pick_text(item, ["新闻标题", "标题"]),
                    "source": pick_text(item, ["文章来源", "来源"], "eastmoney"),
                    "publish_time": pick_text(item, ["发布时间", "时间"]),
                    "url": pick_text(item, ["新闻链接", "链接"]),
                }
            )
        return {"symbol": symbol, "events": limit_items(events, payload.get("limit") or 20)}

    def news_market_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        candidates = [
            getattr(ak, "stock_info_global_cls", None),
            getattr(ak, "stock_info_global_ths", None),
        ]
        for fn in candidates:
            if fn is None:
                continue
            frame = fn()
            events = [
                {
                    "title": pick_text(item, ["标题", "资讯标题"]),
                    "source": pick_text(item, ["来源"], "market"),
                    "publish_time": pick_text(item, ["发布时间", "时间"]),
                }
                for item in to_records(frame)
            ]
            if events:
                return {"events": limit_items(events, payload.get("limit") or 20)}
        raise LookupError("market news source unavailable")

    def flow_main_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        frame = ak.stock_individual_fund_flow(stock=symbol, market=infer_exchange(symbol).lower())
        latest = to_records(frame.tail(1))[0]
        return {
            "symbol": symbol,
            "date": pick_text(latest, ["日期"]),
            "main_net_inflow": pick_number(latest, ["主力净流入-净额", "主力净流入"]),
            "super_large_net": pick_number(latest, ["超大单净流入-净额"]),
            "large_net": pick_number(latest, ["大单净流入-净额"]),
            "medium_net": pick_number(latest, ["中单净流入-净额"]),
            "small_net": pick_number(latest, ["小单净流入-净额"]),
        }

    def flow_order_size_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = self.flow_main_get(payload)
        total = abs(data.get("super_large_net", 0)) + abs(data.get("large_net", 0)) + abs(data.get("medium_net", 0)) + abs(data.get("small_net", 0))
        if total <= 0:
            total = 1.0
        big = abs(data.get("super_large_net", 0)) + abs(data.get("large_net", 0))
        small = abs(data.get("small_net", 0))
        return {
            "date": data["date"],
            "big_order_ratio": round(big / total, 4),
            "small_order_ratio": round(small / total, 4),
            "buy_sell_imbalance": round(data["main_net_inflow"] / total, 4),
        }

    def fundamental_valuation_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        frame = ak.stock_zh_valuation_baidu(symbol=symbol)
        latest = to_records(frame.tail(1))[0]
        return {
            "symbol": symbol,
            "pe_ttm": pick_number(latest, ["市盈率TTM", "市盈率(TTM)", "pe_ttm"]),
            "pb": pick_number(latest, ["市净率", "pb"]),
            "market_cap": pick_number(latest, ["总市值", "market_cap", "总市值(元)"]),
            "ps_ttm": pick_number(latest, ["市销率", "ps"]),
        }

    def fundamental_metrics_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        frame = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按报告期")
        latest = to_records(frame.tail(1))[0]
        return {
            "report_date": pick_text(latest, ["报告期"]),
            "revenue_yoy": pick_number(latest, ["营业总收入同比增长率"]),
            "profit_yoy": pick_number(latest, ["净利润同比增长率"]),
            "roe": pick_number(latest, ["净资产收益率"]),
            "gross_margin": pick_number(latest, ["销售毛利率"]),
            "debt_ratio": pick_number(latest, ["资产负债率"]),
        }

    def etf_pcf_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        fund_code = normalize_symbol(payload.get("fund_code") or payload.get("symbol"))
        query_date = self._resolve_query_date(payload)
        session = self._availability_session(query_date)
        items: List[Dict[str, Any]] = []
        publish_time = ""
        source_name = "unavailable"
        for fn_name, kwargs in [
            ("fund_etf_pcf_em", {"symbol": fund_code}),
            ("fund_etf_pr_list_em", {"symbol": fund_code}),
        ]:
            fn = getattr(ak, fn_name, None)
            if fn is None:
                continue
            frame = fn(**kwargs)
            records = to_records(frame)
            if not records:
                continue
            source_name = fn_name
            publish_time = datetime.now().isoformat(timespec="seconds")
            items = [
                {
                    "symbol": self._safe_normalize_symbol(item.get("证券代码", item.get("成分券代码", item.get("code", "")))),
                    "name": pick_text(item, ["证券简称", "成分券名称", "name"]),
                    "quantity": pick_number(item, ["数量", "现金替代比例", "quantity"]),
                    "cash_substitution_flag": pick_text(item, ["现金替代标志", "申赎现金替代标志"]),
                }
                for item in records[:200]
            ]
            break
        return {
            "fund_code": fund_code,
            "date": query_date.isoformat(),
            "pcf_items": items,
            "cash_component": 0.0,
            "publish_time": publish_time,
            "availability": "pre_open_available",
            "session_constraint": "盘前可获取PCF，不能代表盘中实时净申赎",
            "is_pcf_not_real_flow": True,
            "source_hint": source_name,
        }

    def margin_balance_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        query_date = self._resolve_query_date(payload)
        if query_date >= datetime.now().date():
            previous_day = self._previous_trade_date(query_date)
            return {
                "symbol": symbol,
                "requested_date": query_date.isoformat(),
                "as_of_date": previous_day.isoformat(),
                "is_latest_trading_day": False,
                "availability": "previous_trading_day_only",
                "session_constraint": "融资融券余额按盘后或下一交易日口径处理，盘中不提供当日正式值",
                "financing_balance": 0.0,
                "financing_buy": 0.0,
                "financing_repay": 0.0,
                "securities_lending_balance": 0.0,
                "balance_change": 0.0,
            }
        detail = self._load_margin_detail(symbol, query_date)
        detail["availability"] = "post_close_only"
        detail["requested_date"] = query_date.isoformat()
        detail["is_latest_trading_day"] = True
        return detail

    def hsgt_top10_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query_date = self._resolve_query_date(payload)
        if query_date >= datetime.now().date() and self._availability_session(query_date) != "post":
            return {
                "date": query_date.isoformat(),
                "channel": "shanghai_connect",
                "availability": "post_close_only",
                "items": [],
                "notes": "沪股通十大活跃股以盘后确认数据为准",
            }
        items: List[Dict[str, Any]] = []
        source_name = "unavailable"
        for fn_name, kwargs in [
            ("stock_hsgt_top_10_em", {"symbol": "沪股通", "date": query_date.strftime("%Y%m%d")}),
            ("stock_hsgt_top_10_em", {"symbol": "沪股通", "market_type": "沪股通", "date": query_date.strftime("%Y%m%d")}),
        ]:
            fn = getattr(ak, fn_name, None)
            if fn is None:
                continue
            try:
                frame = fn(**kwargs)
            except TypeError:
                continue
            records = to_records(frame)
            if not records:
                continue
            source_name = fn_name
            items = [
                {
                    "symbol": self._safe_normalize_symbol(item.get("代码", item.get("股票代码", ""))),
                    "name": pick_text(item, ["名称", "股票名称"]),
                    "net_buy": pick_number(item, ["净买额", "净买入额"]),
                    "buy_amount": pick_number(item, ["买入金额", "买入成交额"]),
                    "sell_amount": pick_number(item, ["卖出金额", "卖出成交额"]),
                    "turnover": pick_number(item, ["成交额", "总成交额"]),
                }
                for item in records[:10]
            ]
            break
        return {
            "date": query_date.isoformat(),
            "channel": "shanghai_connect",
            "availability": "post_close_only",
            "items": items,
            "source_hint": source_name,
        }

    def lhb_detail_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        query_date = self._resolve_query_date(payload)
        if query_date >= datetime.now().date() and self._availability_session(query_date) != "post":
            return {
                "symbol": symbol,
                "date": query_date.isoformat(),
                "availability": "conditional_only",
                "eligible": False,
                "reason": "龙虎榜盘后确认，盘中不可用",
                "items": [],
                "institution_summary": {"buy_amount": 0.0, "sell_amount": 0.0},
                "northbound_seat_present": False,
            }
        items = self._load_lhb_items(symbol, query_date)
        if not items:
            return {
                "symbol": symbol,
                "date": query_date.isoformat(),
                "availability": "conditional_only",
                "eligible": False,
                "reason": "未满足当日交易公开信息条件或无公开记录",
                "items": [],
                "institution_summary": {"buy_amount": 0.0, "sell_amount": 0.0},
                "northbound_seat_present": False,
            }
        institution_buy = sum(item["buy_amount"] for item in items if item["seat_type"] == "institution")
        institution_sell = sum(item["sell_amount"] for item in items if item["seat_type"] == "institution")
        return {
            "symbol": symbol,
            "date": query_date.isoformat(),
            "availability": "conditional_only",
            "eligible": True,
            "reason": "存在当日龙虎榜公开记录",
            "items": items,
            "institution_summary": {"buy_amount": institution_buy, "sell_amount": institution_sell},
            "northbound_seat_present": any(item["seat_type"] == "northbound" for item in items),
        }

    def block_trade_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        query_date = self._resolve_query_date(payload)
        if query_date >= datetime.now().date() and self._availability_session(query_date) != "post":
            return {
                "symbol": symbol,
                "date": query_date.isoformat(),
                "availability": "post_close_only",
                "items": [],
                "total_amount": 0.0,
                "avg_discount_rate": 0.0,
                "buyer_seller_pairs": [],
                "notes": "大宗交易以盘后公开数据为准",
            }
        items = self._load_block_trade_items(symbol, query_date)
        total_amount = sum(item["amount"] for item in items)
        discount_values = [item["discount_rate"] for item in items if isinstance(item.get("discount_rate"), (int, float))]
        buyer_seller_pairs = [
            {
                "buyer": item["buyer"],
                "seller": item["seller"],
            }
            for item in items
        ]
        return {
            "symbol": symbol,
            "date": query_date.isoformat(),
            "availability": "post_close_only",
            "items": items,
            "total_amount": total_amount,
            "avg_discount_rate": round(sum(discount_values) / len(discount_values), 4) if discount_values else 0.0,
            "buyer_seller_pairs": buyer_seller_pairs,
        }

    def sector_map_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(payload["symbol"])
        primary_sector = self._get_primary_sector(symbol)
        try:
            concepts = self._get_concepts_for_symbol(symbol)
        except Exception:
            concepts = []
        sectors = [primary_sector] if primary_sector else []
        sectors.extend(item for item in concepts if item not in sectors)
        if not sectors:
            raise LookupError(f"sector mapping not found for {symbol}")
        return {"symbol": symbol, "sectors": sectors, "primary_sector": sectors[0], "concept_tags": concepts}

    def sector_heat_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sector = str(payload.get("sector") or "").strip()
        if not sector:
            raise ValueError("sector is required")
        boards = to_records(ak.stock_board_industry_name_em())
        row = next((item for item in boards if pick_text(item, ["板块名称"]) == sector), None)
        if not row:
            boards = to_records(ak.stock_board_concept_name_em())
            row = next((item for item in boards if pick_text(item, ["板块名称"]) == sector), None)
        if not row:
            raise LookupError(f"sector not found: {sector}")
        leader_symbols = []
        try:
            members = to_records(ak.stock_board_concept_cons_em(symbol=sector))
            leader_symbols = [normalize_symbol(item.get("代码", "")) for item in members[:5]]
        except Exception:
            try:
                members = to_records(ak.stock_board_industry_cons_em(symbol=sector))
                leader_symbols = [normalize_symbol(item.get("代码", "")) for item in members[:5]]
            except Exception:
                leader_symbols = []
        return {
            "sector": sector,
            "change_pct": pick_number(row, ["涨跌幅"]),
            "leader_symbols": leader_symbols,
            "sector_fund_flow": pick_number(row, ["主力净流入"]),
            "continuity_score": 0.6,
        }

    def _normalize_quote_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        symbol = normalize_symbol(row.get("代码", ""))
        price = pick_number(row, ["最新价"])
        pre_close = pick_number(row, ["昨收"])
        change = price - pre_close if pre_close else pick_number(row, ["涨跌额"])
        change_pct = (change / pre_close * 100) if pre_close else pick_number(row, ["涨跌幅"])
        return {
            "symbol": symbol,
            "name": pick_text(row, ["名称"], symbol),
            "price": price,
            "change": round(change, 4),
            "change_pct": round(change_pct, 4),
            "open": pick_number(row, ["今开"]),
            "high": pick_number(row, ["最高"]),
            "low": pick_number(row, ["最低"]),
            "pre_close": pre_close,
            "volume": int(pick_number(row, ["成交量"])),
            "amount": pick_number(row, ["成交额"]),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }

    def _get_trade_dates(self) -> List[dt.date]:
        frame = ak.tool_trade_date_hist_sina()
        records = to_records(frame)
        trade_dates: List[dt.date] = []
        for row in records:
            raw = row.get("trade_date")
            if isinstance(raw, dt.date):
                trade_dates.append(raw)
            elif raw:
                trade_dates.append(datetime.fromisoformat(str(raw)).date())
        if not trade_dates:
            raise LookupError("trade calendar unavailable")
        return sorted(trade_dates)

    def _next_trade_date(self, trade_dates: List[dt.date], target_date: dt.date) -> dt.date:
        idx = bisect_right(trade_dates, target_date)
        if idx >= len(trade_dates):
            raise LookupError(f"next trading day unavailable after {target_date.isoformat()}")
        return trade_dates[idx]

    def _infer_session(self, query_date: dt.date) -> str:
        today = datetime.now().date()
        if query_date < today:
            return "close"
        if query_date > today:
            return "pre"
        now_hour = datetime.now().hour
        if now_hour < 9:
            return "pre"
        if now_hour < 11:
            return "open"
        if now_hour < 13:
            return "noon"
        if now_hour < 15:
            return "open"
        return "post"

    def _resolve_query_date(self, payload: Dict[str, Any]) -> dt.date:
        raw_date = str(payload.get("date") or datetime.now().date().isoformat())
        return datetime.fromisoformat(raw_date[:10]).date()

    def _previous_trade_date(self, query_date: dt.date) -> dt.date:
        trade_dates = self._get_trade_dates()
        previous = None
        for value in trade_dates:
            if value >= query_date:
                break
            previous = value
        if previous is not None:
            return previous
        if trade_dates:
            return trade_dates[0]
        raise LookupError("previous trading day unavailable")

    def _availability_session(self, query_date: dt.date) -> str:
        if query_date < datetime.now().date():
            return "post"
        return self._infer_session(query_date)

    def _load_margin_detail(self, symbol: str, query_date: dt.date) -> Dict[str, Any]:
        date_text = query_date.strftime("%Y%m%d")
        candidates = [
            ("stock_margin_detail_sse", {"date": date_text}),
            ("stock_margin_detail_szse", {"date": date_text}),
            ("stock_margin_sse", {"start_date": date_text, "end_date": date_text}),
            ("stock_margin_szse", {"date": date_text}),
        ]
        for fn_name, kwargs in candidates:
            fn = getattr(ak, fn_name, None)
            if fn is None:
                continue
            try:
                frame = fn(**kwargs)
            except TypeError:
                continue
            row = self._find_symbol_row(to_records(frame), symbol)
            if row:
                financing_balance = pick_number(row, ["融资余额", "融资余额(元)", "融资余额(万元)"])
                financing_buy = pick_number(row, ["融资买入额", "融资买入额(元)", "融资买入额(万元)"])
                financing_repay = pick_number(row, ["融资偿还额", "融资偿还额(元)", "融资偿还额(万元)"])
                securities_lending_balance = pick_number(row, ["融券余额", "融券余量", "融券余额(元)", "融券余量(股)"])
                return {
                    "symbol": symbol,
                    "as_of_date": query_date.isoformat(),
                    "financing_balance": financing_balance,
                    "financing_buy": financing_buy,
                    "financing_repay": financing_repay,
                    "securities_lending_balance": securities_lending_balance,
                    "balance_change": financing_buy - financing_repay,
                }
        return {
            "symbol": symbol,
            "as_of_date": query_date.isoformat(),
            "financing_balance": 0.0,
            "financing_buy": 0.0,
            "financing_repay": 0.0,
            "securities_lending_balance": 0.0,
            "balance_change": 0.0,
        }

    def _load_lhb_items(self, symbol: str, query_date: dt.date) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for fn_name, kwargs in [
            ("stock_lhb_detail_em", {"start_date": query_date.isoformat(), "end_date": query_date.isoformat()}),
            ("stock_lhb_detail_daily_sina", {"date": query_date.isoformat()}),
        ]:
            fn = getattr(ak, fn_name, None)
            if fn is None:
                continue
            try:
                frame = fn(**kwargs)
            except TypeError:
                continue
            records = [
                row
                for row in to_records(frame)
                if self._safe_normalize_symbol(row.get("代码", row.get("股票代码", ""))) == symbol
            ]
            if not records:
                continue
            for row in records:
                seat_name = pick_text(row, ["营业部名称", "买方营业部", "卖方营业部", "席位名称"])
                items.append(
                    {
                        "seat_name": seat_name,
                        "seat_type": self._classify_lhb_seat(seat_name),
                        "buy_amount": pick_number(row, ["买入金额", "买入额"]),
                        "sell_amount": pick_number(row, ["卖出金额", "卖出额"]),
                        "net_amount": pick_number(row, ["净额", "净买额"]),
                        "reason": pick_text(row, ["上榜原因", "解读"]),
                    }
                )
            break
        return items

    def _load_block_trade_items(self, symbol: str, query_date: dt.date) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for fn_name, kwargs in [
            ("stock_dzjy_mrmx", {"start_date": query_date.isoformat(), "end_date": query_date.isoformat()}),
            ("stock_dzjy_mrmx", {"symbol": "A股", "start_date": query_date.isoformat(), "end_date": query_date.isoformat()}),
        ]:
            fn = getattr(ak, fn_name, None)
            if fn is None:
                continue
            try:
                frame = fn(**kwargs)
            except TypeError:
                continue
            records = [
                row
                for row in to_records(frame)
                if self._safe_normalize_symbol(row.get("证券代码", row.get("股票代码", row.get("代码", "")))) == symbol
            ]
            if not records:
                continue
            for row in records:
                amount = pick_number(row, ["成交额", "成交金额"])
                trade_price = pick_number(row, ["成交价", "价格"])
                close_price = pick_number(row, ["收盘价", "收盘价格"])
                discount_rate = 0.0
                if close_price > 0 and trade_price > 0:
                    discount_rate = round((trade_price - close_price) / close_price * 100, 4)
                items.append(
                    {
                        "price": trade_price,
                        "volume": pick_number(row, ["成交量", "成交股数"]),
                        "amount": amount,
                        "discount_rate": discount_rate,
                        "buyer": pick_text(row, ["买方营业部", "买方"]),
                        "seller": pick_text(row, ["卖方营业部", "卖方"]),
                    }
                )
            break
        return items

    def _find_symbol_row(self, records: List[Dict[str, Any]], symbol: str) -> Dict[str, Any] | None:
        for row in records:
            raw_code = row.get("代码", row.get("证券代码", row.get("股票代码", row.get("标的证券代码", ""))))
            if not raw_code:
                continue
            if self._safe_normalize_symbol(raw_code) == symbol:
                return row
        return None

    def _classify_lhb_seat(self, seat_name: str) -> str:
        if "机构专用" in seat_name:
            return "institution"
        if "沪股通" in seat_name or "深股通" in seat_name:
            return "northbound"
        return "broker"

    def _safe_normalize_symbol(self, raw_code: Any) -> str:
        try:
            return normalize_symbol(str(raw_code or ""))
        except ValueError:
            return ""

    def _get_primary_sector(self, symbol: str) -> str:
        frame = ak.stock_individual_info_em(symbol=symbol)
        item_map = {pick_text(row, ["item"]): pick_text(row, ["value"]) for row in to_records(frame)}
        return item_map.get("行业", "")

    def _get_concepts_for_symbol(self, symbol: str) -> List[str]:
        concepts: List[str] = []
        concept_list = to_records(ak.stock_board_concept_name_em())
        for concept in concept_list:
            name = pick_text(concept, ["板块名称"])
            if not name:
                continue
            try:
                members = to_records(ak.stock_board_concept_cons_em(symbol=name))
            except Exception:
                continue
            if any(normalize_symbol(item.get("代码", "")) == symbol for item in members):
                concepts.append(name)
        return concepts
