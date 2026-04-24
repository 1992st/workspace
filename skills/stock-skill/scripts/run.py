#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

SKILL_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = SKILL_ROOT / "skill_runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from registry import SkillRegistry


def _json_or_file(value: str) -> Dict[str, Any]:
    candidate = Path(value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))
    return json.loads(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Win_Stock stock-skill runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list skills")
    list_parser.add_argument("--json", action="store_true")

    run_parser = subparsers.add_parser("run", help="run a skill action")
    run_parser.add_argument("--skill", required=True)
    run_parser.add_argument("--action", required=True)
    run_parser.add_argument("--input", default="{}")

    args = parser.parse_args()
    registry = SkillRegistry()

    if args.command == "list":
        names = registry.names()
        if args.json:
            print(json.dumps({"skills": names}, ensure_ascii=False, indent=2))
        else:
            print("\n".join(names))
        return 0

    payload = _json_or_file(args.input)
    payload["action"] = args.action
    result = registry.get(args.skill).run(payload)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"ok", "degraded"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
