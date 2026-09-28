#!/usr/bin/env python3
"""CLI for immutable prediction-case lifecycle operations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from adversarial_audit import build_audit, validate_case
from case_store import ImmutableCaseStore


def build_case_id(symbol: str, decision_time: str, horizon: str, sequence: int) -> str:
    parsed = datetime.fromisoformat(decision_time.replace("Z", "+00:00"))
    safe_horizon = re.sub(r"[^A-Za-z0-9]+", "", horizon.upper())
    return f"{parsed:%Y%m%d}-{symbol.zfill(6)}-{parsed:%H%M}-{safe_horizon}-{sequence:03d}"


def read_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def create_records(store: ImmutableCaseStore, payload: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_case(payload)
    if not validation["valid"]:
        raise ValueError("invalid case: " + "; ".join(validation["errors"]))
    meta = payload["case"]
    case_id = meta["case_id"]
    created = {"case": store.create_case(meta, case_id=case_id)}
    created["facts"] = [
        store.append_fact(case_id, item, fact_id=item["fact_id"]) for item in payload.get("facts", [])
    ]
    created["features"] = [
        store.append_feature(case_id, item, feature_id=item["feature_id"]) for item in payload.get("features", [])
    ]
    prediction = payload.get("prediction") or {}
    if prediction:
        created["prediction"] = store.append_prediction(
            case_id, prediction, prediction_id=prediction["prediction_id"]
        )
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Win_Stock immutable case pipeline")
    parser.add_argument("--store", type=Path, default=Path("data/market/case_store"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    id_parser = subparsers.add_parser("case-id")
    id_parser.add_argument("--symbol", required=True)
    id_parser.add_argument("--decision-time", required=True)
    id_parser.add_argument("--horizon", required=True)
    id_parser.add_argument("--sequence", required=True, type=int)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--input", required=True, type=Path)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--input", required=True, type=Path)
    audit_parser.add_argument("--counter-case", required=True)
    audit_parser.add_argument("--counter-evidence-id", action="append", default=[])

    outcome_parser = subparsers.add_parser("outcome")
    outcome_parser.add_argument("--case-id", required=True)
    outcome_parser.add_argument("--input", required=True, type=Path)
    outcome_parser.add_argument("--outcome-id", required=True)

    args = parser.parse_args()
    if args.command == "case-id":
        print(build_case_id(args.symbol, args.decision_time, args.horizon, args.sequence))
        return 0

    store = ImmutableCaseStore(args.store)
    if args.command == "create":
        result = create_records(store, read_json(args.input))
    elif args.command == "audit":
        payload = read_json(args.input)
        result = build_audit(
            payload,
            counter_case=args.counter_case,
            counter_evidence_ids=args.counter_evidence_id,
        )
        case_id = payload["case"]["case_id"]
        store.append_audit(case_id, result, audit_id=f"audit-{case_id}")
    else:
        result = store.append_outcome(
            args.case_id, read_json(args.input), outcome_id=args.outcome_id
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
