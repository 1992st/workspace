from __future__ import annotations

from typing import Any, Dict, List


TRADE_ACTIONS = {"BUY", "SELL"}
OFFENSIVE_ACTIONS = {"BUY", "ADD"}
HIGH_CONFIDENCE_THRESHOLD = 70
RUMOR_CONFIRMED = {"official_confirmed", "multi_source_confirmed"}


def validate_analysis_result(
    *,
    analysis_result: Dict[str, Any],
    prompt_bundle: Dict[str, Any],
    data_quality: Dict[str, Any],
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    strategy_usage = analysis_result.get("strategy_usage")
    if not isinstance(strategy_usage, dict):
        errors.append("missing strategy_usage block")
        strategy_usage = {}

    required_strategy_fields = [
        "bundle_version",
        "injected_strategy_ids",
        "cited_strategy_ids",
        "violated_strategy_ids",
        "selection_reason",
        "strategy_notes",
    ]
    for field in required_strategy_fields:
        if field not in strategy_usage:
            errors.append(f"strategy_usage.{field} is required")

    expected_injected = _string_list(prompt_bundle.get("injected_strategy_ids", []))
    reported_injected = _string_list(strategy_usage.get("injected_strategy_ids", []))
    cited_ids = _string_list(strategy_usage.get("cited_strategy_ids", []))
    violated_ids = _string_list(strategy_usage.get("violated_strategy_ids", []))

    if sorted(reported_injected) != sorted(expected_injected):
        errors.append(
            "strategy_usage.injected_strategy_ids must match prompt_bundle.injected_strategy_ids"
        )

    invalid_citations = sorted(set(cited_ids) - set(expected_injected))
    if invalid_citations:
        errors.append(
            f"strategy_usage.cited_strategy_ids contains non-injected strategies: {invalid_citations}"
        )

    invalid_violations = sorted(set(violated_ids) - set(expected_injected))
    if invalid_violations:
        errors.append(
            f"strategy_usage.violated_strategy_ids contains non-injected strategies: {invalid_violations}"
        )

    expected_bundle_version = prompt_bundle.get("bundle_version")
    if strategy_usage.get("bundle_version") != expected_bundle_version:
        errors.append("strategy_usage.bundle_version must match prompt_bundle.bundle_version")

    recommendation = analysis_result.get("recommendation", {})
    if not isinstance(recommendation, dict):
        errors.append("recommendation block is required")
        recommendation = {}

    required_blocks = [
        "analysis_meta",
        "counter_evidence",
        "bias_check",
        "reasoning",
        "market_regime",
        "sector_positioning",
        "expectation_analysis",
        "capital_confirmation",
        "scenario_plan",
        "trigger_and_invalidation",
        "source_reliability",
        "rumor_check",
    ]
    for field in required_blocks:
        if not isinstance(analysis_result.get(field), dict):
            errors.append(f"{field} block is required")
    if not str(analysis_result.get("summary") or "").strip():
        errors.append("summary is required")

    action = str(recommendation.get("action") or "").upper()
    confidence = _coerce_confidence(recommendation.get("confidence"))
    confidence_gate = str(data_quality.get("confidence_gate") or "")
    position_size = str(recommendation.get("position_size") or "").upper()
    blocked_actions = _string_list(recommendation.get("blocked_actions", []))
    analysis_meta = analysis_result.get("analysis_meta", {})
    counter_evidence = analysis_result.get("counter_evidence", {})
    bias_check = analysis_result.get("bias_check", {})
    expectation_analysis = analysis_result.get("expectation_analysis", {})
    capital_confirmation = analysis_result.get("capital_confirmation", {})
    scenario_plan = analysis_result.get("scenario_plan", {})
    trigger_and_invalidation = analysis_result.get("trigger_and_invalidation", {})
    source_reliability = analysis_result.get("source_reliability", {})
    rumor_check = analysis_result.get("rumor_check", {})
    risk_gate = analysis_result.get("risk_gate", {})
    t_guide = analysis_result.get("t_guide", {})
    data_status = analysis_result.get("data_status", {})
    missing_sections = _missing_sections_from_quality(data_quality)

    if action in TRADE_ACTIONS and confidence >= 60 and len(cited_ids) < 2:
        errors.append("high-confidence BUY/SELL recommendations must cite at least 2 injected strategies")

    confidence_cap = _coerce_confidence(data_quality.get("confidence_cap"))
    if confidence_cap > 0 and confidence > confidence_cap:
        errors.append("recommendation.confidence exceeds data_quality.confidence_cap")

    requested_type = str(data_quality.get("analysis_type_requested") or "")
    actual_type = str(data_quality.get("analysis_type_actual") or "")
    if actual_type and analysis_meta.get("analysis_type") != actual_type:
        errors.append("analysis_meta.analysis_type must match data_quality.analysis_type_actual")

    if actual_type != requested_type and action in TRADE_ACTIONS and confidence >= 60:
        errors.append("degraded analyses cannot output BUY/SELL with confidence >= 60")

    if confidence_gate != "ready_for_trade_plan" and action in TRADE_ACTIONS and confidence >= 60:
        errors.append("insufficient-data runs cannot output high-confidence BUY/SELL recommendations")

    if confidence_gate == "observe_only" and action in TRADE_ACTIONS and confidence >= 60:
        errors.append("missing capital confirmation only allows WATCH/HOLD or sub-60 conviction trades")

    if confidence_gate == "observe_only" and position_size == "HEAVY":
        errors.append("HEAVY position_size is forbidden when capital confirmation is unavailable")

    _validate_risk_gate(
        errors=errors,
        risk_gate=risk_gate,
        recommendation=recommendation,
        action=action,
        confidence=confidence,
        blocked_actions=blocked_actions,
    )
    _validate_data_gap_boundaries(
        errors=errors,
        analysis_result=analysis_result,
        data_status=data_status,
        t_guide=t_guide,
        missing_sections=missing_sections,
    )
    _validate_funding_language(errors=errors, analysis_result=analysis_result, missing_sections=missing_sections)

    expected_categories = {"market", "sector", "capital"}
    supporting_evidence = expectation_analysis.get("supporting_evidence", [])
    categories = {
        str(item.get("category")).strip().lower()
        for item in supporting_evidence
        if isinstance(item, dict) and str(item.get("category") or "").strip()
    }
    if action in TRADE_ACTIONS and confidence >= HIGH_CONFIDENCE_THRESHOLD and not expected_categories.issubset(categories):
        errors.append("high-confidence BUY/SELL recommendations must cite market, sector, and capital evidence")

    capital_verdict = str(capital_confirmation.get("verdict") or "").strip().lower()
    if capital_verdict in {"", "unknown"}:
        errors.append("capital_confirmation.verdict must be explicit")

    if not _has_any_values(analysis_meta, ("analysis_type", "data_completeness", "confidence_cap")):
        errors.append("analysis_meta must include analysis_type, data_completeness, and confidence_cap")

    if not _has_any_values(counter_evidence, ("strongest_counter_points", "why_not_decisive")):
        errors.append("counter_evidence must include strongest_counter_points and why_not_decisive")

    if not _has_any_values(
        bias_check,
        (
            "recency_bias_check",
            "single_variable_check",
            "narrative_check",
            "cross_ticker_framework_check",
        ),
    ):
        errors.append("bias_check must include all four bias checks")

    if not _has_any_values(scenario_plan, ("bull_case", "base_case", "bear_case")):
        errors.append("scenario_plan must include bull_case, base_case, and bear_case")

    if not _has_any_values(trigger_and_invalidation, ("entry_triggers", "hold_triggers", "invalidation_signals", "exit_triggers")):
        errors.append("trigger_and_invalidation must include entry/hold/invalidation/exit signals")

    if not _has_any_values(source_reliability, ("primary_sources", "tradeable_signal_threshold")):
        errors.append("source_reliability must include primary_sources and tradeable_signal_threshold")

    rumor_verdict = str(rumor_check.get("final_verdict") or "").strip()
    if action in TRADE_ACTIONS and position_size == "HEAVY" and rumor_verdict not in RUMOR_CONFIRMED:
        errors.append("HEAVY position_size requires official_confirmed or multi_source_confirmed rumor_check")

    if action not in TRADE_ACTIONS and confidence >= 80:
        warnings.append("high confidence on non-trade action; verify recommendation wording is intentional")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "storage_payload": {
            "bundle_version": expected_bundle_version,
            "injected_strategy_ids": expected_injected,
            "strategy_citations": cited_ids,
            "violated_strategy_ids": violated_ids,
            "selection_reason": strategy_usage.get("selection_reason"),
        },
    }


