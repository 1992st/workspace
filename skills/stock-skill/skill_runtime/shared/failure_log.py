from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .utils import ensure_parent, now_iso


class ToolFailureRecorder:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def record(self, event: Dict[str, Any]) -> str:
        timestamp = now_iso()
        record = {
            "timestamp": timestamp,
            **event,
        }
        path = self.root / f"{timestamp[:10]}.jsonl"
        ensure_parent(path)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return str(path)
