from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class IndexWriter:
    def __init__(self, root: Path) -> None:
        self.root = root

    def write(self, record: Dict[str, Any]) -> None:
        target_type = record.get("target_type")
        if target_type == "market":
            path = self.root / "data" / "market" / "predictions" / "index.jsonl"
        elif target_type == "sector":
            path = self.root / "data" / "sectors" / "predictions" / "index.jsonl"
        else:
            path = self.root / "data" / "predictions" / "vibe_runs" / "index.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = self._read_rows(path)
        key = self._key(record)
        replaced = False
        for idx, row in enumerate(rows):
            if self._key(row) == key:
                rows[idx] = record
                replaced = True
        if not replaced:
            rows.append(record)
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def write_vibe_run(self, record: Dict[str, Any]) -> None:
        payload = {"target_type": "vibe_run", **record}
        self.write(payload)

    def _read_rows(self, path: Path) -> list[Dict[str, Any]]:
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except Exception:
                continue
            if isinstance(value, dict):
                rows.append(value)
        return rows

    def _key(self, record: Dict[str, Any]) -> tuple[Any, ...]:
        return (
            record.get("date"),
            record.get("target_type"),
            record.get("target"),
            record.get("horizon"),
            record.get("mode"),
        )
