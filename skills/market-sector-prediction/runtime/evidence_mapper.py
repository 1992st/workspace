from __future__ import annotations

import json
from typing import Any, Dict


def _successful_vibe_results(vibe_results: Dict[str, Any]) -> list[str]:
    return sorted(
        name for name, result in vibe_results.items() if isinstance(result, dict) and result.get("status") == "ok"
    )


def _failed_vibe_results(vibe_results: Dict[str, Any]) -> list[str]:
    return sorted(
        name
        for name, result in vibe_results.items()
        if not isinstance(result, dict) or result.get("status") not in {"ok", "skipped"}
    )


def _skipped_vibe_results(vibe_results: Dict[str, Any]) -> list[str]:
    return sorted(
        name for name, result in vibe_results.items() if isinstance(result, dict) and result.get("status") == "skipped"
    )


def _payload_result_json(result: Dict[str, Any]) -> Dict[str, Any]:
    payload = result.get("payload") or {}
    structured = payload.get("structuredContent") or {}
    raw = structured.get("result")
    if raw is None:
        for item in payload.get("content") or []:
            if isinstance(item, dict) and item.get("type") == "text":
                raw = item.get("text")
                break
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _market_pattern_evidence(result: Dict[str, Any]) -> Dict[str, list[str]]:
    parsed = _payload_result_json(result)
    tool_results = parsed.get("results") or {}
    names = {"000001.SH": "上证指数", "399001.SZ": "深证成指", "399006.SZ": "创业板指"}
    evidence = {"bullish": [], "bearish": [], "neutral": [], "vibe_opinions": []}
    if not tool_results:
        return evidence

    evidence["vibe_opinions"].append("Vibe pattern_recognition 已基于 Win_Stock 本地指数 OHLCV 运行")
    for code, detail in tool_results.items():
        if not isinstance(detail, dict):
            continue
        name = names.get(str(code), str(code))
        slope = (detail.get("trend_slope") or {}).get("mean_slope")
        try:
            slope_value = float(slope)
        except Exception:
            slope_value = None
        if slope_value is not None:
            if slope_value > 1:
                evidence["bullish"].append(f"Vibe 形态识别: {name} 60日趋势斜率为正({slope_value:.2f})")
            elif slope_value < -1:
                evidence["bearish"].append(f"Vibe 形态识别: {name} 60日趋势斜率为负({slope_value:.2f})")
            else:
                evidence["neutral"].append(f"Vibe 形态识别: {name} 60日趋势斜率接近中性({slope_value:.2f})")

        support_resistance = detail.get("support_resistance") or {}
        supports = support_resistance.get("support") or []
        resistances = support_resistance.get("resistance") or []
        if supports:
            evidence["neutral"].append(f"Vibe 识别{name}支撑位: {', '.join(str(x) for x in supports[:3])}")
        if resistances:
            evidence["neutral"].append(f"Vibe 识别{name}压力位: {', '.join(str(x) for x in resistances[:3])}")

        patterns = detail.get("patterns") or {}
        broadening = len(patterns.get("broadening") or [])
        double_tops = len(patterns.get("double_tops") or [])
        double_bottoms = len(patterns.get("double_bottoms") or [])
        if broadening:
            evidence["neutral"].append(f"Vibe 形态识别: {name} 出现 {broadening} 个波动扩张形态")
        if double_tops:
            evidence["bearish"].append(f"Vibe 形态识别: {name} 出现 {double_tops} 个双顶风险形态")
        if double_bottoms:
            evidence["bullish"].append(f"Vibe 形态识别: {name} 出现 {double_bottoms} 个双底修复形态")
    return evidence


