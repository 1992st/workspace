from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

RUNTIME_DIR = Path(__file__).resolve().parents[1]
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from compile_book_strategies import compile_strategies, load_registries, write_outputs


def _sample_payload(book_id: str) -> dict:
    return {
        "book_id": book_id,
        "book_title": "Test Book",
        "scene": "stock_analysis",
        "strategies": [
            {
                "strategy_id": f"{book_id}-001",
                "source_principle_id": "p01",
                "title_cn": "测试策略",
                "status": "approved",
                "injection_mode": "global",
                "category": "market_understanding",
                "priority": 100,
                "scenes": ["stock_analysis"],
                "trigger_tags": ["market_understanding"],
                "prompt_snippet": "test snippet",
                "checklist": ["check1"],
            }
        ],
    }


class CompileBookStrategiesTests(unittest.TestCase):
    def test_prefers_strategy_folder_registry(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        book_dir = root / "books" / "book_a"
        (book_dir / "strategy").mkdir(parents=True, exist_ok=True)

        new_payload = _sample_payload("new_book")
        old_payload = _sample_payload("old_book")
        (book_dir / "strategy" / "registry.json").write_text(
            json.dumps(new_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        (book_dir / "strategy_registry.json").write_text(
            json.dumps(old_payload, ensure_ascii=False),
            encoding="utf-8",
        )

        registries = load_registries(root)
        self.assertEqual(len(registries), 1)
        self.assertEqual(registries[0]["book_id"], "new_book")
        self.assertTrue(registries[0]["_registry_path"].endswith("strategy/registry.json"))

    def test_reads_legacy_registry_when_strategy_folder_missing(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        book_dir = root / "books" / "book_b"
        book_dir.mkdir(parents=True, exist_ok=True)
        payload = _sample_payload("legacy_book")
        (book_dir / "strategy_registry.json").write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )

        registries = load_registries(root)
        self.assertEqual(len(registries), 1)
        self.assertEqual(registries[0]["book_id"], "legacy_book")
        self.assertTrue(registries[0]["_registry_path"].endswith("strategy_registry.json"))

    def test_write_outputs_syncs_version_and_current_compiled_dirs(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        book_dir = root / "books" / "book_c" / "strategy"
        book_dir.mkdir(parents=True, exist_ok=True)
        (book_dir / "registry.json").write_text(
            json.dumps(_sample_payload("book_c"), ensure_ascii=False),
            encoding="utf-8",
        )

        compiled = compile_strategies(root, "v9")
        write_outputs(root, "v9", compiled)

        version_manifest = root / "prompts" / "v9" / "compiled" / "strategy_manifest.json"
        current_manifest = root / "prompts" / "current" / "compiled" / "strategy_manifest.json"
        self.assertTrue(version_manifest.exists())
        self.assertTrue(current_manifest.exists())
        self.assertEqual(
            json.loads(version_manifest.read_text(encoding="utf-8")),
            json.loads(current_manifest.read_text(encoding="utf-8")),
        )


if __name__ == "__main__":
    unittest.main()
