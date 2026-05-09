from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class AnalysisResourceLoader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo_root = root.parents[1]
        self.prompts_dir = root / "resources" / "prompts" / "v1"
        self.knowledge_dir = root / "resources" / "knowledge" / "v1"
        self.strategy_prompt_root = self.repo_root / "prompts"
        self.active_strategy_dir = self.strategy_prompt_root / "current" / "compiled"

    def load_stock_analysis_bundle(self) -> Dict[str, object]:
        prompt_files = [
            "master.md",
            "market-analysis.md",
            "stock-analysis.md",
            "insufficient-data.md",
            "output-style.md",
            "review-framework.md",
        ]
        knowledge_files = [
            "evidence-thresholds.md",
            "short-swing-playbook.md",
            "data-quality-guidelines.md",
        ]
        prompts = self._load_entries(self.prompts_dir, prompt_files)
        knowledge = self._load_entries(self.knowledge_dir, knowledge_files)
        compiled_prompt = "\n\n".join(
            [f"# {entry['name']}\n{entry['content']}" for entry in prompts]
        )
        strategy_artifacts = self._load_strategy_artifacts()
        return {
            "version": "v1",
            "prompt_modules": prompts,
            "knowledge_entries": knowledge,
            "compiled_prompt": compiled_prompt,
            "evidence_threshold": self._extract_evidence_threshold(knowledge),
            "strategy_artifacts": strategy_artifacts,
        }

    def _load_entries(self, base: Path, names: List[str]) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        for name in names:
            path = base / name
            content = path.read_text(encoding="utf-8").strip()
            entries.append(
                {
                    "name": name,
                    "path": str(path),
                    "content": content,
                }
            )
        return entries

    def _extract_evidence_threshold(self, knowledge: List[Dict[str, str]]) -> Dict[str, object]:
        threshold = {
            "minimum_sections_for_trade_plan": [
                "quote",
                "kline",
                "market_snapshot",
                "sector_map",
                "sector_heat",
                "flow_main",
            ],
            "hard_blockers": [
                "quote.get",
                "kline.get",
                "market.snapshot.get",
                "sector.map.get",
            ],
            "guidance": "",
        }
        for entry in knowledge:
            if entry["name"] == "evidence-thresholds.md":
                threshold["guidance"] = entry["content"]
                break
        return threshold

    def _load_strategy_artifacts(self) -> Dict[str, object]:
        compiled_dir, activation_source = self._resolve_strategy_artifact_dir()
        if compiled_dir is None:
            return {
                "bundle_version": None,
                "compiled_at": None,
                "activation_source": "unavailable",
                "base_prompt": "",
                "catalog": [],
                "conditional_profiles": {},
                "manifest_path": None,
            }

        manifest_path = compiled_dir / "strategy_manifest.json"
        base_prompt_path = compiled_dir / "stock_strategy_base.md"
        catalog_path = compiled_dir / "stock_strategy_catalog.json"
        conditional_path = compiled_dir / "stock_strategy_conditional.json"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        conditional_profiles = json.loads(conditional_path.read_text(encoding="utf-8"))
        base_prompt = base_prompt_path.read_text(encoding="utf-8").strip()
        return {
            "bundle_version": manifest["bundle_version"],
            "compiled_at": manifest["compiled_at"],
            "activation_source": activation_source,
            "scene": manifest["scene"],
            "source_books": manifest["source_books"],
            "base_prompt": base_prompt,
            "catalog": catalog,
            "conditional_profiles": conditional_profiles,
            "manifest_path": str(manifest_path),
        }

    def _resolve_strategy_artifact_dir(self) -> tuple[Path | None, str]:
        manifest = self.active_strategy_dir / "strategy_manifest.json"
        if manifest.exists():
            return self.active_strategy_dir, "current"
        return None, "unavailable"
