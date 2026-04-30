from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, List


REQUIRED_FIELDS = {
    "strategy_id",
    "source_principle_id",
    "title_cn",
    "status",
    "injection_mode",
    "category",
    "priority",
    "scenes",
    "trigger_tags",
    "prompt_snippet",
    "checklist",
}


def load_registries(root: Path) -> List[Dict[str, object]]:
    registries: List[Dict[str, object]] = []
    for book_dir in sorted(root.glob("books/*")):
        if not book_dir.is_dir():
            continue
        new_path = book_dir / "strategy" / "registry.json"
        legacy_path = book_dir / "strategy_registry.json"
        selected_path = None
        if new_path.exists():
            selected_path = new_path
        elif legacy_path.exists():
            selected_path = legacy_path
            print(
                f"[DEPRECATION] legacy strategy registry path detected: {legacy_path}. "
                f"Please migrate to {new_path}.",
                file=sys.stderr,
            )
        if selected_path is None:
            continue
        payload = json.loads(selected_path.read_text(encoding="utf-8"))
        payload["_registry_path"] = str(selected_path)
        registries.append(payload)
    return registries


def validate_strategy(strategy: Dict[str, object], registry_path: str) -> None:
    missing = REQUIRED_FIELDS - set(strategy.keys())
    if missing:
        raise ValueError(f"{registry_path}: missing fields for {strategy.get('strategy_id')}: {sorted(missing)}")
    if strategy["status"] not in {"draft", "candidate", "approved", "deprecated"}:
        raise ValueError(f"{registry_path}: invalid status for {strategy['strategy_id']}")
    if strategy["injection_mode"] not in {"global", "conditional"}:
        raise ValueError(f"{registry_path}: invalid injection_mode for {strategy['strategy_id']}")
    if not strategy["prompt_snippet"]:
        raise ValueError(f"{registry_path}: empty prompt_snippet for {strategy['strategy_id']}")
    if "stock_analysis" not in strategy["scenes"]:
        raise ValueError(f"{registry_path}: strategy {strategy['strategy_id']} must include stock_analysis scene")


def compile_strategies(root: Path, target_version: str) -> Dict[str, object]:
    registries = load_registries(root)
    strategy_ids = set()
    approved: List[Dict[str, object]] = []
    source_books: List[Dict[str, str]] = []

    for registry in registries:
        source_books.append(
            {
                "book_id": str(registry["book_id"]),
                "book_title": str(registry["book_title"]),
                "registry_path": registry["_registry_path"],
            }
        )
        for strategy in registry["strategies"]:
            validate_strategy(strategy, str(registry["_registry_path"]))
            strategy_id = str(strategy["strategy_id"])
            if strategy_id in strategy_ids:
                raise ValueError(f"duplicate strategy_id detected: {strategy_id}")
            strategy_ids.add(strategy_id)
            merged = dict(strategy)
            merged["book_id"] = registry["book_id"]
            merged["book_title"] = registry["book_title"]
            if merged["status"] == "approved":
                approved.append(merged)

    approved.sort(key=lambda item: (-int(item["priority"]), str(item["strategy_id"])))
    globals_ = [item for item in approved if item["injection_mode"] == "global"]
    conditionals = [item for item in approved if item["injection_mode"] == "conditional"]

    compiled_at = dt.date.today().isoformat()
    return {
        "strategy_version": target_version,
        "prompt_version": target_version,
        "compiled_at": compiled_at,
        "scene": "stock_analysis",
        "source_books": source_books,
        "catalog": approved,
        "global_strategies": globals_,
        "conditional_strategies": conditionals,
        "conditional_profiles": {
            "buy_watch": {
                "action_intents": ["buy", "watch", "observe", "build"],
                "include_tags": ["buy_decision", "trend_following", "timing"],
            },
            "sell_hold": {
                "action_intents": ["sell", "hold", "trim", "exit", "reduce"],
                "include_tags": ["sell_decision", "downside_defense", "profit_protection"],
            },
            "strong_market": {
                "action_intents": ["buy", "watch", "observe", "build"],
                "market_bias": ["bullish"],
                "include_tags": ["trend_following", "buy_decision"],
            },
            "weak_market": {
                "action_intents": ["sell", "hold", "trim", "exit", "reduce"],
                "market_bias": ["bearish"],
                "include_tags": ["sell_decision", "downside_defense"],
            },
            "insufficient_data": {
                "confidence_gate": ["insufficient_data"],
                "include_tags": [],
                "note": "no extra conditional strategy should be injected when key evidence is missing",
            },
        },
        "base_prompt": build_base_prompt(target_version, globals_),
        "changelog": build_changelog(target_version, compiled_at, globals_, conditionals),
    }


def build_base_prompt(target_version: str, strategies: List[Dict[str, object]]) -> str:
    lines = [
        "# Book Strategy Base",
        f"",
        f"- strategy_version: {target_version}",
        "- scene: stock_analysis",
        "- rule: always apply these global book strategies before generating a trade recommendation",
        "",
    ]
    for strategy in strategies:
        lines.append(f"## {strategy['strategy_id']} {strategy['title_cn']}")
        lines.append(f"- snippet: {strategy['prompt_snippet']}")
        for item in strategy["checklist"]:
            lines.append(f"- check: {item}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_changelog(
    target_version: str,
    compiled_at: str,
    globals_: List[Dict[str, object]],
    conditionals: List[Dict[str, object]],
) -> str:
    return (
        f"# Strategy Changelog\n\n"
        f"## {target_version} ({compiled_at})\n"
        f"- 初次引入 book 策略编译产物。\n"
        f"- 全量注入策略 {len(globals_)} 条。\n"
        f"- 条件注入策略 {len(conditionals)} 条。\n"
        f"- 运行时由 `analysis.stock.prepare` 记录注入策略 ID、选择原因和策略版本。\n"
    )


def write_outputs(root: Path, target_version: str, compiled: Dict[str, object]) -> None:
    version_dir = root / "prompts" / target_version / "compiled"
    active_dir = root / "prompts" / "current" / "compiled"
    payloads = {
        "strategy_manifest.json": json.dumps(
            {
                "strategy_version": compiled["strategy_version"],
                "prompt_version": compiled["prompt_version"],
                "compiled_at": compiled["compiled_at"],
                "scene": compiled["scene"],
                "source_books": compiled["source_books"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        "stock_strategy_catalog.json": json.dumps(compiled["catalog"], ensure_ascii=False, indent=2) + "\n",
        "stock_strategy_conditional.json": json.dumps(
            compiled["conditional_profiles"], ensure_ascii=False, indent=2
        )
        + "\n",
        "stock_strategy_base.md": str(compiled["base_prompt"]),
        "CHANGELOG.md": str(compiled["changelog"]),
    }
    for compiled_dir in (version_dir, active_dir):
        compiled_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in payloads.items():
            (compiled_dir / filename).write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path(__file__).resolve().parents[2], type=Path)
    parser.add_argument("--target-version", required=True)
    args = parser.parse_args()

    compiled = compile_strategies(args.root, args.target_version)
    write_outputs(args.root, args.target_version, compiled)


if __name__ == "__main__":
    main()
