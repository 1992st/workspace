from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict

from index_writer import IndexWriter


CN_TZ = timezone(timedelta(hours=8))


class BlockedReportWriter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.index = IndexWriter(root)

    def write(self, payload: Dict[str, Any]) -> Dict[str, str]:
        target_type = payload["target_type"]
        date = payload["trading_date"]
        if target_type == "market":
            base = self.root / "data" / "market" / "predictions"
            stem = f"{date}_market_blocked"
        else:
            sector = str(payload["target"]).replace("/", "_")
            base = self.root / "data" / "sectors" / "predictions" / sector
            stem = f"{date}_blocked"
        base.mkdir(parents=True, exist_ok=True)
        md_path = base / f"{stem}.md"
        json_path = base / f"{stem}.json"
        raw_path = base / f"{stem}_vibe_raw.json"
        payload.setdefault("artifacts", {})
        payload["artifacts"]["blocked_report_path"] = str(md_path)
        payload["artifacts"]["json_path"] = str(json_path)
        payload["artifacts"]["markdown_path"] = str(md_path)
        payload["artifacts"]["vibe_raw_path"] = str(raw_path)
        raw_path.write_text(json.dumps(payload.get("vibe_raw", {}), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self._markdown(payload), encoding="utf-8")
        self.index.write(
            {
                "date": date,
                "target_type": target_type,
                "target": payload.get("target"),
                "horizon": payload.get("horizon"),
                "mode": payload.get("mode"),
                "status": "blocked",
                "confidence": 0,
                "json_path": str(json_path),
                "markdown_path": str(md_path),
                "vibe_run_id": payload.get("engine", {}).get("vibe_run_id", ""),
                "review_status": "reviewed",
            }
        )
        return {
            "json_path": str(json_path),
            "markdown_path": str(md_path),
            "blocked_report_path": str(md_path),
            "vibe_raw_path": str(raw_path),
        }

    def _markdown(self, payload: Dict[str, Any]) -> str:
        quality = payload.get("data_quality", {})
        return "\n".join(
            [
                f"# {payload.get('target')} 预测阻断报告",
                "",
                f"- 生成时间: {payload.get('generated_at')}",
                f"- 目标: {payload.get('target')}",
                f"- 周期: {payload.get('horizon')}",
                "",
                "## 结论",
                "本次不输出方向预测。",
                "",
                "## 阻断原因",
                *[f"- {item}" for item in quality.get("blocking_reasons", [])],
                "",
                "## 缺失数据",
                *[f"- {item}" for item in quality.get("missing_sections", [])],
                "",
                "## Vibe 可用工具",
                json.dumps(payload.get("engine", {}), ensure_ascii=False, indent=2),
                "",
                "## 本地数据状态",
                json.dumps(payload.get("local_snapshot", {}), ensure_ascii=False, indent=2),
                "",
                "## 事实冲突",
                json.dumps(payload.get("fact_reconciliation", {}), ensure_ascii=False, indent=2),
            ]
        )
