import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from quantity_contract import select_protocol


class QuantityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = json.loads((ROOT / "data/chemistry_experiments.json").read_text(encoding="utf-8"))["experiments"]

    def test_every_record_has_explicit_draft_contract(self):
        self.assertEqual(len(self.records), 100)
        for record in self.records:
            contract = record["rendering_contract"]
            self.assertFalse(contract["numeric_values_inferred"])
            self.assertFalse(contract["source_reviewed"])
            for step in record["procedure_steps"]:
                self.assertIn("science_spec", step)
                self.assertIn("quantities", step)

    def test_alternatives_require_selection(self):
        record = next(r for r in self.records if r["experiment_id"] == "chem_12_301")
        self.assertEqual(select_protocol(record), [])
        steps = select_protocol(record, "chloride_silver")
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[0]["quantities"][0]["role"], "aliquot")
        self.assertEqual(steps[0]["quantities"][0]["value"], 1)
        self.assertTrue(all(q["qualifier"] == "not_specified" for s in steps[1:] for q in s["quantities"]))

    def test_all_records_match_schema(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / "schema/experiment.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        for record in self.records:
            errors = list(validator.iter_errors(record))
            self.assertFalse(errors, f"{record['experiment_id']}: " + "; ".join(str(e.message) for e in errors[:3]))


if __name__ == "__main__":
    unittest.main()