def _market_tool_notes(vibe_results: Dict[str, Any]) -> list[str]:
    notes = []
    market_data = vibe_results.get("market_data") or {}
    if market_data and market_data.get("status") != "ok":
        notes.append("Vibe get_market_data 未形成可用 A 股指数事实，已由 Win_Stock 本地快照接管事实口径")

    factor = vibe_results.get("factor_analysis") or {}
    if factor.get("status") == "skipped":
        notes.append(f"Vibe factor_analysis 已跳过：{factor.get('error') or 'standard mode uses local factor analysis'}")
    elif factor and factor.get("status") != "ok":
        notes.append("Vibe factor_analysis 未形成可用因子结果，未作为方向证据")

    backtest = vibe_results.get("backtest") or {}
    if backtest.get("status") == "skipped":
        notes.append(f"Vibe backtest 已跳过：{backtest.get('error') or 'standard mode uses local backtest'}")
    elif backtest and backtest.get("status") != "ok":
        notes.append("Vibe backtest 未纳入：当前指数历史数据 loader 未取到可回测数据")

    pattern = vibe_results.get("pattern_recognition") or {}
    if pattern.get("status") == "skipped":
        notes.append("Vibe pattern_recognition 已跳过：本地指数 OHLCV 历史不足")
    elif pattern and pattern.get("status") != "ok":
        notes.append("Vibe pattern_recognition 未形成可用形态结果")
    return notes


def default_market_evidence(local_snapshot: Dict[str, Any], vibe_results: Dict[str, Any]) -> Dict[str, Any]:
    breadth = local_snapshot.get("market_breadth") or {}
    bullish = []
    successful = _successful_vibe_results(vibe_results)
    bearish = []
    neutral = _market_tool_notes(vibe_results)
    if not successful:
        neutral.append("Vibe-Trading 暂无可用结构化研究结果，方向判断不引用外部研究观点")
    if breadth.get("advancers") and breadth.get("decliners"):
        ratio = _breadth_ratio(breadth)
        label = "抽样市场宽度" if breadth.get("sampled") else "市场宽度"
        text = f"{label}: 上涨 {breadth.get('advancers')} / 下跌 {breadth.get('decliners')}"
        if ratio is not None and ratio >= 0.58:
            bullish.append(text)
        elif ratio is not None and ratio <= 0.42:
            bearish.append(text)
        else:
            neutral.append(text)

    pattern = _market_pattern_evidence(vibe_results.get("pattern_recognition") or {})
    bullish.extend(pattern["bullish"])
    bearish.extend(pattern["bearish"])
    neutral.extend(pattern["neutral"])

    vibe_opinions = []
    if successful:
        vibe_opinions.append(f"Vibe-Trading 已成功调用工具: {', '.join(successful)}")
    vibe_opinions.extend(pattern["vibe_opinions"])
    return {
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "capital_flow": [],
        "market_breadth": [breadth] if breadth else [],
        "backtest_summary": [],
        "vibe_opinions": vibe_opinions,
        "next_day_checks": ["验证主要指数方向、成交额、市场宽度和资金流是否同步"],
    }


def _breadth_ratio(breadth: Dict[str, Any]) -> float | None:
    try:
        advancers = float(breadth.get("advancers"))
        decliners = float(breadth.get("decliners"))
    except Exception:
        return None
    total = advancers + decliners
    if total <= 0:
        return None
    return advancers / total


def default_sector_evidence(local_snapshot: Dict[str, Any], vibe_results: Dict[str, Any]) -> Dict[str, Any]:
    successful = _successful_vibe_results(vibe_results)
    failed = _failed_vibe_results(vibe_results)
    skipped = _skipped_vibe_results(vibe_results)
    bearish = []
    neutral = []
    if failed:
        neutral.append(f"Vibe-Trading 部分板块工具未形成可用结果: {', '.join(failed)}")
    if skipped:
        neutral.append(f"Vibe-Trading 部分板块工具已跳过: {', '.join(skipped)}")
    if not successful:
        bearish.append("Vibe-Trading 板块研究结果不可用，不能确认板块持续性")
    return {
        "bullish": [],
        "bearish": bearish,
        "neutral": neutral,
        "capital_flow": [],
        "relative_strength": [],
        "sector_stage": "",
        "leaders": [],
        "fade_signals": [],
        "backtest_summary": [],
        "vibe_opinions": [f"Vibe-Trading 已调用板块工具: {', '.join(successful)}"] if successful else [],
        "next_day_checks": ["验证板块涨跌、成分股同步率、龙头承接和资金方向"],
    }
