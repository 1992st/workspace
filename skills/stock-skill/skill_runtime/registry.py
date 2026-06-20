from __future__ import annotations

from typing import Callable, Dict

from base import BaseSkill
from prediction_skill import PredictionSkill
from stock_skill import StockSkill


class SkillRegistry:
    def __init__(self) -> None:
        self._factories: Dict[str, Callable[[], BaseSkill]] = {
            "prediction": PredictionSkill,
            "stock": StockSkill,
        }
        self._instances: Dict[str, BaseSkill] = {}

    def get(self, name: str) -> BaseSkill:
        if name not in self._factories:
            raise KeyError(f"unknown skill: {name}")
        if name not in self._instances:
            self._instances[name] = self._factories[name]()
        return self._instances[name]

    def names(self):
        return sorted(self._factories.keys())
