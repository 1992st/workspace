import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_ROOT = ROOT / "skills" / "daily-review" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from case_pipeline import build_case_id, create_records  # noqa: E402

sys.path.insert(0, str(ROOT / "skills" / "daily-review"))
from case_store import ImmutableCaseStore  # noqa: E402

from test_adversarial_audit import make_case  # noqa: E402


class CasePipelineTests(unittest.TestCase):
    def test_case_id_separates_decision_events(self):
        first = build_case_id("601211", "2026-08-18T09:57:00+08:00", "T+1", 1)
        second = build_case_id("601211", "2026-08-18T10:23:00+08:00", "INTRADAY", 2)
        self.assertEqual(first, "20260818-601211-0957-T1-001")
        self.assertNotEqual(first, second)

    def test_create_records_freezes_all_input_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ImmutableCaseStore(directory)
            result = create_records(store, make_case())
            self.assertEqual(result["case"]["id"], "20260818-601211-0957-T1-001")
            self.assertEqual(len(store.for_case("facts", result["case"]["id"])), 1)
            self.assertEqual(len(store.for_case("features", result["case"]["id"])), 1)
            self.assertEqual(len(store.for_case("predictions", result["case"]["id"])), 1)


if __name__ == "__main__":
    unittest.main()
