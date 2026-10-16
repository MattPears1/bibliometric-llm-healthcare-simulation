"""Offline regression tests for the publication validator; no files are written."""
import copy
import unittest
from unittest.mock import patch
import verify_public_release as v

class ScientificChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = v.Path(__file__).resolve().parents[1]
        cls.original = staticmethod(v.read_rows)

    def test_release_data(self):
        result = v.verify(self.root)
        self.assertEqual(result["status"], "PASS")

    def altered(self, suffix, transform):
        def reader(path):
            rows = self.original(path)
            if path.name == suffix:
                rows = copy.deepcopy(rows)
                transform(rows)
            return rows
        return reader

    def test_rejects_duplicate_study_identifier(self):
        with patch.object(v, "read_rows", self.altered("CHECKED_STUDY_DATASET_N483.csv", lambda r: r[0].update(paper_id=r[1]["paper_id"]))):
            with self.assertRaisesRegex(ValueError, "unique study"):
                v.check_science(self.root)

    def test_rejects_wrong_model_count(self):
        with patch.object(v, "read_rows", self.altered("CORRECTED_MODEL_FAMILY_COUNTS_N483.csv", lambda r: r[0].update(publications=str(int(r[0]["publications"])+1)))):
            with self.assertRaisesRegex(ValueError, "model family"):
                v.check_science(self.root)

    def test_rejects_changed_pilot_identity(self):
        with patch.object(v, "read_rows", self.altered("PILOT_RECORDS_N100.csv", lambda r: r[0].update(paper_id=r[1]["paper_id"]))):
            with self.assertRaisesRegex(ValueError, "Pilot"):
                v.check_science(self.root)

    def test_rejects_overwritten_human_stage(self):
        def change(rows):
            row = next(r for r in rows if r["after_blank_clarification"] == "UNCERTAIN")
            row["after_blank_clarification"] = row["frozen_production_decision"]
        with patch.object(v, "read_rows", self.altered("DECISIONS_AND_RATIONALES_100.csv", change)):
            with self.assertRaisesRegex(ValueError, "initial human"):
                v.check_science(self.root)

    def test_rejects_wrong_nts_judgement(self):
        with patch.object(v, "read_rows", self.altered("COMPARISONS_38_STUDIES_342_JUDGEMENTS.csv", lambda r: r[0].update(comparison="INVALID"))):
            with self.assertRaisesRegex(ValueError, "NTS"):
                v.check_science(self.root)

    def test_rejects_hash_failure(self):
        with patch.object(v, "sha256", return_value="0"*64):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                v.verify(self.root)

    def test_rejects_duplicate_checksum_entry(self):
        with patch.object(v, "read_rows", self.altered("SHA256SUMS.csv", lambda r: r.append(dict(r[0])))):
            with self.assertRaisesRegex(ValueError, "checksum"):
                v.verify(self.root)

if __name__ == "__main__":
    unittest.main()
