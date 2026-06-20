from __future__ import annotations

from typing import Literal


Direction = Literal["up", "sideways", "down"]


def market_threshold(horizon: str) -> float:
    return 2.5 if horizon == "mid" else 0.8


def sector_threshold(horizon: str, volatility_20d: float | None = None) -> float:
    vol = abs(float(volatility_20d or 0.0))
    if horizon == "mid":
        return max(3.0, vol)
    return max(1.0, 0.5 * vol)


def classify_return(change_pct: float, threshold: float) -> Direction:
    if change_pct > threshold:
        return "up"
    if change_pct < -threshold:
        return "down"
    return "sideways"


def support_resistance_hit(actual: float, level: float, tolerance_pct: float = 0.3) -> bool:
    if level == 0:
        return False
    return abs(actual - level) / abs(level) * 100 <= tolerance_pct
