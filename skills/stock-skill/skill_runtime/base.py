from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SkillResult:
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    trace_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "trace_id": self.trace_id,
        }


class BaseSkill:
    name = "base"

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        raise NotImplementedError