def _validate_risk_gate(
    *,
    errors: List[str],
    risk_gate: Any,
    recommendation: Dict[str, Any],
    action: str,
    confidence: float,
    blocked_actions: List[str],
) -> None:
    if not isinstance(risk_gate, dict):
        errors.append("risk_gate block is required")
        return
    mode = str(risk_gate.get("mode") or "").strip()
    if mode not in {"normal_analysis", "risk_gate"}:
        errors.append("risk_gate.mode must be normal_analysis or risk_gate")
        return
    if mode != "risk_gate":
        return

    gate_blocked = set(_string_list(risk_gate.get("blocked_actions", []))) | set(blocked_actions)
    offensive_allowed = bool(risk_gate.get("offensive_advice_allowed", True))
    if offensive_allowed:
        errors.append("risk_gate.offensive_advice_allowed must be false in risk_gate mode")
    if action in OFFENSIVE_ACTIONS:
        errors.append("risk_gate mode forbids BUY/ADD recommendations")
    if action == "SELL" and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        errors.append("risk_gate mode forbids high-confidence SELL; use risk-reduction wording")
    if "DO_T" not in gate_blocked:
        errors.append("risk_gate.blocked_actions must include DO_T")
    if "HIGH_CONFIDENCE_SELL" not in gate_blocked:
        errors.append("risk_gate.blocked_actions must include HIGH_CONFIDENCE_SELL")
    if not str(risk_gate.get("reason") or "").strip():
        errors.append("risk_gate.reason is required in risk_gate mode")
    if not risk_gate.get("account_info_required"):
        errors.append("risk_gate.account_info_required is required in risk_gate mode")
    if recommendation.get("target_price") not in (None, "", 0, 0.0):
        errors.append("risk_gate mode forbids target_price")


