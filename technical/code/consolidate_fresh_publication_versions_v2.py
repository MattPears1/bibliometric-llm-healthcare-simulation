#!/usr/bin/env python3
"""Prepare and finalize conservative post-screen publication-version review.

This workflow starts only from a finalized fresh-V2 record-level screening
package.  It never changes eligibility, never uses E8 as an exclusion, and
never collapses records automatically.  ``prepare`` creates tamper-evident
pair and all-record decision templates.  ``finalize`` requires every detected
pair and every eligible record to have a complete reviewed decision, then
emits a version ledger and one-preferred-version-per-work analysis corpus.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from finalize_fresh_screening_v2 import (
    FINALIZED_WITH_HUMAN_AUDIT_DEFERRED_STATUS,
    FINALIZED_WITH_HUMAN_AUDIT_STATUS,
    FINAL_FIELDS,
    HUMAN_AUDIT_DEFERRAL_OUTPUT,
    POST_ELIGIBILITY_VERSION_FIELDS,
    load_human_audit_deferral,
)
from compare_fresh_independent_reviews_v2 import HUMAN_AUDIT_LINK_FIELDS
from fresh_screening_review_common_v2 import (
    DEFAULT_CODEBOOK,
    EXCLUSION_CODES,
    FreshReviewError,
    UNCERTAIN_CODES,
    VALID_CONFIDENCE,
    VALID_DECISIONS,
    canonical_json,
    file_entry,
    read_csv,
    safe_relative,
    sha256_file,
    sha256_text,
    validate_file_entry,
    validate_locked_codebook,
    validate_sha256,
    write_csv,
)


SCHEMA_VERSION = "fresh-publication-version-consolidation-v2.0"
PREPARE_PIPELINE = "fresh_v2_publication_version_review_preparation"
FINAL_PIPELINE = "fresh_v2_publication_version_consolidation"
FINALIZATION_PIPELINE = "fresh_v2_record_level_screening_finalization"
FINALIZATION_STATUS = FINALIZED_WITH_HUMAN_AUDIT_STATUS
FINALIZATION_DEFERRED_STATUS = FINALIZED_WITH_HUMAN_AUDIT_DEFERRED_STATUS
FINAL_STATUS = "publication_version_consolidation_finalized_analysis_unit_ready"

FINALIZATION_MANIFEST = "SCREENING_FINALIZATION_MANIFEST_V2.json"
FINALIZATION_HASH_LEDGER = "SCREENING_FINALIZATION_HASH_MANIFEST_V2.csv"
REVIEW_MANIFEST = "PUBLICATION_VERSION_REVIEW_MANIFEST_V2.json"
REVIEW_HASH_LEDGER = "PUBLICATION_VERSION_REVIEW_HASH_MANIFEST_V2.csv"
REVIEW_FROZEN_MARKER = "PUBLICATION_VERSION_REVIEW_FROZEN_V2.json"
PAIR_TEMPLATE = "VERSION_CANDIDATE_PAIR_DECISIONS_TEMPLATE_V2.csv"
FAMILY_TEMPLATE = "VERSION_FAMILY_DECISIONS_TEMPLATE_V2.csv"
REVIEW_SUMMARY = "PUBLICATION_VERSION_REVIEW_PREPARATION_SUMMARY_V2.json"

PAIR_DECISIONS_USED = "VERSION_CANDIDATE_PAIR_DECISIONS_USED_V2.csv"
FAMILY_DECISIONS_USED = "VERSION_FAMILY_DECISIONS_USED_V2.csv"
PRESERVED_SCREENING = "ALL_RECORD_LEVEL_SCREENING_PRESERVED_V2.csv"
VERSION_LEDGER = "ELIGIBLE_PUBLICATION_VERSION_LEDGER_V2.csv"
ANALYSIS_CORPUS = "ONE_WORK_ANALYSIS_CORPUS_V2.csv"
FINAL_SUMMARY = "PUBLICATION_VERSION_CONSOLIDATION_SUMMARY_V2.json"
FINAL_MANIFEST = "PUBLICATION_VERSION_CONSOLIDATION_MANIFEST_V2.json"
FINAL_HASH_LEDGER = "PUBLICATION_VERSION_CONSOLIDATION_HASH_MANIFEST_V2.csv"
FINAL_FROZEN_MARKER = "PUBLICATION_VERSION_CONSOLIDATION_FROZEN_V2.json"

PIPELINE_DIR = Path(__file__).resolve().parent
DEPENDENCY_PATHS = {
    "fresh_screening_review_common_v2.py": PIPELINE_DIR
    / "fresh_screening_review_common_v2.py",
    "finalize_fresh_screening_v2.py": PIPELINE_DIR / "finalize_fresh_screening_v2.py",
    "compare_fresh_independent_reviews_v2.py": PIPELINE_DIR
    / "compare_fresh_independent_reviews_v2.py",
}

PROTECTED_ROOT_NAMES = {
    "old_archive",
    "current_gse",
    "journal_route",
    "other_copies",
    "publisher",
}

PAIR_DECISION_FIELDS = [
    "relationship_decision",
    "relationship_type",
    "decision_rationale",
    "evidence_locator_1",
    "evidence_locator_2",
    "reviewed_by",
    "reviewed_at_utc",
]
PAIR_PROTECTED_FIELDS = [
    "schema_version",
    "source_finalization_manifest_sha256",
    "pair_id",
    "paper_id_a",
    "doi_a",
    "title_a",
    "authors_a",
    "year_a",
    "publication_date_a",
    "journal_a",
    "record_type_a",
    "abstract_a",
    "url_a",
    "paper_id_b",
    "doi_b",
    "title_b",
    "authors_b",
    "year_b",
    "publication_date_b",
    "journal_b",
    "record_type_b",
    "abstract_b",
    "url_b",
    "candidate_reasons",
    "title_similarity",
    "shared_author_tokens",
    "year_gap",
    "finalizer_relationship_ids",
]
PAIR_FIELDS = PAIR_PROTECTED_FIELDS + ["pair_evidence_sha256"] + PAIR_DECISION_FIELDS

FAMILY_DECISION_FIELDS = [
    "review_family_label",
    "family_status",
    "version_role",
    "preferred_for_analysis",
    "preferred_paper_id",
    "preferred_basis",
    "relationship_to_preferred",
    "family_link_review_basis",
    "family_membership_rationale",
    "family_evidence_locator",
    "preferred_selection_rationale",
    "preferred_selection_evidence",
    "reviewed_by",
    "reviewed_at_utc",
]
FAMILY_PROTECTED_FIELDS = [
    "schema_version",
    "source_finalization_manifest_sha256",
    "paper_id",
    "doi",
    "title",
    "authors",
    "year",
    "publication_date",
    "journal",
    "record_type",
    "abstract",
    "url",
    "candidate_pair_ids",
    "record_level_row_sha256",
]
FAMILY_FIELDS = (
    FAMILY_PROTECTED_FIELDS + ["record_evidence_sha256"] + FAMILY_DECISION_FIELDS
)

SAME_DECISION = "SAME_SCHOLARLY_WORK_VERSION"
DISTINCT_DECISION = "DISTINCT_SCHOLARLY_WORK"
PAIR_DECISIONS = {SAME_DECISION, DISTINCT_DECISION}
SAME_RELATIONSHIPS = {
    "preprint_to_journal",
    "conference_to_journal",
    "correction_of",
    "supplement_of",
    "translated_version",
    "updated_version",
    "other_version",
}
DISTINCT_RELATIONSHIPS = {
    "companion_report",
    "different_study",
    "same_topic_only",
    "other_distinct_work",
}
FAMILY_STATUSES = {"SINGLETON_WORK", "LINKED_VERSION_FAMILY"}
VERSION_ROLES = {
    "standalone_publication",
    "final_journal_article",
    "preprint",
    "conference_full_paper",
    "conference_abstract",
    "correction",
    "supplement",
    "translated_publication",
    "other_version",
}
PREFERRED_BASES = {
    "only_eligible_version",
    "final_most_complete_publication",
    "most_complete_available_report",
    "corrected_or_updated_publication",
    "other_evidence_based_choice",
}
RELATIONSHIPS_TO_PREFERRED = {
    "self_preferred",
    "preprint_of",
    "conference_version_of",
    "correction_of",
    "supplement_to",
    "translated_version_of",
    "earlier_version_of",
    "later_version_of",
    "other_version_of",
}
FAMILY_LINK_REVIEW_BASES = {
    "singleton_systematic_check",
    "candidate_pair_review",
    "manual_systematic_relationship_check",
}

LEDGER_AUDIT_FIELDS = [
    "version_family_id",
    "review_family_label",
    "family_size",
    "family_members_sha256",
    "record_level_row_sha256",
    "version_role",
    "preferred_for_analysis",
    "preferred_paper_id",
    "preferred_basis",
    "relationship_to_preferred",
    "family_link_review_basis",
    "family_membership_rationale",
    "family_evidence_locator",
    "preferred_selection_rationale",
    "preferred_selection_evidence",
    "reviewed_by",
    "reviewed_at_utc",
    "candidate_pair_ids",
    "same_version_pair_ids",
    "distinct_work_pair_ids",
    "source_finalization_manifest_sha256",
    "source_review_manifest_sha256",
]
LEDGER_FIELDS = [
    "version_family_id",
    "review_family_label",
    "family_size",
    "family_members_sha256",
    "paper_id",
    "doi",
    "title",
    "year",
    "publication_date",
    "authors",
    "journal",
    "record_type",
    "url",
    "final_decision",
    "final_primary_code",
    "record_level_row_sha256",
    "version_role",
    "preferred_for_analysis",
    "preferred_paper_id",
    "preferred_basis",
    "relationship_to_preferred",
    "family_link_review_basis",
    "family_membership_rationale",
    "family_evidence_locator",
    "preferred_selection_rationale",
    "preferred_selection_evidence",
    "reviewed_by",
    "reviewed_at_utc",
    "candidate_pair_ids",
    "same_version_pair_ids",
    "distinct_work_pair_ids",
    "source_finalization_manifest_sha256",
    "source_review_manifest_sha256",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "using",
    "with",
}


class VersionConsolidationError(FreshReviewError):
    """Raised when the post-screen version-review contract is violated."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _assert_fresh_path(path: Path, *, role: str) -> None:
    lowered = {part.casefold() for part in path.resolve().parts}
    blocked = sorted(lowered & PROTECTED_ROOT_NAMES)
    if blocked:
        raise VersionConsolidationError(
            f"{role} path is inside protected historical/frozen material: {path}"
        )


