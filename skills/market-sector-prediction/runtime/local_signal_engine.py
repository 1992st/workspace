from __future__ import annotations

from typing import Any, Dict, List


def market_local_signal(
    local_snapshot: Dict[str, Any],
    horizon: str,
    constraints: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    indices = local_snapshot.get("indices") or []
    by_code = {str(item.get("code")): item for item in indices}
    sh = by_code.get("000001") or (indices[0] if indices else {})
    sz = by_code.get("399001") or {}
    cyb = by_code.get("399006") or {}

    bullish: List[str] = []
    bearish: List[str] = []
    neutral: List[str] = []
    score = 0.0

    for item in [sh, sz, cyb]:
        name = item.get("name") or item.get("code")
        change = _num(item.get("change_pct"))
        change_5d = _num(item.get("change_5d"))
        change_20d = _num(item.get("change_20d"))
        if change is not None:
            score += _score_change(change, 0.8)
            target = bullish if change > 0.8 else bearish if change < -0.8 else neutral
            target.append(f"{name} 当日涨跌幅 {change:.2f}%")
        if change_5d is not None:
            score += _score_change(change_5d, 1.2)
            target = bullish if change_5d > 1.2 else bearish if change_5d < -1.2 else neutral
            target.append(f"{name} 5日涨跌幅 {change_5d:.2f}%")
        if horizon == "mid" and change_20d is not None:
            score += _score_change(change_20d, 2.5)
            target = bullish if change_20d > 2.5 else bearish if change_20d < -2.5 else neutral
            target.append(f"{name} 20日涨跌幅 {change_20d:.2f}%")

    breadth = local_snapshot.get("market_breadth") or {}
    advancers = _num(breadth.get("advancers"))
    decliners = _num(breadth.get("decliners"))
    if advancers is not None and decliners is not None and advancers + decliners > 0:
        breadth_ratio = advancers / (advancers + decliners)
        universe_size = _num(breadth.get("universe_size"))
        sampled_breadth = bool(breadth.get("sampled")) or (universe_size is not None and universe_size < 1000)
        breadth_label = "抽样市场宽度" if sampled_breadth else "市场宽度"
        if sampled_breadth and breadth_ratio >= 0.58:
            neutral.append(f"{breadth_label}偏强，上涨占比 {breadth_ratio:.1%}，但样本不足，不能单独支持看多")
        elif breadth_ratio >= 0.58:
            score += 1.0
            bullish.append(f"{breadth_label}偏强，上涨占比 {breadth_ratio:.1%}")
        elif sampled_breadth and breadth_ratio <= 0.42:
            score -= 0.6
            bearish.append(f"{breadth_label}偏弱，上涨占比 {breadth_ratio:.1%}，提示风险但不代表全市场")
        elif breadth_ratio <= 0.42:
            score -= 1.0
            bearish.append(f"{breadth_label}偏弱，上涨占比 {breadth_ratio:.1%}")
        else:
            neutral.append(f"{breadth_label}中性，上涨占比 {breadth_ratio:.1%}")
    elif breadth.get("error"):
        bearish.append("市场宽度数据缺失，无法确认上涨家数和市场赚钱效应")

    amount = _num(sh.get("amount"))
    volume = _num(sh.get("volume"))
    amount_avg_5d = _num(sh.get("amount_avg_5d"))
    if amount and amount_avg_5d:
        ratio = amount / amount_avg_5d
        if ratio >= 1.08:
            score += 0.8
            bullish.append(f"上证成交额较5日均值放大 {ratio:.2f} 倍")
        elif ratio <= 0.92:
            score -= 0.6
            bearish.append(f"上证成交额较5日均值收缩 {ratio:.2f} 倍")
    elif amount:
        neutral.append(f"上证成交额约 {amount:.2f}，但5日均值缺失，量能趋势暂不参与评分")
    else:
        total_amount = _num(breadth.get("total_amount"))
        if total_amount is not None:
            neutral.append(f"全市场成交额约 {total_amount:.2f}，但指数成交额均值缺失，量能只作替代参考")
        else:
            if volume is not None:
                neutral.append(f"上证成交量约 {volume:.0f}，成交额字段缺失，量能金额口径暂不参与评分")
            else:
                neutral.append("成交额/成交量字段缺失，量能证据降权")

    capital_items = (local_snapshot.get("capital_flow") or {}).get("items") or []
    capital_flow = []
    has_real_capital_flow = False
    for item in capital_items:
        net = _num(item.get("net"))
        if net is None:
            continue
        payload = dict(item)
        payload.setdefault("proxy", False)
        capital_flow.append(payload)
        is_proxy = bool(payload.get("proxy"))
        if not is_proxy:
            has_real_capital_flow = True
        if is_proxy and item.get("direction") == "inflow":
            score += 0.5
            bullish.append(f"{item.get('name')}偏流入 {net:.2f}{item.get('unit', '')}，代理指标低权重参考")
            if item.get("note"):
                neutral.append(str(item.get("note")))
        elif is_proxy and item.get("direction") == "outflow":
            score -= 0.5
            bearish.append(f"{item.get('name')}偏流出 {abs(net):.2f}{item.get('unit', '')}，代理指标低权重提示风险")
            if item.get("note"):
                neutral.append(str(item.get("note")))
        elif is_proxy:
            neutral.append(f"{item.get('name')}方向不明显，代理指标仅作背景参考")
            if item.get("note"):
                neutral.append(str(item.get("note")))
        elif item.get("direction") == "inflow":
            score += 1.0
            bullish.append(f"{item.get('name')}净流入 {net:.2f}{item.get('unit', '')}")
        elif item.get("direction") == "outflow":
            score -= 1.0
            bearish.append(f"{item.get('name')}净流出 {abs(net):.2f}{item.get('unit', '')}")

    if not capital_flow:
        proxy_flow = _volume_price_proxy([sh, sz, cyb])
        if proxy_flow:
            capital_flow.append(proxy_flow)
            if proxy_flow["direction"] == "inflow":
                score += 0.5
                bullish.append("量价代理资金偏流入，低权重支持短线风险偏好")
            elif proxy_flow["direction"] == "outflow":
                score -= 0.5
                bearish.append("量价代理资金偏流出，低权重提示短线风险偏好不足")
            else:
                neutral.append("量价代理资金方向不明显")
            neutral.append(proxy_flow["note"])

    raw_direction = "up" if score >= 2.0 else "down" if score <= -2.0 else "sideways"
    raw_probabilities = _probabilities(score)
    direction = raw_direction
    probabilities = dict(raw_probabilities)
    confidence_ceiling = 62 if has_real_capital_flow else 58 if capital_flow else 55
    confidence = min(confidence_ceiling, 35 + int(min(abs(score), 4) * 5))
    confirmation_gaps = []
    if advancers is None or decliners is None:
        confirmation_gaps.append("市场宽度")
    if amount is None and volume is None:
        confirmation_gaps.append("量能")
    if not capital_flow:
        confirmation_gaps.append("资金流")
    gap_text = "，但仍需" + "/".join(confirmation_gaps) + "确认" if confirmation_gaps else ""
    constraint_reasons: List[str] = []
    if constraints:
        direction, probabilities, applied_reasons = _apply_direction_cap(
            direction,
            probabilities,
            str(constraints.get("direction_cap") or ""),
        )
        constraint_reasons.extend(applied_reasons)
        cap = _int_or_none(constraints.get("confidence_cap"))
        if cap is not None and confidence > cap:
            confidence = cap
            constraint_reasons.append(f"置信度受市场风险约束压制至 {cap}")
        forced_reasons = constraints.get("forced_neutral_reasons") or []
        constraint_reasons.extend(str(item) for item in forced_reasons if item)
        if constraint_reasons:
            neutral.extend(f"风险约束: {item}" for item in constraint_reasons[:5])

    base_case = {
        "up": f"本地指数动量偏强，短线倾向震荡上行{gap_text}",
        "down": "本地指数动量和宽度偏弱，短线倾向防守，等待止跌或资金回流确认",
        "sideways": "本地证据显示多空分歧，短线以震荡观察为主",
    }[direction]
    position_environment = _position_environment(direction, confidence)
    if constraints:
        position_environment = _apply_position_cap(position_environment, str(constraints.get("position_cap") or ""))
    return {
        "raw_direction": raw_direction,
        "direction": direction,
        "score": round(score, 2),
        "raw_probabilities": raw_probabilities,
        "probabilities": probabilities,
        "raw_confidence": min(confidence_ceiling, 35 + int(min(abs(score), 4) * 5)),
        "confidence": confidence,
        "base_case": base_case,
        "position_environment": position_environment,
        "constraint_reasons": constraint_reasons,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "capital_flow": capital_flow,
        "support": _support_levels(indices),
        "resistance": _resistance_levels(indices),
    }


def sector_local_signal(local_snapshot: Dict[str, Any], horizon: str) -> Dict[str, Any]:
    heat = local_snapshot.get("sector_heat") or {}
    members = heat.get("members") or []
    bullish: List[str] = []
    bearish: List[str] = []
    neutral: List[str] = []
    score = 0.0

    change = _num(heat.get("change_pct"))
    if change is not None:
        score += _score_change(change, 1.0 if horizon == "short" else 3.0)
        target = bullish if change > 1.0 else bearish if change < -1.0 else neutral
        target.append(f"板块涨跌幅 {change:.2f}%")

    main_flow = _num(heat.get("main_flow"))
    capital_flow = []
    if main_flow is not None:
        if main_flow > 0:
            score += 1.0
            bullish.append(f"板块主力净流入 {main_flow:.2f}")
        elif main_flow < 0:
            score -= 1.0
            bearish.append(f"板块主力净流出 {main_flow:.2f}")
    sector_flow = local_snapshot.get("capital_flow") or {}
    summary = sector_flow.get("summary") or {}
    total = _num(summary.get("main_net_total"))
    if total is not None:
        capital_flow.append(summary)
        if total > 0:
            score += 1.0
            bullish.append(f"代表成分股主力合计净流入 {total:.2f}元")
        elif total < 0:
            score -= 1.0
            bearish.append(f"代表成分股主力合计净流出 {abs(total):.2f}元")

    leaders = sorted(members, key=lambda item: _num(item.get("change_pct")) or -999, reverse=True)[:3]
    laggards = sorted(members, key=lambda item: _num(item.get("change_pct")) or 999)[:3]
    if leaders:
        bullish.append("领涨成分: " + ", ".join(f"{item.get('name')}({item.get('change_pct')}%)" for item in leaders))
    if laggards:
        bearish.append("掉队成分: " + ", ".join(f"{item.get('name')}({item.get('change_pct')}%)" for item in laggards))

    direction = "up" if score >= 1.5 else "down" if score <= -1.5 else "sideways"
    return {
        "direction": direction,
        "score": round(score, 2),
        "probabilities": _probabilities(score),
        "confidence": min(55, 32 + int(min(abs(score), 4) * 5)),
        "base_case": "板块本地热度偏强" if direction == "up" else "板块本地热度偏弱" if direction == "down" else "板块本地热度中性，等待资金和龙头确认",
        "position_environment": _position_environment(direction, 45),
        "bullish": bullish,
        "bearish": bearish or ["反方证据: 板块资金、成分股同步率或龙头持续性不足"],
        "neutral": neutral,
        "capital_flow": capital_flow or ([main_flow] if main_flow is not None else []),
        "relative_strength": [change] if change is not None else [],
        "sector_stage": "扩散" if direction == "up" else "退潮" if direction == "down" else "震荡",
        "leaders": [str(item.get("code")) for item in leaders if item.get("code")],
        "fade_signals": ["龙头跌破5日线或板块主力资金转负"] if direction != "down" else ["板块主力流出且掉队股扩大"],
    }


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _score_change(change: float, threshold: float) -> float:
    if change > threshold:
        return 1.0
    if change < -threshold:
        return -1.0
    return change / max(threshold, 0.01) * 0.35


def _probabilities(score: float) -> Dict[str, int]:
    if score >= 2.0:
        up = min(65, 45 + int(score * 5))
        down = max(15, 25 - int(score * 2))
        return {"up": up, "sideways": 100 - up - down, "down": down}
    if score <= -2.0:
        down = min(65, 45 + int(abs(score) * 5))
        up = max(15, 25 - int(abs(score) * 2))
        return {"up": up, "sideways": 100 - up - down, "down": down}
    sideways = max(45, 60 - int(abs(score) * 5))
    up = int((100 - sideways) / 2 + max(score, 0) * 4)
    down = 100 - sideways - up
    return {"up": up, "sideways": sideways, "down": down}


def _apply_direction_cap(
    direction: str,
    probabilities: Dict[str, int],
    cap: str,
) -> tuple[str, Dict[str, int], List[str]]:
    reasons: List[str] = []
    adjusted = dict(probabilities)
    if cap in ("", "up", "none"):
        return direction, adjusted, reasons
    if cap == "sideways_up":
        if direction == "up":
            direction = "sideways"
            reasons.append("弱反弹或确认不足，禁止直接输出上涨方向")
        if direction == "down":
            direction = "sideways"
            reasons.append("约束要求仅允许震荡偏强观察，修正下跌方向")
        adjusted = _ensure_sideways_dominant(adjusted)
        if adjusted["down"] > adjusted["up"]:
            adjusted["up"], adjusted["down"] = adjusted["down"], adjusted["up"]
        return direction, _ensure_normalized_sideways_dominant(adjusted), reasons
    if cap == "sideways":
        if direction != "sideways":
            reasons.append(f"市场风险约束将 {direction} 修正为 sideways")
        direction = "sideways"
        return direction, _ensure_normalized_sideways_dominant(adjusted), reasons
    if cap == "sideways_down":
        if direction == "up":
            direction = "sideways"
            reasons.append("宽度或反弹质量不足，上涨方向被压制为震荡")
        elif direction == "down":
            reasons.append("风险约束确认下行压力")
        else:
            reasons.append("风险约束要求下跌概率不得低于上涨概率")
        adjusted = _ensure_sideways_dominant(adjusted)
        if adjusted["down"] < adjusted["up"]:
            adjusted["down"], adjusted["up"] = adjusted["up"], adjusted["down"]
        normalized = _ensure_normalized_sideways_dominant(adjusted)
        if normalized["down"] < normalized["up"]:
            normalized["down"], normalized["up"] = normalized["up"], normalized["down"]
        return direction, normalized, reasons
    if cap == "down":
        if direction != "down":
            reasons.append(f"风险约束将 {direction} 修正为 down")
        adjusted["down"] = max(adjusted.get("down", 0), adjusted.get("up", 0), adjusted.get("sideways", 0))
        adjusted["up"] = min(adjusted.get("up", 0), 20)
        direction = "down"
        return direction, _normalize_probabilities(adjusted), reasons
    return direction, adjusted, reasons


def _ensure_sideways_dominant(probabilities: Dict[str, int]) -> Dict[str, int]:
    adjusted = {
        "up": int(probabilities.get("up", 0)),
        "sideways": int(probabilities.get("sideways", 0)),
        "down": int(probabilities.get("down", 0)),
    }
    adjusted["sideways"] = max(adjusted["sideways"], adjusted["up"] + 1, adjusted["down"] + 1, 45)
    return adjusted


def _normalize_probabilities(probabilities: Dict[str, int]) -> Dict[str, int]:
    total = sum(max(int(value), 0) for value in probabilities.values())
    if total <= 0:
        return {"up": 0, "sideways": 100, "down": 0}
    up = round(max(int(probabilities.get("up", 0)), 0) / total * 100)
    sideways = round(max(int(probabilities.get("sideways", 0)), 0) / total * 100)
    down = 100 - up - sideways
    if down < 0:
        sideways += down
        down = 0
    return {"up": up, "sideways": sideways, "down": down}


def _ensure_normalized_sideways_dominant(probabilities: Dict[str, int]) -> Dict[str, int]:
    normalized = _normalize_probabilities(_ensure_sideways_dominant(probabilities))
    leader = max(normalized["up"], normalized["down"])
    if normalized["sideways"] <= leader:
        gap = leader - normalized["sideways"] + 1
        donor = "up" if normalized["up"] >= normalized["down"] else "down"
        normalized[donor] = max(0, normalized[donor] - gap)
        normalized["sideways"] += gap
    total = normalized["up"] + normalized["sideways"] + normalized["down"]
    if total != 100:
        normalized["sideways"] += 100 - total
    return normalized


def _apply_position_cap(position: str, cap: str) -> str:
    if cap in ("", "attack"):
        return position
    if cap == "probe" and position == "attack":
        return "probe"
    if cap == "hold" and position in ("attack", "probe"):
        return "hold"
    if cap == "defense" and position not in ("cash_watch", "defense"):
        return "defense"
    if cap == "cash_watch":
        return "cash_watch"
    return position


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _volume_price_proxy(indices: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    signed_volume = 0.0
    total_volume = 0.0
    used = 0
    for item in indices:
        change = _num(item.get("change_pct"))
        volume = _num(item.get("volume"))
        if change is None or volume is None or volume <= 0:
            continue
        direction = 1 if change > 0 else -1 if change < 0 else 0
        strength = min(abs(change) / 2.0, 1.5)
        signed_volume += direction * strength * volume
        total_volume += volume
        used += 1
    if used == 0 or total_volume <= 0:
        return None
    normalized = signed_volume / total_volume
    direction = "inflow" if normalized > 0.05 else "outflow" if normalized < -0.05 else "flat"
    return {
        "name": "量价代理资金",
        "net": round(normalized, 4),
        "unit": "proxy_score",
        "direction": direction,
        "proxy": True,
        "sample_size": used,
        "note": "量价代理资金由指数涨跌幅与成交量构造，仅作资金方向代理，不等同真实北向或主力资金。",
    }


def _position_environment(direction: str, confidence: int) -> str:
    if confidence < 40:
        return "cash_watch"
    if direction == "up":
        return "probe"
    if direction == "down":
        return "defense"
    return "hold"


def _support_levels(indices: List[Dict[str, Any]]) -> List[float]:
    return [round(float(item["low"]), 3) for item in indices if item.get("low")][:3]


def _resistance_levels(indices: List[Dict[str, Any]]) -> List[float]:
    return [round(float(item["high"]), 3) for item in indices if item.get("high")][:3]
