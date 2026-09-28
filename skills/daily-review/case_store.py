"""Append-only storage for multi-agent prediction cases.

The store deliberately has no update or delete operation.  A review can only
append a new outcome/audit record, which keeps the original facts and
predictions reproducible.
"""

from __future__ import annotations

import hashlib
import json
import uuid
import fcntl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


RECORD_TYPES = ("cases", "facts", "features", "predictions", "audits", "outcomes")


class ImmutableCaseStore:
    """Small filesystem-backed append-only repository.

    Records are JSON Lines so a partially completed nightly run remains
    inspectable.  Existing record IDs cannot be written again, even when the
    payload is identical; this prevents a later agent from silently replacing
    a frozen prediction.
    """

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        for record_type in RECORD_TYPES:
            (self.root / f"{record_type}.jsonl").touch(exist_ok=True)

    def create_case(self, payload: Dict[str, Any], *, case_id: str | None = None) -> Dict[str, Any]:
        return self._append("cases", payload, record_id=case_id or self._id("case"))

    def append_fact(self, case_id: str, payload: Dict[str, Any], *, fact_id: str | None = None) -> Dict[str, Any]:
        return self._append_child("facts", case_id, payload, record_id=fact_id or self._id("fact"))

    def append_prediction(self, case_id: str, payload: Dict[str, Any], *, prediction_id: str | None = None) -> Dict[str, Any]:
        if self.for_case("predictions", case_id):
            raise ValueError(f"prediction already frozen for case: {case_id}; create a revision case")
        return self._append_child("predictions", case_id, payload, record_id=prediction_id or self._id("prediction"))

    def append_feature(self, case_id: str, payload: Dict[str, Any], *, feature_id: str | None = None) -> Dict[str, Any]:
        return self._append_child("features", case_id, payload, record_id=feature_id or self._id("feature"))

    def append_audit(self, case_id: str, payload: Dict[str, Any], *, audit_id: str | None = None) -> Dict[str, Any]:
        if not self.for_case("predictions", case_id):
            raise ValueError(f"audit requires frozen prediction: {case_id}")
        return self._append_child("audits", case_id, payload, record_id=audit_id or self._id("audit"))

    def append_outcome(self, case_id: str, payload: Dict[str, Any], *, outcome_id: str | None = None) -> Dict[str, Any]:
        if not self.for_case("predictions", case_id):
            raise ValueError(f"outcome requires frozen prediction: {case_id}")
        return self._append_child("outcomes", case_id, payload, record_id=outcome_id or self._id("outcome"))

    def get(self, record_type: str, record_id: str) -> Optional[Dict[str, Any]]:
        return next((row for row in self._read(record_type) if row.get("id") == record_id), None)

    def for_case(self, record_type: str, case_id: str) -> List[Dict[str, Any]]:
        return [row for row in self._read(record_type) if row.get("case_id") == case_id or (record_type == "cases" and row.get("id") == case_id)]

    def _append(self, record_type: str, payload: Dict[str, Any], *, record_id: str) -> Dict[str, Any]:
        if record_type not in RECORD_TYPES:
            raise ValueError(f"unsupported record type: {record_type}")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        record = dict(payload)
        record["id"] = record_id
        record["record_type"] = record_type[:-1]
        record["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record["content_sha256"] = self._hash(record)
        path = self.root / f"{record_type}.jsonl"
        lock_path = self.root / ".append.lock"
        with lock_path.open("a", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            if self.get(record_type, record_id) is not None:
                raise ValueError(f"immutable record already exists: {record_type}/{record_id}")
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
        return record

    def _append_child(self, record_type: str, case_id: str, payload: Dict[str, Any], *, record_id: str) -> Dict[str, Any]:
        if self.get("cases", case_id) is None:
            raise ValueError(f"case does not exist: {case_id}")
        child_payload = dict(payload)
        child_payload["case_id"] = case_id
        return self._append(record_type, child_payload, record_id=record_id)

    def _read(self, record_type: str) -> Iterable[Dict[str, Any]]:
        if record_type not in RECORD_TYPES:
            raise ValueError(f"unsupported record type: {record_type}")
        path = self.root / f"{record_type}.jsonl"
        if not path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    @staticmethod
    def _hash(record: Dict[str, Any]) -> str:
        unsigned = {key: value for key, value in record.items() if key != "content_sha256"}
        raw = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