def _ensure_new_output(output: Path, *immutable_roots: Path) -> Path:
    resolved = output.resolve()
    _assert_fresh_path(resolved, role="Output")
    if resolved.exists():
        raise VersionConsolidationError(
            f"Output already exists; refusing to overwrite or append: {resolved}"
        )
    for root in immutable_roots:
        if _within(resolved, root):
            raise VersionConsolidationError(
                f"Output must not be inside immutable input directory: {root.resolve()}"
            )
    return resolved


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersionConsolidationError(f"Invalid JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise VersionConsolidationError(f"Expected a JSON object: {path}")
    return value


def _validate_manifested_file(
    root: Path, entry: Mapping[str, Any], *, label: str
) -> Path:
    try:
        return validate_file_entry(root, entry, label=label)
    except FreshReviewError as exc:
        raise VersionConsolidationError(str(exc)) from exc


def _validate_codebook(codebook: Path) -> tuple[Path, str]:
    try:
        return validate_locked_codebook(codebook)
    except FreshReviewError as exc:
        raise VersionConsolidationError(str(exc)) from exc


def _read_exact_csv(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    observed_fields, rows = read_csv(path)
    if observed_fields != list(fields):
        raise VersionConsolidationError(
            f"{path}: unexpected CSV schema/order; expected {list(fields)}, "
            f"observed {observed_fields}"
        )
    for number, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            raise VersionConsolidationError(f"{path}:{number}: malformed CSV row")
    return rows


def _validate_hash_ledger(
    root: Path,
    filename: str,
    *,
    required_output_paths: Iterable[str] = (),
) -> None:
    path = root / filename
    rows = _read_exact_csv(path, ["scope", "path", "role", "bytes", "sha256"])
    seen: set[tuple[str, str, str]] = set()
    observed_output_paths: set[str] = set()
    for row in rows:
        key = (row["scope"], row["path"], row["role"])
        if key in seen:
            raise VersionConsolidationError(f"{path}: duplicate hash-ledger row {key}")
        seen.add(key)
        if row["scope"] != "output":
            continue
        observed_output_paths.add(row["path"].replace("\\", "/"))
        try:
            target = safe_relative(root, row["path"], label="output hash-ledger")
        except FreshReviewError as exc:
            raise VersionConsolidationError(str(exc)) from exc
        if not target.is_file():
            raise VersionConsolidationError(f"Hash-ledger target is missing: {target}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise VersionConsolidationError(
                f"{path}: invalid byte count for {row['path']}"
            ) from exc
        if (
            target.stat().st_size != expected_bytes
            or sha256_file(target).casefold() != row["sha256"].casefold()
        ):
            raise VersionConsolidationError(f"Hash-ledger mismatch: {target}")
    missing = {
        path.replace("\\", "/") for path in required_output_paths
    } - observed_output_paths
    if missing:
        raise VersionConsolidationError(
            f"{path}: required output rows are missing from hash ledger: {sorted(missing)}"
        )


def _validate_review_code_ledger(root: Path) -> None:
    path = root / REVIEW_HASH_LEDGER
    rows = _read_exact_csv(path, ["scope", "path", "role", "bytes", "sha256"])
    expected_paths = {Path(__file__).name: Path(__file__), **DEPENDENCY_PATHS}
    code_rows = {
        row["path"]: row
        for row in rows
        if row["scope"] == "code"
        and row["role"]
        in {"version_consolidation_program", "version_consolidation_dependency"}
    }
    if set(code_rows) != set(expected_paths):
        raise VersionConsolidationError(
            "Version-review hash ledger does not bind the complete program dependency set"
        )
    for name, code_path in expected_paths.items():
        row = code_rows[name]
        if (
            row["sha256"].casefold() != sha256_file(code_path).casefold()
            or row["bytes"] != str(code_path.stat().st_size)
        ):
            raise VersionConsolidationError(
                f"Version-review dependency code changed: {name}"
            )


def _decision_code_fields(row: Mapping[str, str]) -> Iterable[tuple[str, str]]:
    for field, value in row.items():
        if field.endswith("primary_code") or field in {
            "reviewer_A_primary_code",
            "reviewer_B_primary_code",
        }:
            yield field, clean(value)


def _source_binding(paths: Iterable[Path]) -> dict[str, str]:
    return {str(path.resolve()): sha256_file(path.resolve()) for path in paths}


def _dependency_hashes() -> dict[str, str]:
    missing = [name for name, path in DEPENDENCY_PATHS.items() if not path.is_file()]
    if missing:
        raise VersionConsolidationError(
            f"Required version-workflow dependency files are missing: {missing}"
        )
    return {
        name: sha256_file(path) for name, path in sorted(DEPENDENCY_PATHS.items())
    }


def _verify_binding(binding: Mapping[str, str], *, label: str) -> None:
    for raw_path, expected in binding.items():
        path = Path(raw_path)
        if not path.is_file() or sha256_file(path) != expected:
            raise VersionConsolidationError(f"{label} changed during processing: {path}")


def load_finalization_package(
    finalization_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
) -> dict[str, Any]:
    root = finalization_dir.resolve()
    _assert_fresh_path(root, role="Finalization input")
    if not root.is_dir():
        raise VersionConsolidationError(
            f"Finalization directory does not exist: {root}"
        )
    codebook_path, codebook_sha = _validate_codebook(codebook)
    manifest_path = root / FINALIZATION_MANIFEST
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != "fresh-screening-finalization-manifest-v2.0":
        raise VersionConsolidationError("Unsupported screening-finalization schema")
    if manifest.get("pipeline") != FINALIZATION_PIPELINE:
        raise VersionConsolidationError(
            "Input is not the fresh V2 record-level finalization package"
        )
    finalization_status = manifest.get("status")
    if finalization_status not in {FINALIZATION_STATUS, FINALIZATION_DEFERRED_STATUS}:
        raise VersionConsolidationError(
            "Publication-version review requires resolved record-level decisions with "
            "either a completed prospective human audit or an explicit author deferral; "
            "provisional screening is rejected"
        )
    human_audit_mode = (
        "completed_prospective_human_audit"
        if finalization_status == FINALIZATION_STATUS
        else "explicit_author_deferral"
    )
    contracts = manifest.get("contracts") or {}
    required_contracts = {
        "prospective_human_audit_linked": human_audit_mode
        == "completed_prospective_human_audit",
        "prospective_human_audit_deferred_by_author": human_audit_mode
        == "explicit_author_deferral",
        "human_reference_standard_available": False,
        "screening_sensitivity_or_specificity_claim_permitted": False,
        "model_agreement_may_be_reported_as_human_reliability": False,
        "retired_E8_allowed": False,
        "possible_version_of_used_as_exclusion": False,
        "automatic_version_collapse": False,
        "analysis_unit_ready": False,
        "systematic_version_review_still_required": True,
    }
    for key, expected in required_contracts.items():
        if contracts.get(key) is not expected:
            raise VersionConsolidationError(
                f"Finalization contract {key!r} must be {expected!r}"
            )
    manifested_codebook = ((manifest.get("inputs") or {}).get("codebook") or {})
    if clean(manifested_codebook.get("sha256")).casefold() != codebook_sha.casefold():
        raise VersionConsolidationError(
            "Finalization package is not bound to the locked fresh-V2 codebook"
        )

    outputs = manifest.get("outputs") or {}
    final_path = _validate_manifested_file(
        root,
        outputs.get("final_record_level_screening") or {},
        label="final record-level screening",
    )
    included_path = _validate_manifested_file(
        root,
        outputs.get("final_included_records") or {},
        label="final included record versions",
    )
    queue_path = _validate_manifested_file(
        root,
        outputs.get("post_eligibility_version_review_queue") or {},
        label="post-eligibility version queue",
    )
    summary_path = _validate_manifested_file(
        root, outputs.get("summary") or {}, label="screening finalization summary"
    )
    human_path = _validate_manifested_file(
        root,
        outputs.get("human_audit_linkage_used") or {},
        label="human-audit linkage used",
    )
    deferral_path: Path | None = None
    deferral_note_path: Path | None = None
    deferral_entry = outputs.get("human_audit_deferral_used")
    if human_audit_mode == "explicit_author_deferral":
        deferral_path = _validate_manifested_file(
            root,
            deferral_entry or {},
            label="explicit author human-audit deferral",
        )
        try:
            _, validated_deferral_path, validated_note_path = load_human_audit_deferral(
                deferral_path
            )
        except FreshReviewError as exc:
            raise VersionConsolidationError(str(exc)) from exc
        if validated_deferral_path != deferral_path:
            raise VersionConsolidationError("Human-audit deferral path did not resolve exactly")
        deferral_note_path = _validate_manifested_file(
            root,
            outputs.get("human_audit_deferral_source_note_used") or {},
            label="human-readable author human-audit deferral",
        )
        if validated_note_path != deferral_note_path:
            raise VersionConsolidationError(
                "Human-audit deferral does not bind the manifested source note"
            )
    elif deferral_entry is not None:
        raise VersionConsolidationError(
            "A completed-human-audit package must not also contain a deferral record"
        )
    _validate_hash_ledger(
        root,
        FINALIZATION_HASH_LEDGER,
        required_output_paths=(
            final_path.name,
            included_path.name,
            queue_path.name,
            human_path.name,
            summary_path.name,
            FINALIZATION_MANIFEST,
            *((deferral_path.name,) if deferral_path is not None else ()),
            *((deferral_note_path.name,) if deferral_note_path is not None else ()),
        ),
    )

    final_rows = _read_exact_csv(final_path, FINAL_FIELDS)
    included_rows = _read_exact_csv(included_path, FINAL_FIELDS)
    queue_rows = _read_exact_csv(queue_path, POST_ELIGIBILITY_VERSION_FIELDS)
    human_rows = _read_exact_csv(human_path, HUMAN_AUDIT_LINK_FIELDS)
    ids = [row["paper_id"] for row in final_rows]
    if any(not paper_id for paper_id in ids) or len(ids) != len(set(ids)):
        raise VersionConsolidationError(
            "Final record-level screening contains blank or duplicate paper_id values"
        )
    for row in final_rows:
        decision = row["final_decision"]
        code = row["final_primary_code"]
        if decision == "INCLUDE" and code != "INCLUDE":
            raise VersionConsolidationError(
                f"{row['paper_id']}: INCLUDE must retain primary code INCLUDE"
            )
        if decision == "EXCLUDE" and code not in EXCLUSION_CODES:
            raise VersionConsolidationError(
                f"{row['paper_id']}: invalid final exclusion code {code!r}"
            )
        if decision not in {"INCLUDE", "EXCLUDE"}:
            raise VersionConsolidationError(
                f"{row['paper_id']}: unresolved final decision {decision!r}"
            )
        for field, value in _decision_code_fields(row):
            if value.casefold().startswith("e8"):
                raise VersionConsolidationError(
                    f"{row['paper_id']}: retired E8 appears in {field}; version review "
                    "must never be represented as a screening exclusion"
                )
    expected_included = [row for row in final_rows if row["final_decision"] == "INCLUDE"]
    if included_rows != expected_included:
        raise VersionConsolidationError(
            "FINAL_INCLUDED_RECORDS_V2.csv is not the exact ordered INCLUDE projection"
        )
    if [row["paper_id"] for row in human_rows] != ids:
        raise VersionConsolidationError(
            "Human-audit linkage must retain every final record in the same order"
        )
    seen_human_audit_ids: set[str] = set()
    audited_count = 0
    human_result_fields = HUMAN_AUDIT_LINK_FIELDS[4:]
    for final_row, human_row in zip(final_rows, human_rows):
        paper_id = final_row["paper_id"]
        if any(value != value.strip() for value in human_row.values()):
            raise VersionConsolidationError(
                f"{paper_id}: human-audit linkage contains leading/trailing whitespace"
            )
        expected_linkage = {
            "audit_link_id": final_row["audit_link_id"],
            "paper_id": paper_id,
            "batch": final_row["batch"],
            "candidate_row_sha256": final_row["candidate_row_sha256"],
        }
        for field, expected in expected_linkage.items():
            if human_row[field] != expected:
                raise VersionConsolidationError(
                    f"{paper_id}: human-audit immutable linkage mismatch for {field}"
                )
        populated = [bool(human_row[field]) for field in human_result_fields]
        if any(populated) and not all(populated):
            raise VersionConsolidationError(
                f"{paper_id}: human-audit linkage is only partly completed"
            )
        for field in human_result_fields:
            if human_row[field] != final_row[field]:
                raise VersionConsolidationError(
                    f"{paper_id}: human-audit linkage and final record differ in {field}"
                )
        if not all(populated):
            continue
        audited_count += 1
        audit_id = human_row["human_audit_id"]
        if audit_id in seen_human_audit_ids:
            raise VersionConsolidationError("Duplicate human_audit_id in linkage")
        seen_human_audit_ids.add(audit_id)
        human_decision = human_row["human_decision"]
        human_code = human_row["human_primary_code"]
        if human_decision not in VALID_DECISIONS:
            raise VersionConsolidationError(
                f"{paper_id}: invalid human-audit decision {human_decision!r}"
            )
        valid_human_codes = (
            {"INCLUDE"}
            if human_decision == "INCLUDE"
            else EXCLUSION_CODES
            if human_decision == "EXCLUDE"
            else UNCERTAIN_CODES
        )
        if human_code not in valid_human_codes or human_code.casefold().startswith("e8"):
            raise VersionConsolidationError(
                f"{paper_id}: human-audit decision/code mismatch"
            )
        if human_row["human_confidence"] not in VALID_CONFIDENCE:
            raise VersionConsolidationError(
                f"{paper_id}: invalid human-audit confidence"
            )
        if not validate_sha256(human_row["human_audit_source_sha256"]):
            raise VersionConsolidationError(
                f"{paper_id}: invalid frozen human-audit source SHA-256"
            )
        try:
            datetime.fromisoformat(
                human_row["human_audit_completed_utc"].replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise VersionConsolidationError(
                f"{paper_id}: invalid human-audit completion time"
            ) from exc
    if human_audit_mode == "completed_prospective_human_audit" and audited_count < 1:
        raise VersionConsolidationError(
            "Publication-version review cannot start in completed-audit mode without "
            "a completed human-audit linkage"
        )
    if human_audit_mode == "explicit_author_deferral" and audited_count != 0:
        raise VersionConsolidationError(
            "A human-audit deferral package must not contain invented human-audit rows"
        )
    counts = manifest.get("counts") or {}
    if int(counts.get("records", -1)) != len(final_rows) or int(
        counts.get("included_records", -1)
    ) != len(included_rows):
        raise VersionConsolidationError(
            "Finalization manifest record counts do not match the CSV files"
        )
    if int(counts.get("human_audited_records_linked", -1)) != audited_count:
        raise VersionConsolidationError(
            "Finalization manifest human-audit count does not match the linkage file"
        )
    if int(counts.get("human_audit_deferred_by_author", -1)) != int(
        human_audit_mode == "explicit_author_deferral"
    ):
        raise VersionConsolidationError(
            "Finalization manifest human-audit deferral count does not match its mode"
        )
    by_id = {row["paper_id"]: row for row in final_rows}
    seen_relationships: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for row in queue_rows:
        relationship_id = row["relationship_id"]
        if not relationship_id or relationship_id in seen_relationships:
            raise VersionConsolidationError(
                "Version queue contains blank or duplicate relationship IDs"
            )
        seen_relationships.add(relationship_id)
        if row["source_paper_id"] not in by_id or row["target_paper_id"] not in by_id:
            raise VersionConsolidationError(
                f"{relationship_id}: version queue points outside final screening"
            )
        source_row = by_id[row["source_paper_id"]]
        target_row = by_id[row["target_paper_id"]]
        if source_row["paper_id"] == target_row["paper_id"]:
            raise VersionConsolidationError(
                f"{relationship_id}: a version relationship cannot point to itself"
            )
        pair = tuple(sorted((source_row["paper_id"], target_row["paper_id"])))
        if pair in seen_pairs:
            raise VersionConsolidationError(
                f"{relationship_id}: duplicate relationship pair {pair}"
            )
        seen_pairs.add(pair)
        expected_relationship_id = f"VR2-{sha256_text(chr(0).join(pair))[:24]}"
        if relationship_id != expected_relationship_id:
            raise VersionConsolidationError(
                f"{relationship_id}: expected stable finalizer ID {expected_relationship_id}"
            )
        expected_context = {
            "source_final_decision": source_row["final_decision"],
            "target_final_decision": target_row["final_decision"],
            "source_doi": source_row["doi"],
            "source_title": source_row["title"],
            "target_doi": target_row["doi"],
            "target_title": target_row["title"],
        }
        for field, expected in expected_context.items():
            if row[field] != expected:
                raise VersionConsolidationError(
                    f"{relationship_id}: version queue context mismatch for {field}"
                )
        if source_row["final_decision"] != "INCLUDE":
            raise VersionConsolidationError(
                f"{relationship_id}: queue source must be an eligible record"
            )
        if any(
            clean(row[field])
            for field in (
                "relationship_decision",
                "canonical_work_id",
                "relationship_rationale",
                "evidence_locator_1",
                "evidence_locator_2",
            )
        ):
            raise VersionConsolidationError(
                "The finalizer version queue must remain unresolved/frozen"
            )
    summary = _load_json(summary_path)
    if summary.get("status") != finalization_status:
        raise VersionConsolidationError(
            "Finalization summary and manifest statuses do not agree"
        )
    if int(summary.get("human_audited_records_linked", -1)) != audited_count:
        raise VersionConsolidationError(
            "Finalization summary human-audit count does not match the linkage file"
        )
    if bool(summary.get("human_audit_deferred_by_author")) is not (
        human_audit_mode == "explicit_author_deferral"
    ):
        raise VersionConsolidationError(
            "Finalization summary human-audit deferral state does not match the manifest"
        )
    bound_paths = [
        codebook_path,
        manifest_path,
        final_path,
        included_path,
        queue_path,
        human_path,
        summary_path,
        root / FINALIZATION_HASH_LEDGER,
    ]
    if deferral_path is not None:
        bound_paths.extend([deferral_path, deferral_note_path])
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "codebook_path": codebook_path,
        "codebook_sha256": codebook_sha,
        "final_path": final_path,
        "included_path": included_path,
        "queue_path": queue_path,
        "human_path": human_path,
        "human_rows": human_rows,
        "human_audited_records_linked": audited_count,
        "human_audit_mode": human_audit_mode,
        "human_audit_deferral_path": deferral_path,
        "human_audit_deferral_note_path": deferral_note_path,
        "summary_path": summary_path,
        "final_rows": final_rows,
        "included_rows": included_rows,
        "queue_rows": queue_rows,
        "final_by_id": by_id,
        "binding": _source_binding(bound_paths),
    }


def normalize_doi(value: Any) -> str:
    text = clean(value).casefold()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().rstrip(".")


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", clean(value)).casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def title_tokens(value: Any) -> set[str]:
    return {
        token
        for token in normalize_text(value).split()
        if token not in STOPWORDS and len(token) > 1
    }


def author_tokens(value: Any) -> set[str]:
    result: set[str] = set()
    for author in re.split(r"\s*;\s*", clean(value)):
        tokens = re.findall(r"[a-z][a-z'-]+", normalize_text(author))
        if tokens:
            result.add(tokens[-1])
    return result


def _year(value: Any) -> int | None:
    text = clean(value)
    return int(text) if re.fullmatch(r"\d{4}", text) else None


def _title_similarity(left: Mapping[str, str], right: Mapping[str, str]) -> float:
    left_text, right_text = normalize_text(left["title"]), normalize_text(right["title"])
    if not left_text or not right_text:
        return 0.0
    char_similarity = SequenceMatcher(None, left_text, right_text, autojunk=False).ratio()
    left_tokens, right_tokens = title_tokens(left_text), title_tokens(right_text)
    union = left_tokens | right_tokens
    jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
    return max(char_similarity, jaccard)


def _pair_id(manifest_sha: str, left: str, right: str) -> str:
    first, second = sorted((left, right))
    return f"PVR2-{sha256_text(chr(0).join((manifest_sha, first, second)))[:24]}"


def _evidence_hash(prefix: str, fields: Sequence[str], row: Mapping[str, Any]) -> str:
    payload = {field: clean(row.get(field)) for field in fields}
    return sha256_text(f"{prefix}\0{canonical_json(payload)}")


def build_candidate_pairs(source: Mapping[str, Any]) -> list[dict[str, str]]:
    included = source["included_rows"]
    included_by_id = {row["paper_id"]: row for row in included}
    doi_owner: dict[str, str] = {}
    for row in included:
        doi = normalize_doi(row["doi"])
        if doi and doi in doi_owner:
            raise VersionConsolidationError(
                "Eligible records share an exact DOI, which is an upstream technical-"
                f"deduplication problem: {doi_owner[doi]} and {row['paper_id']} ({doi})"
            )
        if doi:
            doi_owner[doi] = row["paper_id"]

    flagged: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    for queue_row in source["queue_rows"]:
        left, right = sorted(
            (queue_row["source_paper_id"], queue_row["target_paper_id"])
        )
        if left in included_by_id and right in included_by_id:
            flagged[(left, right)].append(queue_row["relationship_id"])

    output: list[dict[str, str]] = []
    for left, right in combinations(included, 2):
        left_id, right_id = sorted((left["paper_id"], right["paper_id"]))
        if left_id != left["paper_id"]:
            left, right = right, left
        pair_key = (left_id, right_id)
        reasons: list[str] = []
        relationship_ids = sorted(flagged.get(pair_key, []))
        if relationship_ids:
            reasons.append("independent_reviewer_version_flag")
        similarity = _title_similarity(left, right)
        shared_authors = sorted(author_tokens(left["authors"]) & author_tokens(right["authors"]))
        left_year, right_year = _year(left["year"]), _year(right["year"])
        gap = abs(left_year - right_year) if left_year is not None and right_year is not None else None
        exact_title = bool(normalize_text(left["title"])) and normalize_text(
            left["title"]
        ) == normalize_text(right["title"])
        if exact_title and shared_authors and (gap is None or gap <= 5):
            reasons.append("exact_title_plus_shared_author")
        elif similarity >= 0.84 and shared_authors and gap is not None and gap <= 5:
            reasons.append("high_title_author_date_similarity")
        if not reasons:
            continue
        row: dict[str, str] = {
            "schema_version": SCHEMA_VERSION,
            "source_finalization_manifest_sha256": source["manifest_sha256"],
            "pair_id": _pair_id(source["manifest_sha256"], left_id, right_id),
            "paper_id_a": left_id,
            "doi_a": left["doi"],
            "title_a": left["title"],
            "authors_a": left["authors"],
            "year_a": left["year"],
            "publication_date_a": left["publication_date"],
            "journal_a": left["journal"],
            "record_type_a": left["record_type"],
            "abstract_a": left["abstract"],
            "url_a": left["url"],
            "paper_id_b": right_id,
            "doi_b": right["doi"],
            "title_b": right["title"],
            "authors_b": right["authors"],
            "year_b": right["year"],
            "publication_date_b": right["publication_date"],
            "journal_b": right["journal"],
            "record_type_b": right["record_type"],
            "abstract_b": right["abstract"],
            "url_b": right["url"],
            "candidate_reasons": ";".join(sorted(set(reasons))),
            "title_similarity": f"{similarity:.6f}",
            "shared_author_tokens": ";".join(shared_authors),
            "year_gap": "" if gap is None else str(gap),
            "finalizer_relationship_ids": ";".join(relationship_ids),
        }
        row["pair_evidence_sha256"] = _evidence_hash(
            "fresh-v2-version-pair-evidence", PAIR_PROTECTED_FIELDS, row
        )
        row.update({field: "" for field in PAIR_DECISION_FIELDS})
        output.append(row)
    return sorted(output, key=lambda row: (row["paper_id_a"], row["paper_id_b"]))


def build_family_template_rows(
    source: Mapping[str, Any], pair_rows: Sequence[Mapping[str, str]]
) -> list[dict[str, str]]:
    pairs_by_id: defaultdict[str, list[str]] = defaultdict(list)
    for pair in pair_rows:
        pairs_by_id[pair["paper_id_a"]].append(pair["pair_id"])
        pairs_by_id[pair["paper_id_b"]].append(pair["pair_id"])
    rows: list[dict[str, str]] = []
    for record in source["included_rows"]:
        row: dict[str, str] = {
            "schema_version": SCHEMA_VERSION,
            "source_finalization_manifest_sha256": source["manifest_sha256"],
            "paper_id": record["paper_id"],
            "doi": record["doi"],
            "title": record["title"],
            "authors": record["authors"],
            "year": record["year"],
            "publication_date": record["publication_date"],
            "journal": record["journal"],
            "record_type": record["record_type"],
            "abstract": record["abstract"],
            "url": record["url"],
            "candidate_pair_ids": ";".join(sorted(pairs_by_id[record["paper_id"]])),
            "record_level_row_sha256": sha256_text(canonical_json(dict(record))),
        }
        row["record_evidence_sha256"] = _evidence_hash(
            "fresh-v2-version-record-evidence", FAMILY_PROTECTED_FIELDS, row
        )
        row.update({field: "" for field in FAMILY_DECISION_FIELDS})
        rows.append(row)
    return rows


def _write_hash_ledger(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    ordered = sorted(rows, key=lambda row: (row["scope"], row["path"], row["role"]))
    write_csv(path, ordered, ["scope", "path", "role", "bytes", "sha256"])


def prepare_review_package(
    finalization_dir: Path,
    output_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
) -> Mapping[str, Any]:
    source = load_finalization_package(finalization_dir, codebook=codebook)
    output = _ensure_new_output(output_dir, source["root"])
    pair_rows = build_candidate_pairs(source)
    family_rows = build_family_template_rows(source, pair_rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        pair_path = temp / PAIR_TEMPLATE
        family_path = temp / FAMILY_TEMPLATE
        summary_path = temp / REVIEW_SUMMARY
        write_csv(pair_path, pair_rows, PAIR_FIELDS)
        write_csv(family_path, family_rows, FAMILY_FIELDS)
        reason_counts = Counter(
            reason
            for row in pair_rows
            for reason in row["candidate_reasons"].split(";")
            if reason
        )
        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "status": "frozen_blank_version_review_package_ready",
            "record_level_inclusions": len(source["included_rows"]),
            "candidate_pairs_requiring_review": len(pair_rows),
            "candidate_reason_counts": dict(sorted(reason_counts.items())),
            "all_eligible_records_require_family_decision": True,
            "automatic_version_collapse": False,
            "analysis_unit_ready": False,
            "human_audit_mode": source["human_audit_mode"],
            "note": (
                "Candidate rules identify relationships for review only. Every eligible "
                "record still requires an explicit family decision, and title similarity "
                "alone never establishes a version relationship."
            ),
        }
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        outputs = {
            "pair_decision_template": file_entry(
                pair_path, temp, "blank_candidate_pair_decision_template"
            ),
            "family_decision_template": file_entry(
                family_path, temp, "blank_all_eligible_record_family_template"
            ),
            "summary": file_entry(summary_path, temp, "review_preparation_summary"),
        }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "pipeline": PREPARE_PIPELINE,
            "status": "frozen_blank_version_review_package_ready",
            "source": {
                "finalization_directory_name": source["root"].name,
                "finalization_manifest_sha256": source["manifest_sha256"],
                "final_record_level_screening_sha256": sha256_file(source["final_path"]),
                "final_included_records_sha256": sha256_file(source["included_path"]),
                "post_eligibility_queue_sha256": sha256_file(source["queue_path"]),
                "human_audit_linkage_sha256": sha256_file(source["human_path"]),
                "human_audit_mode": source["human_audit_mode"],
                "human_audit_deferral_sha256": (
                    sha256_file(source["human_audit_deferral_path"])
                    if source["human_audit_deferral_path"] is not None
                    else None
                ),
                "human_audit_deferral_note_sha256": (
                    sha256_file(source["human_audit_deferral_note_path"])
                    if source["human_audit_deferral_note_path"] is not None
                    else None
                ),
                "codebook_sha256": source["codebook_sha256"],
            },
            "counts": {
                "all_record_level_rows": len(source["final_rows"]),
                "eligible_record_versions": len(source["included_rows"]),
                "candidate_pairs": len(pair_rows),
            },
            "contracts": {
                "record_level_eligibility_is_immutable": True,
                "retired_E8_allowed": False,
                "title_similarity_alone_can_link_versions": False,
                "automatic_version_collapse": False,
                "all_candidate_pairs_must_be_reviewed": True,
                "all_eligible_records_must_receive_family_decision": True,
                "one_preferred_analytical_version_per_family_required": True,
                "unresolved_relationships_allowed_at_finalization": False,
                "analysis_unit_ready": False,
                "prospective_human_audit_linked": source["human_audit_mode"]
                == "completed_prospective_human_audit",
                "prospective_human_audit_deferred_by_author": source["human_audit_mode"]
                == "explicit_author_deferral",
                "human_validation_claims_permitted": False,
            },
            "outputs": outputs,
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "dependencies": _dependency_hashes(),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp / REVIEW_MANIFEST
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        hash_rows: list[dict[str, Any]] = []
        for scope, path, role, display in (
            ("code", Path(__file__), "version_consolidation_program", Path(__file__).name),
            ("input", source["codebook_path"], "locked_screening_codebook", str(source["codebook_path"])),
            ("input", source["manifest_path"], "screening_finalization_manifest", str(source["manifest_path"])),
            ("input", source["final_path"], "all_record_level_screening", str(source["final_path"])),
            ("input", source["included_path"], "eligible_record_versions", str(source["included_path"])),
            ("input", source["queue_path"], "model_flagged_version_queue", str(source["queue_path"])),
            ("input", source["human_path"], "human_audit_linkage_or_blank_audit_trail", str(source["human_path"])),
            ("output", pair_path, "blank_pair_decision_template", pair_path.name),
            ("output", family_path, "blank_family_decision_template", family_path.name),
            ("output", summary_path, "review_preparation_summary", summary_path.name),
            ("output", manifest_path, "version_review_manifest", manifest_path.name),
        ):
            hash_rows.append(
                {
                    "scope": scope,
                    "path": display,
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for path, role in (
            (
                source["human_audit_deferral_path"],
                "explicit_author_human_audit_deferral",
            ),
            (
                source["human_audit_deferral_note_path"],
                "human_readable_author_human_audit_deferral",
            ),
        ):
            if path is None:
                continue
            hash_rows.append(
                {
                    "scope": "input",
                    "path": str(path),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for dependency_name, dependency_path in sorted(DEPENDENCY_PATHS.items()):
            hash_rows.append(
                {
                    "scope": "code",
                    "path": dependency_name,
                    "role": "version_consolidation_dependency",
                    "bytes": dependency_path.stat().st_size,
                    "sha256": sha256_file(dependency_path),
                }
            )
        hash_path = temp / REVIEW_HASH_LEDGER
        _write_hash_ledger(hash_path, hash_rows)
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "status": "frozen_blank_version_review_package_ready",
            "review_manifest_sha256": sha256_file(manifest_path),
            "review_hash_ledger_sha256": sha256_file(hash_path),
            "pair_template_sha256": sha256_file(pair_path),
            "family_template_sha256": sha256_file(family_path),
            "source_finalization_manifest_sha256": source["manifest_sha256"],
            "instruction": (
                "Do not edit this package. Copy both CSV templates outside it, complete "
                "the decision columns, and retain this frozen package for finalization."
            ),
        }
        (temp / REVIEW_FROZEN_MARKER).write_text(
            json.dumps(frozen, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _verify_binding(source["binding"], label="Screening finalization input")
        temp.rename(output)
        return manifest
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise


def load_review_package(
    review_dir: Path,
    finalization_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
) -> dict[str, Any]:
    source = load_finalization_package(finalization_dir, codebook=codebook)
    root = review_dir.resolve()
    _assert_fresh_path(root, role="Version-review package")
    if not root.is_dir():
        raise VersionConsolidationError(f"Version-review package is missing: {root}")
    manifest_path = root / REVIEW_MANIFEST
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get(
        "pipeline"
    ) != PREPARE_PIPELINE:
        raise VersionConsolidationError("Unsupported version-review package")
    if manifest.get("status") != "frozen_blank_version_review_package_ready":
        raise VersionConsolidationError("Version-review package is not frozen/blank")
    source_manifest = manifest.get("source") or {}
    expected_source = {
        "finalization_manifest_sha256": source["manifest_sha256"],
        "final_record_level_screening_sha256": sha256_file(source["final_path"]),
        "final_included_records_sha256": sha256_file(source["included_path"]),
        "post_eligibility_queue_sha256": sha256_file(source["queue_path"]),
        "human_audit_linkage_sha256": sha256_file(source["human_path"]),
        "human_audit_mode": source["human_audit_mode"],
        "human_audit_deferral_sha256": (
            sha256_file(source["human_audit_deferral_path"])
            if source["human_audit_deferral_path"] is not None
            else ""
        ),
        "human_audit_deferral_note_sha256": (
            sha256_file(source["human_audit_deferral_note_path"])
            if source["human_audit_deferral_note_path"] is not None
            else ""
        ),
        "codebook_sha256": source["codebook_sha256"],
    }
    for field, expected in expected_source.items():
        if clean(source_manifest.get(field)).casefold() != expected.casefold():
            raise VersionConsolidationError(
                f"Version-review package source binding mismatch for {field}"
            )
    contracts = manifest.get("contracts") or {}
    required_true = (
        "record_level_eligibility_is_immutable",
        "all_candidate_pairs_must_be_reviewed",
        "all_eligible_records_must_receive_family_decision",
        "one_preferred_analytical_version_per_family_required",
    )
    if any(contracts.get(field) is not True for field in required_true):
        raise VersionConsolidationError("Version-review package contracts are incomplete")
    if contracts.get("retired_E8_allowed") is not False or contracts.get(
        "automatic_version_collapse"
    ) is not False:
        raise VersionConsolidationError("Unsafe version-review package contracts")
    if contracts.get("prospective_human_audit_linked") is not (
        source["human_audit_mode"] == "completed_prospective_human_audit"
    ) or contracts.get("prospective_human_audit_deferred_by_author") is not (
        source["human_audit_mode"] == "explicit_author_deferral"
    ):
        raise VersionConsolidationError("Version-review human-audit mode changed")
    if contracts.get("human_validation_claims_permitted") is not False:
        raise VersionConsolidationError("Version-review package permits unsupported claims")
    outputs = manifest.get("outputs") or {}
    pair_path = _validate_manifested_file(
        root, outputs.get("pair_decision_template") or {}, label="pair template"
    )
    family_path = _validate_manifested_file(
        root, outputs.get("family_decision_template") or {}, label="family template"
    )
    summary_path = _validate_manifested_file(
        root, outputs.get("summary") or {}, label="review preparation summary"
    )
    _validate_hash_ledger(
        root,
        REVIEW_HASH_LEDGER,
        required_output_paths=(
            pair_path.name,
            family_path.name,
            summary_path.name,
            REVIEW_MANIFEST,
        ),
    )
    _validate_review_code_ledger(root)
    script = manifest.get("script") or {}
    if clean(script.get("sha256")).casefold() != sha256_file(Path(__file__)).casefold():
        raise VersionConsolidationError(
            "Version-review package was prepared with different code; regenerate it"
        )
    manifested_dependencies = script.get("dependencies") or {}
    if manifested_dependencies != _dependency_hashes():
        raise VersionConsolidationError(
            "Version-review package dependency code changed; regenerate it"
        )
    frozen_path = root / REVIEW_FROZEN_MARKER
    frozen = _load_json(frozen_path)
    frozen_expected = {
        "review_manifest_sha256": sha256_file(manifest_path),
        "review_hash_ledger_sha256": sha256_file(root / REVIEW_HASH_LEDGER),
        "pair_template_sha256": sha256_file(pair_path),
        "family_template_sha256": sha256_file(family_path),
        "source_finalization_manifest_sha256": source["manifest_sha256"],
    }
    for field, expected in frozen_expected.items():
        if clean(frozen.get(field)).casefold() != expected.casefold():
            raise VersionConsolidationError(
                f"Frozen review marker mismatch for {field}; do not repair in place"
            )
    pair_rows = _read_exact_csv(pair_path, PAIR_FIELDS)
    family_rows = _read_exact_csv(family_path, FAMILY_FIELDS)
    if any(any(clean(row[field]) for field in PAIR_DECISION_FIELDS) for row in pair_rows):
        raise VersionConsolidationError("Frozen pair template contains decision data")
    if any(any(clean(row[field]) for field in FAMILY_DECISION_FIELDS) for row in family_rows):
        raise VersionConsolidationError("Frozen family template contains decision data")
    if [row["paper_id"] for row in family_rows] != [
        row["paper_id"] for row in source["included_rows"]
    ]:
        raise VersionConsolidationError(
            "Family template does not cover eligible records in frozen order"
        )
    expected_pairs = build_candidate_pairs(source)
    if pair_rows != expected_pairs:
        raise VersionConsolidationError(
            "Frozen candidate-pair template cannot be reproduced from finalization input"
        )
    expected_family = build_family_template_rows(source, pair_rows)
    if family_rows != expected_family:
        raise VersionConsolidationError(
            "Frozen family template cannot be reproduced from finalization input"
        )
    bound_paths = [
        Path(__file__),
        *DEPENDENCY_PATHS.values(),
        manifest_path,
        root / REVIEW_HASH_LEDGER,
        frozen_path,
        pair_path,
        family_path,
        summary_path,
    ]
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "pair_path": pair_path,
        "family_path": family_path,
        "pair_rows": pair_rows,
        "family_rows": family_rows,
        "source": source,
        "binding": _source_binding(bound_paths),
    }


def _validate_trimmed(row: Mapping[str, str], path: Path, line: int) -> None:
    for field, value in row.items():
        if value != value.strip():
            raise VersionConsolidationError(
                f"{path}:{line}: leading/trailing whitespace in {field}"
            )


def _parse_review_time(value: str, *, path: Path, paper_or_pair: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise VersionConsolidationError(
            f"{path}: {paper_or_pair} reviewed_at_utc must be YYYY-MM-DDTHH:MM:SSZ"
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise VersionConsolidationError(
            f"{path}: invalid review time for {paper_or_pair}"
        ) from exc


def validate_pair_decisions(
    path: Path, review: Mapping[str, Any]
) -> list[dict[str, str]]:
    resolved = path.resolve()
    if _within(resolved, review["root"]) or _within(resolved, review["source"]["root"]):
        raise VersionConsolidationError(
            "Reviewed pair decisions must be stored outside immutable input packages"
        )
    rows = _read_exact_csv(resolved, PAIR_FIELDS)
    templates = review["pair_rows"]
    if [row["pair_id"] for row in rows] != [row["pair_id"] for row in templates]:
        raise VersionConsolidationError(
            "Reviewed pair decisions must preserve every template row and order"
        )
    for line, (row, template) in enumerate(zip(rows, templates), start=2):
        _validate_trimmed(row, resolved, line)
        for field in PAIR_PROTECTED_FIELDS + ["pair_evidence_sha256"]:
            if row[field] != template[field]:
                raise VersionConsolidationError(
                    f"{resolved}:{line}: protected pair evidence changed in {field}"
                )
        expected_hash = _evidence_hash(
            "fresh-v2-version-pair-evidence", PAIR_PROTECTED_FIELDS, row
        )
        if row["pair_evidence_sha256"] != expected_hash:
            raise VersionConsolidationError(
                f"{resolved}:{line}: pair evidence hash mismatch"
            )
        decision = row["relationship_decision"]
        relationship = row["relationship_type"]
        if decision not in PAIR_DECISIONS:
            raise VersionConsolidationError(
                f"{resolved}:{line}: unresolved/invalid relationship decision {decision!r}"
            )
        valid_relationships = (
            SAME_RELATIONSHIPS if decision == SAME_DECISION else DISTINCT_RELATIONSHIPS
        )
        if relationship not in valid_relationships:
            raise VersionConsolidationError(
                f"{resolved}:{line}: relationship type {relationship!r} does not match {decision}"
            )
        for field in (
            "decision_rationale",
            "evidence_locator_1",
            "reviewed_by",
            "reviewed_at_utc",
        ):
            if not row[field]:
                raise VersionConsolidationError(
                    f"{resolved}:{line}: {field} is required"
                )
        _parse_review_time(
            row["reviewed_at_utc"], path=resolved, paper_or_pair=row["pair_id"]
        )
    return rows


def validate_family_decisions(
    path: Path,
    review: Mapping[str, Any],
    pair_rows: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, str]], dict[str, list[dict[str, str]]]]:
    resolved = path.resolve()
    if _within(resolved, review["root"]) or _within(resolved, review["source"]["root"]):
        raise VersionConsolidationError(
            "Reviewed family decisions must be stored outside immutable input packages"
        )
    rows = _read_exact_csv(resolved, FAMILY_FIELDS)
    templates = review["family_rows"]
    if [row["paper_id"] for row in rows] != [row["paper_id"] for row in templates]:
        raise VersionConsolidationError(
            "Reviewed family decisions must preserve every eligible record and order"
        )
    by_label: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for line, (row, template) in enumerate(zip(rows, templates), start=2):
        _validate_trimmed(row, resolved, line)
        for field in FAMILY_PROTECTED_FIELDS + ["record_evidence_sha256"]:
            if row[field] != template[field]:
                raise VersionConsolidationError(
                    f"{resolved}:{line}: protected record evidence changed in {field}"
                )
        expected_hash = _evidence_hash(
            "fresh-v2-version-record-evidence", FAMILY_PROTECTED_FIELDS, row
        )
        if row["record_evidence_sha256"] != expected_hash:
            raise VersionConsolidationError(
                f"{resolved}:{line}: record evidence hash mismatch"
            )
        required = (
            "review_family_label",
            "family_status",
            "version_role",
            "preferred_for_analysis",
            "preferred_paper_id",
            "preferred_basis",
            "relationship_to_preferred",
            "family_link_review_basis",
            "family_membership_rationale",
            "family_evidence_locator",
            "preferred_selection_rationale",
            "preferred_selection_evidence",
            "reviewed_by",
            "reviewed_at_utc",
        )
        if any(not row[field] for field in required):
            missing = [field for field in required if not row[field]]
            raise VersionConsolidationError(
                f"{resolved}:{line}: incomplete family decision fields {missing}"
            )
        if row["family_status"] not in FAMILY_STATUSES:
            raise VersionConsolidationError(
                f"{resolved}:{line}: invalid family_status {row['family_status']!r}"
            )
        if row["version_role"] not in VERSION_ROLES:
            raise VersionConsolidationError(
                f"{resolved}:{line}: invalid version_role {row['version_role']!r}"
            )
        if row["preferred_for_analysis"] not in {"yes", "no"}:
            raise VersionConsolidationError(
                f"{resolved}:{line}: preferred_for_analysis must be yes or no"
            )
        if row["preferred_basis"] not in PREFERRED_BASES:
            raise VersionConsolidationError(
                f"{resolved}:{line}: invalid preferred_basis {row['preferred_basis']!r}"
            )
        if row["relationship_to_preferred"] not in RELATIONSHIPS_TO_PREFERRED:
            raise VersionConsolidationError(
                f"{resolved}:{line}: invalid relationship_to_preferred"
            )
        if row["family_link_review_basis"] not in FAMILY_LINK_REVIEW_BASES:
            raise VersionConsolidationError(
                f"{resolved}:{line}: invalid family_link_review_basis"
            )
        _parse_review_time(
            row["reviewed_at_utc"], path=resolved, paper_or_pair=row["paper_id"]
        )
        by_label[row["review_family_label"]].append(row)

    paper_to_label = {row["paper_id"]: row["review_family_label"] for row in rows}
    for pair in pair_rows:
        same_label = paper_to_label[pair["paper_id_a"]] == paper_to_label[pair["paper_id_b"]]
        if pair["relationship_decision"] == SAME_DECISION and not same_label:
            raise VersionConsolidationError(
                f"{pair['pair_id']}: SAME_SCHOLARLY_WORK_VERSION records must share a family"
            )
        if pair["relationship_decision"] == DISTINCT_DECISION and same_label:
            raise VersionConsolidationError(
                f"{pair['pair_id']}: DISTINCT_SCHOLARLY_WORK records cannot share a family"
            )

    family_row_by_id = {row["paper_id"]: row for row in rows}
    same_pair_neighbours: defaultdict[str, set[str]] = defaultdict(set)
    for pair in pair_rows:
        if pair["relationship_decision"] != SAME_DECISION:
            continue
        left = family_row_by_id[pair["paper_id_a"]]
        right = family_row_by_id[pair["paper_id_b"]]
        roles = {left["version_role"], right["version_role"]}
        relationship = pair["relationship_type"]
        if relationship == "preprint_to_journal" and not {
            "preprint",
            "final_journal_article",
        } <= roles:
            raise VersionConsolidationError(
                f"{pair['pair_id']}: preprint_to_journal requires preprint and final journal roles"
            )
        if relationship == "conference_to_journal" and not (
            "final_journal_article" in roles
            and roles & {"conference_full_paper", "conference_abstract"}
        ):
            raise VersionConsolidationError(
                f"{pair['pair_id']}: conference_to_journal requires conference and final journal roles"
            )
        role_required = {
            "correction_of": "correction",
            "supplement_of": "supplement",
            "translated_version": "translated_publication",
        }
        if relationship in role_required and role_required[relationship] not in roles:
            raise VersionConsolidationError(
                f"{pair['pair_id']}: {relationship} requires role {role_required[relationship]}"
            )
        if relationship == "updated_version" and not {
            left["relationship_to_preferred"],
            right["relationship_to_preferred"],
        } & {"earlier_version_of", "later_version_of"}:
            raise VersionConsolidationError(
                f"{pair['pair_id']}: updated_version needs an earlier/later relationship"
            )
        same_pair_neighbours[left["paper_id"]].add(right["paper_id"])
        same_pair_neighbours[right["paper_id"]].add(left["paper_id"])

    all_ids = set(paper_to_label)
    for label, members in by_label.items():
        member_ids = {row["paper_id"] for row in members}
        status_values = {row["family_status"] for row in members}
        preferred_ids = {row["preferred_paper_id"] for row in members}
        basis_values = {row["preferred_basis"] for row in members}
        selection_rationales = {row["preferred_selection_rationale"] for row in members}
        selection_evidence = {row["preferred_selection_evidence"] for row in members}
        if len(status_values) != 1:
            raise VersionConsolidationError(f"Family {label!r} has inconsistent status")
        if len(preferred_ids) != 1 or not preferred_ids <= member_ids:
            raise VersionConsolidationError(
                f"Family {label!r} must name one preferred member consistently"
            )
        if len(basis_values) != 1 or len(selection_rationales) != 1 or len(
            selection_evidence
        ) != 1:
            raise VersionConsolidationError(
                f"Family {label!r} must use one explicit preferred-version rationale/evidence"
            )
        preferred_id = next(iter(preferred_ids))
        yes_rows = [row for row in members if row["preferred_for_analysis"] == "yes"]
        if len(yes_rows) != 1 or yes_rows[0]["paper_id"] != preferred_id:
            raise VersionConsolidationError(
                f"Family {label!r} must have exactly one preferred_for_analysis=yes row"
            )
        for member in members:
            if member["paper_id"] == preferred_id:
                if member["relationship_to_preferred"] != "self_preferred":
                    raise VersionConsolidationError(
                        f"Family {label!r} preferred record must use self_preferred"
                    )
            elif member["relationship_to_preferred"] == "self_preferred":
                raise VersionConsolidationError(
                    f"Family {label!r} nonpreferred record cannot use self_preferred"
                )
        status = next(iter(status_values))
        basis = next(iter(basis_values))
        if len(members) == 1:
            only = members[0]
            if status != "SINGLETON_WORK" or basis != "only_eligible_version":
                raise VersionConsolidationError(
                    f"Singleton family {label!r} must use SINGLETON_WORK and only_eligible_version"
                )
            if only["preferred_for_analysis"] != "yes":
                raise VersionConsolidationError(
                    f"Singleton family {label!r} must be retained for analysis"
                )
            if only["family_link_review_basis"] != "singleton_systematic_check":
                raise VersionConsolidationError(
                    f"Singleton family {label!r} must record singleton_systematic_check"
                )
        else:
            if status != "LINKED_VERSION_FAMILY" or basis == "only_eligible_version":
                raise VersionConsolidationError(
                    f"Multi-record family {label!r} must be a linked family with a comparative basis"
                )
            if any(member["version_role"] == "standalone_publication" for member in members):
                raise VersionConsolidationError(
                    f"Linked family {label!r} cannot use standalone_publication role"
                )
            member_ids = {member["paper_id"] for member in members}
            nonpreferred_relationships = {
                "preprint": {"preprint_of"},
                "conference_full_paper": {"conference_version_of"},
                "conference_abstract": {"conference_version_of"},
                "correction": {"correction_of"},
                "supplement": {"supplement_to"},
                "translated_publication": {"translated_version_of"},
                "final_journal_article": {
                    "earlier_version_of",
                    "later_version_of",
                    "other_version_of",
                },
                "other_version": {
                    "earlier_version_of",
                    "later_version_of",
                    "other_version_of",
                },
            }
            for member in members:
                paper_id = member["paper_id"]
                has_same_candidate = bool(same_pair_neighbours[paper_id] & member_ids)
                expected_link_basis = (
                    "candidate_pair_review"
                    if has_same_candidate
                    else "manual_systematic_relationship_check"
                )
                if member["family_link_review_basis"] != expected_link_basis:
                    raise VersionConsolidationError(
                        f"Family {label!r} record {paper_id} must use {expected_link_basis}"
                    )
                if paper_id == preferred_id:
                    continue
                allowed = nonpreferred_relationships[member["version_role"]]
                if member["relationship_to_preferred"] not in allowed:
                    raise VersionConsolidationError(
                        f"Family {label!r} record {paper_id} has a version role/relationship mismatch"
                    )
            preferred = next(
                member for member in members if member["paper_id"] == preferred_id
            )
            if (
                basis == "final_most_complete_publication"
                and preferred["version_role"] != "final_journal_article"
            ):
                raise VersionConsolidationError(
                    f"Family {label!r} final_most_complete_publication must prefer the final journal role"
                )
        if not preferred_ids <= all_ids:
            raise AssertionError("Preferred ID validation failed")
    return rows, dict(by_label)


def _stable_family_id(member_ids: Sequence[str]) -> str:
    material = "\0".join(sorted(member_ids))
    return f"VWF2-{sha256_text(material)[:24]}"


def _output_version_rows(
    review: Mapping[str, Any],
    family_rows: Sequence[Mapping[str, str]],
    families: Mapping[str, Sequence[Mapping[str, str]]],
    pair_rows: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    source = review["source"]
    source_by_id = {row["paper_id"]: row for row in source["included_rows"]}
    pair_by_paper: defaultdict[str, list[Mapping[str, str]]] = defaultdict(list)
    for pair in pair_rows:
        pair_by_paper[pair["paper_id_a"]].append(pair)
        pair_by_paper[pair["paper_id_b"]].append(pair)
    family_meta: dict[str, dict[str, str]] = {}
    for label, members in families.items():
        ids = sorted(member["paper_id"] for member in members)
        family_meta[label] = {
            "version_family_id": _stable_family_id(ids),
            "family_size": str(len(ids)),
            "family_members_sha256": sha256_text("\0".join(ids)),
        }
    ledger: list[dict[str, str]] = []
    corpus: list[dict[str, str]] = []
    for decision in family_rows:
        source_row = source_by_id[decision["paper_id"]]
        label = decision["review_family_label"]
        pair_items = sorted(pair_by_paper[decision["paper_id"]], key=lambda row: row["pair_id"])
        same_ids = [
            pair["pair_id"]
            for pair in pair_items
            if pair["relationship_decision"] == SAME_DECISION
        ]
        distinct_ids = [
            pair["pair_id"]
            for pair in pair_items
            if pair["relationship_decision"] == DISTINCT_DECISION
        ]
        audit = {
            **family_meta[label],
            "review_family_label": label,
            "record_level_row_sha256": decision["record_level_row_sha256"],
            "version_role": decision["version_role"],
            "preferred_for_analysis": decision["preferred_for_analysis"],
            "preferred_paper_id": decision["preferred_paper_id"],
            "preferred_basis": decision["preferred_basis"],
            "relationship_to_preferred": decision["relationship_to_preferred"],
            "family_link_review_basis": decision["family_link_review_basis"],
            "family_membership_rationale": decision["family_membership_rationale"],
            "family_evidence_locator": decision["family_evidence_locator"],
            "preferred_selection_rationale": decision["preferred_selection_rationale"],
            "preferred_selection_evidence": decision["preferred_selection_evidence"],
            "reviewed_by": decision["reviewed_by"],
            "reviewed_at_utc": decision["reviewed_at_utc"],
            "candidate_pair_ids": decision["candidate_pair_ids"],
            "same_version_pair_ids": ";".join(same_ids),
            "distinct_work_pair_ids": ";".join(distinct_ids),
            "source_finalization_manifest_sha256": source["manifest_sha256"],
            "source_review_manifest_sha256": review["manifest_sha256"],
        }
        ledger_row = {
            "version_family_id": audit["version_family_id"],
            "review_family_label": label,
            "family_size": audit["family_size"],
            "family_members_sha256": audit["family_members_sha256"],
            "paper_id": source_row["paper_id"],
            "doi": source_row["doi"],
            "title": source_row["title"],
            "year": source_row["year"],
            "publication_date": source_row["publication_date"],
            "authors": source_row["authors"],
            "journal": source_row["journal"],
            "record_type": source_row["record_type"],
            "url": source_row["url"],
            "final_decision": source_row["final_decision"],
            "final_primary_code": source_row["final_primary_code"],
            **{field: audit[field] for field in LEDGER_FIELDS if field in audit},
        }
        ledger.append(ledger_row)
        if decision["preferred_for_analysis"] == "yes":
            corpus.append(
                {
                    **source_row,
                    **{field: audit[field] for field in LEDGER_AUDIT_FIELDS},
                }
            )
    ledger.sort(key=lambda row: (row["version_family_id"], row["paper_id"]))
    corpus.sort(key=lambda row: (row["version_family_id"], row["paper_id"]))
    return ledger, corpus


def finalize_consolidation(
    finalization_dir: Path,
    review_dir: Path,
    pair_decisions: Path,
    family_decisions: Path,
    output_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
) -> Mapping[str, Any]:
    review = load_review_package(review_dir, finalization_dir, codebook=codebook)
    output = _ensure_new_output(output_dir, review["source"]["root"], review["root"])
    if pair_decisions.resolve() == family_decisions.resolve():
        raise VersionConsolidationError("Pair and family decision files must be separate")
    pair_rows = validate_pair_decisions(pair_decisions, review)
    family_rows, families = validate_family_decisions(
        family_decisions, review, pair_rows
    )
    ledger_rows, corpus_rows = _output_version_rows(
        review, family_rows, families, pair_rows
    )
    source = review["source"]
    if len(ledger_rows) != len(source["included_rows"]):
        raise AssertionError("Version ledger lost eligible record versions")
    if len(corpus_rows) != len(families):
        raise AssertionError("Analysis corpus is not one row per reviewed family")
    if {row["paper_id"] for row in ledger_rows} != {
        row["paper_id"] for row in source["included_rows"]
    }:
        raise AssertionError("Version ledger changed the eligible record ID set")
    if any(row["final_primary_code"].casefold().startswith("e8") for row in ledger_rows):
        raise AssertionError("E8 must never appear in the version ledger")

    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        preserved_path = temp / PRESERVED_SCREENING
        pair_used_path = temp / PAIR_DECISIONS_USED
        family_used_path = temp / FAMILY_DECISIONS_USED
        ledger_path = temp / VERSION_LEDGER
        corpus_path = temp / ANALYSIS_CORPUS
        summary_path = temp / FINAL_SUMMARY
        write_csv(preserved_path, source["final_rows"], FINAL_FIELDS)
        write_csv(pair_used_path, pair_rows, PAIR_FIELDS)
        write_csv(family_used_path, family_rows, FAMILY_FIELDS)
        write_csv(ledger_path, ledger_rows, LEDGER_FIELDS)
        write_csv(corpus_path, corpus_rows, FINAL_FIELDS + LEDGER_AUDIT_FIELDS)
        family_sizes = Counter(len(members) for members in families.values())
        linked_families = sum(1 for members in families.values() if len(members) > 1)
        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "status": FINAL_STATUS,
            "all_record_level_rows_preserved": len(source["final_rows"]),
            "record_level_included_versions": len(source["included_rows"]),
            "eligible_version_ledger_rows": len(ledger_rows),
            "canonical_unique_works_for_analysis": len(corpus_rows),
            "linked_version_families": linked_families,
            "nonpreferred_eligible_versions_retained_in_ledger": len(ledger_rows)
            - len(corpus_rows),
            "manual_systematic_family_link_rows": sum(
                row["family_link_review_basis"]
                == "manual_systematic_relationship_check"
                for row in family_rows
            ),
            "candidate_pairs_reviewed": len(pair_rows),
            "same_work_version_pairs": sum(
                row["relationship_decision"] == SAME_DECISION for row in pair_rows
            ),
            "distinct_work_pairs": sum(
                row["relationship_decision"] == DISTINCT_DECISION for row in pair_rows
            ),
            "family_size_distribution": {
                str(size): count for size, count in sorted(family_sizes.items())
            },
            "record_level_eligibility_changed": False,
            "retired_E8_used": False,
            "analysis_unit_ready": True,
            "human_audit_mode": source["human_audit_mode"],
            "human_validation_claims_permitted": False,
        }
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        outputs = {
            "all_record_level_screening_preserved": file_entry(
                preserved_path, temp, "immutable_record_level_decision_copy"
            ),
            "pair_decisions_used": file_entry(
                pair_used_path, temp, "reviewed_candidate_pair_decisions"
            ),
            "family_decisions_used": file_entry(
                family_used_path, temp, "reviewed_all_record_family_decisions"
            ),
            "eligible_version_ledger": file_entry(
                ledger_path, temp, "all_eligible_publication_versions_and_provenance"
            ),
            "one_work_analysis_corpus": file_entry(
                corpus_path, temp, "one_preferred_version_per_scholarly_work"
            ),
            "summary": file_entry(summary_path, temp, "consolidation_summary"),
        }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "pipeline": FINAL_PIPELINE,
            "status": FINAL_STATUS,
            "inputs": {
                "screening_finalization_manifest": {
                    "path": str(source["manifest_path"]),
                    "sha256": source["manifest_sha256"],
                },
                "version_review_manifest": {
                    "path": str(review["manifest_path"]),
                    "sha256": review["manifest_sha256"],
                },
                "human_audit_linkage_or_blank_audit_trail": {
                    "path": str(source["human_path"]),
                    "sha256": sha256_file(source["human_path"]),
                },
                "human_audit_deferral_used": (
                    {
                        "path": str(source["human_audit_deferral_path"]),
                        "sha256": sha256_file(source["human_audit_deferral_path"]),
                    }
                    if source["human_audit_deferral_path"] is not None
                    else None
                ),
                "human_audit_deferral_source_note_used": (
                    {
                        "path": str(source["human_audit_deferral_note_path"]),
                        "sha256": sha256_file(
                            source["human_audit_deferral_note_path"]
                        ),
                    }
                    if source["human_audit_deferral_note_path"] is not None
                    else None
                ),
                "pair_decisions": {
                    "path": str(pair_decisions.resolve()),
                    "sha256": sha256_file(pair_decisions.resolve()),
                },
                "family_decisions": {
                    "path": str(family_decisions.resolve()),
                    "sha256": sha256_file(family_decisions.resolve()),
                },
                "codebook": {
                    "path": str(source["codebook_path"]),
                    "sha256": source["codebook_sha256"],
                },
            },
            "counts": {
                "all_record_level_rows": len(source["final_rows"]),
                "eligible_record_versions": len(ledger_rows),
                "reviewed_candidate_pairs": len(pair_rows),
                "reviewed_version_families": len(families),
                "one_work_analysis_rows": len(corpus_rows),
            },
            "contracts": {
                "record_level_eligibility_unchanged": True,
                "all_record_level_rows_preserved": True,
                "all_eligible_versions_preserved_in_ledger": True,
                "all_candidate_pairs_reviewed": True,
                "all_eligible_records_family_reviewed": True,
                "manual_family_links_explicitly_reviewed": True,
                "ambiguous_relationships_unresolved": False,
                "one_preferred_version_per_family": True,
                "preferred_choice_has_evidence_and_rationale": True,
                "retired_E8_allowed": False,
                "automatic_version_collapse": False,
                "analysis_unit_ready": True,
                "prospective_human_audit_linked": source["human_audit_mode"]
                == "completed_prospective_human_audit",
                "prospective_human_audit_deferred_by_author": source["human_audit_mode"]
                == "explicit_author_deferral",
                "human_validation_claims_permitted": False,
            },
            "outputs": outputs,
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "dependencies": _dependency_hashes(),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp / FINAL_MANIFEST
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        hash_rows: list[dict[str, Any]] = []
        input_items = [
            (Path(__file__), "code", "version_consolidation_program"),
            (source["codebook_path"], "input", "locked_screening_codebook"),
            (source["manifest_path"], "input", "screening_finalization_manifest"),
            (source["final_path"], "input", "all_record_level_screening"),
            (source["included_path"], "input", "eligible_record_versions"),
            (
                source["human_path"],
                "input",
                "human_audit_linkage_or_blank_audit_trail",
            ),
            (review["manifest_path"], "input", "frozen_version_review_manifest"),
            (review["pair_path"], "input", "blank_pair_template"),
            (review["family_path"], "input", "blank_family_template"),
            (pair_decisions.resolve(), "input", "reviewed_pair_decisions"),
            (family_decisions.resolve(), "input", "reviewed_family_decisions"),
        ]
        for path, role in (
            (
                source["human_audit_deferral_path"],
                "explicit_author_human_audit_deferral",
            ),
            (
                source["human_audit_deferral_note_path"],
                "human_readable_author_human_audit_deferral",
            ),
        ):
            if path is not None:
                input_items.append((path, "input", role))
        for path, scope, role in input_items:
            hash_rows.append(
                {
                    "scope": scope,
                    "path": str(path),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for dependency_name, dependency_path in sorted(DEPENDENCY_PATHS.items()):
            hash_rows.append(
                {
                    "scope": "code",
                    "path": dependency_name,
                    "role": "version_consolidation_dependency",
                    "bytes": dependency_path.stat().st_size,
                    "sha256": sha256_file(dependency_path),
                }
            )
        for path, role in (
            (preserved_path, "immutable_record_level_decision_copy"),
            (pair_used_path, "reviewed_candidate_pair_decisions"),
            (family_used_path, "reviewed_all_record_family_decisions"),
            (ledger_path, "all_eligible_version_ledger"),
            (corpus_path, "one_work_analysis_corpus"),
            (summary_path, "consolidation_summary"),
            (manifest_path, "consolidation_manifest"),
        ):
            hash_rows.append(
                {
                    "scope": "output",
                    "path": path.name,
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        hash_path = temp / FINAL_HASH_LEDGER
        _write_hash_ledger(hash_path, hash_rows)
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "status": FINAL_STATUS,
            "consolidation_manifest_sha256": sha256_file(manifest_path),
            "consolidation_hash_ledger_sha256": sha256_file(hash_path),
            "eligible_version_ledger_sha256": sha256_file(ledger_path),
            "one_work_analysis_corpus_sha256": sha256_file(corpus_path),
            "source_finalization_manifest_sha256": source["manifest_sha256"],
            "source_review_manifest_sha256": review["manifest_sha256"],
        }
        (temp / FINAL_FROZEN_MARKER).write_text(
            json.dumps(frozen, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        _verify_binding(source["binding"], label="Screening finalization input")
        _verify_binding(review["binding"], label="Frozen version-review package")
        if sha256_file(pair_decisions.resolve()) != manifest["inputs"]["pair_decisions"]["sha256"]:
            raise VersionConsolidationError("Reviewed pair decisions changed during finalization")
        if sha256_file(family_decisions.resolve()) != manifest["inputs"]["family_decisions"]["sha256"]:
            raise VersionConsolidationError("Reviewed family decisions changed during finalization")
        temp.rename(output)
        return manifest
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser(
        "prepare", help="Create a frozen blank publication-version review package"
    )
    prepare.add_argument("--finalization-dir", required=True, type=Path)
    prepare.add_argument("--output-dir", required=True, type=Path)
    prepare.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)

    finalize = subparsers.add_parser(
        "finalize", help="Validate reviewed decisions and create one-work analysis corpus"
    )
    finalize.add_argument("--finalization-dir", required=True, type=Path)
    finalize.add_argument("--review-dir", required=True, type=Path)
    finalize.add_argument("--pair-decisions", required=True, type=Path)
    finalize.add_argument("--family-decisions", required=True, type=Path)
    finalize.add_argument("--output-dir", required=True, type=Path)
    finalize.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "prepare":
        manifest = prepare_review_package(
            args.finalization_dir, args.output_dir, codebook=args.codebook
        )
    else:
        manifest = finalize_consolidation(
            args.finalization_dir,
            args.review_dir,
            args.pair_decisions,
            args.family_decisions,
            args.output_dir,
            codebook=args.codebook,
        )
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
