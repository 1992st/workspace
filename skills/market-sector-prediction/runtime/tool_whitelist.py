from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


ALLOWED_TOOLS = {
    "get_market_data",
    "factor_analysis",
    "backtest",
    "pattern_recognition",
    "run_swarm",
    "get_swarm_status",
    "get_run_result",
    "list_runs",
    "web_search",
    "read_url",
}

FORBIDDEN_TOOLS = {"write_file", "execute_code", "shell"}


@dataclass(frozen=True)
class ToolPolicy:
    allowed_tools: set[str]

    @classmethod
    def default(cls) -> "ToolPolicy":
        return cls(allowed_tools=set(ALLOWED_TOOLS))

    def validate(self, tool_name: str) -> None:
        if tool_name in FORBIDDEN_TOOLS or tool_name not in self.allowed_tools:
            raise ValueError(f"Vibe tool is not allowed: {tool_name}")

    def enabled_from_manifest(self, detected: Iterable[str]) -> List[str]:
        return sorted(tool for tool in detected if tool in self.allowed_tools)

    def disabled_from_manifest(self, detected: Iterable[str]) -> List[str]:
        detected_set = set(detected)
        missing = self.allowed_tools - detected_set
        forbidden_detected = detected_set & FORBIDDEN_TOOLS
        return sorted(missing | forbidden_detected)
