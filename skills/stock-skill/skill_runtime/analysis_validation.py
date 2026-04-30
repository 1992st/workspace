from __future__ import annotations

from typing import Any, Dict, List


TRADE_ACTIONS = {"BUY", "SELL"}
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
        "strategy_version",
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

    expected_strategy_version = prompt_bundle.get("strategy_version")
    if strategy_usage.get("strategy_version") != expected_strategy_version:
        errors.append("strategy_usage.strategy_version must match prompt_bundle.strategy_version")

    recommendation = analysis_result.get("recommendation", {})
    if not isinstance(recommendation, dict):
        errors.append("recommendation block is required")
        recommendation = {}

    required_blocks = [
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
    expectation_analysis = analysis_result.get("expectation_analysis", {})
    capital_confirmation = analysis_result.get("capital_confirmation", {})
    scenario_plan = analysis_result.get("scenario_plan", {})
    trigger_and_invalidation = analysis_result.get("trigger_and_invalidation", {})
    source_reliability = analysis_result.get("source_reliability", {})
    rumor_check = analysis_result.get("rumor_check", {})

    if action in TRADE_ACTIONS and confidence >= 60 and len(cited_ids) < 2:
        errors.append("high-confidence BUY/SELL recommendations must cite at least 2 injected strategies")

    if confidence_gate != "ready_for_trade_plan" and action in TRADE_ACTIONS and confidence >= 60:
        errors.append("insufficient-data runs cannot output high-confidence BUY/SELL recommendations")

    if confidence_gate == "observe_only" and action in TRADE_ACTIONS and confidence >= 60:
        errors.append("missing capital confirmation only allows WATCH/HOLD or sub-60 conviction trades")

    if confidence_gate == "observe_only" and position_size == "HEAVY":
        errors.append("HEAVY position_size is forbidden when capital confirmation is unavailable")

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
            "strategy_version": expected_strategy_version,
            "injected_strategy_ids": expected_injected,
            "strategy_citations": cited_ids,
            "violated_strategy_ids": violated_ids,
            "selection_reason": strategy_usage.get("selection_reason"),
        },
    }


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
