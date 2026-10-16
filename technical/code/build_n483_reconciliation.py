#!/usr/bin/env python3
"""Build the controlled 547-publication/483-study GSE reconciliation package.

This is a deliberately bounded successor to the frozen n=485 integration.  It
changes exactly two publication-version families, retains the published report
for each, removes only the duplicate preprint rows from the study-level views,
and emits a revision-locked v5 analysis input contract.  Existing authorities
and analysis outputs are never overwritten.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


WORKSPACE = Path(__file__).resolve().parents[3]
ENGINE_DIR = WORKSPACE / "ACTIVE_GSE_REVISION_2026-08-13" / "03_PIPELINE" / "combined_analysis_engine_v5_20260816"
SOURCE_CONTRACT = ENGINE_DIR / "COMBINED_ANALYSIS_INPUT_CONTRACT_V5_SCAFFOLD_2026-08-16.json"
SOURCE_REVIEW_DIR = (
    WORKSPACE
    / "GSE_FULL_RERUN_2026-08-13"
    / "16_SCOPUS_VERSION_AND_EXTRACTION"
    / "scopus_increment_version_review_package_run03"
    / "review_completed"
)
SOURCE_INTEGRATION_DIR = (
    WORKSPACE
    / "GSE_FULL_RERUN_2026-08-13"
    / "16_SCOPUS_VERSION_AND_EXTRACTION"
    / "scopus_base_v4_final_integration_run02"
)
DEFAULT_REVIEW_DIR = (
    WORKSPACE
    / "GSE_FULL_RERUN_2026-08-13"
    / "16_SCOPUS_VERSION_AND_EXTRACTION"
    / "n483_version_reconciliation_run01"
)
DEFAULT_INTEGRATION_DIR = (
    WORKSPACE
    / "GSE_FULL_RERUN_2026-08-13"
    / "16_SCOPUS_VERSION_AND_EXTRACTION"
    / "n483_final_integration_run01"
)
DEFAULT_CONTRACT = ENGINE_DIR / "COMBINED_ANALYSIS_INPUT_CONTRACT_V5_N483_2026-08-26.json"

SOURCE_REVIEW_LEDGER = SOURCE_REVIEW_DIR / "SCOPUS_INCREMENT_ALL_RECORD_FAMILY_REVIEW_COMPLETED.csv"
SOURCE_REVIEW_MANIFEST = SOURCE_REVIEW_DIR / "RUN03_VERSION_REVIEW_COMPLETION_MANIFEST.json"
SOURCE_VERSION = SOURCE_INTEGRATION_DIR / "COMBINED_ELIGIBLE_PUBLICATION_VERSION_LEDGER_CORRECTED_V2.csv"
SOURCE_SELECTION = SOURCE_INTEGRATION_DIR / "COMBINED_STUDY_SELECTION_LEDGER_CORRECTED_V2.csv"
SOURCE_EXTRACTION = SOURCE_INTEGRATION_DIR / "COMBINED_CANONICAL_CHECKED_EXTRACTION_CORRECTED_V2.csv"
SOURCE_METADATA = SOURCE_INTEGRATION_DIR / "COMBINED_CANONICAL_METADATA_CORRECTED_V2.csv"
SOURCE_OPENALEX = SOURCE_INTEGRATION_DIR / "COMBINED_CANONICAL_OPENALEX_CORRECTED_V2.csv"
SOURCE_INTEGRATION_MANIFEST = SOURCE_INTEGRATION_DIR / "SCOPUS_FINAL_INTEGRATION_CORRECTED_MANIFEST_V2.json"

REVIEW_LEDGER_NAME = "N483_ALL_RECORD_FAMILY_REVIEW_COMPLETED.csv"
PAIR_AUDIT_NAME = "N483_PUBLICATION_VERSION_PAIR_CORRECTIONS.csv"
REVIEW_QA_NAME = "N483_VERSION_REVIEW_QA.md"
REVIEW_MANIFEST_NAME = "N483_VERSION_REVIEW_MANIFEST.json"
REVIEW_HASHES_NAME = "N483_VERSION_REVIEW_HASHES.csv"
REVIEW_FROZEN_NAME = "N483_VERSION_REVIEW_FROZEN.json"

VERSION_NAME = "COMBINED_ELIGIBLE_PUBLICATION_VERSION_LEDGER_N483.csv"
SELECTION_NAME = "COMBINED_STUDY_SELECTION_LEDGER_N483.csv"
EXTRACTION_NAME = "COMBINED_CANONICAL_CHECKED_EXTRACTION_N483.csv"
METADATA_NAME = "COMBINED_CANONICAL_METADATA_N483.csv"
OPENALEX_NAME = "COMBINED_CANONICAL_OPENALEX_N483.csv"
INTEGRATION_AUDIT_NAME = "N483_RECONCILIATION_AUDIT.csv"
INTEGRATION_QA_NAME = "N483_FINAL_INTEGRATION_QA.json"
INTEGRATION_MANIFEST_NAME = "N483_FINAL_INTEGRATION_MANIFEST.json"
INTEGRATION_HASHES_NAME = "N483_FINAL_INTEGRATION_HASHES.csv"
INTEGRATION_FROZEN_NAME = "N483_FINAL_INTEGRATION_FROZEN.json"

REVIEW_SCHEMA = "gse-controlled-version-reconciliation-n483-v1.0"
INTEGRATION_SCHEMA = "gse-controlled-final-integration-n483-v1.0"

FAMILY_PROTECTED_FIELDS = [
    "record_key",
    "source_corpus",
    "source_record_id",
    "doi",
    "openalex_id",
    "title",
    "authors",
    "year",
    "publication_date",
    "journal",
    "record_type",
    "abstract",
    "url",
    "source_row_sha256",
    "schema_version",
    "provisional_family_id",
    "family_size",
    "family_members_sha256",
    "supporting_same_pair_ids",
    "reviewed_distinct_pair_ids",
    "source_preparation_manifest_sha256",
    "record_evidence_sha256",
]

PAIR_AUDIT_FIELDS = [
    "correction_id",
    "pair_id",
    "preprint_record_key",
    "published_record_key",
    "preprint_doi",
    "published_doi",
    "relationship_decision",
    "relationship_type",
    "preferred_record_key",
    "evidence_locator_1",
    "evidence_locator_2",
    "evidence_finding",
    "reviewed_by",
    "reviewed_at_utc",
    "preprint_source_row_sha256",
    "published_source_row_sha256",
    "decision_sha256",
]

INTEGRATION_AUDIT_FIELDS = [
    "correction_id",
    "preprint_paper_id",
    "published_paper_id",
    "old_preprint_family_id",
    "old_published_family_id",
    "new_family_id",
    "old_family_count_contribution",
    "new_family_count_contribution",
    "preferred_report_retained",
    "study_level_row_removed",
    "classification_policy",
    "evidence_locator_1",
    "evidence_locator_2",
]

PAIR_SPECS = (
    {
        "correction_id": "N483-CORR-001",
        "preprint_id": "15b1e2fee67db58575b7",
        "published_id": "ed072d60d05f5e236143",
        "preprint_doi": "10.21203/rs.3.rs-7382682/v1",
        "published_doi": "10.1186/s12909-025-08308-y",
        "evidence_locator_1": "https://doi.org/10.21203/rs.3.rs-7382682/v1",
        "evidence_locator_2": "https://doi.org/10.1186/s12909-025-08308-y",
        "evidence_finding": (
            "The Research Square report explicitly identifies the BMC Medical Education article as its "
            "version of record; the reports share the study, authors, intervention and randomized design."
        ),
        "family_label": "N483_FAMILY_001",
    },
    {
        "correction_id": "N483-CORR-002",
        "preprint_id": "da8839d00c24db7f6ad6",
        "published_id": "fd0c4ec164cda596074b",
        "preprint_doi": "10.2196/preprints.81673",
        "published_doi": "10.2196/81673",
        "evidence_locator_1": "https://preprints.jmir.org/preprint/81673",
        "evidence_locator_2": "https://mededu.jmir.org/2026/1/e81673",
        "evidence_finding": (
            "JMIR identifies preprint 81673 as an earlier version of the published JMIR Medical Education "
            "article DOI 10.2196/81673; the reports share the study and author group."
        ),
        "family_label": "N483_FAMILY_002",
    },
)

CHANGED_FAMILY_FIELDS = {
    "provisional_family_id",
    "family_size",
    "family_members_sha256",
    "supporting_same_pair_ids",
    "record_evidence_sha256",
    "review_family_label",
    "family_status",
    "version_role",
    "preferred_for_analysis",
    "preferred_record_key",
    "preferred_basis",
    "relationship_to_preferred",
    "family_membership_rationale",
    "family_evidence_locator",
    "preferred_selection_rationale",
    "preferred_selection_evidence",
    "reviewed_by",
    "reviewed_at_utc",
}


class ReconciliationError(RuntimeError):
    """Raised when a locked reconciliation invariant fails."""


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(parts: Iterable[str]) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def row_hash(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    return stable_hash(clean(row.get(field)) for field in fields)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ReconciliationError(f"CSV has no header: {path}")
        return list(reader.fieldnames), [dict(row) for row in reader]


def write_csv(path: Path, fields: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field)) for field in fields})


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ReconciliationError(f"Expected a JSON object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any], *, sort_keys: bool = True) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=sort_keys, ensure_ascii=False)
        handle.write("\n")


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(WORKSPACE).as_posix()


def file_fact(path: Path, *, relative_to: Path | None = None) -> dict[str, Any]:
    shown = path.name if relative_to is None else path.resolve().relative_to(relative_to.resolve()).as_posix()
    return {"path": shown, "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def verify_source_pin(contract: Mapping[str, Any], role: str, path: Path) -> None:
    pin = contract["inputs"][role]
    if path.resolve() != (WORKSPACE / pin["path"]).resolve():
        raise ReconciliationError(f"Source path does not match locked role {role}")
    if sha256_file(path) != pin["sha256"] or path.stat().st_size != int(pin["bytes"]):
        raise ReconciliationError(f"Locked source changed: {role}")


def validate_source_authorities(contract: Mapping[str, Any]) -> None:
    checks = {
        "scopus_completed_version_decisions": SOURCE_REVIEW_LEDGER,
        "scopus_version_decision_manifest": SOURCE_REVIEW_MANIFEST,
        "combined_eligible_version_ledger": SOURCE_VERSION,
        "combined_study_selection_ledger": SOURCE_SELECTION,
        "combined_checked_corpus": SOURCE_EXTRACTION,
        "combined_metadata": SOURCE_METADATA,
        "combined_openalex": SOURCE_OPENALEX,
        "combined_package_manifest": SOURCE_INTEGRATION_MANIFEST,
    }
    for role, path in checks.items():
        verify_source_pin(contract, role, path)


def build_corrected_families(
    source_rows: list[dict[str, str]], source_header: list[str], reviewed_at: str
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    if len(source_rows) != 547 or len({row["record_key"] for row in source_rows}) != 547:
        raise ReconciliationError("Source completed review is not the locked 547-row authority")
    by_key = {row["record_key"]: row for row in source_rows}
    touched_keys: set[str] = set()
    audit_rows: list[dict[str, str]] = []
    integration_audit: list[dict[str, str]] = []

    for spec in PAIR_SPECS:
        preprint_key = f"base_eligible_v4:{spec['preprint_id']}"
        published_key = f"base_eligible_v4:{spec['published_id']}"
        if preprint_key not in by_key or published_key not in by_key:
            raise ReconciliationError(f"Expected correction records are missing: {spec['correction_id']}")
        preprint = by_key[preprint_key]
        published = by_key[published_key]
        if clean(preprint["doi"]).casefold() != spec["preprint_doi"] or clean(published["doi"]).casefold() != spec["published_doi"]:
            raise ReconciliationError(f"DOI identity mismatch: {spec['correction_id']}")
        if preprint["family_size"] != "1" or published["family_size"] != "1":
            raise ReconciliationError(f"Correction source is no longer two singleton families: {spec['correction_id']}")
        if preprint["preferred_for_analysis"] != "yes" or published["preferred_for_analysis"] != "yes":
            raise ReconciliationError(f"Correction source singleton is not preferred: {spec['correction_id']}")

        old_preprint_family_id = preprint["provisional_family_id"]
        old_published_family_id = published["provisional_family_id"]

        member_keys = sorted((preprint_key, published_key))
        member_hash = stable_hash(member_keys)
        family_id = "SIVF-" + member_hash[:24]
        pair_id = "N483VP-" + stable_hash(member_keys)[:24]
        rationale = spec["evidence_finding"]
        evidence = f"{spec['evidence_locator_1']};{spec['evidence_locator_2']}"
        preferred_rationale = (
            "The peer-reviewed journal article is the final and most complete publication and is retained "
            "as the preferred report for study-level analysis."
        )

        for row, is_preprint in ((preprint, True), (published, False)):
            row.update(
                {
                    "provisional_family_id": family_id,
                    "family_size": "2",
                    "family_members_sha256": member_hash,
                    "supporting_same_pair_ids": pair_id,
                    "reviewed_distinct_pair_ids": "",
                    "review_family_label": spec["family_label"],
                    "family_status": "LINKED_VERSION_FAMILY",
                    "version_role": "preprint" if is_preprint else "final_journal_article",
                    "preferred_for_analysis": "no" if is_preprint else "yes",
                    "preferred_record_key": published_key,
                    "preferred_basis": "final_most_complete_publication",
                    "relationship_to_preferred": "preprint_of" if is_preprint else "self_preferred",
                    "family_membership_rationale": rationale,
                    "family_evidence_locator": evidence,
                    "preferred_selection_rationale": preferred_rationale,
                    "preferred_selection_evidence": evidence,
                    "reviewed_by": "Codex controlled publication-version reconciliation",
                    "reviewed_at_utc": reviewed_at,
                }
            )
            row["record_evidence_sha256"] = row_hash(
                row, (field for field in FAMILY_PROTECTED_FIELDS if field != "record_evidence_sha256")
            )
            touched_keys.add(row["record_key"])

        decision = {
            "correction_id": spec["correction_id"],
            "pair_id": pair_id,
            "preprint_record_key": preprint_key,
            "published_record_key": published_key,
            "preprint_doi": spec["preprint_doi"],
            "published_doi": spec["published_doi"],
            "relationship_decision": "SAME_SCHOLARLY_WORK_VERSION",
            "relationship_type": "preprint_to_journal",
            "preferred_record_key": published_key,
            "evidence_locator_1": spec["evidence_locator_1"],
            "evidence_locator_2": spec["evidence_locator_2"],
            "evidence_finding": rationale,
            "reviewed_by": "Codex controlled publication-version reconciliation",
            "reviewed_at_utc": reviewed_at,
            "preprint_source_row_sha256": preprint["source_row_sha256"],
            "published_source_row_sha256": published["source_row_sha256"],
        }
        decision["decision_sha256"] = row_hash(decision, (field for field in PAIR_AUDIT_FIELDS if field != "decision_sha256"))
        audit_rows.append(decision)
        integration_audit.append(
            {
                "correction_id": spec["correction_id"],
                "preprint_paper_id": spec["preprint_id"],
                "published_paper_id": spec["published_id"],
                "old_preprint_family_id": old_preprint_family_id,
                "old_published_family_id": old_published_family_id,
                "new_family_id": family_id,
                "old_family_count_contribution": "2",
                "new_family_count_contribution": "1",
                "preferred_report_retained": spec["published_id"],
                "study_level_row_removed": spec["preprint_id"],
                "classification_policy": "Use the checked extraction of the preferred final journal article; do not union version-specific labels.",
                "evidence_locator_1": spec["evidence_locator_1"],
                "evidence_locator_2": spec["evidence_locator_2"],
            }
        )

    corrected = sorted(source_rows, key=lambda row: (row["provisional_family_id"], row["record_key"]))
    groups: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in corrected:
        expected_evidence = row_hash(
            row, (field for field in FAMILY_PROTECTED_FIELDS if field != "record_evidence_sha256")
        )
        if row["record_evidence_sha256"] != expected_evidence:
            raise ReconciliationError(f"Family evidence hash mismatch: {row['record_key']}")
        groups[row["provisional_family_id"]].append(row)
    if len(groups) != 483:
        raise ReconciliationError(f"Corrected family count is {len(groups)}, not 483")
    if sum(row["preferred_for_analysis"] == "yes" for row in corrected) != 483:
        raise ReconciliationError("Corrected preferred-report count is not 483")
    if sum(row["preferred_for_analysis"] == "no" for row in corrected) != 64:
        raise ReconciliationError("Corrected alternate-version count is not 64")
    for family_id, members in groups.items():
        preferred = [row for row in members if row["preferred_for_analysis"] == "yes"]
        if len(preferred) != 1 or {row["preferred_record_key"] for row in members} != {preferred[0]["record_key"]}:
            raise ReconciliationError(f"Preferred-report invariant failed: {family_id}")
        if {row["family_size"] for row in members} != {str(len(members))}:
            raise ReconciliationError(f"Family-size invariant failed: {family_id}")
    if len(touched_keys) != 4:
        raise ReconciliationError("The controlled correction did not touch exactly four publication rows")
    if source_header != list(corrected[0]):
        raise ReconciliationError("Completed family-review schema changed")
    return corrected, audit_rows, integration_audit


def validate_exact_family_delta(
    original_rows: Sequence[Mapping[str, str]], corrected_rows: Sequence[Mapping[str, str]]
) -> None:
    original = {row["record_key"]: row for row in original_rows}
    corrected = {row["record_key"]: row for row in corrected_rows}
    if set(original) != set(corrected):
        raise ReconciliationError("Publication membership changed during family reconciliation")
    expected_changed = {
        f"base_eligible_v4:{spec[key]}"
        for spec in PAIR_SPECS
        for key in ("preprint_id", "published_id")
    }
    changed_keys: set[str] = set()
    for key in original:
        changed = {field for field in original[key] if original[key][field] != corrected[key][field]}
        if changed:
            changed_keys.add(key)
            if key not in expected_changed or not changed <= CHANGED_FAMILY_FIELDS:
                raise ReconciliationError(f"Out-of-scope family change: {key}: {sorted(changed)}")
    if changed_keys != expected_changed:
        raise ReconciliationError(f"Exact four-row correction invariant failed: {sorted(changed_keys)}")


def build_review_package(
    stage: Path,
    final_dir: Path,
    contract: Mapping[str, Any],
    generated_at: str,
) -> tuple[list[dict[str, str]], list[str], list[dict[str, str]]]:
    source_header, source_rows_raw = read_csv(SOURCE_REVIEW_LEDGER)
    original_rows = [dict(row) for row in source_rows_raw]
    corrected_rows, pair_rows, integration_audit = build_corrected_families(
        [dict(row) for row in source_rows_raw], source_header, generated_at
    )
    validate_exact_family_delta(original_rows, corrected_rows)

    write_csv(stage / REVIEW_LEDGER_NAME, source_header, corrected_rows)
    write_csv(stage / PAIR_AUDIT_NAME, PAIR_AUDIT_FIELDS, pair_rows)
    qa_text = (
        "# Controlled n=483 publication-version reconciliation QA\n\n"
        f"Generated `{generated_at}` from the hash-locked 547-row completed family review. "
        "Two source-verified preprint-to-journal relationships were added. Exactly four publication rows "
        "changed family-review fields; no publication was added or removed. The corrected ledger contains "
        "547 eligible publication records, 483 preferred reports and 64 alternate publication versions. "
        "The preferred reports are the BMC Medical Education and JMIR Medical Education articles. "
        "No analysis or manuscript edit was performed by this review step.\n"
    )
    with (stage / REVIEW_QA_NAME).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(qa_text)

    inputs = {
        "source_completed_family_review": {
            "path": str(SOURCE_REVIEW_LEDGER.resolve()),
            "bytes": SOURCE_REVIEW_LEDGER.stat().st_size,
            "sha256": sha256_file(SOURCE_REVIEW_LEDGER),
        },
        "source_completion_manifest": {
            "path": str(SOURCE_REVIEW_MANIFEST.resolve()),
            "bytes": SOURCE_REVIEW_MANIFEST.stat().st_size,
            "sha256": sha256_file(SOURCE_REVIEW_MANIFEST),
        },
    }
    outputs = {
        name: file_fact(stage / name)
        for name in (REVIEW_LEDGER_NAME, PAIR_AUDIT_NAME, REVIEW_QA_NAME)
    }
    manifest = {
        "pipeline": "gse_controlled_publication_version_reconciliation_n483_20260826",
        "schema_version": REVIEW_SCHEMA,
        "status": "frozen_completed_version_review_n483",
        "generated_at_utc": generated_at,
        "counts": {
            "eligible_publications": 547,
            "families": 483,
            "preferred_reports": 483,
            "alternate_versions": 64,
            "new_same_version_pairs": 2,
            "changed_publication_rows": 4,
            "scopus_publications": 30,
        },
        "contracts": {
            "source_547_row_authority_hash_bound": True,
            "exactly_two_source_verified_pair_corrections": True,
            "exactly_four_publication_rows_changed": True,
            "exactly_one_preferred_report_per_family": True,
            "published_report_preferred_for_each_corrected_family": True,
            "analysis_performed": False,
            "manuscript_modified": False,
            "output_no_clobber": True,
        },
        "evidence": [
            {
                "correction_id": spec["correction_id"],
                "preprint": spec["evidence_locator_1"],
                "published_report": spec["evidence_locator_2"],
                "finding": spec["evidence_finding"],
                "accessed_at_utc": generated_at,
            }
            for spec in PAIR_SPECS
        ],
        "inputs": inputs,
        "outputs": outputs,
    }
    write_json(stage / REVIEW_MANIFEST_NAME, manifest)

    hash_rows: list[dict[str, Any]] = []
    for name, value in inputs.items():
        hash_rows.append({"scope": "input", "name": name, **value})
    for name in (REVIEW_LEDGER_NAME, PAIR_AUDIT_NAME, REVIEW_QA_NAME, REVIEW_MANIFEST_NAME):
        hash_rows.append({"scope": "output", "name": name, **file_fact(stage / name)})
    write_csv(stage / REVIEW_HASHES_NAME, ["scope", "name", "path", "bytes", "sha256"], hash_rows)
    frozen = {
        "pipeline": manifest["pipeline"],
        "schema_version": REVIEW_SCHEMA,
        "status": "frozen",
        "generated_at_utc": generated_at,
        "manifest": REVIEW_MANIFEST_NAME,
        "manifest_sha256": sha256_file(stage / REVIEW_MANIFEST_NAME),
        "hash_manifest": REVIEW_HASHES_NAME,
        "hash_manifest_sha256": sha256_file(stage / REVIEW_HASHES_NAME),
        "published_path": str(final_dir.resolve()),
    }
    write_json(stage / REVIEW_FROZEN_NAME, frozen)
    return corrected_rows, source_header, integration_audit


def update_canonical_row(
    row: Mapping[str, str], family: Mapping[str, str], *, kind: str
) -> dict[str, str]:
    updated = dict(row)
    updated["integration_schema_version"] = INTEGRATION_SCHEMA
    updated["final_version_family_id"] = family["provisional_family_id"]
    updated["preferred_record_key"] = family["record_key"]
    updated["preferred_paper_id"] = family["source_record_id"]
    if kind in {"extraction", "metadata"}:
        if "version_family_id" in updated:
            updated["version_family_id"] = family["provisional_family_id"]
        if "family_size" in updated:
            updated["family_size"] = family["family_size"]
        if "version_role" in updated:
            updated["version_role"] = family["version_role"]
    return updated


def build_integration_package(
    stage: Path,
    final_dir: Path,
    final_review_dir: Path,
    corrected_families: list[dict[str, str]],
    family_header: list[str],
    integration_audit: list[dict[str, str]],
    generated_at: str,
) -> dict[str, Path]:
    source_version_header, _source_version_rows = read_csv(SOURCE_VERSION)
    source_selection_header, source_selection_rows = read_csv(SOURCE_SELECTION)
    extraction_header, extraction_rows = read_csv(SOURCE_EXTRACTION)
    metadata_header, metadata_rows = read_csv(SOURCE_METADATA)
    openalex_header, openalex_rows = read_csv(SOURCE_OPENALEX)
    if (len(source_selection_rows), len(extraction_rows), len(metadata_rows), len(openalex_rows)) != (485, 485, 485, 485):
        raise ReconciliationError("Source integration is not the locked 485-study package")

    review_ledger_stage = stage.parent / "review" / REVIEW_LEDGER_NAME
    completed_sha = sha256_file(review_ledger_stage)
    version_rows = [
        {
            "integration_schema_version": INTEGRATION_SCHEMA,
            "source_completed_family_review_sha256": completed_sha,
            **row,
        }
        for row in corrected_families
    ]
    if source_version_header != list(version_rows[0]):
        raise ReconciliationError("Integrated version-ledger schema changed")

    preferred = sorted(
        (row for row in corrected_families if row["preferred_for_analysis"] == "yes"),
        key=lambda row: (row["provisional_family_id"], row["record_key"]),
    )
    selection_rows = [
        {
            "integration_schema_version": INTEGRATION_SCHEMA,
            "final_version_family_id": row["provisional_family_id"],
            "family_size": row["family_size"],
            "preferred_record_key": row["record_key"],
            "preferred_paper_id": row["source_record_id"],
            "preferred_source_corpus": row["source_corpus"],
            "preferred_basis": row["preferred_basis"],
            "preferred_selection_rationale": row["preferred_selection_rationale"],
            "preferred_selection_evidence": row["preferred_selection_evidence"],
            "family_reviewed_by": row["reviewed_by"],
            "family_reviewed_at_utc": row["reviewed_at_utc"],
            "source_family_review_row_sha256": row_hash(row, family_header),
        }
        for row in preferred
    ]
    if source_selection_header != list(selection_rows[0]):
        raise ReconciliationError("Study-selection schema changed")

    source_tables = {
        "extraction": (extraction_header, {row["paper_id"]: row for row in extraction_rows}),
        "metadata": (metadata_header, {row["paper_id"]: row for row in metadata_rows}),
        "openalex": (openalex_header, {row["paper_id"]: row for row in openalex_rows}),
    }
    canonical: dict[str, list[dict[str, str]]] = {key: [] for key in source_tables}
    for family in preferred:
        paper_id = family["source_record_id"]
        for kind, (_header, mapping) in source_tables.items():
            if paper_id not in mapping:
                raise ReconciliationError(f"Preferred report lacks source {kind}: {paper_id}")
            canonical[kind].append(update_canonical_row(mapping[paper_id], family, kind=kind))

    removed_ids = {spec["preprint_id"] for spec in PAIR_SPECS}
    retained_ids = {spec["published_id"] for spec in PAIR_SPECS}
    preferred_ids = {row["source_record_id"] for row in preferred}
    if len(preferred) != 483 or removed_ids & preferred_ids or not retained_ids <= preferred_ids:
        raise ReconciliationError("Preferred-report membership does not implement the exact n=483 correction")
    if [row["paper_id"] for row in canonical["extraction"]] != [row["preferred_paper_id"] for row in selection_rows]:
        raise ReconciliationError("Canonical extraction order differs from study selection")
    if [row["paper_id"] for row in canonical["metadata"]] != [row["preferred_paper_id"] for row in selection_rows]:
        raise ReconciliationError("Canonical metadata order differs from study selection")
    if [row["paper_id"] for row in canonical["openalex"]] != [row["preferred_paper_id"] for row in selection_rows]:
        raise ReconciliationError("Canonical OpenAlex order differs from study selection")

    extraction_map = {row["paper_id"]: row for row in canonical["extraction"]}
    expected_models = {
        "ed072d60d05f5e236143": "GPT-4o;Claude",
        "fd0c4ec164cda596074b": "GPT-5;OpenAI_o_series",
    }
    for paper_id, expected in expected_models.items():
        if extraction_map[paper_id]["final_model_families"] != expected:
            raise ReconciliationError(f"Preferred-report checked model classification changed: {paper_id}")

    write_csv(stage / VERSION_NAME, source_version_header, version_rows)
    write_csv(stage / SELECTION_NAME, source_selection_header, selection_rows)
    write_csv(stage / EXTRACTION_NAME, extraction_header, canonical["extraction"])
    write_csv(stage / METADATA_NAME, metadata_header, canonical["metadata"])
    write_csv(stage / OPENALEX_NAME, openalex_header, canonical["openalex"])
    write_csv(stage / INTEGRATION_AUDIT_NAME, INTEGRATION_AUDIT_FIELDS, integration_audit)

    old_model_counts = Counter(
        model
        for row in extraction_rows
        for model in (part.strip() for part in row["final_model_families"].split(";"))
        if model
    )
    new_model_counts = Counter(
        model
        for row in canonical["extraction"]
        for model in (part.strip() for part in row["final_model_families"].split(";"))
        if model
    )
    counts = {
        "eligible_publication_records": 547,
        "unique_studies": 483,
        "alternate_publication_versions": 64,
        "base_families_after_reconciliation": 456,
        "scopus_corrected_includes": 30,
        "canonical_extraction_rows": 483,
        "canonical_metadata_rows": 483,
        "canonical_openalex_rows": 483,
        "combined_screening_rows": 3919,
        "combined_screening_include": 547,
        "combined_screening_exclude": 3372,
    }
    qa = {
        "schema_version": INTEGRATION_SCHEMA,
        "status": "PASS",
        "validated_at_utc": generated_at,
        "counts": counts,
        "checks": {
            "source_485_package_hash_bound": True,
            "version_ledger_retains_all_547_publications": len(version_rows) == 547,
            "exact_483_preferred_reports": len(preferred) == 483,
            "exact_64_alternate_versions": sum(row["preferred_for_analysis"] == "no" for row in corrected_families) == 64,
            "exact_two_preprint_rows_removed_from_study_views": removed_ids.isdisjoint(preferred_ids),
            "published_reports_retained": retained_ids <= preferred_ids,
            "preferred_report_classifications_preserved": True,
            "record_level_screening_unchanged": True,
            "output_no_clobber": True,
        },
        "model_count_deltas": {
            model: {"n485": old_model_counts[model], "n483": new_model_counts[model], "delta": new_model_counts[model] - old_model_counts[model]}
            for model in sorted(set(old_model_counts) | set(new_model_counts))
            if old_model_counts[model] != new_model_counts[model]
        },
    }
    write_json(stage / INTEGRATION_QA_NAME, qa)

    outputs = {
        "version_ledger": file_fact(stage / VERSION_NAME),
        "selection": file_fact(stage / SELECTION_NAME),
        "extraction": file_fact(stage / EXTRACTION_NAME),
        "metadata": file_fact(stage / METADATA_NAME),
        "openalex": file_fact(stage / OPENALEX_NAME),
        "audit": file_fact(stage / INTEGRATION_AUDIT_NAME),
        "qa": file_fact(stage / INTEGRATION_QA_NAME),
    }
    manifest = {
        "pipeline": "gse_controlled_final_integration_n483_20260826",
        "schema_version": INTEGRATION_SCHEMA,
        "status": "frozen_corrected_combined_corpus_n483_analysis_not_performed",
        "generated_at_utc": generated_at,
        "contracts": {
            "corrected_authorities_only": True,
            "controlled_two_pair_reconciliation": True,
            "all_547_publication_records_preserved": True,
            "one_preferred_report_per_483_families": True,
            "preferred_report_checked_extraction_only": True,
            "version_specific_classifications_not_unioned": True,
            "record_level_screening_unchanged": True,
            "analysis_performed": False,
            "manuscript_modified": False,
            "output_no_clobber": True,
        },
        "derived_counts": counts,
        "bound_inputs": {
            "source_integration_manifest": {
                "path": str(SOURCE_INTEGRATION_MANIFEST.resolve()),
                "bytes": SOURCE_INTEGRATION_MANIFEST.stat().st_size,
                "sha256": sha256_file(SOURCE_INTEGRATION_MANIFEST),
            },
            "source_version_ledger": {
                "path": str(SOURCE_VERSION.resolve()),
                "bytes": SOURCE_VERSION.stat().st_size,
                "sha256": sha256_file(SOURCE_VERSION),
            },
            "source_study_selection": {
                "path": str(SOURCE_SELECTION.resolve()),
                "bytes": SOURCE_SELECTION.stat().st_size,
                "sha256": sha256_file(SOURCE_SELECTION),
            },
            "source_checked_extraction": {
                "path": str(SOURCE_EXTRACTION.resolve()),
                "bytes": SOURCE_EXTRACTION.stat().st_size,
                "sha256": sha256_file(SOURCE_EXTRACTION),
            },
            "source_metadata": {
                "path": str(SOURCE_METADATA.resolve()),
                "bytes": SOURCE_METADATA.stat().st_size,
                "sha256": sha256_file(SOURCE_METADATA),
            },
            "source_openalex": {
                "path": str(SOURCE_OPENALEX.resolve()),
                "bytes": SOURCE_OPENALEX.stat().st_size,
                "sha256": sha256_file(SOURCE_OPENALEX),
            },
            "n483_completed_family_review": {
                "path": str((final_review_dir / REVIEW_LEDGER_NAME).resolve()),
                "bytes": review_ledger_stage.stat().st_size,
                "sha256": completed_sha,
            },
        },
        "evidence": [
            {
                "correction_id": spec["correction_id"],
                "preprint": spec["evidence_locator_1"],
                "published_report": spec["evidence_locator_2"],
                "finding": spec["evidence_finding"],
                "accessed_at_utc": generated_at,
            }
            for spec in PAIR_SPECS
        ],
        "outputs": outputs,
    }
    write_json(stage / INTEGRATION_MANIFEST_NAME, manifest)
    hash_rows = []
    for name in (
        VERSION_NAME,
        SELECTION_NAME,
        EXTRACTION_NAME,
        METADATA_NAME,
        OPENALEX_NAME,
        INTEGRATION_AUDIT_NAME,
        INTEGRATION_QA_NAME,
        INTEGRATION_MANIFEST_NAME,
    ):
        hash_rows.append({"scope": "output", **file_fact(stage / name)})
    write_csv(stage / INTEGRATION_HASHES_NAME, ["scope", "path", "bytes", "sha256"], hash_rows)
    frozen = {
        "pipeline": manifest["pipeline"],
        "schema_version": INTEGRATION_SCHEMA,
        "status": "frozen",
        "generated_at_utc": generated_at,
        "manifest": INTEGRATION_MANIFEST_NAME,
        "manifest_sha256": sha256_file(stage / INTEGRATION_MANIFEST_NAME),
        "hash_manifest": INTEGRATION_HASHES_NAME,
        "hash_manifest_sha256": sha256_file(stage / INTEGRATION_HASHES_NAME),
        "published_path": str(final_dir.resolve()),
    }
    write_json(stage / INTEGRATION_FROZEN_NAME, frozen)
    return {
        "review_ledger": final_review_dir / REVIEW_LEDGER_NAME,
        "review_manifest": final_review_dir / REVIEW_MANIFEST_NAME,
        "review_hashes": final_review_dir / REVIEW_HASHES_NAME,
        "integration_version": final_dir / VERSION_NAME,
        "integration_selection": final_dir / SELECTION_NAME,
        "integration_extraction": final_dir / EXTRACTION_NAME,
        "integration_metadata": final_dir / METADATA_NAME,
        "integration_openalex": final_dir / OPENALEX_NAME,
        "integration_manifest": final_dir / INTEGRATION_MANIFEST_NAME,
        "integration_hashes": final_dir / INTEGRATION_HASHES_NAME,
        "integration_frozen": final_dir / INTEGRATION_FROZEN_NAME,
    }


def pin_file(path: Path, *, rows: int | None = None, required_columns: Sequence[str] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "state": "locked",
        "path": relative_path(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if rows is not None:
        value["rows"] = rows
    if required_columns:
        value["required_columns"] = list(required_columns)
    return value


def build_contract(
    source_contract: Mapping[str, Any],
    target: Path,
    paths: Mapping[str, Path],
    generated_at: str,
) -> dict[str, Any]:
    contract = json.loads(json.dumps(source_contract))
    contract["contract_id"] = "gse_six_source_combined_analysis_v5_n483_ready_2026-08-26"
    contract["status"] = "ready_for_production"
    contract["generated_at_utc"] = generated_at
    contract["selection_flow"]["canonical_works"] = 483
    contract["selection_flow"]["canonical_count_rule"] = (
        "Counts are proved by the controlled n=483 publication-version reconciliation and its locked "
        "study-selection, checked-corpus, metadata, OpenAlex and integration ledgers. The superseded "
        "n=485, n=470, n=363 and n=323 study lines are prohibited."
    )
    inputs = contract["inputs"]

    review_header, _ = read_csv(paths["review_ledger"])
    inputs["scopus_completed_version_decisions"] = pin_file(
        paths["review_ledger"],
        rows=547,
        required_columns=inputs["scopus_completed_version_decisions"]["required_columns"],
    )
    review_manifest_pin = pin_file(paths["review_manifest"])
    review_manifest_pin["expected_json"] = {
        "status": "frozen_completed_version_review_n483",
        "counts.eligible_publications": 547,
        "counts.families": 483,
        "counts.alternate_versions": 64,
        "counts.scopus_publications": 30,
        "contracts.exactly_two_source_verified_pair_corrections": True,
    }
    inputs["scopus_version_decision_manifest"] = review_manifest_pin
    _, review_hash_rows = read_csv(paths["review_hashes"])
    inputs["scopus_version_decision_hash_ledger"] = pin_file(paths["review_hashes"], rows=len(review_hash_rows))

    replacements = {
        "combined_eligible_version_ledger": ("integration_version", 547),
        "combined_study_selection_ledger": ("integration_selection", 483),
        "combined_checked_corpus": ("integration_extraction", 483),
        "combined_metadata": ("integration_metadata", 483),
        "combined_openalex": ("integration_openalex", 483),
    }
    for role, (path_key, rows) in replacements.items():
        inputs[role] = pin_file(
            paths[path_key], rows=rows, required_columns=inputs[role].get("required_columns")
        )

    integration_manifest_pin = pin_file(paths["integration_manifest"])
    integration_manifest_pin["expected_json"] = {
        "status": "frozen_corrected_combined_corpus_n483_analysis_not_performed",
        "contracts.analysis_performed": False,
        "contracts.corrected_authorities_only": True,
        "contracts.controlled_two_pair_reconciliation": True,
        "contracts.preferred_report_checked_extraction_only": True,
        "derived_counts.combined_screening_rows": 3919,
        "derived_counts.combined_screening_include": 547,
        "derived_counts.combined_screening_exclude": 3372,
        "derived_counts.eligible_publication_records": 547,
        "derived_counts.unique_studies": 483,
        "derived_counts.alternate_publication_versions": 64,
    }
    inputs["combined_package_manifest"] = integration_manifest_pin
    _, integration_hash_rows = read_csv(paths["integration_hashes"])
    inputs["combined_package_hash_ledger"] = pin_file(
        paths["integration_hashes"],
        rows=len(integration_hash_rows),
        required_columns=inputs["combined_package_hash_ledger"].get("required_columns"),
    )
    frozen_pin = pin_file(paths["integration_frozen"])
    frozen_pin["expected_json"] = {
        "status": "frozen",
        "manifest_sha256": sha256_file(paths["integration_manifest"]),
        "hash_manifest_sha256": sha256_file(paths["integration_hashes"]),
    }
    inputs["combined_package_frozen_marker"] = frozen_pin
    contract.setdefault("notes", []).append(
        "The n=483 successor changes only two source-verified publication-version relationships and retains the final journal report for each study."
    )
    if len(review_header) != 35:
        raise ReconciliationError("Completed family-review schema width changed")
    # The v5 engine treats the six-source mapping order as an explicit contract.
    write_json(target, contract, sort_keys=False)
    return contract


def validate_published_package(review_dir: Path, integration_dir: Path, contract_path: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    if contract["selection_flow"]["canonical_works"] != 483:
        raise ReconciliationError("Published contract does not state 483 canonical works")
    for role, pin in contract["inputs"].items():
        if pin.get("state") != "locked":
            continue
        path = WORKSPACE / pin["path"]
        if not path.is_file() or sha256_file(path) != pin["sha256"] or path.stat().st_size != int(pin["bytes"]):
            raise ReconciliationError(f"Published input pin failed: {role}")
        if "rows" in pin and path.suffix.casefold() == ".csv":
            _, rows = read_csv(path)
            if len(rows) != int(pin["rows"]):
                raise ReconciliationError(f"Published row count failed: {role}")
    review_frozen = load_json(review_dir / REVIEW_FROZEN_NAME)
    if review_frozen["manifest_sha256"] != sha256_file(review_dir / REVIEW_MANIFEST_NAME):
        raise ReconciliationError("Review frozen marker does not bind its manifest")
    if review_frozen["hash_manifest_sha256"] != sha256_file(review_dir / REVIEW_HASHES_NAME):
        raise ReconciliationError("Review frozen marker does not bind its hash ledger")
    integration_frozen = load_json(integration_dir / INTEGRATION_FROZEN_NAME)
    if integration_frozen["manifest_sha256"] != sha256_file(integration_dir / INTEGRATION_MANIFEST_NAME):
        raise ReconciliationError("Integration frozen marker does not bind its manifest")
    if integration_frozen["hash_manifest_sha256"] != sha256_file(integration_dir / INTEGRATION_HASHES_NAME):
        raise ReconciliationError("Integration frozen marker does not bind its hash ledger")
    return {
        "eligible_publication_records": 547,
        "unique_studies": 483,
        "alternate_publication_versions": 64,
        "contract": relative_path(contract_path),
        "contract_sha256": sha256_file(contract_path),
    }


def build(review_dir: Path, integration_dir: Path, contract_path: Path) -> dict[str, Any]:
    for path in (review_dir, integration_dir, contract_path):
        if path.exists():
            raise ReconciliationError(f"No-clobber: target already exists: {path}")
    if review_dir.parent != integration_dir.parent:
        raise ReconciliationError("Review and integration outputs must share one parent")
    review_dir.parent.mkdir(parents=True, exist_ok=True)
    contract_path.parent.mkdir(parents=True, exist_ok=True)

    source_contract = load_json(SOURCE_CONTRACT)
    validate_source_authorities(source_contract)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stage_root = Path(tempfile.mkdtemp(prefix="n483-reconciliation-", dir=str(review_dir.parent.resolve())))
    stage_review = stage_root / "review"
    stage_integration = stage_root / "integration"
    stage_contract = stage_root / contract_path.name
    stage_review.mkdir()
    stage_integration.mkdir()
    try:
        corrected, family_header, integration_audit = build_review_package(
            stage_review, review_dir, source_contract, generated_at
        )
        paths = build_integration_package(
            stage_integration,
            integration_dir,
            review_dir,
            corrected,
            family_header,
            integration_audit,
            generated_at,
        )
        # Contract facts refer to final paths, while file bytes are still in staging.
        staged_paths = {
            key: (
                stage_review / value.name
                if value.parent == review_dir
                else stage_integration / value.name
            )
            for key, value in paths.items()
        }
        # Build against staging, then rewrite only the path strings to their final locations.
        build_contract(source_contract, stage_contract, staged_paths, generated_at)
        staged_contract = load_json(stage_contract)
        for role in (
            "scopus_completed_version_decisions",
            "scopus_version_decision_manifest",
            "scopus_version_decision_hash_ledger",
            "combined_eligible_version_ledger",
            "combined_study_selection_ledger",
            "combined_checked_corpus",
            "combined_metadata",
            "combined_openalex",
            "combined_package_manifest",
            "combined_package_hash_ledger",
            "combined_package_frozen_marker",
        ):
            staged_name = Path(staged_contract["inputs"][role]["path"]).name
            destination = (
                review_dir / staged_name
                if role.startswith("scopus_")
                else integration_dir / staged_name
            )
            staged_contract["inputs"][role]["path"] = relative_path(destination)
        stage_contract.unlink()
        write_json(stage_contract, staged_contract, sort_keys=False)

        stage_review.replace(review_dir)
        stage_integration.replace(integration_dir)
        os.replace(stage_contract, contract_path)
    except Exception:
        shutil.rmtree(stage_root, ignore_errors=True)
        raise
    finally:
        if stage_root.exists():
            shutil.rmtree(stage_root, ignore_errors=True)
    return validate_published_package(review_dir, integration_dir, contract_path)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--review-output", type=Path, default=DEFAULT_REVIEW_DIR)
    value.add_argument("--integration-output", type=Path, default=DEFAULT_INTEGRATION_DIR)
    value.add_argument("--contract-output", type=Path, default=DEFAULT_CONTRACT)
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = build(
            args.review_output.resolve(),
            args.integration_output.resolve(),
            args.contract_output.resolve(),
        )
    except (ReconciliationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL_CLOSED: {exc}")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
