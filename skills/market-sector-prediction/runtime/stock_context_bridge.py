from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional


CN_TZ = timezone(timedelta(hours=8))


class StockContextBridge:
    def __init__(self, root: Path) -> None:
        self.root = root

    def latest_market_prediction(self) -> Optional[Dict[str, Any]]:
        return self._latest_from_index(self.root / "data" / "market" / "predictions" / "index.jsonl")

    def latest_sector_prediction(self, sector: str) -> Optional[Dict[str, Any]]:
        index_path = self.root / "data" / "sectors" / "predictions" / "index.jsonl"
        return self._latest_from_index(index_path, target=sector)

    def build_context(self, sector: str | None = None) -> Dict[str, Any]:
        return {
            "market_prediction": self.latest_market_prediction(),
            "sector_prediction": self.latest_sector_prediction(sector) if sector else None,
            "freshness_rule": "盘中2小时、盘前盘后至下一交易日开盘、中期5交易日",
        }

    def _latest_from_index(self, path: Path, target: str | None = None) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if target:
            records = [record for record in records if record.get("target") == target]
        records = [record for record in records if record.get("status") in {"ok", "degraded"} and self._is_fresh(record)]
        if not records:
            return None
        latest = records[-1]
        json_path = latest.get("json_path")
        if json_path and Path(json_path).exists():
            return json.loads(Path(json_path).read_text(encoding="utf-8"))
        return latest

    def _is_fresh(self, record: Dict[str, Any]) -> bool:
        horizon = record.get("horizon")
        date_text = str(record.get("date") or "")
        if not date_text:
            return False
        try:
            record_date = datetime.fromisoformat(date_text)
        except ValueError:
            try:
                record_date = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=CN_TZ)
            except ValueError:
                return False
        now = datetime.now(CN_TZ)
        if horizon == "mid":
            return now - record_date <= timedelta(days=7)
        return now.date() == record_date.date() or now - record_date <= timedelta(days=1)
