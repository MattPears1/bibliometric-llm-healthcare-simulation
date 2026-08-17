import csv
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve()
MODULE = HERE.parents[1] / "scopus_final_integration_corrected.py"
SPEC = importlib.util.spec_from_file_location("corrected", MODULE)
corrected = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(corrected)
WORKSPACE = HERE.parents[4]
BINDINGS = HERE.parents[1] / "PRODUCTION_INPUT_BINDINGS_RUN02.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CorrectedIntegrationRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def binding_copy(self):
        data = json.loads(BINDINGS.read_text(encoding="utf-8"))
        for item in data["inputs"].values():
            path = Path(item["path"])
            if not path.is_absolute():
                path = (BINDINGS.parent / path).resolve()
            item["path"] = str(path)
        target = self.root / "bindings.json"
        target.write_text(json.dumps(data), encoding="utf-8")
        return target, data

    def reissue_package_hashes(self, package):
        manifest_path = package / corrected.MANIFEST
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key, name in {**corrected.OUTPUTS, "qa": corrected.QA}.items():
            candidate = package / name
            manifest["outputs"][key]["bytes"] = candidate.stat().st_size
            manifest["outputs"][key]["sha256"] = digest(candidate)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        hashes_path = package / corrected.HASHES
        with hashes_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = list(reader.fieldnames), list(reader)
        for row in rows:
            candidate = package / row["path"]
            row["bytes"] = str(candidate.stat().st_size)
            row["sha256"] = digest(candidate)
        with hashes_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        frozen_path = package / corrected.FROZEN
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        frozen["manifest_sha256"] = digest(manifest_path)
        frozen["hash_manifest_sha256"] = digest(hashes_path)
        frozen_path.write_text(
            json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def test_authoritative_integration_no_clobber_schema_order_and_tamper(self):
        bindings, _ = self.binding_copy()
        output = self.root / "output"
        counts = corrected.integrate(bindings, output)
        self.assertEqual(counts["eligible_publication_records"], 547)
        self.assertEqual(counts["unique_studies"], 485)
        self.assertEqual(counts["alternate_publication_versions"], 62)
        self.assertEqual(corrected.validate_package(output), counts)
        with self.assertRaises(corrected.CorrectedIntegrationError):
            corrected.integrate(bindings, output)
        selection = output / corrected.OUTPUTS["selection"]
        selection.write_text(selection.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
        with self.assertRaises(corrected.CorrectedIntegrationError):
            corrected.validate_package(output)

    def test_historical_31_row_extraction_is_rejected(self):
        bindings, data = self.binding_copy()
        historical = WORKSPACE / "GSE_FULL_RERUN_2026-08-13/16_SCOPUS_VERSION_AND_EXTRACTION/scopus_increment_extraction_run01/SCOPUS_INCREMENT_CHECKED_WORK_LEVEL_EXTRACTION.csv"
        data["inputs"]["corrected_extraction"] = {"path": str(historical), "sha256": digest(historical)}
        bindings.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(corrected.CorrectedIntegrationError):
            corrected.integrate(bindings, self.root / "must_not_exist")

    def test_historical_548_486_review_is_rejected(self):
        bindings, data = self.binding_copy()
        old = WORKSPACE / "GSE_FULL_RERUN_2026-08-13/16_SCOPUS_VERSION_AND_EXTRACTION/scopus_increment_version_review_package_run02/review_completed/SCOPUS_INCREMENT_ALL_RECORD_FAMILY_REVIEW_COMPLETED.csv"
        data["inputs"]["run03_family_review"] = {"path": str(old), "sha256": digest(old)}
        bindings.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(corrected.CorrectedIntegrationError):
            corrected.integrate(bindings, self.root / "must_not_exist")

    def test_protected_family_field_tamper_is_rejected_even_when_rehashed(self):
        bindings, data = self.binding_copy()
        source = Path(data["inputs"]["run03_family_review"]["path"])
        tampered = self.root / "tampered_family.csv"
        with source.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = list(reader.fieldnames), list(reader)
        rows[0]["title"] = "tampered protected title"
        with tampered.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        data["inputs"]["run03_family_review"] = {"path": str(tampered), "sha256": digest(tampered)}
        # Replace the completion manifest with a hash-consistent forged copy so
        # template comparison, rather than the outer binding, must reject it.
        manifest_source = Path(data["inputs"]["run03_completion_manifest"]["path"])
        manifest = json.loads(manifest_source.read_text(encoding="utf-8"))
        manifest["outputs"]["SCOPUS_INCREMENT_ALL_RECORD_FAMILY_REVIEW_COMPLETED.csv"]["sha256"] = digest(tampered)
        forged = self.root / "forged_completion_manifest.json"
        forged.write_text(json.dumps(manifest), encoding="utf-8")
        data["inputs"]["run03_completion_manifest"] = {"path": str(forged), "sha256": digest(forged)}
        bindings.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(corrected.CorrectedIntegrationError):
            corrected.integrate(bindings, self.root / "must_not_exist")

    def test_rehashed_screening_code_tamper_is_rejected_by_source_binding(self):
        bindings, _ = self.binding_copy()
        output = self.root / "output"
        corrected.integrate(bindings, output)
        screening = output / corrected.OUTPUTS["screening"]
        with screening.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = list(reader.fieldnames), list(reader)
        target = next(
            row for row in rows if row["paper_id"] == corrected.REMOVED_PAPER_ID
        )
        self.assertEqual(target["final_primary_code"], "E2_NOT_HEALTH_ED")
        target["final_primary_code"] = "E1_NOT_LLM"
        with screening.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        self.reissue_package_hashes(output)

        with self.assertRaisesRegex(
            corrected.CorrectedIntegrationError, "screening source"
        ):
            corrected.validate_package(output)


if __name__ == "__main__":
    unittest.main()
