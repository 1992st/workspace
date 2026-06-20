from __future__ import annotations

from typing import Iterable


def confidence_cap(
    *,
    mode: str,
    complete_data: bool,
    has_backtest: bool,
    has_swarm: bool,
    missing_sections: Iterable[str],
    taxonomy_conflict: bool = False,
    local_only: bool = False,
) -> int:
    missing = set(missing_sections)
    if taxonomy_conflict:
        return 50
    if local_only:
        return 45
    if "fund_flow" in missing:
        return 55
    if "market_breadth" in missing:
        return 55
    if "backtest" in missing or not has_backtest:
        return 68
    if mode == "deep" and complete_data and has_swarm and has_backtest:
        return 82
    if complete_data:
        return 72
    return 55
