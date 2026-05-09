#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
STOCK_CLIENT = ROOT / "skills" / "stock-data" / "scripts" / "stock_client.py"
STOCK_SKILL = ROOT / "skills" / "stock-skill" / "scripts" / "run.py"
REPORT_DIR = ROOT / "logs" / "selftest"


@dataclass
class CheckResult:
    name: str
    passed: bool
    command: List[str]
    summary: str
    details: List[str]
    payload_status: Optional[str] = None


def run_json(cmd: List[str], timeout: int = 20) -> Dict[str, Any]:
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    raw = result.stdout.strip() or result.stderr.strip()
    if not raw:
        raise RuntimeError("empty output")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid json output: {exc}: {raw[:300]}") from exc
    payload["_exit_code"] = result.returncode
    payload["_raw"] = raw
    return payload


def get_nested(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate_fields(payload: Dict[str, Any], fields: List[str]) -> List[str]:
    missing: List[str] = []
    for field in fields:
        value = get_nested(payload, field)
        if value is None or value == "":
            missing.append(field)
            continue
        if isinstance(value, dict) and not value:
            missing.append(field)
    return missing


def check_stock_client_command(
    name: str,
    args: List[str],
    required_fields: List[str],
    *,
    timeout: int,
) -> CheckResult:
    cmd = ["python3", str(STOCK_CLIENT), *args]
    try:
        payload = run_json(cmd, timeout=timeout)
        details: List[str] = []
        if not payload.get("success"):
            details.append(payload.get("error") or "; ".join(payload.get("errors", [])) or "success=false")
            return CheckResult(name, False, cmd, "stock-data command failed", details)
        missing = validate_fields(payload, required_fields)
        if missing:
            details.extend([f"missing field: {field}" for field in missing])
            return CheckResult(name, False, cmd, "stock-data contract mismatch", details)
        return CheckResult(name, True, cmd, "ok", details, payload_status="success")
    except Exception as exc:
        return CheckResult(name, False, cmd, "exception", [str(exc)])


def check_stock_skill_action(
    name: str,
    action: str,
    input_payload: Dict[str, Any],
    required_fields: List[str],
    *,
    timeout: int,
) -> CheckResult:
    cmd = [
        "python3",
        str(STOCK_SKILL),
        "run",
        "--skill",
        "stock",
        "--action",
        action,
        "--input",
        json.dumps(input_payload, ensure_ascii=False),
    ]
    try:
        payload = run_json(cmd, timeout=timeout)
        top_status = payload.get("status")
        details: List[str] = []
        if top_status not in {"ok", "degraded"}:
            error_data = payload.get("data", {}).get("error", {})
            details.append(error_data.get("message") or f"top-level status={top_status}")
            return CheckResult(name, False, cmd, "stock-skill action failed", details, payload_status=top_status)
        missing = validate_fields(payload, required_fields)
        if missing:
            details.extend([f"missing field: {field}" for field in missing])
            return CheckResult(name, False, cmd, "stock-skill contract mismatch", details, payload_status=top_status)
        return CheckResult(name, True, cmd, "ok", details, payload_status=top_status)
    except Exception as exc:
        return CheckResult(name, False, cmd, "exception", [str(exc)])


def build_validation_payload(prepared: Dict[str, Any]) -> Dict[str, Any]:
    prompt_bundle = prepared["prompt_bundle"]
    cited = prompt_bundle["injected_strategy_ids"][:2] or prompt_bundle["injected_strategy_ids"]
    return {
        "analysis_result": {
            "market_regime": {
                "current_regime": "theme_rotation",
                "risk_appetite": "neutral",
                "main_themes": ["证券"],
                "incremental_capital_direction": "券商",
                "next_verification_events": ["次日竞价资金承接"],
            },
            "sector_positioning": {
                "sector": "证券",
                "theme_role": "main_theme",
                "leader_status": "confirmed",
                "continuity": "good",
            },
            "expectation_analysis": {
                "market_expectation": "risk-on",
                "stock_expectation": "券商弹性延续",
                "priced_in": "partially_priced_in",
                "expectation_gap": "若量能继续放大仍有补涨空间",
                "catalyst_path": ["market", "sector", "stock"],
                "supporting_evidence": [
                    {"category": "market", "detail": "风险偏好抬升"},
                    {"category": "sector", "detail": "券商板块领涨"},
                    {"category": "capital", "detail": "主力净流入为正"},
                ],
            },
            "capital_confirmation": {
                "verdict": "confirmed",
                "main_flow": "positive",
                "order_structure": "big_order_dominant",
                "price_volume_fit": "yes",
                "relative_strength": "stronger_than_index",
                "notes": "量价和资金方向一致。",
            },
            "scenario_plan": {
                "bull_case": "放量突破后加速",
                "base_case": "维持强势震荡",
                "bear_case": "冲高回落失守均线",
            },
            "trigger_and_invalidation": {
                "entry_triggers": ["放量站稳前高"],
                "hold_triggers": ["主力持续净流入"],
                "invalidation_signals": ["跌破前一日低点"],
                "exit_triggers": ["放量滞涨且资金转负"],
            },
            "source_reliability": {
                "primary_sources": ["巨潮资讯", "东财"],
                "tradeable_signal_threshold": "S or A+capital confirmation",
            },
            "rumor_check": {
                "final_verdict": "official_confirmed",
            },
            "recommendation": {
                "action": "HOLD",
                "confidence": 62,
                "position_size": "LIGHT",
            },
            "reasoning": {
                "primary_factors": ["趋势仍在，但需要继续确认量能"],
            },
            "summary": "维持观察或轻仓持有，等进一步确认。",
            "strategy_usage": {
                "strategy_version": prompt_bundle["strategy_version"],
                "injected_strategy_ids": prompt_bundle["injected_strategy_ids"],
                "cited_strategy_ids": cited,
                "violated_strategy_ids": [],
                "selection_reason": prompt_bundle["selection_reason"],
                "strategy_notes": "用于自测校验。",
            },
        },
        "prompt_bundle": prompt_bundle,
        "data_quality": prepared["data_quality"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Win_Stock 接口自测脚本")
    parser.add_argument("--symbol", default="601211", help="测试股票代码，默认 601211")
    parser.add_argument("--symbols", nargs="*", default=["601211", "002241"], help="批量测试代码")
    parser.add_argument("--report", action="store_true", help="保存 JSON 报告到 logs/selftest/")
    parser.add_argument("--per-command-timeout", type=int, default=20, help="单个接口命令超时秒数，默认 20")
    args = parser.parse_args()

    symbol = str(args.symbol).zfill(6)
    batch_symbols = [str(item).zfill(6) for item in args.symbols]
    checks: List[CheckResult] = []

    stock_data_checks = [
        ("stock-data quote", ["quote", symbol], ["data.symbol", "data.price", "data.change_pct"]),
        ("stock-data quotes", ["quotes", *batch_symbols], ["data.items"]),
        ("stock-data kline", ["kline", symbol, "60"], ["data.symbol", "data.bars", "data.period"]),
        ("stock-data klinex-weekly", ["klinex", symbol, "weekly", "104"], ["data.symbol", "data.bars", "data.period"]),
        ("stock-data klinex-monthly", ["klinex", symbol, "monthly", "60"], ["data.symbol", "data.bars", "data.period"]),
        ("stock-data market", ["market"], ["data.indices"]),
        ("stock-data sector", ["sector", symbol], ["data.symbol", "data.industry"]),
        ("stock-data finance", ["finance", symbol], ["data.symbol", "data.pe_ttm", "data.pb"]),
        ("stock-data finance-trend", ["finance-trend", symbol], ["data.symbol", "data.periods", "data.latest.report_date"]),
        ("stock-data margin", ["margin", symbol], ["data.financing_balance"]),
        ("stock-data flow", ["flow", symbol], ["data.symbol", "data.date", "data.main_net_inflow"]),
        ("stock-data intraday-1m", ["intraday", symbol, "1", "3"], ["data.symbol", "data.interval", "data.bars"]),
        ("stock-data intraday-5m", ["intraday", symbol, "5", "5"], ["data.symbol", "data.interval", "data.bars"]),
        ("stock-data analysis", ["analysis", symbol], ["data.symbol", "data.quote", "data.kline_daily", "data.technical_indicators", "data.quality"]),
        ("stock-data snapshot", ["snapshot", *batch_symbols], ["data.items", "data.total"]),
    ]
    for name, command_args, required in stock_data_checks:
        print(f"Running {name} ...", flush=True)
        checks.append(
            check_stock_client_command(
                name,
                command_args,
                required,
                timeout=args.per_command_timeout,
            )
        )

    stock_skill_checks = [
        ("stock-skill quote.get", "quote.get", {"symbol": symbol}, ["data.data.symbol", "data.data.price"]),
        ("stock-skill quotes.batch.get", "quotes.batch.get", {"symbols": batch_symbols}, ["data.data.items"]),
        ("stock-skill kline.get", "kline.get", {"symbol": symbol, "timeframe": "1d", "limit": 60}, ["data.data.symbol", "data.data.bars"]),
        ("stock-skill index.get", "index.get", {"index_code": "sh000001"}, ["data.data.index_name", "data.data.change_pct"]),
        ("stock-skill trading.calendar.get", "trading.calendar.get", {}, ["data.data.date", "data.data.session", "data.data.next_trading_day"]),
        ("stock-skill market.snapshot.get", "market.snapshot.get", {"limit": 50}, ["data.data.market_change_pct", "data.data.total_amount"]),
        ("stock-skill news.stock.get", "news.stock.get", {"symbol": symbol, "limit": 10}, ["data.data.symbol", "data.data.events"]),
        ("stock-skill news.market.get", "news.market.get", {"limit": 10}, ["data.data.events"]),
        ("stock-skill flow.main.get", "flow.main.get", {"symbol": symbol}, ["data.data.symbol", "data.data.main_net_inflow"]),
        ("stock-skill flow.order_size.get", "flow.order_size.get", {"symbol": symbol}, ["data.data.big_order_ratio", "data.data.small_order_ratio"]),
        ("stock-skill etf.pcf.get", "etf.pcf.get", {"fund_code": "512000"}, ["data.data.fund_code", "data.data.pcf_items"]),
        ("stock-skill margin.balance.get", "margin.balance.get", {"symbol": symbol}, ["data.data.financing_balance"]),
        ("stock-skill hsgt.top10.get", "hsgt.top10.get", {}, ["data.data.items"]),
        ("stock-skill lhb.detail.get", "lhb.detail.get", {"symbol": symbol}, ["data.data.eligible", "data.data.items"]),
        ("stock-skill block_trade.get", "block_trade.get", {"symbol": symbol}, ["data.data.items"]),
        ("stock-skill fundamental.valuation.get", "fundamental.valuation.get", {"symbol": symbol}, ["data.data.pe_ttm", "data.data.pb"]),
        ("stock-skill fundamental.metrics.get", "fundamental.metrics.get", {"symbol": symbol}, ["data.data.report_date", "data.data.roe"]),
        ("stock-skill sector.map.get", "sector.map.get", {"symbol": symbol}, ["data.data.primary_sector"]),
        ("stock-skill sector.heat.get", "sector.heat.get", {"sector": "证券"}, ["data.data.sector", "data.data.change_pct"]),
        ("stock-skill health.report.get", "health.report.get", {}, ["data.data.data.sources"]),
        ("stock-skill analysis.stock.prepare", "analysis.stock.prepare", {"symbol": symbol}, ["data.data.prompt_bundle", "data.data.data_quality", "data.data.stock_context"]),
    ]
    for name, action, payload, required in stock_skill_checks:
        print(f"Running {name} ...", flush=True)
        checks.append(
            check_stock_skill_action(
                name,
                action,
                payload,
                required,
                timeout=args.per_command_timeout,
            )
        )

    prepared_cmd = [
        "python3",
        str(STOCK_SKILL),
        "run",
        "--skill",
        "stock",
        "--action",
        "analysis.stock.prepare",
        "--input",
        json.dumps({"symbol": symbol}, ensure_ascii=False),
    ]
    prepared_payload = None
    try:
        prepared_result = run_json(prepared_cmd, timeout=args.per_command_timeout)
        if prepared_result.get("status") in {"ok", "degraded"}:
            prepared_payload = prepared_result.get("data", {}).get("data")
    except Exception:
        prepared_payload = None

    if prepared_payload:
        validation_input = build_validation_payload(prepared_payload)
        checks.append(
            check_stock_skill_action(
                "stock-skill analysis.result.validate",
                "analysis.result.validate",
                validation_input,
                ["data.data.valid", "data.data.warnings", "data.data.errors"],
                timeout=args.per_command_timeout,
            )
        )
    else:
        checks.append(
            CheckResult(
                "stock-skill analysis.result.validate",
                False,
                prepared_cmd,
                "prepare step unavailable",
                ["analysis.stock.prepare 未成功，无法构造 validate 自测"],
            )
        )

    passed = sum(1 for item in checks if item.passed)
    failed = len(checks) - passed

    print(f"Self-test summary: {passed}/{len(checks)} passed, {failed} failed")
    for item in checks:
        status = "PASS" if item.passed else "FAIL"
        print(f"[{status}] {item.name} - {item.summary}")
        if item.details:
            for detail in item.details:
                print(f"  - {detail}")

    if args.report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / f"stock_interface_selftest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "symbol": symbol,
            "batch_symbols": batch_symbols,
            "summary": {"total": len(checks), "passed": passed, "failed": failed},
            "checks": [
                {
                    "name": item.name,
                    "passed": item.passed,
                    "command": item.command,
                    "summary": item.summary,
                    "details": item.details,
                    "payload_status": item.payload_status,
                }
                for item in checks
            ],
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report saved: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
