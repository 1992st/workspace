from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class PredictionDataCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / "data" / "predictions" / "cache"

    def read(self, key: str, max_age_sec: int | None = None, allow_stale: bool = False) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        age = time.time() - float(payload.get("_ts") or 0)
        if max_age_sec is not None and age > max_age_sec and not allow_stale:
            return None
        return {
            "data": payload.get("data"),
            "age_sec": round(age, 1),
            "stale": bool(max_age_sec is not None and age > max_age_sec),
            "path": str(path),
        }

    def write(self, key: str, data: Any) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"_ts": time.time(), "data": data}, ensure_ascii=False, default=str), encoding="utf-8")
        return str(path)

    def _path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.base / f"{safe}.json"
