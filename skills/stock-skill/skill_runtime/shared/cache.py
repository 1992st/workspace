from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from .utils import ensure_parent, now_iso


class FileCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, key: str, max_age_sec: Optional[int] = None) -> Optional[Dict[str, Any]]:
        path = self._path(key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if max_age_sec is not None:
            stored_at = payload.get("stored_at")
            if stored_at:
                age = datetime.fromisoformat(now_iso()) - datetime.fromisoformat(stored_at)
                if age > timedelta(seconds=max_age_sec):
                    return None
        return payload

    def get_any(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, key: str, response: Dict[str, Any]) -> str:
        path = self._path(key)
        ensure_parent(path)
        wrapped = {"stored_at": now_iso(), "response": response}
        path.write_text(json.dumps(wrapped, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
