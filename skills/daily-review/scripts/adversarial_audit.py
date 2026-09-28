#!/usr/bin/env python3
"""Validate immutable prediction cases and produce adversarial audit results."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


IDENTITY_FIELDS = ("case_id", "symbol", "decision_time", "data_cutoff", "horizon")
REQUIRED_CASE_FIELDS = IDENTITY_FIELDS + (
    "market_session",
    "snapshot_id",
    "universe_version",
    "prompt_version",
    "rule_version",
)
REQUIRED_PREDICTION_FIELDS = ("prediction_id", "case_id", "direction", "horizon")
FORBIDDEN_DIRECTIONAL_PHRASES = (
    "不排除上涨",
    "可能反弹也可能继续下跌",
    "方向偏弱但仍有机会",
    "若突破看多，若跌破看空",
)
INTENT_PHRASES = ("主力出货", "主力吸筹", "诱多", "护盘", "庄家")


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def validate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    case_meta = case.get("case") if isinstance(case.get("case"), dict) else case
    for field in REQUIRED_CASE_FIELDS:
        if not str(case_meta.get(field) or "").strip():
            errors.append(f"missing case.{field}")

    decision_time = _parse_time(case_meta.get("decision_time"))
    cutoff = _parse_time(case_meta.get("data_cutoff"))
    if case_meta.get("decision_time") and decision_time is None:
        errors.append("case.decision_time must be ISO-8601")
    if case_meta.get("data_cutoff") and cutoff is None:
        errors.append("case.data_cutoff must be ISO-8601")
    if decision_time and cutoff and cutoff > decision_time:
        errors.append("case.data_cutoff cannot be later than decision_time")

    facts = case.get("facts", [])
    features = case.get("features", [])
    if not isinstance(facts, list):
        errors.append("facts must be a list")
    if not isinstance(features, list):
        errors.append("features must be a list")

    fact_ids = {item.get("fact_id") for item in facts if isinstance(item, dict)}
    for index, fact in enumerate(facts if isinstance(facts, list) else []):
        if not isinstance(fact, dict):
            errors.append(f"facts[{index}] must be an object")
            continue
        if not fact.get("fact_id"):
            errors.append(f"facts[{index}].fact_id is required")
        source_time = _parse_time(fact.get("source_time"))
        if source_time is None:
            errors.append(f"facts[{index}].source_time must be ISO-8601")
        elif cutoff and source_time > cutoff:
            errors.append(f"facts[{index}] is newer than data_cutoff")
        if not fact.get("source"):
            errors.append(f"facts[{index}].source is required")

    for index, feature in enumerate(features if isinstance(features, list) else []):
        if not isinstance(feature, dict):
            errors.append(f"features[{index}] must be an object")
            continue
        if not feature.get("feature_id"):
            errors.append(f"features[{index}].feature_id is required")
        references = feature.get("fact_ids", [])
        if not isinstance(references, list) or not references:
            errors.append(f"features[{index}].fact_ids is required")
        elif not set(references).issubset(fact_ids):
            errors.append(f"features[{index}] references unknown fact_ids")
        if not feature.get("formula"):
            errors.append(f"features[{index}].formula is required")

    prediction = case.get("prediction") or {}
    if prediction:
        for field in REQUIRED_PREDICTION_FIELDS:
            if not str(prediction.get(field) or "").strip():
                errors.append(f"prediction.{field} is required")
        if prediction.get("case_id") and prediction.get("case_id") != case_meta.get("case_id"):
            errors.append("prediction.case_id must match case.case_id")
        if not prediction.get("invalidation"):
            errors.append("prediction.invalidation is required")
        text = _canonical(prediction)
        for phrase in FORBIDDEN_DIRECTIONAL_PHRASES:
            if phrase in text:
                errors.append(f"non-falsifiable phrase: {phrase}")

    return {"valid": not errors, "errors": errors}


def build_audit(case: Dict[str, Any], *, counter_case: str = "", counter_evidence_ids: Iterable[str] = ()) -> Dict[str, Any]:
    validation = validate_case(case)
    prediction = case.get("prediction") or {}
    text = _canonical(case)
    intent_phrases = [phrase for phrase in INTENT_PHRASES if phrase in text]
    issues = list(validation["errors"])
    if intent_phrases:
        issues.append("intent language requires traceable funding evidence")
    if not counter_case.strip():
        issues.append("counter_case is required")
    severity = "P0" if any("newer than data_cutoff" in item for item in issues) else "P1" if issues else "P3"
    status = "blocked" if issues else "pass"
    return {
        "audit_status": status,
        "severity": severity,
        "errors": issues,
        "counter_case": counter_case,
        "counter_evidence_ids": list(counter_evidence_ids),
        "root_cause_category": ["data_integrity"] if any("data_cutoff" in item for item in issues) else [],
        "allowed_action_scope": "blocked" if issues else "observe",
        "prediction_hash": content_hash(prediction),
        "audited_at": datetime.now(timezone.utc).isoformat(),
    }


def save_case(case: Dict[str, Any], root: Path) -> Path:
    validation = validate_case(case)
    if not validation["valid"]:
        raise ValueError("invalid case: " + "; ".join(validation["errors"]))
    meta = case.get("case", case)
    case_id = str(meta["case_id"])
    destination = root / case_id
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("case", "facts", "features", "prediction"):
        value = case.get(name, meta if name == "case" else {})
        path = destination / f"{name}.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            if _canonical(existing) != _canonical(value):
                raise FileExistsError(f"immutable artifact already exists: {path}")
            continue
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    (destination / "_SUCCESS").write_text("ok\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    parser.add_argument("--root", type=Path, default=Path("data/market/cases"))
    args = parser.parse_args()
    payload = json.loads(args.case.read_text(encoding="utf-8"))
    validation = validate_case(payload)
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    if not validation["valid"]:
        return 2
    save_case(payload, args.root / str(payload.get("case", payload)["trade_date"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
