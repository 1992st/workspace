import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_ROOT = ROOT / "skills" / "daily-review" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from adversarial_audit import build_audit, save_case, validate_case  # noqa: E402


def make_case():
    return {
        "case": {
            "case_id": "20260818-601211-0957-T1-001",
            "symbol": "601211",
            "trade_date": "2026-08-18",
            "decision_time": "2026-08-18T09:57:00+08:00",
            "data_cutoff": "2026-08-18T09:57:00+08:00",
            "horizon": "T+1",
            "market_session": "morning",
            "snapshot_id": "snapshot-1",
            "universe_version": "watchlist-v1",
            "prompt_version": "stock-analysis-v1",
            "rule_version": "cross-section-v1",
        },
        "facts": [
            {
                "fact_id": "fact-1",
                "field": "price",
                "value": 17.91,
                "source": "quote",
                "source_time": "2026-08-18T09:57:00+08:00",
                "quality": "ok",
            }
        ],
        "features": [
            {
                "feature_id": "feature-1",
                "field": "relative_strength",
                "value": -0.3,
                "formula": "stock_return_1d - sector_return_1d",
                "fact_ids": ["fact-1"],
            }
        ],
        "prediction": {
            "prediction_id": "prediction-1",
            "case_id": "20260818-601211-0957-T1-001",
            "direction": "bearish",
            "horizon": "T+1",
            "invalidation": ["close_above_18.05"],
        },
    }


class AdversarialAuditTests(unittest.TestCase):
    def test_valid_case(self):
        self.assertTrue(validate_case(make_case())["valid"])

    def test_future_fact_is_rejected(self):
        case = make_case()
        case["facts"][0]["source_time"] = "2026-08-18T10:00:00+08:00"
        result = validate_case(case)
        self.assertFalse(result["valid"])
        self.assertTrue(any("newer than data_cutoff" in item for item in result["errors"]))

    def test_non_falsifiable_prediction_is_rejected(self):
        case = make_case()
        case["prediction"]["reasoning"] = "可能反弹也可能继续下跌"
        self.assertFalse(validate_case(case)["valid"])

    def test_audit_requires_counter_case(self):
        audit = build_audit(make_case())
        self.assertEqual(audit["audit_status"], "blocked")
        self.assertIn("counter_case is required", audit["errors"])

    def test_case_artifacts_are_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = save_case(make_case(), root / "2026-08-18")
            self.assertTrue((destination / "_SUCCESS").exists())
            changed = make_case()
            changed["prediction"]["direction"] = "bullish"
            with self.assertRaises(FileExistsError):
                save_case(changed, root / "2026-08-18")


if __name__ == "__main__":
    unittest.main()