def _validate_data_gap_boundaries(
    *,
    errors: List[str],
    analysis_result: Dict[str, Any],
    data_status: Any,
    t_guide: Any,
    missing_sections: set[str],
) -> None:
    if "intraday_1m" in missing_sections and _t_guide_allows_trade(t_guide):
        errors.append("missing intraday_1m forbids do-T plan")
    if {"kline_daily_120", "kline_daily_60"} & missing_sections and _has_precise_trade_prices(analysis_result):
        errors.append("missing kline data forbids precise target/stop/entry prices")
    if "margin" in missing_sections and _contains_funding_assertion(analysis_result, ("融资", "融券", "融资盘", "融券盘")):
        errors.append("missing margin forbids financing/securities-lending conclusions")
    if "north_south" in missing_sections and _contains_funding_assertion(analysis_result, ("北向", "南向", "外资")):
        errors.append("missing north_south forbids foreign capital conclusions")
    if "sector" in missing_sections and _contains_funding_assertion(analysis_result, ("主线", "板块退潮", "顺应主线")):
        errors.append("missing sector forbids main-theme/sector-retreat conclusions")
    if isinstance(data_status, dict):
        sections = data_status.get("sections") or {}
        for name, section in sections.items():
            if isinstance(section, dict) and section.get("is_cached") and not section.get("cache_age_hours") and section.get("cache_age_hours") != 0:
                errors.append(f"cached data section {name} must disclose cache_age_hours")


def _validate_funding_language(
    *,
    errors: List[str],
    analysis_result: Dict[str, Any],
    missing_sections: set[str],
) -> None:
    text = _collect_text(analysis_result)
    strong_phrases = ("主力出货", "主力吸筹", "机构出货", "庄家", "真实意图")
    if any(phrase in text for phrase in strong_phrases) and "platform_fund_flow_disclaimer" not in text:
        errors.append("strong funding language requires platform_fund_flow_disclaimer")
    if "龙虎榜" in text and "盘中" in text and "盘后" not in text:
        errors.append("lhb conclusions must disclose post-close/conditional nature")
    if "大宗交易" in text and "盘中" in text and "盘后" not in text:
        errors.append("block trade conclusions must disclose post-close nature")
    if "margin" in missing_sections and "杠杆" in text:
        errors.append("missing margin forbids leverage-pressure conclusions")


def _missing_sections_from_quality(data_quality: Dict[str, Any]) -> set[str]:
    raw = data_quality.get("missing_sections") or data_quality.get("data_gaps") or []
    missing = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                value = item.get("section") or item.get("name")
            else:
                value = item
            if value:
                missing.add(str(value))
    return missing


def _t_guide_allows_trade(t_guide: Any) -> bool:
    if not isinstance(t_guide, dict):
        return False
    decision = str(t_guide.get("decision") or t_guide.get("action") or t_guide.get("recommendation") or "").upper()
    if decision in {"DO_T", "正T", "反T", "T", "YES"}:
        return True
    if t_guide.get("plan") not in (None, "", [], {}):
        return True
    return False


def _has_precise_trade_prices(analysis_result: Dict[str, Any]) -> bool:
    recommendation = analysis_result.get("recommendation") or {}
    if isinstance(recommendation, dict):
        for key in ("target_price", "stop_loss_price", "entry_price"):
            value = recommendation.get(key)
            if value not in (None, "", 0, 0.0):
                return True
    triggers = analysis_result.get("trigger_and_invalidation") or {}
    return _contains_numeric_price(triggers)


def _contains_numeric_price(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_numeric_price(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_numeric_price(item) for item in value)
    if isinstance(value, str):
        return any(char.isdigit() for char in value) and any(unit in value for unit in ("元", "price", "价"))
    return isinstance(value, (int, float)) and value > 0


def _contains_funding_assertion(value: Any, needles: tuple[str, ...]) -> bool:
    text = _collect_text(value)
    return any(needle in text for needle in needles)


def _collect_text(value: Any) -> str:
    pieces: List[str] = []
    if isinstance(value, dict):
        for item in value.values():
            pieces.append(_collect_text(item))
    elif isinstance(value, list):
        for item in value:
            pieces.append(_collect_text(item))
    elif value is not None:
        pieces.append(str(value))
    return " ".join(pieces)


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _coerce_confidence(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _has_any_values(block: Any, keys: tuple[str, ...]) -> bool:
    if not isinstance(block, dict):
        return False
    return all(key in block and block.get(key) not in (None, "", [], {}) for key in keys)
