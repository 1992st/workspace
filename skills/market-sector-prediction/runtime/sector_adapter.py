from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

from blocked_report_writer import BlockedReportWriter
from evidence_mapper import default_sector_evidence
from fact_reconciliation import reconcile_sector
from local_snapshot import LocalSnapshotBuilder
from local_signal_engine import sector_local_signal
from quality_gate import QualityGate
from report_writer import ReportWriter
from sector_taxonomy import SectorTaxonomyResolver
from vibe_client import VibeClient
from vibe_templates import SECTOR_REPRESENTATIVES, build_run_dir, market_data_payload, write_local_ohlcv


CN_TZ = timezone(timedelta(hours=8))


class SectorPredictionAdapter:
    def __init__(self, root: Path, vibe: VibeClient | None = None) -> None:
        self.root = root
        self.vibe = vibe or VibeClient()
        self.snapshot = LocalSnapshotBuilder(root)
        self.taxonomy = SectorTaxonomyResolver(root)
        self.gate = QualityGate()
        self.report_writer = ReportWriter(root)
        self.blocked_writer = BlockedReportWriter(root)

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sector = str(payload.get("sector") or payload.get("target") or "").strip()
        if not sector:
            sector = "未指定板块"
        horizon = str(payload.get("horizon") or "short")
        mode = str(payload.get("mode") or "standard")
        caps = self.vibe.health_check()
        taxonomy = self.taxonomy.resolve(sector, payload.get("sector_taxonomy"))
        local = self.snapshot.sector(sector, taxonomy)
        taxonomy = {
            **taxonomy,
            "members_snapshot_path": local.get("members_snapshot_path", taxonomy.get("members_snapshot_path")),
            "member_count": local.get("member_count", taxonomy.get("member_count", 0)),
        }
        vibe_results = self._collect_vibe_standard(sector, horizon, mode, caps, local)
        reconciliation = reconcile_sector(local, vibe_results.get("market_data", {}).get("payload"))
        evidence = default_sector_evidence(local, vibe_results)
        local_signal = sector_local_signal(local, horizon)
        self._merge_local_signal(evidence, local_signal)
        prediction = self._prediction_from_signal(local_signal)
        quality = self.gate.evaluate(
            target_type="sector",
            mode=mode,
            local_snapshot=local,
            evidence=evidence,
            prediction=prediction,
            reconciliation=reconciliation,
            capabilities=caps,
            taxonomy=taxonomy,
        )
        prediction["confidence"] = min(prediction["confidence"], quality["confidence_cap"])
        output = self._build_output(sector, horizon, mode, caps, taxonomy, local, reconciliation, quality, prediction, evidence, vibe_results)
        if quality["status"] == "blocked":
            artifacts = self.blocked_writer.write(output)
            output["artifacts"].update(artifacts)
        else:
            artifacts = self.report_writer.write_prediction(output)
            output["artifacts"].update(artifacts)
        return output

    def _collect_vibe_standard(self, sector: str, horizon: str, mode: str, caps: Dict[str, Any], local: Dict[str, Any]) -> Dict[str, Any]:
        if not caps.get("vibe_available"):
            return {}
        results: Dict[str, Any] = {}
        codes = self._vibe_codes(local.get("member_codes") or [], sector)
        if "get_market_data" in caps.get("tools_enabled", []):
            if codes:
                results["market_data"] = self.vibe.get_market_data(market_data_payload(codes[:20], horizon))
            else:
                results["market_data"] = {
                    "status": "skipped",
                    "tool": "get_market_data",
                    "error": "sector adapter has no mapped representative codes",
                    "payload": {},
                }
        if "factor_analysis" in caps.get("tools_enabled", []):
            if len(codes) >= 3:
                results["factor_analysis"] = {
                    "status": "skipped",
                    "tool": "factor_analysis",
                    "error": "Vibe MCP schema expects codes/factor_name but installed tool implementation expects factor_csv/return_csv; disabled until upstream contract is reconciled",
                    "payload": {},
                }
            else:
                results["factor_analysis"] = {
                    "status": "skipped",
                    "tool": "factor_analysis",
                    "error": "requires at least 3 representative codes",
                    "payload": {},
                }
        run_dir = build_run_dir(self.root, "sector", sector, horizon, codes[:20]) if codes else None
        ohlcv_status = None
        if run_dir:
            ohlcv_status = write_local_ohlcv(run_dir, local.get("sector_heat", {}).get("members", []))
            results["local_ohlcv"] = {"status": "ok" if ohlcv_status["written"] else "skipped", "payload": ohlcv_status}
        if "pattern_recognition" in caps.get("tools_enabled", []):
            if run_dir and ohlcv_status and ohlcv_status["written"]:
                results["pattern_recognition"] = self.vibe.pattern_recognition({"run_dir": str(run_dir)})
            elif run_dir:
                results["pattern_recognition"] = {
                    "status": "skipped",
                    "tool": "pattern_recognition",
                    "error": "local OHLCV history is insufficient for Vibe pattern recognition",
                    "payload": ohlcv_status or {},
                }
            else:
                results["pattern_recognition"] = {
                    "status": "skipped",
                    "tool": "pattern_recognition",
                    "error": "requires representative codes to prepare run_dir",
                    "payload": {},
                }
        if "backtest" in caps.get("tools_enabled", []):
            if run_dir:
                results["backtest"] = self.vibe.backtest({"run_dir": str(run_dir)})
            else:
                results["backtest"] = {
                    "status": "skipped",
                    "tool": "backtest",
                    "error": "requires representative codes to prepare run_dir",
                    "payload": {},
                }
        if mode == "deep" and caps.get("modes_available", {}).get("deep"):
            results["swarm"] = self.vibe.run_swarm({"preset": "sector_committee", "market": "CN-A", "sector": sector, "horizon": horizon})
        return results

    def _vibe_codes(self, member_codes: list[str], sector: str) -> list[str]:
        if member_codes:
            return [self._with_exchange(code) for code in member_codes if code][:30]
        return SECTOR_REPRESENTATIVES.get(sector, [])

    def _with_exchange(self, code: str) -> str:
        code = str(code).strip()
        if "." in code:
            return code
        code = code.zfill(6)
        suffix = "SH" if code.startswith(("5", "6", "9")) else "SZ"
        return f"{code}.{suffix}"

    def _default_prediction(self) -> Dict[str, Any]:
        return {
            "base_case": "板块研究证据不足，保持观察，不输出强方向判断",
            "probabilities": {"up": 0, "sideways": 100, "down": 0},
            "confidence": 25,
            "position_environment": "cash_watch",
            "support": [],
            "resistance": [],
            "trigger_conditions": ["Vibe-Trading 板块工具恢复", "成分股、资金、龙头证据齐备"],
            "invalidation_conditions": ["板块 taxonomy 或成分股快照缺失", "关键事实无法对齐"],
        }

    def _prediction_from_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "base_case": signal.get("base_case") or "板块本地证据不足，保持观察",
            "probabilities": signal.get("probabilities") or {"up": 0, "sideways": 100, "down": 0},
            "confidence": signal.get("confidence", 25),
            "position_environment": signal.get("position_environment", "cash_watch"),
            "support": [],
            "resistance": [],
            "trigger_conditions": ["板块主力资金转强", "龙头股继续领涨并带动成分股扩散"],
            "invalidation_conditions": ["板块 taxonomy 或成分股快照缺失", "龙头股退潮且主力资金转负"],
        }

    def _merge_local_signal(self, evidence: Dict[str, Any], signal: Dict[str, Any]) -> None:
        evidence.setdefault("bullish", []).extend(signal.get("bullish", []))
        evidence.setdefault("bearish", []).extend(signal.get("bearish", []))
        evidence.setdefault("neutral", []).extend(signal.get("neutral", []))
        evidence.setdefault("capital_flow", []).extend(signal.get("capital_flow", []))
        evidence.setdefault("relative_strength", []).extend(signal.get("relative_strength", []))
        if signal.get("sector_stage"):
            evidence["sector_stage"] = signal["sector_stage"]
        evidence.setdefault("leaders", []).extend(signal.get("leaders", []))
        evidence.setdefault("fade_signals", []).extend(signal.get("fade_signals", []))
        evidence.setdefault("vibe_opinions", []).append(
            f"Win_Stock 本地板块信号: direction={signal.get('direction')}, score={signal.get('score')}"
        )

    def _build_output(
        self,
        sector: str,
        horizon: str,
        mode: str,
        caps: Dict[str, Any],
        taxonomy: Dict[str, Any],
        local: Dict[str, Any],
        reconciliation: Dict[str, Any],
        quality: Dict[str, Any],
        prediction: Dict[str, Any],
        evidence: Dict[str, Any],
        vibe_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        date = local.get("trading_date") or datetime.now(CN_TZ).strftime("%Y-%m-%d")
        return {
            "schema_version": "1.0",
            "target_type": "sector",
            "target": sector,
            "sector_taxonomy": taxonomy,
            "horizon": horizon,
            "mode": mode,
            "trading_date": date,
            "generated_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
            "engine": {
                "primary": "vibe-trading",
                "vibe_version": caps.get("vibe_version", ""),
                "vibe_run_id": "",
                "tools_used": sorted(vibe_results.keys()),
                "tools_missing": caps.get("tools_disabled", []),
            },
            "local_snapshot": local,
            "fact_reconciliation": reconciliation,
            "data_quality": quality,
            "prediction": prediction,
            "evidence": {
                "bullish": evidence.get("bullish", []),
                "bearish": evidence.get("bearish", []),
                "neutral": evidence.get("neutral", []),
                "capital_flow": evidence.get("capital_flow", []),
                "relative_strength": evidence.get("relative_strength", []),
                "backtest_summary": evidence.get("backtest_summary", []),
                "vibe_opinions": evidence.get("vibe_opinions", []),
            },
            "sector_state": {
                "stage": evidence.get("sector_stage", ""),
                "role": "",
                "leaders": evidence.get("leaders", []),
                "followers": [],
                "laggards": [],
                "synchronization_rate": 0,
                "capital_persistence": "",
                "catalyst_freshness": "",
            },
            "review_plan": {
                "direction_threshold": "short: max(1.0%, 0.5*vol20); mid: max(3.0%, vol20)",
                "next_day_checks": evidence.get("next_day_checks", []),
                "mid_term_checks": ["验证5-20交易日板块方向、龙头和退潮信号"] if horizon == "mid" else [],
            },
            "artifacts": {"json_path": "", "markdown_path": "", "blocked_report_path": None, "vibe_raw_path": ""},
            "vibe_raw": vibe_results,
        }
