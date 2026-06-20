from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List


CN_TZ = timezone(timedelta(hours=8))
SUPPORTED_TAXONOMIES = {"eastmoney_industry", "eastmoney_concept", "shenwan_industry", "custom_watchlist_sector"}


class SectorTaxonomyResolver:
    def __init__(self, root: Path) -> None:
        self.root = root

    def resolve(self, sector: str, taxonomy: str | None = None, members: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        sector_name = str(sector or "").replace("板块", "").strip()
        selected = taxonomy or "eastmoney_industry"
        if selected not in SUPPORTED_TAXONOMIES:
            return {
                "status": "blocked",
                "reason": f"unsupported sector taxonomy: {selected}",
                "sector_name": sector_name,
                "sector_taxonomy": selected,
            }
        snapshot_members = members or []
        date = datetime.now(CN_TZ).strftime("%Y-%m-%d")
        path = self.root / "data" / "sectors" / "snapshots" / sector_name / f"{date}_members.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sector_name": sector_name,
            "sector_taxonomy": selected,
            "sector_id": f"{selected}:{sector_name}",
            "member_count": len(snapshot_members),
            "members": snapshot_members,
            "generated_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "status": "ok",
            "sector_name": sector_name,
            "sector_taxonomy": selected,
            "sector_id": payload["sector_id"],
            "members_snapshot_path": str(path),
            "member_count": len(snapshot_members),
        }
