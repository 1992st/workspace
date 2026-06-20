from __future__ import annotations

from typing import Any, Dict, List


def reconcile_market(local: Dict[str, Any], vibe: Dict[str, Any] | None = None) -> Dict[str, Any]:
    vibe = vibe or {}
    conflicts: List[Dict[str, Any]] = []
    authoritative: List[Dict[str, Any]] = []
    status = "ok"

    local_date = local.get("trading_date")
    vibe_date = vibe.get("trading_date") or vibe.get("date")
    if local_date and vibe_date and str(local_date) != str(vibe_date):
        conflicts.append({"field": "trading_date", "local": local_date, "vibe": vibe_date, "severity": "blocked"})
        status = "blocked"

    if local.get("amount_unit_uncertain"):
        conflicts.append({"field": "amount", "severity": "blocked", "reason": "成交额单位无法确认"})
        status = "blocked"

    if local.get("indices"):
        authoritative.append({"field": "indices", "source": "win_stock_local", "value": local.get("indices")})

    return {"status": status, "conflicts": conflicts, "authoritative_values": authoritative}


def reconcile_sector(local: Dict[str, Any], vibe: Dict[str, Any] | None = None) -> Dict[str, Any]:
    result = reconcile_market(local, vibe)
    local_members = set(local.get("member_codes") or [])
    vibe_members = set((vibe or {}).get("member_codes") or [])
    if local_members and vibe_members:
        diff = local_members.symmetric_difference(vibe_members)
        denominator = max(len(local_members | vibe_members), 1)
        diff_ratio = len(diff) / denominator
        if diff_ratio > 0.2:
            result["status"] = "degraded" if result["status"] != "blocked" else "blocked"
            result["conflicts"].append(
                {
                    "field": "sector_members",
                    "severity": "degraded",
                    "reason": "板块成分股差异超过20%",
                    "diff_ratio": round(diff_ratio, 4),
                }
            )
    return result
