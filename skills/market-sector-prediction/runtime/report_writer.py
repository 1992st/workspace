from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

from index_writer import IndexWriter


CN_TZ = timezone(timedelta(hours=8))


class ReportWriter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.index = IndexWriter(root)

    def write_prediction(self, payload: Dict[str, Any]) -> Dict[str, str]:
        target_type = payload["target_type"]
        date = payload["trading_date"]
        horizon = payload["horizon"]
        if target_type == "market":
            base = self.root / "data" / "market" / "predictions"
            stem = f"{date}_market_{horizon}_prediction"
        else:
            sector = str(payload["target"]).replace("/", "_")
            base = self.root / "data" / "sectors" / "predictions" / sector
            stem = f"{date}_{horizon}_prediction"
        base.mkdir(parents=True, exist_ok=True)
        json_path = base / f"{stem}.json"
        md_path = base / f"{stem}.md"
        raw_path = base / f"{stem}_vibe_raw.json"
        payload["artifacts"]["json_path"] = str(json_path)
        payload["artifacts"]["markdown_path"] = str(md_path)
        payload["artifacts"]["vibe_raw_path"] = str(raw_path)
        raw_path.write_text(json.dumps(payload.get("vibe_raw", {}), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self._markdown(payload), encoding="utf-8")
        market_context = payload.get("market_context") or {}
        constraints = market_context.get("constraints") or {}
        prediction = payload.get("prediction") or {}
        self.index.write(
            {
                "date": date,
                "target_type": target_type,
                "target": payload.get("target"),
                "horizon": horizon,
                "mode": payload.get("mode"),
                "status": payload.get("data_quality", {}).get("status"),
                "confidence": payload.get("prediction", {}).get("confidence", 0),
                "json_path": str(json_path),
                "markdown_path": str(md_path),
                "vibe_run_id": payload.get("engine", {}).get("vibe_run_id", ""),
                "review_status": "pending",
                "regime": (market_context.get("regime") or {}).get("primary_regime", ""),
                "risk_level": self._risk_level(constraints),
                "direction": self._direction(prediction),
                "position_environment": prediction.get("position_environment", ""),
            }
        )
        return {"json_path": str(json_path), "markdown_path": str(md_path), "vibe_raw_path": str(raw_path)}

    def _markdown(self, payload: Dict[str, Any]) -> str:
        prediction = payload.get("prediction", {})
        probabilities = prediction.get("probabilities", {})
        evidence = payload.get("evidence", {})
        return "\n".join(
            [
                f"# {payload.get('target')} {payload.get('horizon')} 预测",
                "",
                f"- 生成时间: {payload.get('generated_at')}",
                f"- 模式: {payload.get('mode')}",
                f"- 状态: {payload.get('data_quality', {}).get('status')}",
                f"- 置信度: {prediction.get('confidence')} / 上限 {payload.get('data_quality', {}).get('confidence_cap')}",
                f"- 方向概率: 上涨 {probabilities.get('up')} / 震荡 {probabilities.get('sideways')} / 下跌 {probabilities.get('down')}",
                f"- 仓位环境: {prediction.get('position_environment')}",
                "",
                "## 主结论",
                prediction.get("base_case", ""),
                "",
                *self._market_context_markdown(payload),
                "## 看多证据",
                *[f"- {item}" for item in evidence.get("bullish", [])],
                "",
                "## 看空/反方证据",
                *[f"- {item}" for item in evidence.get("bearish", [])],
                "",
                "## 中性/待确认证据",
                *[f"- {item}" for item in evidence.get("neutral", [])],
                "",
                "## 回测证据",
                *[f"- {item}" for item in evidence.get("backtest_summary", [])],
                "",
                "## 资金与研究引擎说明",
                *[f"- {self._format_capital_flow(item)}" for item in evidence.get("capital_flow", [])],
                *[f"- {item}" for item in evidence.get("vibe_opinions", [])],
                "",
                "## 失效条件",
                *[f"- {item}" for item in prediction.get("invalidation_conditions", [])],
                "",
                "## 下一交易日验证点",
                *[f"- {item}" for item in payload.get("review_plan", {}).get("next_day_checks", [])],
                "",
                "## 数据状态",
                json.dumps(payload.get("data_quality", {}), ensure_ascii=False, indent=2),
            ]
        )

    def _format_capital_flow(self, item: Any) -> str:
        if isinstance(item, dict):
            name = item.get("name") or "资金指标"
            direction = item.get("direction") or "unknown"
            net = item.get("net")
            unit = item.get("unit", "")
            proxy = "，代理指标" if item.get("proxy") else ""
            note = f"，{item.get('note')}" if item.get("note") else ""
            return f"{name}: {direction}, {net}{unit}{proxy}{note}"
        return str(item)

    def _market_context_markdown(self, payload: Dict[str, Any]) -> list[str]:
        market_context = payload.get("market_context") or {}
        if not market_context:
            return []
        breadth = market_context.get("breadth") or {}
        regime = market_context.get("regime") or {}
        rebound = market_context.get("rebound") or {}
        external = market_context.get("external") or {}
        constraints = market_context.get("constraints") or {}
        risk_flags = constraints.get("risk_flags") or []
        return [
            "## 市场状态与风险约束",
            f"- 市场状态: {regime.get('primary_regime', 'unknown')}",
            f"- 宽度状态: {breadth.get('quality', 'unknown')} / {breadth.get('state', 'unknown')}",
            f"- 反弹质量: {rebound.get('quality', 'unknown')}",
            f"- 外部信号: {external.get('signal', 'unknown')} / {external.get('allowed_effect', 'none')}",
            f"- 方向上限: {constraints.get('direction_cap', '') or 'none'}",
            f"- 仓位上限: {constraints.get('position_cap', '') or 'none'}",
            f"- 风险标记: {', '.join(risk_flags) if risk_flags else 'none'}",
            "",
        ]

    def _risk_level(self, constraints: Dict[str, Any]) -> str:
        risk_flags = set(constraints.get("risk_flags") or [])
        direction_cap = str(constraints.get("direction_cap") or "")
        if {"breadth_collapse", "risk_off", "failed_rebound"} & risk_flags or direction_cap in {"down", "sideways_down"}:
            return "high"
        if risk_flags or direction_cap in {"sideways", "sideways_up"}:
            return "medium"
        return "low"

    def _direction(self, prediction: Dict[str, Any]) -> str:
        probabilities = prediction.get("probabilities") or {}
        if not probabilities:
            return "sideways"
        return max(("up", "sideways", "down"), key=lambda key: probabilities.get(key, 0))


def now_iso() -> str:
    return datetime.now(CN_TZ).isoformat(timespec="seconds")
