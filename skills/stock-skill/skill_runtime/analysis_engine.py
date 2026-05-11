from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple


SECTION_ACTIONS: List[Tuple[str, str]] = [
    ("quote", "quote.get"),
    ("kline", "kline.get"),
    ("index", "index.get"),
    ("market_snapshot", "market.snapshot.get"),
    ("sector_map", "sector.map.get"),
    ("sector_heat", "sector.heat.get"),
    ("news_market", "news.market.get"),
    ("news_stock", "news.stock.get"),
    ("flow_main", "flow.main.get"),
    ("flow_order_size", "flow.order_size.get"),
    ("fundamental_valuation", "fundamental.valuation.get"),
    ("fundamental_metrics", "fundamental.metrics.get"),
]


def build_stock_analysis_context(
    *,
    symbol: str,
    responses: Dict[str, Dict[str, Any]],
    resource_bundle: Dict[str, Any],
    selection_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    available_sections: List[str] = []
    missing_sections: List[Dict[str, Any]] = []
    tool_failures: List[Dict[str, Any]] = []
    evidence_map: Dict[str, Dict[str, Any]] = {}
    analysis_context = {
        "quote": responses["quote.get"],
        "kline": responses["kline.get"],
        "index": responses["index.get"],
        "market_snapshot": responses["market.snapshot.get"],
        "sector_map": responses["sector.map.get"],
        "sector_heat": responses["sector.heat.get"],
        "news_market": responses["news.market.get"],
        "news_stock": responses["news.stock.get"],
        "flow_main": responses["flow.main.get"],
        "flow_order_size": responses["flow.order_size.get"],
        "fundamental_valuation": responses["fundamental.valuation.get"],
        "fundamental_metrics": responses["fundamental.metrics.get"],
    }

    for section_name, action in SECTION_ACTIONS:
        response = responses[action]
        section_status = response.get("status")
        evidence_map[section_name] = {
            "action": action,
            "status": section_status,
            "source": response.get("meta", {}).get("source"),
            "quality_score": response.get("quality", {}).get("score", 0.0),
            "issues": response.get("quality", {}).get("issues", []),
        }
        if section_status in {"ok", "degraded"}:
            available_sections.append(section_name)
        else:
            missing_sections.append(
                {
                    "section": section_name,
                    "action": action,
                    "reason": response.get("error", {}).get("message") or "unknown",
                }
            )
        if response.get("error", {}).get("failed_sources"):
            tool_failures.append(
                {
                    "action": action,
                    "failed_sources": response["error"]["failed_sources"],
                    "message": response.get("error", {}).get("message"),
                    "issues": response.get("quality", {}).get("issues", []),
                }
            )

    threshold = resource_bundle["evidence_threshold"]
    requirements = resource_bundle["analysis_requirements"]
    selected_analysis_type = _resolve_analysis_type(selection_context or {}, requirements)
    hard_blockers = threshold["hard_blockers"]
    trade_plan_ready = all(
        responses[action].get("status") in {"ok", "degraded"} for action in hard_blockers
    )
    market_ready = responses["market.snapshot.get"].get("status") in {"ok", "degraded"}
    sector_ready = responses["sector.map.get"].get("status") in {"ok", "degraded"}
    capital_ready = any(
        responses[action].get("status") in {"ok", "degraded"}
        for action in ("flow.main.get", "flow.order_size.get", "sector.heat.get")
    )
    confidence_gate = "ready_for_trade_plan"
    if not trade_plan_ready or not market_ready or not sector_ready:
        confidence_gate = "insufficient_data"
    elif not capital_ready:
        confidence_gate = "observe_only"

    data_requirement_report = _build_data_requirement_report(
        requested_type=selected_analysis_type,
        evidence_map=evidence_map,
        responses=responses,
        requirements=requirements,
    )

    market_context = _build_market_context(analysis_context)
    sector_context = _build_sector_context(analysis_context)
    stock_context = _build_stock_context(analysis_context)
    capital_context = _build_capital_context(analysis_context)
    news_signal_board = _build_news_signal_board(analysis_context, sector_context, stock_context)
    source_reliability_map = _build_source_reliability_map(news_signal_board)
    rumor_check = _build_rumor_check(news_signal_board, capital_context)
    expectation_context = _build_expectation_context(
        market_context=market_context,
        sector_context=sector_context,
        stock_context=stock_context,
        capital_context=capital_context,
        news_signal_board=news_signal_board,
        rumor_check=rumor_check,
    )
    strategy_context = _build_strategy_context(
        responses=responses,
        confidence_gate=confidence_gate,
        selection_context={
            **(selection_context or {}),
            "analysis_type": data_requirement_report["analysis_type_actual"],
        },
    )
    strategy_bundle = _build_strategy_bundle(
        artifacts=resource_bundle.get("strategy_artifacts", {}),
        strategy_context=strategy_context,
    )
    compiled_prompt = resource_bundle["compiled_prompt"]
    if strategy_bundle["compiled_strategy_prompt"]:
        compiled_prompt = (
            f"{compiled_prompt}\n\n# book-strategy-injection\n"
            f"{strategy_bundle['compiled_strategy_prompt']}"
        )

    return {
        "symbol": symbol,
        "analysis_mode": "data_driven_prompt_guided_with_book_strategies",
        "prompt_bundle": {
            "version": resource_bundle["version"],
            "bundle_version": strategy_bundle["bundle_version"],
            "activation_source": strategy_bundle["activation_source"],
            "compiled_prompt": compiled_prompt,
            "modules": [
                {"name": entry["name"], "path": entry["path"]} for entry in resource_bundle["prompt_modules"]
            ],
            "strategy_summary": strategy_bundle["strategy_summary"],
            "candidate_strategy_ids": strategy_bundle["candidate_strategy_ids"],
            "injected_strategy_ids": strategy_bundle["injected_strategy_ids"],
            "selection_reason": strategy_bundle["selection_reason"],
            "output_contract": {
                "required_top_level_fields": [
                    "market_regime",
                    "sector_positioning",
                    "expectation_analysis",
                    "capital_confirmation",
                    "scenario_plan",
                    "trigger_and_invalidation",
                    "source_reliability",
                    "rumor_check",
                    "recommendation",
                    "reasoning",
                    "summary",
                    "strategy_usage",
                ],
                "required_strategy_usage_fields": [
                    "bundle_version",
                    "injected_strategy_ids",
                    "cited_strategy_ids",
                    "violated_strategy_ids",
                    "selection_reason",
                    "strategy_notes",
                ],
                "high_confidence_trade_requires_min_citations": 2,
            },
        },
        "knowledge_base": {
            "version": resource_bundle["version"],
            "entries": [
                {"name": entry["name"], "path": entry["path"], "excerpt": entry["content"][:240]}
                for entry in resource_bundle["knowledge_entries"]
            ] + [
                {
                    "name": "data_requirements_context",
                    "path": resource_bundle["data_requirements_context"]["source_path"],
                    "excerpt": resource_bundle["data_requirements_context"]["summary"][:240],
                },
                {
                    "name": "financial_methodology_context",
                    "path": resource_bundle["financial_methodology_context"]["source_path"],
                    "excerpt": resource_bundle["financial_methodology_context"]["summary"][:240],
                },
            ] + [
                {
                    "name": f"error_case:{signal['code']}",
                    "path": signal["source_path"],
                    "excerpt": signal["summary"],
                }
                for signal in resource_bundle.get("error_case_signals", [])
            ],
        },
        "strategy_bundle": strategy_bundle,
        "analysis_context": analysis_context,
        "market_context": market_context,
        "sector_context": sector_context,
        "stock_context": stock_context,
        "capital_context": capital_context,
        "news_signal_board": news_signal_board,
        "source_reliability_map": source_reliability_map,
        "rumor_check": rumor_check,
        "expectation_context": expectation_context,
        "profile_context": deepcopy((selection_context or {}).get("profile_context") or {}),
        "data_requirements_context": deepcopy(resource_bundle.get("data_requirements_context", {})),
        "financial_methodology_context": deepcopy(resource_bundle.get("financial_methodology_context", {})),
        "error_case_signals": resource_bundle.get("error_case_signals", []),
        "data_quality": {
            "available_sections": available_sections,
            "missing_sections": missing_sections,
            "tool_failures": tool_failures,
            "evidence_map": evidence_map,
            "evidence_threshold": threshold,
            "confidence_gate": confidence_gate,
            "capital_ready": capital_ready,
            "market_ready": market_ready,
            "sector_ready": sector_ready,
            "analysis_type_requested": data_requirement_report["analysis_type_requested"],
            "analysis_type_actual": data_requirement_report["analysis_type_actual"],
            "data_completeness": data_requirement_report["data_completeness"],
            "required_sections": data_requirement_report["required_sections"],
            "optional_sections": data_requirement_report["optional_sections"],
            "missing_required_sections": data_requirement_report["missing_required_sections"],
            "missing_optional_sections": data_requirement_report["missing_optional_sections"],
            "degradation_reason": data_requirement_report["degradation_reason"],
            "confidence_cap": data_requirement_report["confidence_cap"],
            "requirement_report": data_requirement_report,
        },
        "guidance": _build_guidance(
            trade_plan_ready=trade_plan_ready and confidence_gate == "ready_for_trade_plan",
            missing_sections=missing_sections,
            tool_failures=tool_failures,
        ),
    }


def _build_guidance(
    *,
    trade_plan_ready: bool,
    missing_sections: List[Dict[str, Any]],
    tool_failures: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if trade_plan_ready:
        headline = "现有数据足够支撑专业分析，请按 prompt 模块输出明确结论，并显式引用关键证据。"
        next_steps = [
            "先判断市场正在交易什么预期，再确认板块和个股是否在受益链上。",
            "用资金结构、量价关系和相对强弱验证新闻与催化剂是否被市场认可。",
            "如果给交易计划，必须说明触发条件、失效条件、证伪信号和仓位逻辑。",
        ]
    else:
        headline = "当前证据不足，禁止假装有把握。优先说明缺失数据、影响范围和下一步补数动作。"
        next_steps = [
            "列出缺失 section 及其为什么影响判断。",
            "说明工具失败是否会影响结论可信度。",
            "只保留观察性判断，不输出高置信度交易计划。",
        ]
    return {
        "headline": headline,
        "missing_data_reasons": missing_sections,
        "tool_failure_impact": tool_failures,
        "next_steps": next_steps,
    }


def _resolve_analysis_type(selection_context: Dict[str, Any], requirements: Dict[str, Any]) -> str:
    requested = str(selection_context.get("analysis_type") or "").strip().lower()
    if requested in requirements["types"]:
        return requested
    action_intent = str(selection_context.get("action_intent") or "observe").strip().lower()
    if action_intent in {"buy", "add", "rebalance", "build"}:
        return "deep"
    if action_intent in {"sell", "trim", "hold", "exit", "reduce", "watch", "observe"}:
        return "standard"
    if action_intent in {"review", "post_close_review"}:
        return "review"
    return str(requirements.get("default_analysis_type") or "standard")


def _build_data_requirement_report(
    *,
    requested_type: str,
    evidence_map: Dict[str, Dict[str, Any]],
    responses: Dict[str, Dict[str, Any]],
    requirements: Dict[str, Any],
) -> Dict[str, Any]:
    actual_type = requested_type
    config = requirements["types"][actual_type]
    missing_required = _missing_sections(
        config["required_sections"],
        evidence_map,
        responses,
        config["min_kline_bars"],
    )
    degradation_reason = ""
    if missing_required and config["fallback_type"] != actual_type:
        fallback_type = config["fallback_type"]
        fallback_config = requirements["types"][fallback_type]
        fallback_missing = _missing_sections(
            fallback_config["required_sections"],
            evidence_map,
            responses,
            fallback_config["min_kline_bars"],
        )
        actual_type = fallback_type
        config = fallback_config
        degradation_reason = (
            f"{requested_type} 缺少关键数据: {', '.join(missing_required)}，降级为 {fallback_type}"
        )
        missing_required = fallback_missing

    missing_optional = _missing_sections(
        config["optional_sections"],
        evidence_map,
        responses,
        config["min_kline_bars"],
    )
    data_completeness = "完整"
    if missing_required:
        data_completeness = "不足"
    elif missing_optional:
        data_completeness = "部分缺失"
    confidence_cap = int(config["confidence_cap"])
    if missing_required:
        confidence_cap = min(confidence_cap, 35)
    elif missing_optional:
        confidence_cap = max(30, confidence_cap - min(15, len(missing_optional) * 5))
    return {
        "analysis_type_requested": requested_type,
        "analysis_type_actual": actual_type,
        "data_completeness": data_completeness,
        "required_sections": list(config["required_sections"]),
        "optional_sections": list(config["optional_sections"]),
        "missing_required_sections": missing_required,
        "missing_optional_sections": missing_optional,
        "degradation_reason": degradation_reason,
        "confidence_cap": confidence_cap,
    }


def _missing_sections(
    section_names: List[str],
    evidence_map: Dict[str, Dict[str, Any]],
    responses: Dict[str, Dict[str, Any]],
    min_kline_bars: int,
) -> List[str]:
    missing: List[str] = []
    for section_name in section_names:
        status = evidence_map.get(section_name, {}).get("status")
        if status not in {"ok", "degraded"}:
            missing.append(section_name)
            continue
        if section_name == "kline":
            bars = responses.get("kline.get", {}).get("data", {}).get("bars", [])
            if len(bars) < min_kline_bars:
                missing.append(f"kline<{min_kline_bars}")
    return missing


def _build_strategy_context(
    *,
    responses: Dict[str, Dict[str, Any]],
    confidence_gate: str,
    selection_context: Dict[str, Any],
) -> Dict[str, Any]:
    action_intent = str(selection_context.get("action_intent") or "observe").lower()
    requested_tags = [
        str(tag).strip()
        for tag in selection_context.get("requested_tags", [])
        if str(tag).strip()
    ]
    market_bias = _infer_market_bias(responses)
    trend_state = _infer_trend_state(responses)
    return {
        "action_intent": action_intent,
        "requested_tags": requested_tags,
        "market_bias": market_bias,
        "trend_state": trend_state,
        "confidence_gate": confidence_gate,
    }


def _infer_market_bias(responses: Dict[str, Dict[str, Any]]) -> str:
    index_change = (
        responses.get("index.get", {})
        .get("data", {})
        .get("change_pct")
    )
    snapshot = responses.get("market.snapshot.get", {}).get("data", {})
    advancers = snapshot.get("advancers")
    decliners = snapshot.get("decliners")
    breadth_score = 0
    if isinstance(advancers, (int, float)) and isinstance(decliners, (int, float)):
        if advancers > decliners:
            breadth_score = 1
        elif advancers < decliners:
            breadth_score = -1

    index_score = 0
    if isinstance(index_change, (int, float)):
        if index_change >= 0.5:
            index_score = 1
        elif index_change <= -0.5:
            index_score = -1

    score = breadth_score + index_score
    if score >= 2:
        return "bullish"
    if score <= -2:
        return "bearish"
    return "neutral"


def _infer_trend_state(responses: Dict[str, Dict[str, Any]]) -> str:
    bars = (
        responses.get("kline.get", {})
        .get("data", {})
        .get("bars", [])
    )
    closes = [bar.get("close") for bar in bars if isinstance(bar.get("close"), (int, float))]
    if len(closes) < 5:
        return "unknown"
    start = closes[-5]
    end = closes[-1]
    if start <= 0:
        return "unknown"
    change_pct = ((end - start) / start) * 100
    if change_pct >= 3:
        return "bullish"
    if change_pct <= -3:
        return "bearish"
    return "neutral"


def _build_market_context(analysis_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    index_data = analysis_context["index"].get("data", {})
    snapshot_data = analysis_context["market_snapshot"].get("data", {})
    market_news = analysis_context["news_market"].get("data", {}).get("events", [])
    top_sectors = snapshot_data.get("top_sector_list", [])
    advancers = snapshot_data.get("advancers") or 0
    decliners = snapshot_data.get("decliners") or 0
    risk_appetite = "neutral"
    if advancers > decliners * 1.8:
        risk_appetite = "high"
    elif decliners > advancers * 1.8:
        risk_appetite = "low"
    main_theme = top_sectors[0]["sector"] if top_sectors else ""
    return {
        "index_name": index_data.get("index_name"),
        "index_change_pct": index_data.get("change_pct"),
        "market_change_pct": snapshot_data.get("market_change_pct"),
        "total_amount": snapshot_data.get("total_amount"),
        "breadth": {
            "advancers": advancers,
            "decliners": decliners,
            "limit_up_count": snapshot_data.get("limit_up_count"),
            "limit_down_count": snapshot_data.get("limit_down_count"),
        },
        "risk_appetite": risk_appetite,
        "main_theme_hint": main_theme,
        "top_sector_list": top_sectors,
        "market_news": market_news,
    }


def _build_sector_context(analysis_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    sector_map = analysis_context["sector_map"].get("data", {})
    sector_heat = analysis_context["sector_heat"].get("data", {})
    return {
        "primary_sector": sector_map.get("primary_sector"),
        "sectors": sector_map.get("sectors", []),
        "concept_tags": sector_map.get("concept_tags", []),
        "heat": sector_heat,
        "theme_role": _classify_theme_role(sector_heat),
    }


def _build_stock_context(analysis_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    quote = analysis_context["quote"].get("data", {})
    valuation = analysis_context["fundamental_valuation"].get("data", {})
    metrics = analysis_context["fundamental_metrics"].get("data", {})
    stock_news = analysis_context["news_stock"].get("data", {}).get("events", [])
    kline = analysis_context["kline"].get("data", {}).get("bars", [])
    relative_strength = _infer_relative_strength(kline, analysis_context["index"].get("data", {}))
    return {
        "symbol": quote.get("symbol"),
        "name": quote.get("name"),
        "quote": quote,
        "valuation": valuation,
        "fundamentals": metrics,
        "news": stock_news,
        "relative_strength": relative_strength,
    }


def _build_capital_context(analysis_context: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    flow_main = analysis_context["flow_main"].get("data", {})
    order_size = analysis_context["flow_order_size"].get("data", {})
    quote = analysis_context["quote"].get("data", {})
    sector_heat = analysis_context["sector_heat"].get("data", {})
    capital_verdict = "unknown"
    main_flow = flow_main.get("main_net_inflow")
    imbalance = order_size.get("buy_sell_imbalance")
    if isinstance(main_flow, (int, float)) and isinstance(imbalance, (int, float)):
        if main_flow > 0 and imbalance > 0:
            capital_verdict = "confirmed"
        elif main_flow < 0 and imbalance < 0:
            capital_verdict = "distribution"
        else:
            capital_verdict = "mixed"
    return {
        "flow_main": flow_main,
        "flow_order_size": order_size,
        "sector_fund_flow": sector_heat.get("sector_fund_flow"),
        "turnover_rate": quote.get("turnover_rate"),
        "capital_verdict": capital_verdict,
    }


def _build_news_signal_board(
    analysis_context: Dict[str, Dict[str, Any]],
    sector_context: Dict[str, Any],
    stock_context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    board: List[Dict[str, Any]] = []
    sector_name = sector_context.get("primary_sector") or ""
    stock_name = stock_context.get("name") or ""
    for item in analysis_context["news_market"].get("data", {}).get("events", [])[:5]:
        board.append(
            _build_signal_item(
                headline=item.get("title"),
                source=item.get("source"),
                publish_time=item.get("publish_time"),
                scope="market",
                target_name="A股市场",
            )
        )
    for item in analysis_context["news_stock"].get("data", {}).get("events", [])[:5]:
        board.append(
            _build_signal_item(
                headline=item.get("title"),
                source=item.get("source"),
                publish_time=item.get("publish_time"),
                scope="stock",
                target_name=stock_name,
                url=item.get("url"),
                sector_name=sector_name,
            )
        )
    return board


def _build_source_reliability_map(news_signal_board: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    reliability: Dict[str, Dict[str, Any]] = {}
    for item in news_signal_board:
        source = str(item.get("source") or "unknown")
        reliability[source] = {
            "source_grade": item.get("source_grade"),
            "default_trade_weight": _trade_weight_for_grade(item.get("source_grade")),
            "official_confirmed": item.get("confirmation_status") == "official_confirmed",
        }
    return reliability


def _build_rumor_check(
    news_signal_board: List[Dict[str, Any]],
    capital_context: Dict[str, Any],
) -> Dict[str, Any]:
    stock_items = [item for item in news_signal_board if item.get("scope") == "stock"]
    grade_order = {"S": 0, "A": 1, "B": 2, "C": 3}
    highest_grade = "C"
    for item in stock_items:
        grade = str(item.get("source_grade") or "C")
        if grade_order.get(grade, 3) < grade_order.get(highest_grade, 3):
            highest_grade = grade
    official_count = sum(1 for item in stock_items if item.get("source_grade") == "S")
    high_quality_count = sum(1 for item in stock_items if item.get("source_grade") in {"S", "A"})
    market_confirmation = capital_context.get("capital_verdict") in {"confirmed", "distribution", "mixed"}
    if official_count > 0:
        verdict = "official_confirmed"
    elif high_quality_count >= 2:
        verdict = "multi_source_confirmed"
    elif high_quality_count == 1 and market_confirmation:
        verdict = "market_reacting_without_confirmation"
    elif stock_items:
        verdict = "rumor_only"
    else:
        verdict = "no_material_signal"
    return {
        "has_official_source": official_count > 0,
        "cross_source_count": high_quality_count,
        "highest_source_grade": highest_grade,
        "key_missing_fields": ["official notice"] if verdict == "rumor_only" else [],
        "contradictions_found": [],
        "market_confirmation": market_confirmation,
        "final_verdict": verdict,
    }


def _build_expectation_context(
    *,
    market_context: Dict[str, Any],
    sector_context: Dict[str, Any],
    stock_context: Dict[str, Any],
    capital_context: Dict[str, Any],
    news_signal_board: List[Dict[str, Any]],
    rumor_check: Dict[str, Any],
) -> Dict[str, Any]:
    market_expectation = "risk-off"
    if market_context.get("risk_appetite") == "high":
        market_expectation = "risk-on"
    elif market_context.get("main_theme_hint"):
        market_expectation = f"theme-rotation:{market_context['main_theme_hint']}"
    stock_news_titles = [item.get("headline") for item in news_signal_board if item.get("scope") == "stock"]
    sector_name = sector_context.get("primary_sector") or ""
    catalyst_path = [market_expectation]
    if sector_name:
        catalyst_path.append(f"sector:{sector_name}")
    if stock_context.get("symbol"):
        catalyst_path.append(f"stock:{stock_context['symbol']}")
    priced_in = "unknown"
    if stock_context.get("relative_strength") == "stronger_than_index" and capital_context.get("capital_verdict") == "confirmed":
        priced_in = "partially_priced_in"
    if rumor_check.get("final_verdict") == "official_confirmed" and capital_context.get("capital_verdict") == "confirmed":
        priced_in = "being_traded"
    return {
        "current_market_expectation": market_expectation,
        "sector_expected_catalysts": [sector_name] if sector_name else [],
        "stock_known_catalysts": stock_news_titles[:3],
        "priced_in_assessment": priced_in,
        "expectation_gap_hypotheses": _build_expectation_gap_hypotheses(
            market_context=market_context,
            stock_context=stock_context,
            capital_context=capital_context,
        ),
        "catalyst_path": catalyst_path,
    }


def _build_expectation_gap_hypotheses(
    *,
    market_context: Dict[str, Any],
    stock_context: Dict[str, Any],
    capital_context: Dict[str, Any],
) -> List[str]:
    hypotheses: List[str] = []
    if market_context.get("risk_appetite") == "high" and capital_context.get("capital_verdict") == "confirmed":
        hypotheses.append("市场风险偏好抬升，若个股继续强于指数，可能进入资金强化阶段。")
    if stock_context.get("relative_strength") == "weaker_than_index":
        hypotheses.append("个股弱于指数，说明预期尚未形成共识，容易被板块轮动边缘化。")
    if not hypotheses:
        hypotheses.append("当前更多是观察期，需等下一次资金确认或官方催化落地。")
    return hypotheses


def _build_signal_item(
    *,
    headline: Any,
    source: Any,
    publish_time: Any,
    scope: str,
    target_name: str,
    url: Any = None,
    sector_name: str = "",
) -> Dict[str, Any]:
    headline_text = str(headline or "").strip()
    source_text = str(source or "unknown").strip()
    grade = _grade_source(source_text)
    confirmation_status = "official_confirmed" if grade == "S" else "unconfirmed_but_market_moving"
    surprise_level = "medium"
    if any(token in headline_text for token in ["澄清", "问询", "处罚", "减持", "重组", "订单", "回购"]):
        surprise_level = "high"
    priced_in_status = "unknown"
    if any(token in headline_text for token in ["再次", "继续", "延续"]):
        priced_in_status = "likely_priced_in"
    trade_score = 80 if grade == "S" else 65 if grade == "A" else 45 if grade == "B" else 20
    return {
        "headline": headline_text,
        "scope": scope,
        "target_name": target_name,
        "sector_name": sector_name,
        "source": source_text,
        "source_grade": grade,
        "publish_time": publish_time,
        "url": url,
        "confirmation_status": confirmation_status,
        "surprise_level": surprise_level,
        "priced_in_status": priced_in_status,
        "trade_relevance_score": trade_score,
    }


def _grade_source(source: str) -> str:
    source_lower = source.lower()
    if any(token in source_lower for token in ["cninfo", "巨潮", "上交所", "深交所", "证监会", "国务院", "国新办", "统计局", "人民银行", "发改委", "工信部", "商务部", "能源局"]):
        return "S"
    if any(token in source_lower for token in ["reuters", "路透", "bloomberg", "彭博"]):
        return "A"
    if any(token in source_lower for token in ["财联社", "证券时报", "中证", "上证报", "第一财经"]):
        return "B"
    return "C"


def _trade_weight_for_grade(grade: Any) -> str:
    if grade == "S":
        return "high"
    if grade == "A":
        return "medium_high"
    if grade == "B":
        return "medium"
    return "low"


def _classify_theme_role(sector_heat: Dict[str, Any]) -> str:
    change_pct = sector_heat.get("change_pct")
    continuity_score = sector_heat.get("continuity_score")
    if isinstance(change_pct, (int, float)) and isinstance(continuity_score, (int, float)):
        if change_pct >= 2 and continuity_score >= 0.6:
            return "main_theme"
        if change_pct > 0:
            return "supporting_theme"
    return "unclear"


def _infer_relative_strength(kline: List[Dict[str, Any]], index_data: Dict[str, Any]) -> str:
    closes = [bar.get("close") for bar in kline if isinstance(bar.get("close"), (int, float))]
    if len(closes) < 2:
        return "unknown"
    previous_close = closes[-2]
    latest_close = closes[-1]
    if previous_close <= 0:
        return "unknown"
    stock_change = ((latest_close - previous_close) / previous_close) * 100
    index_change = index_data.get("change_pct")
    if not isinstance(index_change, (int, float)):
        return "unknown"
    if stock_change > index_change + 2:
        return "stronger_than_index"
    if stock_change < index_change - 2:
        return "weaker_than_index"
    return "in_line_with_index"


def _build_strategy_bundle(
    *,
    artifacts: Dict[str, Any],
    strategy_context: Dict[str, Any],
) -> Dict[str, Any]:
    catalog = artifacts.get("catalog", [])
    conditional_profiles = artifacts.get("conditional_profiles", {})
    approved_catalog = [
        item for item in catalog
        if item.get("status") == "approved" and "stock_analysis" in item.get("scenes", [])
    ]
    global_strategies = [
        item for item in approved_catalog if item.get("injection_mode") == "global"
    ]
    conditional_strategies = [
        item for item in approved_catalog if item.get("injection_mode") == "conditional"
    ]

    selected_conditional, selection_reason = _select_conditional_strategies(
        conditional_strategies=conditional_strategies,
        conditional_profiles=conditional_profiles,
        strategy_context=strategy_context,
    )
    injected = global_strategies + selected_conditional
    injected_ids = [item["strategy_id"] for item in injected]
    return {
        "bundle_version": artifacts.get("bundle_version"),
        "compiled_at": artifacts.get("compiled_at"),
        "activation_source": artifacts.get("activation_source", "unavailable"),
        "manifest_path": artifacts.get("manifest_path"),
        "source_books": artifacts.get("source_books", []),
        "strategy_context": strategy_context,
        "global_strategies": _strip_strategy_body(global_strategies),
        "candidate_conditional_strategies": _strip_strategy_body(conditional_strategies),
        "selected_conditional_strategies": _strip_strategy_body(selected_conditional),
        "candidate_strategy_ids": [item["strategy_id"] for item in (global_strategies + conditional_strategies)],
        "injected_strategy_ids": injected_ids,
        "selection_reason": selection_reason,
        "strategy_summary": {
            "global_count": len(global_strategies),
            "candidate_conditional_count": len(conditional_strategies),
            "conditional_count": len(selected_conditional),
            "global_strategy_ids": [item["strategy_id"] for item in global_strategies],
            "candidate_conditional_strategy_ids": [item["strategy_id"] for item in conditional_strategies],
            "conditional_strategy_ids": [item["strategy_id"] for item in selected_conditional],
        },
        "compiled_strategy_prompt": _compile_strategy_prompt(
            base_prompt=artifacts.get("base_prompt", ""),
            selected_conditional=selected_conditional,
            strategy_context=strategy_context,
            bundle_version=artifacts.get("bundle_version"),
        ),
    }


def _select_conditional_strategies(
    *,
    conditional_strategies: List[Dict[str, Any]],
    conditional_profiles: Dict[str, Any],
    strategy_context: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    confidence_gate = strategy_context["confidence_gate"]
    if confidence_gate != "ready_for_trade_plan":
        return [], [
            f"confidence_gate={confidence_gate} -> skip conditional strategy injection",
        ]

    include_tags = set(strategy_context.get("requested_tags", []))
    reasons: List[str] = []
    for profile_name, profile in conditional_profiles.items():
        if _profile_matches(profile, strategy_context):
            tags = profile.get("include_tags", [])
            include_tags.update(tags)
            if tags:
                reasons.append(f"profile={profile_name} -> tags={','.join(tags)}")
            else:
                reasons.append(f"profile={profile_name} -> no additional tags")

    selected = []
    seen = set()
    for strategy in sorted(conditional_strategies, key=lambda item: (-int(item["priority"]), item["strategy_id"])):
        if include_tags.intersection(strategy.get("trigger_tags", [])):
            if strategy["strategy_id"] not in seen:
                selected.append(strategy)
                seen.add(strategy["strategy_id"])
    if not reasons:
        reasons.append("no conditional profile matched; global strategies only")
    return selected, reasons


def _profile_matches(profile: Dict[str, Any], strategy_context: Dict[str, Any]) -> bool:
    field_map = {
        "action_intents": "action_intent",
        "market_bias": "market_bias",
        "confidence_gate": "confidence_gate",
    }
    for profile_key, context_key in field_map.items():
        expected = profile.get(profile_key)
        if not expected:
            continue
        actual = strategy_context.get(context_key)
        if actual not in expected:
            return False
    return True


def _compile_strategy_prompt(
    *,
    base_prompt: str,
    selected_conditional: List[Dict[str, Any]],
    strategy_context: Dict[str, Any],
    bundle_version: str | None,
) -> str:
    lines = []
    if base_prompt:
        lines.append(base_prompt.strip())
    lines.extend(
        [
            "",
            "# Conditional Strategy Injection",
            f"- bundle_version: {bundle_version or 'unknown'}",
            f"- action_intent: {strategy_context['action_intent']}",
            f"- market_bias: {strategy_context['market_bias']}",
            f"- trend_state: {strategy_context['trend_state']}",
            f"- confidence_gate: {strategy_context['confidence_gate']}",
        ]
    )
    if not selected_conditional:
        lines.append("- no conditional book strategies injected")
    for strategy in selected_conditional:
        lines.append("")
        lines.append(f"## {strategy['strategy_id']} {strategy['title_cn']}")
        lines.append(f"- snippet: {strategy['prompt_snippet']}")
        for item in strategy.get("checklist", []):
            lines.append(f"- check: {item}")
    lines.extend(
        [
            "",
            "# Strategy Response Contract",
            "- output must include strategy_usage.bundle_version",
            "- output must include strategy_usage.injected_strategy_ids using this run's injected strategy ids",
            "- output must include strategy_usage.cited_strategy_ids with only injected strategy ids",
            "- output must include strategy_usage.violated_strategy_ids with only injected strategy ids",
            "- if recommendation.action is BUY or SELL with confidence >= 60, cite at least 2 injected strategies",
            "- if confidence_gate is insufficient_data, do not output a high-confidence BUY or SELL recommendation",
        ]
    )
    return "\n".join(lines).strip()


def _strip_strategy_body(strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "strategy_id": item["strategy_id"],
            "title_cn": item["title_cn"],
            "source_principle_id": item["source_principle_id"],
            "book_id": item["book_id"],
            "injection_mode": item["injection_mode"],
            "category": item["category"],
            "trigger_tags": item["trigger_tags"],
        }
        for item in strategies
    ]
