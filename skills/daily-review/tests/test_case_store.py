from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "skills" / "daily-review"))

from case_store import ImmutableCaseStore


class ImmutableCaseStoreTests(unittest.TestCase):
    def test_records_are_append_only_and_linked_to_case(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ImmutableCaseStore(directory)
            case = store.create_case({"symbol": "601211", "as_of": "2026-08-18T15:00:00+08:00"}, case_id="case_1")
            fact = store.append_fact("case_1", {"fact_id": "f1", "value": 12.3}, fact_id="fact_1")
            feature = store.append_feature("case_1", {"formula": "price/pre_close-1", "fact_ids": ["fact_1"]}, feature_id="feature_1")
            prediction = store.append_prediction("case_1", {"horizon": "next_day", "view": "neutral"}, prediction_id="prediction_1")
            audit = store.append_audit("case_1", {"agent_role": "bear", "status": "passed"}, audit_id="audit_1")
            outcome = store.append_outcome("case_1", {"horizon": "next_day", "status": "pending"}, outcome_id="outcome_1")
            self.assertEqual(case["record_type"], "case")
            self.assertEqual(fact["case_id"], "case_1")
            self.assertEqual(prediction["id"], "prediction_1")
            self.assertEqual(feature["case_id"], "case_1")
            self.assertEqual(len(store.for_case("features", "case_1")), 1)
            self.assertEqual(len(store.for_case("facts", "case_1")), 1)
            self.assertEqual(len(store.for_case("outcomes", "case_1")), 1)
            self.assertEqual(store.get("audits", "audit_1"), audit)
            self.assertEqual(store.get("predictions", "prediction_1"), prediction)
            self.assertEqual(store.get("outcomes", "outcome_1"), outcome)

    def test_duplicate_id_is_rejected_without_replacing_original(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ImmutableCaseStore(directory)
            store.create_case({"symbol": "601211"}, case_id="case_1")
            with self.assertRaises(ValueError):
                store.create_case({"symbol": "000001"}, case_id="case_1")
            rows = [json.loads(line) for line in (Path(directory) / "cases.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["symbol"], "601211")

    def test_content_hash_is_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ImmutableCaseStore(directory)
            store.create_case({"symbol": "601211"}, case_id="case_1")
            row = store.append_prediction("case_1", {"horizon": "3d", "view": "bearish"}, prediction_id="prediction_1")
            unsigned = {key: value for key, value in row.items() if key != "content_sha256"}
            import hashlib
            raw = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            self.assertEqual(row["content_sha256"], hashlib.sha256(raw).hexdigest())

    def test_child_requires_existing_case_and_cannot_override_link(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ImmutableCaseStore(directory)
            with self.assertRaises(ValueError):
                store.append_fact("missing", {"value": 1})
            store.create_case({"symbol": "601211"}, case_id="case_1")
            fact = store.append_fact("case_1", {"case_id": "case_other", "value": 1})
            self.assertEqual(fact["case_id"], "case_1")

    def test_prediction_cannot_be_replaced_and_audit_requires_prediction(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ImmutableCaseStore(directory)
            store.create_case({"symbol": "601211"}, case_id="case_1")
            with self.assertRaises(ValueError):
                store.append_audit("case_1", {"status": "pass"})
            store.append_prediction("case_1", {"direction": "bearish"}, prediction_id="prediction_1")
            with self.assertRaises(ValueError):
                store.append_prediction("case_1", {"direction": "bullish"}, prediction_id="prediction_2")


if __name__ == "__main__":
    unittest.main()
