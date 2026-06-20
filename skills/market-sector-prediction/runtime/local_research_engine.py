from __future__ import annotations

import math
from typing import Any, Dict, List


def market_backtest(local_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    summaries = []
    for item in local_snapshot.get("indices") or []:
        rows = item.get("ohlcv") or []
        summary = _backtest_one(str(item.get("name") or item.get("code")), rows)
        if summary:
            summaries.append(summary)
    if not summaries:
        return {"status": "missing", "summary": [], "errors": ["local OHLCV is insufficient for backtest"]}
    win_rates = [item["win_rate"] for item in summaries if item.get("win_rate") is not None]
    avg_return = sum(item["strategy_return_pct"] for item in summaries) / len(summaries)
    avg_benchmark = sum(item["benchmark_return_pct"] for item in summaries) / len(summaries)
    max_drawdown = min(item["max_drawdown_pct"] for item in summaries)
    return {
        "status": "ok",
        "method": "local_ma5_ma20_index_backtest",
        "summary": summaries,
        "aggregate": {
            "avg_strategy_return_pct": round(avg_return, 2),
            "avg_benchmark_return_pct": round(avg_benchmark, 2),
            "avg_win_rate": round(sum(win_rates) / len(win_rates), 4) if win_rates else None,
            "worst_max_drawdown_pct": round(max_drawdown, 2),
        },
    }


def market_factor_analysis(local_snapshot: Dict[str, Any], pattern_evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    indices = local_snapshot.get("indices") or []
    breadth = local_snapshot.get("market_breadth") or {}
    capital_items = (local_snapshot.get("capital_flow") or {}).get("items") or []
    factors = []
    for item in indices:
        change = _num(item.get("change_pct"))
        change_5d = _num(item.get("change_5d"))
        change_20d = _num(item.get("change_20d"))
        amount = _num(item.get("amount"))
        amount_avg = _num(item.get("amount_avg_5d"))
        amount_ratio = amount / amount_avg if amount and amount_avg else None
        score = 0.0
        score += _bounded(change, 1.5)
        score += _bounded(change_5d, 3.0)
        if change_20d is not None:
            score += 0.5 * _bounded(change_20d, 6.0)
        if amount_ratio is not None:
            score += 0.6 if amount_ratio >= 1.08 else -0.4 if amount_ratio <= 0.92 else 0.0
        factors.append(
            {
                "name": item.get("name") or item.get("code"),
                "momentum_score": round(score, 3),
                "change_pct": change,
                "change_5d": change_5d,
                "change_20d": change_20d,
                "amount_ratio": round(amount_ratio, 3) if amount_ratio is not None else None,
            }
        )
    up_ratio = _breadth_ratio(breadth)
    breadth_score = 1.0 if up_ratio is not None and up_ratio >= 0.58 else -1.0 if up_ratio is not None and up_ratio <= 0.42 else 0.0
    proxy_scores = [item for item in capital_items if item.get("proxy")]
    proxy_score = _num(proxy_scores[0].get("net")) if proxy_scores else None
    risk_appetite = "risk_on" if breadth_score > 0 and (proxy_score is None or proxy_score >= 0) else "risk_off" if breadth_score < 0 or (proxy_score is not None and proxy_score < -0.03) else "mixed"
    sorted_factors = sorted(factors, key=lambda item: item["momentum_score"], reverse=True)
    return {
        "status": "ok" if factors else "missing",
        "method": "local_index_factor_model",
        "factors": sorted_factors,
        "style": {
            "dominant": _dominant_style(sorted_factors),
            "risk_appetite": risk_appetite,
            "breadth_up_ratio": round(up_ratio, 4) if up_ratio is not None else None,
            "market_flow_proxy": proxy_score,
        },
    }


def backtest_evidence(backtest: Dict[str, Any]) -> list[str]:
    if backtest.get("status") != "ok":
        return []
    aggregate = backtest.get("aggregate") or {}
    return [
        "本地回测 MA5/MA20: 平均策略收益 "
        f"{aggregate.get('avg_strategy_return_pct')}%，基准 {aggregate.get('avg_benchmark_return_pct')}%，"
        f"平均胜率 {aggregate.get('avg_win_rate')}，最差回撤 {aggregate.get('worst_max_drawdown_pct')}%"
    ]


def factor_evidence(factor: Dict[str, Any]) -> Dict[str, list[str]]:
    evidence = {"bullish": [], "bearish": [], "neutral": []}
    if factor.get("status") != "ok":
        return evidence
    style = factor.get("style") or {}
    dominant = style.get("dominant")
    risk = style.get("risk_appetite")
    if dominant:
        evidence["neutral"].append(f"本地因子风格: 当前相对占优为 {dominant}")
    if risk == "risk_on":
        evidence["bullish"].append("本地因子: 市场宽度/资金代理支持 risk-on")
    elif risk == "risk_off":
        evidence["bearish"].append("本地因子: 市场宽度或资金代理提示 risk-off")
    else:
        evidence["neutral"].append("本地因子: 风险偏好分歧，未形成单边风格")
    return evidence


def _backtest_one(name: str, rows: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    closes = [_num(row.get("close")) for row in rows]
    dates = [row.get("date") for row in rows]
    if len([value for value in closes if value is not None]) < 25:
        return None
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    wins = 0
    trades = 0
    holding = False
    entry = None
    for idx in range(20, len(closes)):
        close = closes[idx]
        prev_close = closes[idx - 1]
        if close is None or prev_close is None or prev_close == 0:
            continue
        ma5 = _ma(closes, idx, 5)
        ma20 = _ma(closes, idx, 20)
        should_hold = ma5 is not None and ma20 is not None and ma5 > ma20
        if should_hold:
            equity *= close / prev_close
            if not holding:
                holding = True
                entry = close
        elif holding:
            trades += 1
            if entry is not None and prev_close > entry:
                wins += 1
            holding = False
            entry = None
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, (equity - peak) / peak * 100)
    first = next((value for value in closes if value is not None), None)
    last = next((value for value in reversed(closes) if value is not None), None)
    if first is None or last is None or first == 0:
        return None
    benchmark = (last / first - 1) * 100
    strategy = (equity - 1) * 100
    return {
        "name": name,
        "start_date": next((date for date in dates if date), ""),
        "end_date": next((date for date in reversed(dates) if date), ""),
        "strategy_return_pct": round(strategy, 2),
        "benchmark_return_pct": round(benchmark, 2),
        "excess_return_pct": round(strategy - benchmark, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "trade_count": trades,
        "win_rate": round(wins / trades, 4) if trades else None,
    }


def _ma(values: List[float | None], end_idx: int, window: int) -> float | None:
    window_values = [value for value in values[end_idx - window + 1 : end_idx + 1] if value is not None]
    if len(window_values) < window:
        return None
    return sum(window_values) / window


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
        if math.isnan(number):
            return None
        return number
    except Exception:
        return None


def _bounded(value: float | None, threshold: float) -> float:
    if value is None:
        return 0.0
    return max(-1.0, min(1.0, value / threshold))


def _breadth_ratio(breadth: Dict[str, Any]) -> float | None:
    advancers = _num(breadth.get("advancers"))
    decliners = _num(breadth.get("decliners"))
    if advancers is None or decliners is None or advancers + decliners <= 0:
        return None
    return advancers / (advancers + decliners)


def _dominant_style(factors: List[Dict[str, Any]]) -> str:
    if not factors:
        return ""
    top = factors[0]
    name = str(top.get("name") or "")
    if "创业" in name:
        return "成长/高弹性"
    if "深证" in name:
        return "题材成长/中小盘弹性"
    if "上证" in name:
        return "权重/价值防守"
    return name
