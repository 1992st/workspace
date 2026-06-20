from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

from blocked_report_writer import BlockedReportWriter
from evidence_mapper import default_market_evidence
from fact_reconciliation import reconcile_market
from local_snapshot import LocalSnapshotBuilder
from local_research_engine import backtest_evidence, factor_evidence, market_backtest, market_factor_analysis
from local_signal_engine import market_local_signal
from market_context_builder import MarketContextBuilder
from quality_gate import QualityGate
from report_writer import ReportWriter
from vibe_client import VibeClient
from vibe_templates import MARKET_INDEX_CODES, build_run_dir, factor_csv_payload, market_data_payload, write_local_ohlcv


CN_TZ = timezone(timedelta(hours=8))


class MarketPredictionAdapter:
    def __init__(self, root: Path, vibe: VibeClient | None = None) -> None:
        self.root = root
        self.vibe = vibe or VibeClient()
        self.snapshot = LocalSnapshotBuilder(root)
        self.context_builder = MarketContextBuilder(root)
        self.gate = QualityGate()
        self.report_writer = ReportWriter(root)
        self.blocked_writer = BlockedReportWriter(root)

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        horizon = str(payload.get("horizon") or "short")
        mode = str(payload.get("mode") or "standard")
        caps = self._capabilities(mode)
        local = self.snapshot.market()
        market_context = self.context_builder.build(local, horizon, payload)
        vibe_results = self._collect_vibe_standard(horizon, mode, caps, local)
        reconciliation = reconcile_market(local, vibe_results.get("market_data", {}).get("payload"))
        evidence = default_market_evidence(local, vibe_results)
        local_signal = market_local_signal(local, horizon, market_context.get("constraints"))
        local_factor = market_factor_analysis(local)
        local_backtest = market_backtest(local)
        vibe_results["local_factor_analysis"] = local_factor
        vibe_results["local_backtest"] = local_backtest
        self._merge_local_research(evidence, local_factor, local_backtest)
        self._merge_local_signal(evidence, local_signal)
        prediction = self._prediction_from_signal(local_signal)
        quality = self.gate.evaluate(
            target_type="market",
            mode=mode,
            local_snapshot=local,
            evidence=evidence,
            prediction=prediction,
            reconciliation=reconciliation,
            capabilities=caps,
        )
        prediction["confidence"] = min(prediction["confidence"], quality["confidence_cap"])
        output = self._build_output(
            horizon,
            mode,
            caps,
            local,
            market_context,
            reconciliation,
            quality,
            prediction,
            evidence,
            vibe_results,
        )
        if quality["status"] == "blocked":
            artifacts = self.blocked_writer.write(output)
            output["artifacts"].update(artifacts)
        else:
            artifacts = self.report_writer.write_prediction(output)
            output["artifacts"].update(artifacts)
        return output

    def _capabilities(self, mode: str) -> Dict[str, Any]:
        cache_path = self.root / "data" / "predictions" / "cache" / "vibe_capabilities_latest.json"
        if mode != "deep" and cache_path.exists():
            try:
                cached = __import__("json").loads(cache_path.read_text(encoding="utf-8"))
                return cached
            except Exception:
                pass
        if mode != "deep":
            return {
                "vibe_available": True,
                "vibe_version": "standard-local",
                "tools_detected": [],
                "tools_enabled": [],
                "tools_disabled": [],
                "modes_available": {"standard": True, "deep": False},
                "missing_requirements": ["standard mode skipped live Vibe probe for latency control"],
                "checked_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
            }
        caps = self.vibe.health_check()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(__import__("json").dumps(caps, ensure_ascii=False, indent=2), encoding="utf-8")
        return caps

    def _collect_vibe_standard(
        self, horizon: str, mode: str, caps: Dict[str, Any], local: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not caps.get("vibe_available"):
            return {}
        results: Dict[str, Any] = {}
        codes = MARKET_INDEX_CODES
        run_dir = build_run_dir(self.root, "market", "A股大盘", horizon, codes)
        if mode == "deep" and "get_market_data" in caps.get("tools_enabled", []):
            results["market_data"] = self.vibe.get_market_data(market_data_payload(codes, horizon))
        else:
            results["market_data"] = {
                "status": "skipped",
                "tool": "get_market_data",
                "error": "standard mode uses Win_Stock local snapshot as data authority",
                "payload": {},
            }
        if mode == "deep" and "factor_analysis" in caps.get("tools_enabled", []):
            results["factor_analysis"] = self.vibe.factor_analysis(
                factor_csv_payload(self.root, "market", "A股大盘", horizon, codes)
            )
        else:
            results["factor_analysis"] = {
                "status": "skipped",
                "tool": "factor_analysis",
                "error": "standard mode uses Win_Stock local_factor_analysis; Vibe factor_analysis is reserved for deep mode",
                "payload": {},
            }
        ohlcv_status = write_local_ohlcv(run_dir, local.get("indices", []))
        results["local_ohlcv"] = {"status": "ok" if ohlcv_status["written"] else "skipped", "payload": ohlcv_status}
        if mode == "deep" and "pattern_recognition" in caps.get("tools_enabled", []):
            if ohlcv_status["written"]:
                results["pattern_recognition"] = self.vibe.pattern_recognition({"run_dir": str(run_dir)})
            else:
                results["pattern_recognition"] = {
                    "status": "skipped",
                    "tool": "pattern_recognition",
                    "error": "local OHLCV history is insufficient for Vibe pattern recognition",
                    "payload": ohlcv_status,
                }
        else:
            results["pattern_recognition"] = {
                "status": "skipped",
                "tool": "pattern_recognition",
                "error": "standard mode skips Vibe online pattern tool; local factor/backtest provide stable research evidence",
                "payload": ohlcv_status,
            }
        if mode == "deep" and "backtest" in caps.get("tools_enabled", []):
            results["backtest"] = self.vibe.backtest({"run_dir": str(run_dir)})
        else:
            results["backtest"] = {
                "status": "skipped",
                "tool": "backtest",
                "error": "standard mode uses Win_Stock local_backtest; Vibe backtest is reserved for deep mode",
                "payload": {"run_dir": str(run_dir)},
            }
        if mode == "deep" and caps.get("modes_available", {}).get("deep"):
            results["swarm"] = self.vibe.run_swarm({"preset": "market_committee", "market": "CN-A", "horizon": horizon})
        return results

    def _default_prediction(self, horizon: str) -> Dict[str, Any]:
        return {
            "base_case": "数据不足，保持观察，不输出强方向判断",
            "probabilities": {"up": 0, "sideways": 100, "down": 0},
            "confidence": 30,
            "position_environment": "cash_watch",
            "support": [],
            "resistance": [],
            "trigger_conditions": ["Vibe-Trading 工具恢复并完成结构化研究", "本地资金和市场宽度数据齐备"],
            "invalidation_conditions": ["关键事实与交易日无法对齐", "成交额单位无法确认"],
        }

    def _prediction_from_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "base_case": signal.get("base_case") or "本地证据不足，保持观察",
            "probabilities": signal.get("probabilities") or {"up": 0, "sideways": 100, "down": 0},
            "confidence": signal.get("confidence", 30),
            "position_environment": signal.get("position_environment", "cash_watch"),
            "support": signal.get("support", []),
            "resistance": signal.get("resistance", []),
            "trigger_conditions": ["放量突破前高或市场宽度继续改善", "Vibe-Trading 外部研究恢复并确认方向"],
            "invalidation_conditions": ["主要指数跌破本地支撑位", "成交额无法确认且资金流继续缺失", "Vibe/本地事实出现交易日冲突"],
        }

    def _merge_local_signal(self, evidence: Dict[str, Any], signal: Dict[str, Any]) -> None:
        evidence.setdefault("bullish", []).extend(signal.get("bullish", []))
        evidence.setdefault("bearish", []).extend(signal.get("bearish", []))
        evidence.setdefault("neutral", []).extend(signal.get("neutral", []))
        evidence.setdefault("capital_flow", []).extend(signal.get("capital_flow", []))
        evidence.setdefault("vibe_opinions", []).append(
            f"Win_Stock 本地信号: direction={signal.get('direction')}, score={signal.get('score')}"
        )

    def _merge_local_research(self, evidence: Dict[str, Any], factor: Dict[str, Any], backtest: Dict[str, Any]) -> None:
        factor_items = factor_evidence(factor)
        evidence.setdefault("bullish", []).extend(factor_items.get("bullish", []))
        evidence.setdefault("bearish", []).extend(factor_items.get("bearish", []))
        evidence.setdefault("neutral", []).extend(factor_items.get("neutral", []))
        evidence.setdefault("backtest_summary", []).extend(backtest_evidence(backtest))
        if backtest.get("status") == "ok":
            evidence.setdefault("vibe_opinions", []).append("Win_Stock 本地回测已基于指数 OHLCV 完成")
        if factor.get("status") == "ok":
            evidence.setdefault("vibe_opinions", []).append("Win_Stock 本地因子分析已完成")

    def _build_output(
        self,
        horizon: str,
        mode: str,
        caps: Dict[str, Any],
        local: Dict[str, Any],
        market_context: Dict[str, Any],
        reconciliation: Dict[str, Any],
        quality: Dict[str, Any],
        prediction: Dict[str, Any],
        evidence: Dict[str, Any],
        vibe_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        date = local.get("trading_date") or datetime.now(CN_TZ).strftime("%Y-%m-%d")
        return {
            "schema_version": "1.0",
            "target_type": "market",
            "target": "A股大盘",
            "sector_taxonomy": None,
            "horizon": horizon,
            "mode": mode,
            "trading_date": date,
            "generated_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
            "engine": {
                "primary": "vibe-trading",
                "vibe_version": caps.get("vibe_version", ""),
                "vibe_run_id": "",
                "tools_used": sorted(
                    name
                    for name, result in vibe_results.items()
                    if isinstance(result, dict) and result.get("status") == "ok"
                ),
                "tools_missing": caps.get("tools_disabled", []),
            },
            "local_snapshot": local,
            "market_context": market_context,
            "fact_reconciliation": reconciliation,
            "data_quality": quality,
            "prediction": prediction,
            "evidence": {
                "bullish": evidence.get("bullish", []),
                "bearish": evidence.get("bearish", []),
                "neutral": evidence.get("neutral", []),
                "capital_flow": evidence.get("capital_flow", []),
                "backtest_summary": evidence.get("backtest_summary", []),
                "vibe_opinions": evidence.get("vibe_opinions", []),
            },
            "review_plan": {
                "direction_threshold": "short: +/-0.8%; mid: +/-2.5%",
                "next_day_checks": evidence.get("next_day_checks", []),
                "mid_term_checks": ["验证5-20交易日方向和风险触发条件"] if horizon == "mid" else [],
            },
            "artifacts": {"json_path": "", "markdown_path": "", "blocked_report_path": None, "vibe_raw_path": ""},
            "vibe_raw": vibe_results,
        }
