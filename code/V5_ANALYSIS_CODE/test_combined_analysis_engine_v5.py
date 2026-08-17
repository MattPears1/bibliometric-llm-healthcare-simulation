#!/usr/bin/env python3
"""Strict synthetic and live-pin tests for the prospective V5 engine."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import combined_analysis_engine_v5 as engine


RUN01 = (
    engine.WORKSPACE
    / "GSE_FULL_RERUN_2026-08-13/17_ANALYSIS/combined_analysis_v5_run01"
)


def selection_contract(n: int = 4) -> dict:
    return {
        "retrieval_occurrences_by_source": {
            "openalex": 2,
            "pubmed": 2,
            "europepmc": 2,
            "semantic_scholar": 2,
            "doaj": 2,
            "scopus": 2,
        },
        "retrieval_occurrences_total": 12,
        "scopus_after_cutoff_removed": 1,
        "retrieval_occurrences_after_scopus_cutoff": 11,
        "primary_five_occurrence_date_status": {
            "inside_window": 8,
            "before_window": 1,
            "after_window": 0,
            "unknown": 1,
            "unresolved_boundary": 0,
        },
        "automatic_duplicate_merges": {
            "primary": 2,
            "scopus_within": 1,
            "scopus_to_primary": 1,
            "total": 4,
        },
        "records_after_automatic_merging": 7,
        "reviewed_same_record_merges": {"primary": 1, "scopus_to_primary": 0, "total": 1},
        "deduplicated_records": 6,
        "records_outside_candidate_frame": 0,
        "candidate_records": {"primary_five": 4, "scopus_increment": 2, "total": 6},
        "separate_resolution_checks": {
            "direct_include_exclude": 1,
            "one_or_both_uncertain": 1,
            "exclusion_code_only": 0,
            "total": 2,
        },
        "final_out_of_range_exclusions": 0,
        "excluded_candidate_records": 1,
        "eligible_publication_records": 5,
        "canonical_works": n,
    }


def contract(n: int = 4) -> dict:
    return {
        "schema_version": engine.CONTRACT_SCHEMA_VERSION,
        "status": engine.READY_STATUS,
        "study_window": {"from": "2020-01-01", "through": "2026-08-13", "inclusive": True},
        "lead_author_oversight": {
            "scope": "five_source_pipeline_decision_at_time_of_audit",
            "sampling": "deliberately_stratified_100_record_oversight_sample",
            "successes": 85,
            "total": 100,
            "exact_95pct_lower": 0.7646924998510451,
            "exact_95pct_upper": 0.9135456143583514,
            "unmatched_without_second_human_resolution": 15,
            "covers_scopus_increment": False,
            "independent_reference_standard": False,
            "screening_accuracy_measure": False,
        },
        "selection_flow": selection_contract(n),
    }


def work(
    index: int,
    *,
    title: str,
    abstract: str,
    keywords: str,
    model: str,
    simulation: str,
    nts: str,
    specialty: str,
    design: str,
    year: int,
) -> dict[str, str]:
    paper_id = f"w{index}"
    row = {
        "paper_id": paper_id,
        "version_family_id": f"fam{index}",
        "final_version_family_id": f"fam{index}",
        "preferred_record_key": f"base:{paper_id}" if index < 4 else f"scopus:{paper_id}",
        "doi": f"10.1/{paper_id}",
        "title": title,
        "year": str(year),
        "publication_date": f"{year}-03-01",
        "journal": f"Journal {index}",
        "found_in_sources": "openalex;scopus" if index == 1 else "pubmed",
        "record_type": "journal-article",
        "abstract": abstract,
        "source_keywords": keywords,
        "authors": "",
        "url": f"https://example.org/{paper_id}",
        "family_size": "2" if index == 1 else "1",
        "version_role": "journal_article",
        "final_model_families": model,
        "final_simulation_modalities": simulation,
        "final_nts_domains": nts,
        "final_specialty": specialty,
        "final_study_design": design,
        "source_checked_by": "fixture",
        "source_checked_at_utc": "2026-08-16T12:00:00Z",
        "evidence_url_1": f"https://example.org/{paper_id}",
        "evidence_url_2": "",
        "final_model_description_raw": model,
    }
    for field in engine.v2.METADATA_AUDIT_FIELDS:
        row.setdefault(field, "")
    return row


def openalex(work_row: dict[str, str], *, status: str, oa_status: str, authors: list[dict]) -> dict[str, str]:
    row = {field: "" for field in engine.v2.OPENALEX_FIELDS}
    paper_id = work_row["paper_id"]
    row.update(
        {
            "paper_id": paper_id,
            "input_doi": work_row["doi"],
            "input_title": work_row["title"],
            "input_year": work_row["year"],
            "match_status": status,
            "match_method": "doi_exact" if status == "MATCHED" else "confirmed_unmatched",
            "openalex_id": f"W{paper_id[1:]}" if status == "MATCHED" else "",
            "openalex_doi": work_row["doi"] if status == "MATCHED" else "",
            "openalex_title": work_row["title"] if status == "MATCHED" else "",
            "publication_year": work_row["year"] if status == "MATCHED" else "",
            "publication_date": work_row["publication_date"] if status == "MATCHED" else "",
            "cited_by_count": str(int(paper_id[1:]) - 1) if status == "MATCHED" else "",
            "oa_status": oa_status if status == "MATCHED" else "",
            "authors_json": json.dumps(authors) if status == "MATCHED" else "",
            "source_id": f"S{paper_id[1:]}" if status == "MATCHED" else "",
            "source_name": work_row["journal"] if status == "MATCHED" else "",
            "source_issn_l": f"0000-000{paper_id[1:]}" if status == "MATCHED" else "",
        }
    )
    return row


def fixture_data() -> tuple[dict, dict]:
    spec = engine.v2.load_json(engine.WORKSPACE / "ACTIVE_GSE_REVISION_2026-08-13/06_AUDIT/FRESH_ANALYSIS_SPECIFICATION_V2_2026-08-14.json", "spec")
    works = [
        work(
            1,
            title="Large language model virtual patient training",
            abstract="Communication skills in a virtual patient.",
            keywords="clinical reasoning",
            model="GPT-4",
            simulation="virtual_patient",
            nts="communication",
            specialty="general_surgery",
            design="randomized_trial",
            year=2023,
        ),
        work(
            2,
            title="Generative AI for learners",
            abstract="Generative AI in nursing education with teamwork.",
            keywords="",
            model="unspecified_generative_model",
            simulation="scenario",
            nts="teamwork",
            specialty="nursing",
            design="observational",
            year=2024,
        ),
        work(
            3,
            title="Large language model clinical reasoning",
            abstract="",
            keywords="assessment",
            model="ChatGPT_unspecified",
            simulation="",
            nts="",
            specialty="urology",
            design="development_evaluation",
            year=2025,
        ),
        work(
            4,
            title="Surgical education chatbot",
            abstract="A chatbot for role play.",
            keywords="virtual patient",
            model="GPT-4;Claude",
            simulation="roleplay",
            nts="",
            specialty="health_professions",
            design="qualitative",
            year=2026,
        ),
    ]
    for index, row in enumerate(works, start=1):
        row["integration_source_corpus"] = (
            "scopus_increment" if row["paper_id"] == "w4" else "base_eligible_v4"
        )
        row["integration_source_row_sha256"] = f"{index:x}" * 64
        row["source_finalization_manifest_sha256"] = (
            engine.SCOPUS_EXTRACTION_FINALIZATION_SHA256
            if row["paper_id"] == "w4"
            else "a" * 64
        )
    authors = [
        [
            {
                "author_id": "A1",
                "author_name": "Ada One",
                "orcid": "",
                "institution_ids": ["I1"],
                "countries": ["US", "GB"],
            }
        ],
        [
            {
                "author_id": "A1",
                "author_name": "Ada One",
                "orcid": "",
                "institution_ids": ["I1"],
                "countries": ["US"],
            },
            {
                "author_id": "",
                "author_name": "Unresolved Name",
                "orcid": "",
                "institution_ids": [],
                "countries": ["CA"],
            },
        ],
        [],
        [
            {
                "author_id": "A2",
                "author_name": "Beta Two",
                "orcid": "",
                "institution_ids": ["I2"],
                "countries": ["AU"],
            }
        ],
    ]
    oa_rows = [
        openalex(works[0], status="MATCHED", oa_status="gold", authors=authors[0]),
        openalex(works[1], status="MATCHED", oa_status="closed", authors=authors[1]),
        openalex(works[2], status="UNMATCHED", oa_status="", authors=authors[2]),
        openalex(works[3], status="MATCHED", oa_status="green", authors=authors[3]),
    ]
    candidate_ids = ["w1", "v1", "w2", "w3", "w4", engine.SCOPUS_CORRECTED_RECORD_ID]
    decision_pairs = [
        ("INCLUDE", "INCLUDE"),
        ("EXCLUDE", "EXCLUDE"),
        ("INCLUDE", "EXCLUDE"),
        ("UNCERTAIN", "EXCLUDE"),
        ("INCLUDE", "INCLUDE"),
        ("INCLUDE", "INCLUDE"),
    ]
    comparisons = [
        {
            "paper_id": paper_id,
            "reviewer_A_decision": pair[0],
            "reviewer_B_decision": pair[1],
            "comparison_class": (
                "AGREED_INCLUDE"
                if pair == ("INCLUDE", "INCLUDE")
                else "AGREED_EXCLUDE_SAME_CODE"
                if pair == ("EXCLUDE", "EXCLUDE")
                else "DIRECT_INCLUDE_EXCLUDE"
                if set(pair) == {"INCLUDE", "EXCLUDE"}
                else "ONE_OR_BOTH_UNCERTAIN"
            ),
        }
        for paper_id, pair in zip(candidate_ids, decision_pairs, strict=True)
    ]
    final_rows = [
        {
            **row,
            "screening_source_corpus": "scopus_increment" if row["paper_id"] in {"w4", engine.SCOPUS_CORRECTED_RECORD_ID} else "base_v4",
            "final_decision": "EXCLUDE" if row["paper_id"] == engine.SCOPUS_CORRECTED_RECORD_ID else "INCLUDE",
            "final_primary_code": "E2_NOT_HEALTH_ED" if row["paper_id"] == engine.SCOPUS_CORRECTED_RECORD_ID else "INCLUDE",
            "decision_basis": "fixture",
        }
        for row in comparisons
    ]
    version_rows = [
        {
            "version_family_id": "fam1",
            "provisional_family_id": "fam1",
            "family_size": "2",
            "paper_id": "w1",
            "source_record_id": "w1",
            "record_key": "base:w1",
            "source_corpus": "base_eligible_v4",
            "final_decision": "INCLUDE",
            "preferred_for_analysis": "yes",
            "preferred_paper_id": "w1",
            "preferred_record_key": "base:w1",
            "relationship_to_preferred": "preferred",
        },
        {
            "version_family_id": "fam1",
            "provisional_family_id": "fam1",
            "family_size": "2",
            "paper_id": "v1",
            "source_record_id": "v1",
            "record_key": "base:v1",
            "source_corpus": "base_eligible_v4",
            "final_decision": "INCLUDE",
            "preferred_for_analysis": "no",
            "preferred_paper_id": "w1",
            "preferred_record_key": "base:w1",
            "relationship_to_preferred": "preprint",
        },
    ]
    for index in (2, 3, 4):
        version_rows.append(
            {
                "version_family_id": f"fam{index}",
                "provisional_family_id": f"fam{index}",
                "family_size": "1",
                "paper_id": f"w{index}",
                "source_record_id": f"w{index}",
                "record_key": f"base:w{index}" if index < 4 else f"scopus:w{index}",
                "source_corpus": "base_eligible_v4" if index < 4 else "scopus_increment",
                "final_decision": "INCLUDE",
                "preferred_for_analysis": "yes",
                "preferred_paper_id": f"w{index}",
                "preferred_record_key": f"base:w{index}" if index < 4 else f"scopus:w{index}",
                "relationship_to_preferred": "preferred",
            }
        )
    for row in version_rows:
        row["integration_schema_version"] = "fixture-integration-v1"
        row["source_completed_family_review_sha256"] = "f" * 64
        row["preferred_basis"] = "fixture_preferred_basis"
        row["preferred_selection_rationale"] = "fixture rationale"
        row["preferred_selection_evidence"] = "https://example.org/evidence"
        row["reviewed_by"] = "fixture reviewer"
        row["reviewed_at_utc"] = "2026-08-16T00:00:00Z"
    final_data = {
        "works": works,
        "comparison_rows": comparisons,
        "final_rows": final_rows,
        "version_rows": version_rows,
        "version_fields": list(version_rows[0]),
        "openalex_rows": oa_rows,
        "input_binding_rows": [
            {
                "role": "fixture",
                "path": "fixture",
                "bytes": 1,
                "rows": 4,
                "sha256": "a" * 64,
                "state": "locked",
            }
        ],
    }
    return spec, final_data


class ContractTests(unittest.TestCase):
    def test_live_ready_contract_validates_every_locked_input(self) -> None:
        result = engine.preflight(engine.DEFAULT_CONTRACT)
        self.assertEqual(result["status"], "READY")
        self.assertFalse(result["production_analysis_run"])
        self.assertEqual(result["pending_roles"], [])
        self.assertEqual(
            result["locked_inputs_validated"],
            len(engine.LOCKED_ROLE_NAMES | engine.FINAL_ROLE_NAMES),
        )

    def test_scaffold_status_cannot_run_production(self) -> None:
        document = json.loads(engine.DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        document["status"] = engine.SCAFFOLD_STATUS
        with tempfile.TemporaryDirectory(dir=engine.HERE) as temp_dir:
            path = Path(temp_dir) / "scaffold-contract.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(engine.CombinedAnalysisError, "still a scaffold"):
                engine.validate_input_contract(path, production=True, validate_locked_files=False)

    def test_selection_arithmetic_is_fail_closed(self) -> None:
        bad = selection_contract()
        bad["automatic_duplicate_merges"]["total"] = 3
        with self.assertRaisesRegex(engine.CombinedAnalysisError, "Automatic duplicate-merge components"):
            engine._validate_selection_contract(bad, production=True)

    def test_primary_date_status_must_reconcile_to_the_five_source_total(self) -> None:
        bad = selection_contract()
        bad["primary_five_occurrence_date_status"]["inside_window"] += 1
        with self.assertRaisesRegex(engine.CombinedAnalysisError, "date-status rows do not sum"):
            engine._validate_selection_contract(bad, production=True)

    def test_hash_pin_tampering_is_rejected(self) -> None:
        document = json.loads(engine.DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        document["inputs"]["analysis_specification"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory(dir=engine.HERE) as temp_dir:
            path = Path(temp_dir) / "tampered-contract.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(engine.CombinedAnalysisError, "SHA-256 mismatch"):
                engine.validate_input_contract(path, production=False, validate_locked_files=True)

    def test_combined_pre_resolution_agreement_matches_independent_replay(self) -> None:
        document = json.loads(engine.DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        rows: list[dict[str, str]] = []
        for role in ("primary_review_comparison", "scopus_review_comparison"):
            path = engine._resolve_workspace_path(document["inputs"][role]["path"], role)
            _fields, part = engine.read_csv_any(path)
            rows.extend(part)
        self.assertEqual(len(rows), 3919)
        pairs = [(row["reviewer_A_decision"], row["reviewer_B_decision"]) for row in rows]
        three_way = engine._paired_agreement(
            pairs,
            engine.v2.AGREEMENT_DECISIONS,
            replicates=10_000,
            seed=2026081306,
        )
        binary_pairs = [
            (
                "INCLUDE" if left == "INCLUDE" else "NON_INCLUDE",
                "INCLUDE" if right == "INCLUDE" else "NON_INCLUDE",
            )
            for left, right in pairs
        ]
        binary = engine._paired_agreement(
            binary_pairs,
            ("NON_INCLUDE", "INCLUDE"),
            replicates=10_000,
            seed=2026081306,
        )
        self.assertEqual(three_way["raw_agreement_count"], 3368)
        self.assertAlmostEqual(three_way["raw_agreement"], 0.859402909, places=9)
        self.assertAlmostEqual(three_way["cohen_kappa"], 0.564871964, places=9)
        self.assertAlmostEqual(three_way["cohen_kappa_percentile_bootstrap_95_ci"][0], 0.534312917, places=9)
        self.assertAlmostEqual(three_way["cohen_kappa_percentile_bootstrap_95_ci"][1], 0.594517229, places=9)
        self.assertEqual(binary["raw_agreement_count"], 3418)
        self.assertAlmostEqual(binary["raw_agreement"], 0.872161266, places=9)
        self.assertAlmostEqual(binary["cohen_kappa"], 0.579701675, places=9)
        self.assertAlmostEqual(binary["cohen_kappa_percentile_bootstrap_95_ci"][0], 0.548429865, places=9)
        self.assertAlmostEqual(binary["cohen_kappa_percentile_bootstrap_95_ci"][1], 0.610121734, places=9)

    def test_live_cross_view_allowlist_is_exact_and_metadata_is_authoritative(self) -> None:
        validated = engine.validate_input_contract(
            engine.DEFAULT_CONTRACT,
            production=True,
            validate_locked_files=True,
        )
        spec = engine.v2.load_json(
            engine.WORKSPACE
            / "ACTIVE_GSE_REVISION_2026-08-13/06_AUDIT/FRESH_ANALYSIS_SPECIFICATION_V2_2026-08-14.json",
            "spec",
        )
        final_data = engine._validate_final_rows(validated, spec)
        extraction_fields, extraction_rows = engine._rows_for(
            validated, "combined_checked_corpus"
        )
        metadata_fields, metadata_rows = engine._rows_for(validated, "combined_metadata")
        common = set(extraction_fields) & set(metadata_fields)
        differences = {
            (left["paper_id"], field, left[field], right[field])
            for left, right in zip(extraction_rows, metadata_rows, strict=True)
            for field in common - {"integration_source_row_sha256"}
            if left[field] != right[field]
        }
        self.assertEqual(len(differences), 33)
        self.assertEqual(len({row[0] for row in differences}), 32)
        by_id = {row["paper_id"]: row for row in final_data["works"]}
        self.assertEqual(by_id["8db4130844dc8d367d1f"]["year"], "2026")
        self.assertEqual(
            by_id["8db4130844dc8d367d1f"]["publication_date"], "2026-01-13"
        )
        self.assertEqual(
            by_id["78868accc1f86fb42dce"]["doi"], "10.52979/raoa.1131252.1306"
        )


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec, cls.final_data = fixture_data()
        cls.analysis = engine.build_analysis_from_rows(
            spec=cls.spec,
            contract=contract(),
            final_data=copy.deepcopy(cls.final_data),
            input_bundle_sha256="b" * 64,
        )

    def test_dynamic_n_and_six_source_selection_flow(self) -> None:
        self.assertEqual(self.analysis["n"], 4)
        table1 = self.analysis["tables"]["TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT"][0]
        sources = [row["category"] for row in table1 if row["measure"] == "Retrieval occurrence by source"]
        self.assertEqual(sources, ["OpenAlex", "PubMed", "Europe PMC", "Semantic Scholar", "DOAJ", "Scopus"])
        stages = {row["category"]: row["numerator"] for row in table1 if row["measure"] == "Stage count"}
        self.assertEqual(stages["Scopus results after the cutoff"], 1)
        self.assertEqual(stages["Primary-source results before or after the date window"], 1)
        self.assertEqual(stages["Primary-source results with an unknown or unresolved date"], 1)
        self.assertEqual(stages["Occurrences entering duplicate handling"], 11)
        self.assertEqual(stages["Automatically merged duplicate occurrences"], 4)
        self.assertEqual(stages["Separately confirmed same-record merges"], 1)
        self.assertEqual(stages["All separately resolved review records"], 2)
        self.assertEqual(stages["Alternate publication versions"], 1)

    def test_lead_author_oversight_replaces_stale_deferral_and_limits_scope(self) -> None:
        table1 = self.analysis["tables"]["TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT"][0]
        self.assertFalse(
            any("not performed" in str(value).casefold() for row in table1 for value in row.values())
        )
        rows = [row for row in table1 if row["section"] == "Lead-author oversight"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((int(row["numerator"]), int(row["denominator"])), (85, 100))
        self.assertAlmostEqual(float(row["ci_lower"]), 0.7646924998510451)
        self.assertAlmostEqual(float(row["ci_upper"]), 0.9135456143583514)
        self.assertIn("predates the Scopus extension", row["note"])
        self.assertIn("does not validate the final six-source corpus", row["note"])
        self.assertIn("Fifteen", row["note"])

    def test_exclusions_nts_model_oa_and_missingness_reconcile(self) -> None:
        flow = self.analysis["supplements"]["SUPPLEMENT_SELECTION_FLOW_COMPLETE"][0]
        exclusions = [row for row in flow if row["measure"] == "Final primary exclusion reason"]
        self.assertEqual(sum(int(row["count"]) for row in exclusions), 1)
        nts = self.analysis["tables"]["TABLE_4_RECONCILED_NTS"][0]
        explicit = next(row for row in nts if row["category"] == "At least one explicit NTS domain")
        blank = next(row for row in nts if row["category"] == "No explicit NTS domain")
        self.assertEqual((int(explicit["count"]), int(blank["count"])), (2, 2))
        no_explicit_rows = [
            row
            for collection in ("tables", "supplements")
            for rows, _fields in self.analysis[collection].values()
            for row in rows
            if row.get("category") == "No explicit NTS domain"
            and "response_type" in row
        ]
        self.assertTrue(no_explicit_rows)
        self.assertTrue(
            all("mutually exclusive" in row["response_type"] for row in no_explicit_rows)
        )
        self.assertTrue(
            all("multiple response" not in row["response_type"] for row in no_explicit_rows)
        )
        models = self.analysis["tables"]["TABLE_3_MODEL_SIMULATION_STUDY_DESIGN"][0]
        no_exact = next(row for row in models if row["category"] == "No exact model family established")
        self.assertEqual(int(no_exact["count"]), 1)
        oa = self.analysis["tables"]["TABLE_2_PUBLICATION_SOURCE_OA_CITATION_COVERAGE"][0]
        self.assertEqual(
            {row["category"].casefold() for row in oa if row["measure"] == "OpenAlex OA status"},
            {"gold", "green", "hybrid", "bronze", "diamond", "closed", "unknown"},
        )
        coverage = self.analysis["supplements"]["SUPPLEMENT_COVERAGE_COMPLETE"][0]
        self.assertEqual(len({row["measure"] for row in coverage}), 12)
        for measure in {row["measure"] for row in coverage}:
            self.assertEqual(sum(int(row["count"]) for row in coverage if row["measure"] == measure), 4)

    def test_locked_out_of_range_exclusion_count_is_enforced(self) -> None:
        bad = contract()
        bad["selection_flow"]["final_out_of_range_exclusions"] = 1
        with self.assertRaisesRegex(engine.CombinedAnalysisError, "E6_OUT_OF_RANGE"):
            engine._selection_rows_v5(bad, self.analysis, self.final_data["final_rows"])

    def test_country_pairing_and_international_collaboration(self) -> None:
        table = self.analysis["tables"]["TABLE_5_GEOGRAPHY_WITH_MISSINGNESS"][0]
        whole = [row["category"] for row in table if row["measure"] == "Whole-count country affiliation"]
        fractional = [row["category"] for row in table if row["measure"] == "Fractional country affiliation"]
        self.assertEqual(whole, fractional)
        international = next(row for row in table if row["measure"] == "International collaboration")
        self.assertEqual(int(international["count"]), 2)

    def test_phrase_fields_and_abstract_sensitivity_use_any_field(self) -> None:
        rows = self.analysis["supplements"]["SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE"][0]
        main = next(
            row
            for row in rows
            if row["measure"] == "Predefined phrase frequency" and row["category"] == "large language model"
        )
        sensitivity = next(
            row
            for row in rows
            if row["measure"] == "Retained-abstract sensitivity frequency" and row["category"] == "large language model"
        )
        self.assertEqual(int(main["count"]), 2)
        self.assertEqual(int(main["title_count"]), 2)
        self.assertEqual(int(sensitivity["count"]), 1)
        self.assertEqual(sensitivity["work_ids"], "w1")

    def test_author_specialty_version_and_claim_ledgers(self) -> None:
        authors = self.analysis["supplements"]["SUPPLEMENT_AUTHOR_IDENTITY_LEDGER_V5"][0]
        self.assertTrue(any(row["author_key"] == "openalex:a1" and row["work_count"] == 2 for row in authors))
        self.assertTrue(any(row["unresolved_name_flag"] == "1" for row in authors))
        specialties = self.analysis["supplements"]["SUPPLEMENT_SPECIALTY_GROUPING_DICTIONARY_V5"][0]
        surgical = [row for row in specialties if row["display_group"] == "surgical specialty"]
        self.assertTrue(surgical)
        self.assertTrue(all(row["included_in_figure_5"] == "1" for row in surgical))
        self.assertTrue(all("_" not in row["plain_label"] for row in specialties))
        self.assertEqual(len(self.analysis["version_rows"]), 5)
        claims = self.analysis["supplements"]["SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5"][0]
        self.assertGreater(len(claims), 50)
        self.assertTrue(all(row["input_bundle_sha256"] == "b" * 64 for row in claims))

    def test_final_integration_schema_and_corrected_include_set_are_checked(self) -> None:
        def loaded(rows: list[dict[str, str]]) -> dict:
            fields = list(rows[0])
            return {"loaded_rows": copy.deepcopy(rows), "fields": fields}

        works = copy.deepcopy(self.final_data["works"])
        metadata_works = copy.deepcopy(works)
        for row in metadata_works:
            row["integration_source_row_sha256"] = "d" * 64
            if row["integration_source_corpus"] == "scopus_increment":
                row["source_finalization_manifest_sha256"] = ""
        versions = copy.deepcopy(self.final_data["version_rows"])
        screening = copy.deepcopy(self.final_data["final_rows"])
        comparisons = copy.deepcopy(self.final_data["comparison_rows"])
        inputs = {
            "combined_eligible_version_ledger": loaded(versions),
            "combined_checked_corpus": loaded(works),
            "combined_metadata": loaded(metadata_works),
            "combined_openalex": loaded(self.final_data["openalex_rows"]),
            "combined_record_level_screening": loaded(screening),
            "base_eligible_version_ledger": loaded(
                [
                    {"paper_id": row["source_record_id"]}
                    for row in versions
                    if row["source_corpus"] == "base_eligible_v4"
                ]
            ),
            "scopus_corrected_included_records": loaded([{"paper_id": "w4"}]),
            "base_final_screening": loaded(screening[:4]),
            "scopus_corrected_final_screening": loaded(screening[4:]),
            "primary_review_comparison": loaded(comparisons[:4]),
            "scopus_review_comparison": loaded(comparisons[4:]),
            "base_checked_corpus": loaded(works[:3]),
            "scopus_checked_extraction": loaded(works[3:]),
            "base_openalex": loaded(self.final_data["openalex_rows"][:3]),
            "scopus_openalex": loaded(self.final_data["openalex_rows"][3:]),
            "metadata_correction_ledger": {
                "loaded_rows": [],
                "fields": ["paper_id", "field", "old_value", "new_value"],
            },
        }
        preferred_versions = {
            row["source_record_id"]: row
            for row in versions
            if row["preferred_for_analysis"] == "yes"
        }
        study_selection = []
        for work_row in works:
            preferred = preferred_versions[work_row["paper_id"]]
            study_selection.append(
                {
                    "integration_schema_version": "fixture-integration-v1",
                    "final_version_family_id": preferred["provisional_family_id"],
                    "family_size": preferred["family_size"],
                    "preferred_record_key": preferred["record_key"],
                    "preferred_paper_id": preferred["source_record_id"],
                    "preferred_source_corpus": preferred["source_corpus"],
                    "preferred_basis": preferred["preferred_basis"],
                    "preferred_selection_rationale": preferred["preferred_selection_rationale"],
                    "preferred_selection_evidence": preferred["preferred_selection_evidence"],
                    "family_reviewed_by": preferred["reviewed_by"],
                    "family_reviewed_at_utc": preferred["reviewed_at_utc"],
                    "source_family_review_row_sha256": "e" * 64,
                }
            )
        inputs["combined_study_selection_ledger"] = loaded(study_selection)
        completed_versions = [
            {
                field: value
                for field, value in row.items()
                if field not in {"integration_schema_version", "source_completed_family_review_sha256"}
            }
            for row in versions
        ]
        inputs["scopus_completed_version_decisions"] = loaded(completed_versions)
        inputs["scopus_completed_version_decisions"]["sha256"] = "f" * 64
        validated = {
            "selection": engine._validate_selection_contract(
                contract()["selection_flow"], production=True
            ),
            "inputs": inputs,
        }
        result = engine._validate_final_rows(validated, self.spec)
        self.assertEqual(len(result["version_rows"]), 5)
        self.assertEqual(len(result["works"]), 4)
        self.assertNotIn(engine.SCOPUS_CORRECTED_RECORD_ID, {row["paper_id"] for row in result["works"]})

        broken = copy.deepcopy(validated)
        broken["inputs"]["combined_record_level_screening"]["loaded_rows"][0]["final_decision"] = "EXCLUDE"
        with self.assertRaisesRegex(engine.CombinedAnalysisError, "corrected source screening"):
            engine._validate_final_rows(broken, self.spec)

        broken_cells = copy.deepcopy(validated)
        broken_cells["inputs"]["combined_metadata"]["loaded_rows"][0]["title"] += " altered"
        with self.assertRaisesRegex(engine.CombinedAnalysisError, "exact frozen allow-list"):
            engine._validate_final_rows(broken_cells, self.spec)

    def test_main_figures_are_600_dpi_png_eps_pairs(self) -> None:
        with tempfile.TemporaryDirectory(dir=engine.HERE) as temp_dir:
            root = Path(temp_dir)
            figure_dir = root / "figures"
            paths = engine.create_figures_v5(figure_dir, self.analysis)
            rows = engine._figure_manifest(paths, root)
            self.assertEqual(len(rows), 5)
            self.assertTrue(all(abs(float(row["png_dpi_x"]) - 600.0) <= 1.0 for row in rows))
            self.assertTrue(all(Path(root / row["eps_path"]).is_file() for row in rows))
            self.assertFalse(any("word" in row["figure_stem"].casefold() for row in rows))


class AuditRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validated = engine.validate_input_contract(
            engine.DEFAULT_CONTRACT,
            production=True,
            validate_locked_files=True,
        )
        cls.spec = engine.v2.load_json(
            engine.WORKSPACE
            / "ACTIVE_GSE_REVISION_2026-08-13/06_AUDIT/FRESH_ANALYSIS_SPECIFICATION_V2_2026-08-14.json",
            "spec",
        )
        cls.final_data = engine._validate_final_rows(cls.validated, cls.spec)

    def test_preprint_retained_abstract_phrase_union_repairs_all_21_rows(self) -> None:
        sensitivity_works = [
            row
            for row in self.final_data["works"]
            if not (
                int(row["family_size"]) == 1
                and (
                    row["version_role"].strip().casefold() in {"preprint", "other_version"}
                    or "preprint" in row["record_type"].strip().casefold()
                )
            )
        ]
        rows, _pairs, _network, _hits = engine.v2.phrase_analysis(
            sensitivity_works, self.spec
        )
        sensitivity_rows = [
            row
            for row in rows
            if row["measure"] == "Retained-abstract sensitivity frequency"
        ]
        before = {
            row["category"]: (row["count"], row["work_ids"])
            for row in sensitivity_rows
        }
        self.assertEqual(
            sum(
                len(engine.v2.split_semicolon(row["work_ids"])) != int(row["count"])
                for row in sensitivity_rows
            ),
            21,
        )
        engine._repair_phrase_table_abstract_sensitivity(rows, sensitivity_works)
        after_rows = [
            row
            for row in rows
            if row["measure"] == "Retained-abstract sensitivity frequency"
        ]
        self.assertEqual(
            sum(before[row["category"]] != (row["count"], row["work_ids"]) for row in after_rows),
            21,
        )
        self.assertTrue(
            all(
                len(engine.v2.split_semicolon(row["work_ids"])) == int(row["count"])
                for row in after_rows
            )
        )

    def test_author_ledger_matches_2388_productivity_identities(self) -> None:
        oa_by_id = {
            row["paper_id"]: row for row in self.final_data["openalex_rows"]
        }
        ledger = engine._author_identity_ledger(self.final_data["works"], oa_by_id)
        _fields, productivity_all = engine.read_csv_any(
            RUN01 / "supplements/SUPPLEMENT_AUTHOR_PRODUCTIVITY_COMPLETE.csv"
        )
        productivity = [
            row for row in productivity_all if row["section"] == "Author productivity"
        ]
        self.assertEqual(len(ledger), 2388)
        self.assertEqual(len(productivity), 2388)
        self.assertEqual(
            {row["author_key"] for row in ledger},
            {row["value_text"] for row in productivity},
        )
        aaron = [row for row in ledger if row["display_name"] == "Aaron Lawson McLean"]
        self.assertEqual(len(aaron), 1)
        self.assertEqual(
            aaron[0]["author_key"],
            "openalex:https://openalex.org/a5075371405",
        )
        self.assertIn("ORCID", aaron[0]["identity_type"])
        self.assertIn("institution IDs", aaron[0]["identity_type"])

    def test_sub_tenth_percent_publication_display(self) -> None:
        self.assertEqual(engine._publication_percent(1, 3919), "<0.1%")
        self.assertEqual(engine._publication_percent(3, 3919), "<0.1%")
        self.assertEqual(engine._publication_percent(4, 3919), 0.1)
        self.assertEqual(engine._publication_percent(0, 3919), 0.0)

    def test_phrase_network_layout_reduces_crossings_and_renders_600_dpi(self) -> None:
        _edge_fields, edge_rows = engine.read_csv_any(
            RUN01 / "supplements/SUPPLEMENT_PHRASE_NETWORK_EDGES_CONDITIONAL.csv"
        )
        _node_fields, node_rows = engine.read_csv_any(
            RUN01 / "supplements/SUPPLEMENT_PHRASE_NETWORK_NODES_CONDITIONAL.csv"
        )
        parsed = [
            (*row["category"].split(" + "), int(row["count"]))
            for row in edge_rows
        ]
        nodes = sorted(
            {label for left, right, _count in parsed for label in (left, right)},
            key=str.casefold,
        )
        alphabetical_crossings = engine._phrase_network_crossing_count(nodes, parsed)
        order, optimised_crossings = engine._optimise_phrase_network_circular_order(
            nodes, parsed
        )
        self.assertEqual(set(order), set(nodes))
        self.assertEqual(alphabetical_crossings, 40)
        self.assertEqual(optimised_crossings, 24)
        self.assertLess(optimised_crossings, alphabetical_crossings)
        analysis = {
            "plot_data": {
                "phrase_network_edges": edge_rows,
                "phrase_counts": {
                    row["category"]: int(row["count"]) for row in node_rows
                },
            }
        }
        with tempfile.TemporaryDirectory(dir=engine.HERE) as temp_dir:
            root = Path(temp_dir)
            paths = engine.create_supplementary_phrase_network_v5(root, analysis)
            manifest = engine._figure_manifest(paths, root)
            self.assertEqual(len(manifest), 1)
            self.assertAlmostEqual(float(manifest[0]["png_dpi_x"]), 600.0, delta=1.0)
            self.assertTrue((root / manifest[0]["eps_path"]).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
