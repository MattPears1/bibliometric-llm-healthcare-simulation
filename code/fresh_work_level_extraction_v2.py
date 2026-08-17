#!/usr/bin/env python3
"""Prepare and finalize checked work-level extraction for the fresh V2 rerun.

The program consumes only a frozen, finalized publication-version
consolidation package.  ``prepare`` creates deterministic, hash-bound blank
source-check batches.  ``finalize`` validates an exact completed copy of every
batch and emits a checked one-work corpus plus an extraction provenance ledger.

Screening-review extraction fields remain protected context and suggestions;
they are never promoted to final fields.  Every final row requires a new,
attested source check with evidence URLs, rationale, reviewer identity, and an
exact UTC timestamp.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit

from consolidate_fresh_publication_versions_v2 import (
    ANALYSIS_CORPUS,
    FINAL_FROZEN_MARKER as CONSOLIDATION_FROZEN_MARKER,
    FINAL_HASH_LEDGER as CONSOLIDATION_HASH_LEDGER,
    FINAL_MANIFEST as CONSOLIDATION_MANIFEST,
    FINAL_PIPELINE as CONSOLIDATION_PIPELINE,
    FINAL_STATUS as CONSOLIDATION_STATUS,
    FINAL_SUMMARY as CONSOLIDATION_SUMMARY,
    LEDGER_AUDIT_FIELDS,
    LEDGER_FIELDS as VERSION_LEDGER_FIELDS,
    PRESERVED_SCREENING,
    VERSION_LEDGER,
)
from finalize_fresh_screening_v2 import FINAL_FIELDS
from fresh_screening_review_common_v2 import (
    DEFAULT_CODEBOOK,
    MASTER_FIELDS,
    VALID_MODALITIES,
    VALID_NTS,
    VALID_STUDY_DESIGNS,
    FreshReviewError,
    canonical_json,
    file_entry,
    read_csv,
    safe_relative,
    sha256_file,
    sha256_text,
    validate_file_entry,
    validate_locked_codebook,
    write_csv,
)


SCHEMA_VERSION = "fresh-work-level-extraction-v2.0"
PREPARE_PIPELINE = "fresh_v2_checked_work_extraction_preparation"
FINALIZE_PIPELINE = "fresh_v2_checked_work_extraction_finalization"
PREPARE_STATUS = "work_level_extraction_batches_frozen_source_check_pending"
FINAL_STATUS = "checked_work_level_extraction_finalized_analysis_ready"

PIPELINE_DIR = Path(__file__).resolve().parent
ACTIVE_ROOT = PIPELINE_DIR.parent
DEFAULT_ANALYSIS_SPEC = (
    ACTIVE_ROOT / "06_AUDIT" / "FRESH_ANALYSIS_SPECIFICATION_V2_2026-08-14.json"
)
EXPECTED_ANALYSIS_SPEC_SHA256 = (
    "db0b4354352e684768734ecc7c547708642e9a4037bef74ad0b0ac1350aa804d"
)

PREPARATION_MANIFEST = "WORK_EXTRACTION_PREPARATION_MANIFEST_V2.json"
PREPARATION_HASH_LEDGER = "WORK_EXTRACTION_PREPARATION_HASH_MANIFEST_V2.csv"
PREPARATION_FROZEN_MARKER = "WORK_EXTRACTION_PREPARATION_FROZEN_V2.json"
PREPARATION_SUMMARY = "WORK_EXTRACTION_PREPARATION_SUMMARY_V2.json"
BATCH_MANIFEST = "WORK_EXTRACTION_BATCH_MANIFEST_V2.csv"
BATCH_FILENAME = "WORK_EXTRACTION_BATCH_{number:03d}_V2.csv"

MERGED_COMPLETED = "COMPLETED_WORK_EXTRACTIONS_MERGED_V2.csv"
CHECKED_CORPUS = "CHECKED_ONE_WORK_ANALYSIS_CORPUS_V2.csv"
EXTRACTION_LEDGER = "CHECKED_WORK_EXTRACTION_LEDGER_V2.csv"
FINALIZATION_SUMMARY = "WORK_EXTRACTION_FINALIZATION_SUMMARY_V2.json"
FINALIZATION_MANIFEST = "WORK_EXTRACTION_FINALIZATION_MANIFEST_V2.json"
FINALIZATION_HASH_LEDGER = "WORK_EXTRACTION_FINALIZATION_HASH_MANIFEST_V2.csv"
FINALIZATION_FROZEN_MARKER = "WORK_EXTRACTION_FINALIZATION_FROZEN_V2.json"

SOURCE_CORPUS_FIELDS = list(FINAL_FIELDS) + list(LEDGER_AUDIT_FIELDS)

BINDING_FIELDS = [
    "extraction_schema_version",
    "source_consolidation_manifest_sha256",
    "source_one_work_corpus_sha256",
    "source_row_number",
    "extraction_batch",
    "source_work_row_sha256",
    "human_audit_mode",
]

EXTRACTION_FIELDS = [
    "final_simulation_modalities",
    "final_nts_domains",
    "final_specialty",
    "final_model_families",
    "final_model_description_raw",
    "final_study_design",
    "extraction_rationale",
    "evidence_url_1",
    "evidence_url_2",
    "source_checked_by",
    "source_checked_at_utc",
    "source_check_attestation",
    "screening_suggestions_role",
]

TEMPLATE_FIELDS = BINDING_FIELDS + SOURCE_CORPUS_FIELDS + EXTRACTION_FIELDS
PROTECTED_TEMPLATE_FIELDS = BINDING_FIELDS + SOURCE_CORPUS_FIELDS
CHECKED_CORPUS_FIELDS = SOURCE_CORPUS_FIELDS + BINDING_FIELDS + EXTRACTION_FIELDS

EXTRACTION_LEDGER_FIELDS = [
    "extraction_schema_version",
    "paper_id",
    "version_family_id",
    "title",
    "doi",
    "source_consolidation_manifest_sha256",
    "source_one_work_corpus_sha256",
    "source_row_number",
    "extraction_batch",
    "source_work_row_sha256",
    "human_audit_mode",
    "frozen_preparation_manifest_sha256",
    "frozen_batch_template_sha256",
    "completed_batch_sha256",
] + EXTRACTION_FIELDS

BATCH_MANIFEST_FIELDS = [
    "batch",
    "file",
    "first_source_row",
    "last_source_row",
    "records",
    "first_paper_id",
    "last_paper_id",
    "ordered_paper_ids_sha256",
    "bytes",
    "sha256",
]

HASH_LEDGER_FIELDS = ["scope", "path", "role", "bytes", "sha256"]

CONSOLIDATION_SCRIPT = PIPELINE_DIR / "consolidate_fresh_publication_versions_v2.py"
DEPENDENCY_PATHS = {
    "consolidate_fresh_publication_versions_v2.py": CONSOLIDATION_SCRIPT,
    "finalize_fresh_screening_v2.py": PIPELINE_DIR / "finalize_fresh_screening_v2.py",
    "compare_fresh_independent_reviews_v2.py": PIPELINE_DIR
    / "compare_fresh_independent_reviews_v2.py",
    "fresh_screening_review_common_v2.py": PIPELINE_DIR
    / "fresh_screening_review_common_v2.py",
}

PROTECTED_ROOT_NAMES = {
    "old_archive",
    "current_gse",
    "journal_route",
    "other_copies",
    "publisher",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BLANK_NTS_MARKER = "[no_explicit_nts]"
BLANK_SPECIALTY_MARKER = "[no_explicit_specialty]"
UNCLEAR_DESIGN_MARKER = "[study_design_unclear]"
SOURCE_CHECK_ATTESTATION = "independent_source_check_completed"
SUGGESTIONS_ROLE = "suggestions_only_not_evidence"
PLACEHOLDER_VALUES = {
    "unclear",
    "unknown",
    "n/a",
    "na",
    "none",
    "not sure",
    "tbd",
    "to be checked",
    "not checked",
    "not applicable",
    "not reported",
    "unspecified",
}


class WorkExtractionError(FreshReviewError):
    """Raised when a fresh V2 extraction contract is violated."""


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkExtractionError(f"Invalid JSON object: {path}") from exc
    if not isinstance(value, dict):
        raise WorkExtractionError(f"Expected a JSON object: {path}")
    return value


def _read_exact_csv(path: Path, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        observed_fields, rows = read_csv(path)
    except FreshReviewError as exc:
        raise WorkExtractionError(str(exc)) from exc
    if observed_fields != list(fields):
        raise WorkExtractionError(
            f"{path}: unexpected CSV schema/order; expected {list(fields)}, "
            f"observed {observed_fields}"
        )
    for number, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            raise WorkExtractionError(f"{path}:{number}: malformed CSV row")
    return rows


def _validate_manifested_file(
    root: Path, entry: Mapping[str, Any], *, label: str
) -> Path:
    try:
        return validate_file_entry(root, entry, label=label)
    except FreshReviewError as exc:
        raise WorkExtractionError(str(exc)) from exc


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
        raise WorkExtractionError(
            f"{role} path is inside protected historical/frozen material: {path}"
        )


def _ensure_new_output(output: Path, *immutable_roots: Path) -> Path:
    resolved = output.resolve()
    _assert_fresh_path(resolved, role="Output")
    if resolved.exists():
        raise WorkExtractionError(
            f"Output already exists; refusing to overwrite or append: {resolved}"
        )
    for root in immutable_roots:
        if _within(resolved, root):
            raise WorkExtractionError(
                f"Output must not be inside immutable input directory: {root.resolve()}"
            )
    return resolved


def _source_binding(paths: Iterable[Path]) -> dict[str, str]:
    binding: dict[str, str] = {}
    for raw_path in paths:
        path = raw_path.resolve()
        if not path.is_file():
            raise WorkExtractionError(f"Binding target is missing: {path}")
        binding[str(path)] = sha256_file(path)
    return binding


def _verify_binding(binding: Mapping[str, str], *, label: str) -> None:
    for raw_path, expected in binding.items():
        path = Path(raw_path)
        if not path.is_file() or sha256_file(path) != expected:
            raise WorkExtractionError(f"{label} changed during processing: {path}")


def _dependency_hashes() -> dict[str, str]:
    missing = [name for name, path in DEPENDENCY_PATHS.items() if not path.is_file()]
    if missing:
        raise WorkExtractionError(f"Required dependency files are missing: {missing}")
    return {
        name: sha256_file(path) for name, path in sorted(DEPENDENCY_PATHS.items())
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_hash_ledger(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    ordered = sorted(rows, key=lambda row: (row["scope"], row["path"], row["role"]))
    write_csv(path, ordered, HASH_LEDGER_FIELDS)


def _validate_hash_ledger(
    root: Path,
    filename: str,
    *,
    required_output_paths: Iterable[str],
) -> list[dict[str, str]]:
    path = root / filename
    rows = _read_exact_csv(path, HASH_LEDGER_FIELDS)
    seen: set[tuple[str, str, str]] = set()
    observed_outputs: set[str] = set()
    for row in rows:
        key = (row["scope"], row["path"], row["role"])
        if key in seen:
            raise WorkExtractionError(f"{path}: duplicate hash-ledger row {key}")
        seen.add(key)
        if row["scope"] not in {"code", "input", "output"}:
            raise WorkExtractionError(f"{path}: invalid scope {row['scope']!r}")
        if not SHA256_RE.fullmatch(row["sha256"]):
            raise WorkExtractionError(f"{path}: invalid SHA-256 for {row['path']}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise WorkExtractionError(
                f"{path}: invalid byte count for {row['path']}"
            ) from exc
        if expected_bytes < 0:
            raise WorkExtractionError(f"{path}: negative byte count for {row['path']}")
        if row["scope"] != "output":
            continue
        normalized = row["path"].replace("\\", "/")
        observed_outputs.add(normalized)
        try:
            target = safe_relative(root, normalized, label="output hash-ledger")
        except FreshReviewError as exc:
            raise WorkExtractionError(str(exc)) from exc
        if not target.is_file():
            raise WorkExtractionError(f"Hash-ledger target is missing: {target}")
        if (
            target.stat().st_size != expected_bytes
            or sha256_file(target).casefold() != row["sha256"].casefold()
        ):
            raise WorkExtractionError(f"Hash-ledger mismatch: {target}")
    required = {item.replace("\\", "/") for item in required_output_paths}
    missing = required - observed_outputs
    if missing:
        raise WorkExtractionError(
            f"{path}: required output rows missing: {sorted(missing)}"
        )
    return rows


def _validate_analysis_specification(
    analysis_spec: Path, codebook: Path
) -> tuple[Path, str, dict[str, list[str]], Path, str]:
    spec_path = analysis_spec.resolve()
    if not spec_path.is_file():
        raise WorkExtractionError(f"Missing locked analysis specification: {spec_path}")
    spec_sha = sha256_file(spec_path)
    if spec_sha.casefold() != EXPECTED_ANALYSIS_SPEC_SHA256:
        raise WorkExtractionError(
            "Locked fresh V2 analysis specification SHA-256 mismatch: expected "
            f"{EXPECTED_ANALYSIS_SPEC_SHA256}, observed {spec_sha}"
        )
    spec = _load_json(spec_path)
    if (
        spec.get("schema_version") != "2.0"
        or spec.get("specification_id") != "gse_fresh_analysis_v2_2026-08-14"
        or spec.get("status") != "prespecified_before_final_screening_and_outcome_analysis"
    ):
        raise WorkExtractionError("Locked analysis specification identity/status mismatch")
    gate = spec.get("input_gate") or {}
    if (
        gate.get("required_status") != CONSOLIDATION_STATUS
        or gate.get("required_main_file") != ANALYSIS_CORPUS
        or gate.get("one_preferred_record_per_work_family") is not True
        or gate.get("checked_work_level_extraction_required") is not True
        or gate.get("hash_validation_required") is not True
    ):
        raise WorkExtractionError("Analysis specification input/extraction gate mismatch")
    raw_labels = spec.get("study_level_labels") or {}
    required_groups = {
        "model_families",
        "simulation_methods",
        "nts_domains",
        "study_designs",
    }
    if set(raw_labels) != required_groups:
        raise WorkExtractionError("Analysis specification study-level label groups changed")
    labels: dict[str, list[str]] = {}
    for group in sorted(required_groups):
        values = raw_labels.get(group)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
            or len(values) != len(set(values))
        ):
            raise WorkExtractionError(f"Invalid locked label list: {group}")
        labels[group] = list(values)
    if set(labels["simulation_methods"]) != set(VALID_MODALITIES):
        raise WorkExtractionError("Specification/codebook simulation labels disagree")
    if set(labels["nts_domains"]) != set(VALID_NTS):
        raise WorkExtractionError("Specification/codebook NTS labels disagree")
    if set(labels["study_designs"]) != set(VALID_STUDY_DESIGNS):
        raise WorkExtractionError("Specification/codebook study-design labels disagree")
    if "unclear" not in labels["study_designs"]:
        raise WorkExtractionError("Study design must retain the prespecified unclear label")
    if any(
        "unclear" in labels[group]
        for group in ("model_families", "simulation_methods", "nts_domains")
    ):
        raise WorkExtractionError("Unclear is permitted only for study design")
    try:
        codebook_path, codebook_sha = validate_locked_codebook(codebook)
    except FreshReviewError as exc:
        raise WorkExtractionError(str(exc)) from exc
    codebook_text = codebook_path.read_text(encoding="utf-8-sig")
    for group in ("simulation_methods", "nts_domains", "study_designs"):
        missing = [value for value in labels[group] if f"`{value}`" not in codebook_text]
        if missing:
            raise WorkExtractionError(
                f"Locked codebook no longer states {group} labels: {missing}"
            )
    return spec_path, spec_sha, labels, codebook_path, codebook_sha


def _validate_current_consolidation_code(manifest: Mapping[str, Any]) -> None:
    script = manifest.get("script") or {}
    if script.get("filename") != CONSOLIDATION_SCRIPT.name:
        raise WorkExtractionError("Consolidation manifest script filename mismatch")
    if clean(script.get("sha256")).casefold() != sha256_file(
        CONSOLIDATION_SCRIPT
    ).casefold():
        raise WorkExtractionError(
            "Consolidation program changed since the input package was frozen"
        )
    expected_dependencies = {
        name: sha256_file(path)
        for name, path in sorted(DEPENDENCY_PATHS.items())
        if name != CONSOLIDATION_SCRIPT.name
    }
    if script.get("dependencies") != expected_dependencies:
        raise WorkExtractionError(
            "Consolidation dependency code changed since the input package was frozen"
        )


def _validate_sha(value: str, *, label: str) -> None:
    if not SHA256_RE.fullmatch(value):
        raise WorkExtractionError(f"Invalid SHA-256 in {label}: {value!r}")


def _validate_source_rows(
    corpus_rows: Sequence[Mapping[str, str]],
    ledger_rows: Sequence[Mapping[str, str]],
    preserved_rows: Sequence[Mapping[str, str]],
    manifest: Mapping[str, Any],
    *,
    corpus_path: Path,
    ledger_path: Path,
) -> None:
    if not corpus_rows:
        raise WorkExtractionError("The one-work analysis corpus is empty")
    paper_ids = [row["paper_id"] for row in corpus_rows]
    family_ids = [row["version_family_id"] for row in corpus_rows]
    if any(not paper_id for paper_id in paper_ids) or len(paper_ids) != len(set(paper_ids)):
        raise WorkExtractionError(f"{corpus_path}: blank or duplicate paper_id")
    if any(not family_id for family_id in family_ids) or len(family_ids) != len(
        set(family_ids)
    ):
        raise WorkExtractionError(
            f"{corpus_path}: blank or duplicate version_family_id"
        )
    expected_order = sorted(
        corpus_rows, key=lambda row: (row["version_family_id"], row["paper_id"])
    )
    if list(corpus_rows) != expected_order:
        raise WorkExtractionError(f"{corpus_path}: canonical-work row order changed")

    inputs = manifest.get("inputs") or {}
    expected_finalization_sha = clean(
        (inputs.get("screening_finalization_manifest") or {}).get("sha256")
    )
    expected_review_sha = clean((inputs.get("version_review_manifest") or {}).get("sha256"))
    _validate_sha(expected_finalization_sha, label="consolidation finalization input")
    _validate_sha(expected_review_sha, label="consolidation version-review input")

    for number, row in enumerate(corpus_rows, start=2):
        paper_id = row["paper_id"]
        if row["final_decision"] != "INCLUDE":
            raise WorkExtractionError(f"{corpus_path}:{number}: non-included canonical work")
        if row["final_primary_code"].casefold().startswith("e8"):
            raise WorkExtractionError(f"{corpus_path}:{number}: retired E8 code")
        if row["preferred_for_analysis"] != "yes" or row["preferred_paper_id"] != paper_id:
            raise WorkExtractionError(
                f"{corpus_path}:{number}: row is not its family's preferred record"
            )
        expected_candidate_hash = sha256_text(
            canonical_json({field: row[field] for field in MASTER_FIELDS})
        )
        if row["candidate_row_sha256"] != expected_candidate_hash:
            raise WorkExtractionError(
                f"{corpus_path}:{number}: candidate source-row hash mismatch"
            )
        expected_record_hash = sha256_text(
            canonical_json({field: row[field] for field in FINAL_FIELDS})
        )
        if row["record_level_row_sha256"] != expected_record_hash:
            raise WorkExtractionError(
                f"{corpus_path}:{number}: record-level source-row hash mismatch"
            )
        for field in (
            "family_members_sha256",
            "source_finalization_manifest_sha256",
            "source_review_manifest_sha256",
        ):
            _validate_sha(row[field], label=f"{paper_id}/{field}")
        if row["source_finalization_manifest_sha256"] != expected_finalization_sha:
            raise WorkExtractionError(
                f"{corpus_path}:{number}: finalization source hash changed"
            )
        if row["source_review_manifest_sha256"] != expected_review_sha:
            raise WorkExtractionError(
                f"{corpus_path}:{number}: version-review source hash changed"
            )

    if not ledger_rows:
        raise WorkExtractionError(f"{ledger_path}: eligible-version ledger is empty")
    preserved_by_id = {row["paper_id"]: row for row in preserved_rows}
    if (
        any(not paper_id for paper_id in preserved_by_id)
        or len(preserved_by_id) != len(preserved_rows)
    ):
        raise WorkExtractionError("Preserved record-level screening has blank/duplicate IDs")
    ledger_ids = [row["paper_id"] for row in ledger_rows]
    if any(not item for item in ledger_ids) or len(ledger_ids) != len(set(ledger_ids)):
        raise WorkExtractionError(f"{ledger_path}: blank or duplicate paper_id")
    if list(ledger_rows) != sorted(
        ledger_rows, key=lambda row: (row["version_family_id"], row["paper_id"])
    ):
        raise WorkExtractionError(f"{ledger_path}: eligible-version row order changed")
    by_family: defaultdict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in ledger_rows:
        paper_id = row["paper_id"]
        if paper_id not in preserved_by_id:
            raise WorkExtractionError(
                f"{ledger_path}: eligible version {paper_id} missing from preserved screening"
            )
        preserved = preserved_by_id[paper_id]
        expected_record_hash = sha256_text(canonical_json(dict(preserved)))
        if row["record_level_row_sha256"] != expected_record_hash:
            raise WorkExtractionError(
                f"{ledger_path}: record-level source hash mismatch for {paper_id}"
            )
        for field in (
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
        ):
            if row[field] != preserved[field]:
                raise WorkExtractionError(
                    f"{ledger_path}: preserved source mismatch for {paper_id}/{field}"
                )
        if row["final_decision"] != "INCLUDE":
            raise WorkExtractionError(f"{ledger_path}: non-included version in ledger")
        if row["final_primary_code"].casefold().startswith("e8"):
            raise WorkExtractionError(f"{ledger_path}: retired E8 code in ledger")
        by_family[row["version_family_id"]].append(row)
    if set(by_family) != set(family_ids):
        raise WorkExtractionError("Corpus and eligible-version ledger family sets disagree")
    corpus_by_family = {row["version_family_id"]: row for row in corpus_rows}
    for family_id, members in sorted(by_family.items()):
        member_ids = sorted(row["paper_id"] for row in members)
        family_hash = sha256_text("\0".join(member_ids))
        preferred = [row for row in members if row["preferred_for_analysis"] == "yes"]
        if len(preferred) != 1:
            raise WorkExtractionError(
                f"{ledger_path}: family {family_id} lacks exactly one preferred record"
            )
        preferred_row = preferred[0]
        corpus_row = corpus_by_family[family_id]
        if preferred_row["paper_id"] != corpus_row["paper_id"]:
            raise WorkExtractionError(
                f"Corpus/ledger preferred record mismatch for {family_id}"
            )
        preserved_preferred = preserved_by_id[preferred_row["paper_id"]]
        for field in FINAL_FIELDS:
            if corpus_row[field] != preserved_preferred[field]:
                raise WorkExtractionError(
                    f"Corpus/preserved screening mismatch for {family_id}/{field}"
                )
        for member in members:
            if member["family_size"] != str(len(members)):
                raise WorkExtractionError(f"Family size mismatch for {family_id}")
            if member["family_members_sha256"] != family_hash:
                raise WorkExtractionError(f"Family member hash mismatch for {family_id}")
            if member["preferred_paper_id"] != preferred_row["paper_id"]:
                raise WorkExtractionError(f"Preferred paper ID mismatch for {family_id}")
            if member["source_finalization_manifest_sha256"] != expected_finalization_sha:
                raise WorkExtractionError(f"Finalization hash mismatch for {family_id}")
            if member["source_review_manifest_sha256"] != expected_review_sha:
                raise WorkExtractionError(f"Review hash mismatch for {family_id}")
        for field in LEDGER_AUDIT_FIELDS:
            if corpus_row[field] != preferred_row[field]:
                raise WorkExtractionError(
                    f"Corpus/ledger audit mismatch for {family_id}/{field}"
                )


def load_consolidation_package(consolidation_dir: Path) -> dict[str, Any]:
    root = consolidation_dir.resolve()
    _assert_fresh_path(root, role="Consolidation input")
    if not root.is_dir():
        raise WorkExtractionError(f"Consolidation directory does not exist: {root}")
    manifest_path = root / CONSOLIDATION_MANIFEST
    manifest = _load_json(manifest_path)
    if (
        manifest.get("schema_version") != "fresh-publication-version-consolidation-v2.0"
        or manifest.get("pipeline") != CONSOLIDATION_PIPELINE
        or manifest.get("status") != CONSOLIDATION_STATUS
    ):
        raise WorkExtractionError("Input is not a finalized fresh V2 consolidation package")
    contracts = manifest.get("contracts") or {}
    required_true = (
        "record_level_eligibility_unchanged",
        "all_eligible_versions_preserved_in_ledger",
        "one_preferred_version_per_family",
        "analysis_unit_ready",
    )
    if any(contracts.get(field) is not True for field in required_true):
        raise WorkExtractionError("Consolidation package readiness contracts are incomplete")
    if contracts.get("human_validation_claims_permitted") is not False:
        raise WorkExtractionError("Consolidation package permits unsupported human claims")
    audit_linked = contracts.get("prospective_human_audit_linked") is True
    audit_deferred = contracts.get("prospective_human_audit_deferred_by_author") is True
    if audit_linked == audit_deferred:
        raise WorkExtractionError(
            "Consolidation package must record exactly one human-audit mode"
        )
    human_audit_mode = (
        "completed_prospective_human_audit"
        if audit_linked
        else "explicit_author_deferral"
    )
    outputs = manifest.get("outputs") or {}
    corpus_path = _validate_manifested_file(
        root, outputs.get("one_work_analysis_corpus") or {}, label="one-work corpus"
    )
    ledger_path = _validate_manifested_file(
        root, outputs.get("eligible_version_ledger") or {}, label="version ledger"
    )
    preserved_path = _validate_manifested_file(
        root,
        outputs.get("all_record_level_screening_preserved") or {},
        label="preserved record-level screening",
    )
    summary_path = _validate_manifested_file(
        root, outputs.get("summary") or {}, label="consolidation summary"
    )
    if corpus_path.name != ANALYSIS_CORPUS or ledger_path.name != VERSION_LEDGER:
        raise WorkExtractionError("Consolidation output filenames changed")
    _validate_hash_ledger(
        root,
        CONSOLIDATION_HASH_LEDGER,
        required_output_paths=(
            ANALYSIS_CORPUS,
            VERSION_LEDGER,
            PRESERVED_SCREENING,
            CONSOLIDATION_SUMMARY,
            CONSOLIDATION_MANIFEST,
        ),
    )
    frozen_path = root / CONSOLIDATION_FROZEN_MARKER
    frozen = _load_json(frozen_path)
    frozen_expected = {
        "status": CONSOLIDATION_STATUS,
        "consolidation_manifest_sha256": sha256_file(manifest_path),
        "consolidation_hash_ledger_sha256": sha256_file(
            root / CONSOLIDATION_HASH_LEDGER
        ),
        "eligible_version_ledger_sha256": sha256_file(ledger_path),
        "one_work_analysis_corpus_sha256": sha256_file(corpus_path),
    }
    for field, expected in frozen_expected.items():
        if clean(frozen.get(field)).casefold() != expected.casefold():
            raise WorkExtractionError(
                f"Consolidation frozen-marker mismatch for {field}"
            )
    _validate_current_consolidation_code(manifest)
    corpus_rows = _read_exact_csv(corpus_path, SOURCE_CORPUS_FIELDS)
    ledger_rows = _read_exact_csv(ledger_path, VERSION_LEDGER_FIELDS)
    preserved_rows = _read_exact_csv(preserved_path, FINAL_FIELDS)
    _validate_source_rows(
        corpus_rows,
        ledger_rows,
        preserved_rows,
        manifest,
        corpus_path=corpus_path,
        ledger_path=ledger_path,
    )
    counts = manifest.get("counts") or {}
    if int(counts.get("one_work_analysis_rows", -1)) != len(corpus_rows):
        raise WorkExtractionError("Consolidation manifest corpus count mismatch")
    if int(counts.get("eligible_record_versions", -1)) != len(ledger_rows):
        raise WorkExtractionError("Consolidation manifest ledger count mismatch")
    if int(counts.get("all_record_level_rows", -1)) != len(preserved_rows):
        raise WorkExtractionError("Consolidation manifest preserved-screening count mismatch")
    summary = _load_json(summary_path)
    if (
        summary.get("status") != CONSOLIDATION_STATUS
        or int(summary.get("canonical_unique_works_for_analysis", -1))
        != len(corpus_rows)
        or int(summary.get("eligible_version_ledger_rows", -1)) != len(ledger_rows)
        or summary.get("human_validation_claims_permitted") is not False
    ):
        raise WorkExtractionError("Consolidation summary/count contract mismatch")
    binding_paths = [
        manifest_path,
        root / CONSOLIDATION_HASH_LEDGER,
        frozen_path,
        corpus_path,
        ledger_path,
        preserved_path,
        summary_path,
        CONSOLIDATION_SCRIPT,
        *DEPENDENCY_PATHS.values(),
    ]
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "corpus_path": corpus_path,
        "corpus_sha256": sha256_file(corpus_path),
        "corpus_rows": corpus_rows,
        "ledger_path": ledger_path,
        "ledger_rows": ledger_rows,
        "preserved_path": preserved_path,
        "preserved_rows": preserved_rows,
        "human_audit_mode": human_audit_mode,
        "binding": _source_binding(binding_paths),
    }


def _batch_rows(
    source: Mapping[str, Any], batch_size: int
) -> list[tuple[int, list[dict[str, str]]]]:
    if batch_size <= 0:
        raise WorkExtractionError("Batch size must be a positive integer")
    corpus_rows = source["corpus_rows"]
    output: list[tuple[int, list[dict[str, str]]]] = []
    for offset in range(0, len(corpus_rows), batch_size):
        number = offset // batch_size + 1
        rows: list[dict[str, str]] = []
        for index, source_row in enumerate(
            corpus_rows[offset : offset + batch_size], start=offset + 1
        ):
            row = {
                "extraction_schema_version": SCHEMA_VERSION,
                "source_consolidation_manifest_sha256": source["manifest_sha256"],
                "source_one_work_corpus_sha256": source["corpus_sha256"],
                "source_row_number": str(index),
                "extraction_batch": str(number),
                "source_work_row_sha256": sha256_text(
                    canonical_json(
                        {field: source_row[field] for field in SOURCE_CORPUS_FIELDS}
                    )
                ),
                "human_audit_mode": source["human_audit_mode"],
                **dict(source_row),
                **{field: "" for field in EXTRACTION_FIELDS},
            }
            rows.append(row)
        output.append((number, rows))
    return output


def _limitation_payload(human_audit_mode: str) -> dict[str, Any]:
    deferred = human_audit_mode == "explicit_author_deferral"
    return {
        "prospective_human_audit_mode": human_audit_mode,
        "prospective_human_audit_deferred_by_author": deferred,
        "human_reference_standard_available": not deferred,
        "checked_extraction_is_human_validation": False,
        "human_validation_claims_permitted": False,
        "limitation": (
            "The prospective human screening audit was deferred by the corresponding "
            "author. Independent checked extraction supplies work-level source evidence "
            "but is not a human screening reference standard or human validation."
            if deferred
            else "Checked extraction is a separate work-level source-check stage and is "
            "not, by itself, human validation of screening or corpus recall."
        ),
    }


def prepare_extraction_batches(
    consolidation_dir: Path,
    output_dir: Path,
    *,
    batch_size: int = 25,
    analysis_spec: Path = DEFAULT_ANALYSIS_SPEC,
    codebook: Path = DEFAULT_CODEBOOK,
) -> Mapping[str, Any]:
    source = load_consolidation_package(consolidation_dir)
    spec_path, spec_sha, labels, codebook_path, codebook_sha = (
        _validate_analysis_specification(analysis_spec, codebook)
    )
    output = _ensure_new_output(output_dir, source["root"])
    batches = _batch_rows(source, batch_size)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        batch_manifest_rows: list[dict[str, Any]] = []
        batch_entries: list[dict[str, Any]] = []
        for number, rows in batches:
            filename = BATCH_FILENAME.format(number=number)
            path = temp / filename
            write_csv(path, rows, TEMPLATE_FIELDS)
            ids = [row["paper_id"] for row in rows]
            first_row = int(rows[0]["source_row_number"])
            last_row = int(rows[-1]["source_row_number"])
            batch_manifest_rows.append(
                {
                    "batch": number,
                    "file": filename,
                    "first_source_row": first_row,
                    "last_source_row": last_row,
                    "records": len(rows),
                    "first_paper_id": ids[0],
                    "last_paper_id": ids[-1],
                    "ordered_paper_ids_sha256": sha256_text("\0".join(ids)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
            batch_entries.append(file_entry(path, temp, "frozen_blank_extraction_batch"))
        batch_manifest_path = temp / BATCH_MANIFEST
        write_csv(batch_manifest_path, batch_manifest_rows, BATCH_MANIFEST_FIELDS)
        limitation = _limitation_payload(source["human_audit_mode"])
        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "status": PREPARE_STATUS,
            "canonical_works": len(source["corpus_rows"]),
            "batch_size": batch_size,
            "batches": len(batches),
            "first_source_row": 1,
            "last_source_row": len(source["corpus_rows"]),
            "model_A_B_screening_extractions_are_suggestions_only": True,
            "independent_source_check_required_for_every_work": True,
            "source_check_complete": False,
            **limitation,
        }
        summary_path = temp / PREPARATION_SUMMARY
        _write_json(summary_path, summary)
        outputs = {
            "batch_manifest": file_entry(
                batch_manifest_path, temp, "ordered_frozen_batch_manifest"
            ),
            "summary": file_entry(summary_path, temp, "preparation_summary"),
            "batches": batch_entries,
        }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "pipeline": PREPARE_PIPELINE,
            "status": PREPARE_STATUS,
            "inputs": {
                "publication_version_consolidation_manifest": {
                    "path": str(source["manifest_path"]),
                    "sha256": source["manifest_sha256"],
                },
                "one_work_analysis_corpus": {
                    "path": str(source["corpus_path"]),
                    "sha256": source["corpus_sha256"],
                },
                "eligible_publication_version_ledger": {
                    "path": str(source["ledger_path"]),
                    "sha256": sha256_file(source["ledger_path"]),
                },
                "all_record_level_screening_preserved": {
                    "path": str(source["preserved_path"]),
                    "sha256": sha256_file(source["preserved_path"]),
                },
                "analysis_specification": {
                    "path": str(spec_path),
                    "sha256": spec_sha,
                },
                "screening_codebook": {
                    "path": str(codebook_path),
                    "sha256": codebook_sha,
                },
            },
            "counts": {
                "canonical_works": len(source["corpus_rows"]),
                "batches": len(batches),
                "batch_size": batch_size,
            },
            "locked_labels": labels,
            "contracts": {
                "input_status_required": CONSOLIDATION_STATUS,
                "primary_analysis_unit": "one_canonical_scholarly_work",
                "one_row_per_canonical_work": True,
                "every_work_requires_independent_source_check": True,
                "screening_model_A_B_fields_are_suggestions_only": True,
                "screening_suggestions_are_evidence": False,
                "no_silent_inference": True,
                "all_source_fields_and_row_hashes_protected": True,
                "all_batch_templates_frozen_and_hash_bound": True,
                "unclear_allowed_only_for_study_design": True,
                "modalities_and_model_families_must_be_nonblank": True,
                "blank_nts_or_specialty_requires_explicit_rationale_marker": True,
                "human_validation_claims_permitted": False,
            },
            "human_audit_limitation": limitation,
            "outputs": outputs,
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "dependencies": _dependency_hashes(),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp / PREPARATION_MANIFEST
        _write_json(manifest_path, manifest)

        hash_rows: list[dict[str, Any]] = []
        for path, scope, role in (
            (Path(__file__), "code", "work_extraction_program"),
            (spec_path, "input", "locked_analysis_specification"),
            (codebook_path, "input", "locked_screening_codebook"),
            (source["manifest_path"], "input", "consolidation_manifest"),
            (source["corpus_path"], "input", "one_work_analysis_corpus"),
            (source["ledger_path"], "input", "eligible_version_ledger"),
            (
                source["preserved_path"],
                "input",
                "all_record_level_screening_preserved",
            ),
        ):
            hash_rows.append(
                {
                    "scope": scope,
                    "path": str(path.resolve()),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for name, path in sorted(DEPENDENCY_PATHS.items()):
            hash_rows.append(
                {
                    "scope": "code",
                    "path": name,
                    "role": "work_extraction_dependency",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for path, role in (
            (batch_manifest_path, "ordered_frozen_batch_manifest"),
            (summary_path, "preparation_summary"),
            (manifest_path, "preparation_manifest"),
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
        for number, _rows in batches:
            path = temp / BATCH_FILENAME.format(number=number)
            hash_rows.append(
                {
                    "scope": "output",
                    "path": path.name,
                    "role": "frozen_blank_extraction_batch",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        hash_path = temp / PREPARATION_HASH_LEDGER
        _write_hash_ledger(hash_path, hash_rows)
        batch_set_sha = sha256_text(
            "\0".join(
                f"{row['file']}:{row['sha256']}" for row in batch_manifest_rows
            )
        )
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "status": PREPARE_STATUS,
            "preparation_manifest_sha256": sha256_file(manifest_path),
            "preparation_hash_ledger_sha256": sha256_file(hash_path),
            "batch_manifest_sha256": sha256_file(batch_manifest_path),
            "ordered_batch_set_sha256": batch_set_sha,
            "source_consolidation_manifest_sha256": source["manifest_sha256"],
            "source_one_work_corpus_sha256": source["corpus_sha256"],
            "analysis_specification_sha256": spec_sha,
            "screening_codebook_sha256": codebook_sha,
        }
        _write_json(temp / PREPARATION_FROZEN_MARKER, frozen)
        _verify_binding(source["binding"], label="Consolidation input")
        if sha256_file(spec_path) != spec_sha or sha256_file(codebook_path) != codebook_sha:
            raise WorkExtractionError("Locked specification/codebook changed during preparation")
        if sha256_file(Path(__file__)) != manifest["script"]["sha256"]:
            raise WorkExtractionError("Extraction program changed during preparation")
        if _dependency_hashes() != manifest["script"]["dependencies"]:
            raise WorkExtractionError("Extraction dependencies changed during preparation")
        temp.rename(output)
        return manifest
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise


def _validate_preparation_code(manifest: Mapping[str, Any], hash_rows: Sequence[Mapping[str, str]]) -> None:
    script = manifest.get("script") or {}
    if script.get("filename") != Path(__file__).name:
        raise WorkExtractionError("Preparation manifest program filename mismatch")
    if clean(script.get("sha256")).casefold() != sha256_file(Path(__file__)).casefold():
        raise WorkExtractionError(
            "Extraction program changed since the batches were frozen; regenerate them"
        )
    if script.get("dependencies") != _dependency_hashes():
        raise WorkExtractionError(
            "Extraction dependencies changed since the batches were frozen; regenerate them"
        )
    expected = {Path(__file__).name: Path(__file__), **DEPENDENCY_PATHS}
    code_rows = {
        Path(row["path"]).name: row
        for row in hash_rows
        if row["scope"] == "code"
        and row["role"] in {"work_extraction_program", "work_extraction_dependency"}
    }
    if set(code_rows) != set(expected):
        raise WorkExtractionError("Preparation ledger does not bind the full code set")
    for name, path in expected.items():
        row = code_rows[name]
        if (
            row["sha256"].casefold() != sha256_file(path).casefold()
            or row["bytes"] != str(path.stat().st_size)
        ):
            raise WorkExtractionError(f"Frozen preparation code mismatch: {name}")


def load_preparation_package(
    preparation_dir: Path,
    consolidation_dir: Path,
    *,
    analysis_spec: Path = DEFAULT_ANALYSIS_SPEC,
    codebook: Path = DEFAULT_CODEBOOK,
) -> dict[str, Any]:
    source = load_consolidation_package(consolidation_dir)
    spec_path, spec_sha, labels, codebook_path, codebook_sha = (
        _validate_analysis_specification(analysis_spec, codebook)
    )
    root = preparation_dir.resolve()
    _assert_fresh_path(root, role="Frozen extraction preparation")
    if not root.is_dir():
        raise WorkExtractionError(f"Preparation directory does not exist: {root}")
    if _within(root, source["root"]):
        raise WorkExtractionError(
            "Frozen extraction preparation must be separate from consolidation input"
        )
    manifest_path = root / PREPARATION_MANIFEST
    manifest = _load_json(manifest_path)
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("pipeline") != PREPARE_PIPELINE
        or manifest.get("status") != PREPARE_STATUS
    ):
        raise WorkExtractionError("Invalid fresh V2 extraction preparation manifest")
    inputs = manifest.get("inputs") or {}
    expected_inputs = {
        "publication_version_consolidation_manifest": source["manifest_sha256"],
        "one_work_analysis_corpus": source["corpus_sha256"],
        "eligible_publication_version_ledger": sha256_file(source["ledger_path"]),
        "all_record_level_screening_preserved": sha256_file(source["preserved_path"]),
        "analysis_specification": spec_sha,
        "screening_codebook": codebook_sha,
    }
    for name, expected in expected_inputs.items():
        if clean((inputs.get(name) or {}).get("sha256")).casefold() != expected.casefold():
            raise WorkExtractionError(f"Preparation input hash mismatch: {name}")
    if manifest.get("locked_labels") != labels:
        raise WorkExtractionError("Preparation locked-label set or order changed")
    contracts = manifest.get("contracts") or {}
    required_true = (
        "one_row_per_canonical_work",
        "every_work_requires_independent_source_check",
        "screening_model_A_B_fields_are_suggestions_only",
        "no_silent_inference",
        "all_source_fields_and_row_hashes_protected",
        "all_batch_templates_frozen_and_hash_bound",
        "unclear_allowed_only_for_study_design",
        "modalities_and_model_families_must_be_nonblank",
        "blank_nts_or_specialty_requires_explicit_rationale_marker",
    )
    if any(contracts.get(field) is not True for field in required_true):
        raise WorkExtractionError("Preparation extraction contracts are incomplete")
    if (
        contracts.get("screening_suggestions_are_evidence") is not False
        or contracts.get("human_validation_claims_permitted") is not False
    ):
        raise WorkExtractionError("Preparation permits unsupported evidence/validation claims")
    limitation = manifest.get("human_audit_limitation") or {}
    if limitation != _limitation_payload(source["human_audit_mode"]):
        raise WorkExtractionError("Preparation human-audit limitation changed")
    outputs = manifest.get("outputs") or {}
    batch_manifest_path = _validate_manifested_file(
        root, outputs.get("batch_manifest") or {}, label="extraction batch manifest"
    )
    summary_path = _validate_manifested_file(
        root, outputs.get("summary") or {}, label="extraction preparation summary"
    )
    if batch_manifest_path.name != BATCH_MANIFEST or summary_path.name != PREPARATION_SUMMARY:
        raise WorkExtractionError("Preparation output filenames changed")
    batch_manifest_rows = _read_exact_csv(batch_manifest_path, BATCH_MANIFEST_FIELDS)
    try:
        batch_size = int((manifest.get("counts") or {}).get("batch_size", 0))
    except (TypeError, ValueError) as exc:
        raise WorkExtractionError("Preparation manifest has invalid batch size") from exc
    expected_batches = _batch_rows(source, batch_size)
    if len(batch_manifest_rows) != len(expected_batches):
        raise WorkExtractionError("Frozen batch manifest count mismatch")
    batch_paths: list[Path] = []
    all_rows: list[dict[str, str]] = []
    for position, ((number, expected_rows), entry) in enumerate(
        zip(expected_batches, batch_manifest_rows, strict=True), start=1
    ):
        filename = BATCH_FILENAME.format(number=number)
        if entry["batch"] != str(position) or entry["file"] != filename:
            raise WorkExtractionError("Frozen batches are not contiguous/in exact order")
        path = root / filename
        rows = _read_exact_csv(path, TEMPLATE_FIELDS)
        if rows != expected_rows:
            raise WorkExtractionError(
                f"{path}: frozen batch cannot be reproduced from its source corpus"
            )
        if any(any(row[field] for field in EXTRACTION_FIELDS) for row in rows):
            raise WorkExtractionError(f"{path}: frozen batch contains extraction decisions")
        ids = [row["paper_id"] for row in rows]
        expected_entry = {
            "batch": str(number),
            "file": filename,
            "first_source_row": rows[0]["source_row_number"],
            "last_source_row": rows[-1]["source_row_number"],
            "records": str(len(rows)),
            "first_paper_id": ids[0],
            "last_paper_id": ids[-1],
            "ordered_paper_ids_sha256": sha256_text("\0".join(ids)),
            "bytes": str(path.stat().st_size),
            "sha256": sha256_file(path),
        }
        if entry != expected_entry:
            raise WorkExtractionError(f"{batch_manifest_path}: batch {number} mismatch")
        batch_paths.append(path)
        all_rows.extend(rows)
    if [row["paper_id"] for row in all_rows] != [
        row["paper_id"] for row in source["corpus_rows"]
    ]:
        raise WorkExtractionError("Frozen batches do not cover source works once in order")
    expected_batch_entries = [
        file_entry(path, root, "frozen_blank_extraction_batch") for path in batch_paths
    ]
    if outputs.get("batches") != expected_batch_entries:
        raise WorkExtractionError("Preparation manifest batch entries changed")
    required_outputs = [
        BATCH_MANIFEST,
        PREPARATION_SUMMARY,
        PREPARATION_MANIFEST,
        *(path.name for path in batch_paths),
    ]
    hash_rows = _validate_hash_ledger(
        root, PREPARATION_HASH_LEDGER, required_output_paths=required_outputs
    )
    _validate_preparation_code(manifest, hash_rows)
    frozen_path = root / PREPARATION_FROZEN_MARKER
    frozen = _load_json(frozen_path)
    batch_set_sha = sha256_text(
        "\0".join(f"{row['file']}:{row['sha256']}" for row in batch_manifest_rows)
    )
    frozen_expected = {
        "schema_version": SCHEMA_VERSION,
        "status": PREPARE_STATUS,
        "preparation_manifest_sha256": sha256_file(manifest_path),
        "preparation_hash_ledger_sha256": sha256_file(root / PREPARATION_HASH_LEDGER),
        "batch_manifest_sha256": sha256_file(batch_manifest_path),
        "ordered_batch_set_sha256": batch_set_sha,
        "source_consolidation_manifest_sha256": source["manifest_sha256"],
        "source_one_work_corpus_sha256": source["corpus_sha256"],
        "analysis_specification_sha256": spec_sha,
        "screening_codebook_sha256": codebook_sha,
    }
    for field, expected in frozen_expected.items():
        if clean(frozen.get(field)).casefold() != expected.casefold():
            raise WorkExtractionError(f"Frozen preparation marker mismatch for {field}")
    counts = manifest.get("counts") or {}
    if (
        int(counts.get("canonical_works", -1)) != len(source["corpus_rows"])
        or int(counts.get("batches", -1)) != len(batch_paths)
    ):
        raise WorkExtractionError("Preparation manifest count mismatch")
    summary = _load_json(summary_path)
    if (
        summary.get("status") != PREPARE_STATUS
        or int(summary.get("canonical_works", -1)) != len(source["corpus_rows"])
        or int(summary.get("batches", -1)) != len(batch_paths)
        or summary.get("human_validation_claims_permitted") is not False
        or summary.get("source_check_complete") is not False
    ):
        raise WorkExtractionError("Preparation summary contract mismatch")
    binding_paths = [
        manifest_path,
        root / PREPARATION_HASH_LEDGER,
        frozen_path,
        batch_manifest_path,
        summary_path,
        *batch_paths,
        spec_path,
        codebook_path,
        Path(__file__),
        *DEPENDENCY_PATHS.values(),
    ]
    binding = dict(source["binding"])
    binding.update(_source_binding(binding_paths))
    return {
        "root": root,
        "source": source,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "batch_manifest_path": batch_manifest_path,
        "batch_manifest_rows": batch_manifest_rows,
        "batch_paths": batch_paths,
        "batch_rows": [rows for _number, rows in expected_batches],
        "labels": labels,
        "spec_path": spec_path,
        "spec_sha256": spec_sha,
        "codebook_path": codebook_path,
        "codebook_sha256": codebook_sha,
        "binding": binding,
    }


def _split_controlled(
    value: str,
    allowed_order: Sequence[str],
    *,
    path: Path,
    paper_id: str,
    field: str,
    required: bool,
) -> list[str]:
    if not value:
        if required:
            raise WorkExtractionError(f"{path}: {paper_id} has blank {field}")
        return []
    items = value.split(";")
    if any(not item or item != item.strip() for item in items):
        raise WorkExtractionError(f"{path}: {paper_id} has malformed {field}")
    if len(items) != len(set(items)):
        raise WorkExtractionError(f"{path}: {paper_id} has duplicate {field}")
    allowed = set(allowed_order)
    invalid = [item for item in items if item not in allowed]
    if invalid:
        raise WorkExtractionError(
            f"{path}: {paper_id} has unlocked {field} labels: {invalid}"
        )
    indexes = [allowed_order.index(item) for item in items]
    if indexes != sorted(indexes):
        raise WorkExtractionError(
            f"{path}: {paper_id} must list {field} in locked specification order"
        )
    return items


def _validate_specialty(value: str, *, path: Path, paper_id: str) -> None:
    if not value:
        return
    items = value.split(";")
    if any(not item or item != item.strip() for item in items):
        raise WorkExtractionError(f"{path}: {paper_id} has malformed final_specialty")
    folded = [item.casefold() for item in items]
    if len(folded) != len(set(folded)):
        raise WorkExtractionError(f"{path}: {paper_id} has duplicate final_specialty")
    if any(item in PLACEHOLDER_VALUES for item in folded):
        raise WorkExtractionError(
            f"{path}: {paper_id} uses a placeholder as final_specialty"
        )


def _validate_url(value: str, *, path: Path, paper_id: str, field: str) -> None:
    if not value:
        if field == "evidence_url_1":
            raise WorkExtractionError(f"{path}: {paper_id} lacks a source-evidence URL")
        return
    if any(character.isspace() for character in value):
        raise WorkExtractionError(f"{path}: {paper_id} has whitespace in {field}")
    parsed = urlsplit(value)
    if (
        parsed.scheme.casefold() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise WorkExtractionError(
            f"{path}: {paper_id} has invalid HTTP(S) evidence URL in {field}"
        )


def _validate_completed_extraction(
    row: Mapping[str, str],
    labels: Mapping[str, Sequence[str]],
    *,
    path: Path,
) -> None:
    paper_id = row["paper_id"]
    for field in EXTRACTION_FIELDS:
        value = row[field]
        if value != value.strip():
            raise WorkExtractionError(
                f"{path}: {paper_id} has leading/trailing whitespace in {field}"
            )
    _split_controlled(
        row["final_simulation_modalities"],
        labels["simulation_methods"],
        path=path,
        paper_id=paper_id,
        field="final_simulation_modalities",
        required=True,
    )
    _split_controlled(
        row["final_nts_domains"],
        labels["nts_domains"],
        path=path,
        paper_id=paper_id,
        field="final_nts_domains",
        required=False,
    )
    _split_controlled(
        row["final_model_families"],
        labels["model_families"],
        path=path,
        paper_id=paper_id,
        field="final_model_families",
        required=True,
    )
    _validate_specialty(row["final_specialty"], path=path, paper_id=paper_id)
    design = row["final_study_design"]
    if design not in labels["study_designs"]:
        raise WorkExtractionError(
            f"{path}: {paper_id} has unlocked final_study_design {design!r}"
        )
    raw_description = row["final_model_description_raw"]
    if not raw_description or raw_description.casefold() in PLACEHOLDER_VALUES:
        raise WorkExtractionError(
            f"{path}: {paper_id} lacks a source-grounded raw model description"
        )
    rationale = row["extraction_rationale"]
    if len(rationale) < 20 or rationale.casefold() in PLACEHOLDER_VALUES:
        raise WorkExtractionError(
            f"{path}: {paper_id} needs a substantive extraction rationale"
        )
    if not row["final_nts_domains"] and BLANK_NTS_MARKER not in rationale:
        raise WorkExtractionError(
            f"{path}: {paper_id} blank NTS requires {BLANK_NTS_MARKER}"
        )
    if not row["final_specialty"] and BLANK_SPECIALTY_MARKER not in rationale:
        raise WorkExtractionError(
            f"{path}: {paper_id} blank specialty requires {BLANK_SPECIALTY_MARKER}"
        )
    if design == "unclear" and UNCLEAR_DESIGN_MARKER not in rationale:
        raise WorkExtractionError(
            f"{path}: {paper_id} unclear design requires {UNCLEAR_DESIGN_MARKER}"
        )
    _validate_url(row["evidence_url_1"], path=path, paper_id=paper_id, field="evidence_url_1")
    _validate_url(row["evidence_url_2"], path=path, paper_id=paper_id, field="evidence_url_2")
    reviewer = row["source_checked_by"]
    if not reviewer or reviewer.casefold() in PLACEHOLDER_VALUES:
        raise WorkExtractionError(f"{path}: {paper_id} lacks a named source checker")
    timestamp = row["source_checked_at_utc"]
    if not UTC_RE.fullmatch(timestamp):
        raise WorkExtractionError(
            f"{path}: {paper_id} source_checked_at_utc must be YYYY-MM-DDTHH:MM:SSZ"
        )
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise WorkExtractionError(
            f"{path}: {paper_id} has invalid source_checked_at_utc"
        ) from exc
    if row["source_check_attestation"] != SOURCE_CHECK_ATTESTATION:
        raise WorkExtractionError(
            f"{path}: {paper_id} lacks the independent source-check attestation"
        )
    if row["screening_suggestions_role"] != SUGGESTIONS_ROLE:
        raise WorkExtractionError(
            f"{path}: {paper_id} must attest that screening suggestions are not evidence"
        )


def load_completed_batches(
    preparation: Mapping[str, Any], completed_dir: Path
) -> dict[str, Any]:
    root = completed_dir.resolve()
    _assert_fresh_path(root, role="Completed extraction batches")
    if not root.is_dir():
        raise WorkExtractionError(f"Completed-batch directory does not exist: {root}")
    for frozen_root in (preparation["root"], preparation["source"]["root"]):
        if _within(root, frozen_root):
            raise WorkExtractionError(
                f"Completed batches must not be stored inside frozen input: {frozen_root}"
            )
    expected_names = [path.name for path in preparation["batch_paths"]]
    observed_names = sorted(path.name for path in root.glob("*.csv"))
    if observed_names != sorted(expected_names):
        missing = sorted(set(expected_names) - set(observed_names))
        extra = sorted(set(observed_names) - set(expected_names))
        raise WorkExtractionError(
            f"Completed-batch set is not exact; missing={missing}, extra={extra}"
        )
    merged: list[dict[str, str]] = []
    paths: list[Path] = []
    hashes: dict[str, str] = {}
    for frozen_path, frozen_rows in zip(
        preparation["batch_paths"], preparation["batch_rows"], strict=True
    ):
        path = root / frozen_path.name
        rows = _read_exact_csv(path, TEMPLATE_FIELDS)
        if len(rows) != len(frozen_rows):
            raise WorkExtractionError(f"{path}: completed row count mismatch")
        for position, (row, frozen_row) in enumerate(
            zip(rows, frozen_rows, strict=True), start=2
        ):
            changed = [
                field
                for field in PROTECTED_TEMPLATE_FIELDS
                if row[field] != frozen_row[field]
            ]
            if changed:
                raise WorkExtractionError(
                    f"{path}:{position}: protected source/binding fields changed: {changed}"
                )
            _validate_completed_extraction(
                row, preparation["labels"], path=path
            )
        paths.append(path)
        hashes[path.name] = sha256_file(path)
        merged.extend(rows)
    source_ids = [row["paper_id"] for row in preparation["source"]["corpus_rows"]]
    merged_ids = [row["paper_id"] for row in merged]
    if merged_ids != source_ids or len(merged_ids) != len(set(merged_ids)):
        raise WorkExtractionError(
            "Completed batches do not cover every canonical work once in source order"
        )
    return {
        "root": root,
        "paths": paths,
        "hashes": hashes,
        "rows": merged,
        "binding": _source_binding(paths),
    }


def finalize_extraction(
    consolidation_dir: Path,
    preparation_dir: Path,
    completed_dir: Path,
    output_dir: Path,
    *,
    analysis_spec: Path = DEFAULT_ANALYSIS_SPEC,
    codebook: Path = DEFAULT_CODEBOOK,
) -> Mapping[str, Any]:
    preparation = load_preparation_package(
        preparation_dir,
        consolidation_dir,
        analysis_spec=analysis_spec,
        codebook=codebook,
    )
    completed = load_completed_batches(preparation, completed_dir)
    output = _ensure_new_output(
        output_dir, preparation["source"]["root"], preparation["root"], completed["root"]
    )
    source_rows = preparation["source"]["corpus_rows"]
    checked_rows: list[dict[str, str]] = []
    ledger_rows: list[dict[str, str]] = []
    batch_template_hashes = {
        row["file"]: row["sha256"] for row in preparation["batch_manifest_rows"]
    }
    for source_row, completed_row in zip(source_rows, completed["rows"], strict=True):
        binding = {field: completed_row[field] for field in BINDING_FIELDS}
        extraction = {field: completed_row[field] for field in EXTRACTION_FIELDS}
        checked_rows.append({**dict(source_row), **binding, **extraction})
        batch_name = BATCH_FILENAME.format(number=int(completed_row["extraction_batch"]))
        ledger_rows.append(
            {
                "extraction_schema_version": SCHEMA_VERSION,
                "paper_id": source_row["paper_id"],
                "version_family_id": source_row["version_family_id"],
                "title": source_row["title"],
                "doi": source_row["doi"],
                "source_consolidation_manifest_sha256": completed_row[
                    "source_consolidation_manifest_sha256"
                ],
                "source_one_work_corpus_sha256": completed_row[
                    "source_one_work_corpus_sha256"
                ],
                "source_row_number": completed_row["source_row_number"],
                "extraction_batch": completed_row["extraction_batch"],
                "source_work_row_sha256": completed_row["source_work_row_sha256"],
                "human_audit_mode": completed_row["human_audit_mode"],
                "frozen_preparation_manifest_sha256": preparation["manifest_sha256"],
                "frozen_batch_template_sha256": batch_template_hashes[batch_name],
                "completed_batch_sha256": completed["hashes"][batch_name],
                **extraction,
            }
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        merged_path = temp / MERGED_COMPLETED
        checked_path = temp / CHECKED_CORPUS
        ledger_path = temp / EXTRACTION_LEDGER
        write_csv(merged_path, completed["rows"], TEMPLATE_FIELDS)
        write_csv(checked_path, checked_rows, CHECKED_CORPUS_FIELDS)
        write_csv(ledger_path, ledger_rows, EXTRACTION_LEDGER_FIELDS)
        limitation = _limitation_payload(preparation["source"]["human_audit_mode"])
        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "status": FINAL_STATUS,
            "canonical_works_checked": len(checked_rows),
            "completed_batches": len(completed["paths"]),
            "source_order_preserved": True,
            "all_source_rows_hash_validated": True,
            "all_works_independently_source_checked": True,
            "model_A_B_screening_extractions_used_as_suggestions_only": True,
            "screening_suggestions_used_as_evidence": False,
            "checked_work_level_extraction_complete": True,
            **limitation,
        }
        summary_path = temp / FINALIZATION_SUMMARY
        _write_json(summary_path, summary)
        outputs = {
            "merged_completed_extractions": file_entry(
                merged_path, temp, "validated_completed_batches_in_source_order"
            ),
            "checked_one_work_corpus": file_entry(
                checked_path, temp, "checked_one_work_analysis_corpus"
            ),
            "checked_extraction_ledger": file_entry(
                ledger_path, temp, "one_row_per_work_extraction_provenance"
            ),
            "summary": file_entry(summary_path, temp, "extraction_finalization_summary"),
        }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "pipeline": FINALIZE_PIPELINE,
            "status": FINAL_STATUS,
            "inputs": {
                "publication_version_consolidation_manifest": {
                    "path": str(preparation["source"]["manifest_path"]),
                    "sha256": preparation["source"]["manifest_sha256"],
                },
                "one_work_analysis_corpus": {
                    "path": str(preparation["source"]["corpus_path"]),
                    "sha256": preparation["source"]["corpus_sha256"],
                },
                "frozen_extraction_preparation_manifest": {
                    "path": str(preparation["manifest_path"]),
                    "sha256": preparation["manifest_sha256"],
                },
                "analysis_specification": {
                    "path": str(preparation["spec_path"]),
                    "sha256": preparation["spec_sha256"],
                },
                "screening_codebook": {
                    "path": str(preparation["codebook_path"]),
                    "sha256": preparation["codebook_sha256"],
                },
                "completed_batches": [
                    {
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "sha256": completed["hashes"][path.name],
                    }
                    for path in completed["paths"]
                ],
            },
            "counts": {
                "canonical_works": len(checked_rows),
                "completed_batches": len(completed["paths"]),
                "checked_corpus_rows": len(checked_rows),
                "extraction_ledger_rows": len(ledger_rows),
            },
            "locked_labels": preparation["labels"],
            "contracts": {
                "source_corpus_unchanged": True,
                "source_order_preserved": True,
                "every_frozen_batch_completed_exactly_once": True,
                "every_canonical_work_source_checked": True,
                "screening_model_A_B_fields_are_suggestions_only": True,
                "screening_suggestions_are_evidence": False,
                "final_fields_come_only_from_checked_extraction": True,
                "no_silent_inference": True,
                "unclear_allowed_only_for_study_design": True,
                "modalities_and_model_families_nonblank": True,
                "blank_nts_or_specialty_has_explicit_rationale": True,
                "human_validation_claims_permitted": False,
                "analysis_ready_checked_work_extraction": True,
            },
            "human_audit_limitation": limitation,
            "outputs": outputs,
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "dependencies": _dependency_hashes(),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp / FINALIZATION_MANIFEST
        _write_json(manifest_path, manifest)
        hash_rows: list[dict[str, Any]] = []
        for path, scope, role in (
            (Path(__file__), "code", "work_extraction_program"),
            (preparation["spec_path"], "input", "locked_analysis_specification"),
            (preparation["codebook_path"], "input", "locked_screening_codebook"),
            (
                preparation["source"]["manifest_path"],
                "input",
                "consolidation_manifest",
            ),
            (
                preparation["source"]["corpus_path"],
                "input",
                "one_work_analysis_corpus",
            ),
            (preparation["manifest_path"], "input", "frozen_preparation_manifest"),
        ):
            hash_rows.append(
                {
                    "scope": scope,
                    "path": str(path.resolve()),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for name, path in sorted(DEPENDENCY_PATHS.items()):
            hash_rows.append(
                {
                    "scope": "code",
                    "path": name,
                    "role": "work_extraction_dependency",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        for path in completed["paths"]:
            hash_rows.append(
                {
                    "scope": "input",
                    "path": str(path),
                    "role": "completed_extraction_batch",
                    "bytes": path.stat().st_size,
                    "sha256": completed["hashes"][path.name],
                }
            )
        for path, role in (
            (merged_path, "validated_completed_batches_in_source_order"),
            (checked_path, "checked_one_work_analysis_corpus"),
            (ledger_path, "one_row_per_work_extraction_provenance"),
            (summary_path, "extraction_finalization_summary"),
            (manifest_path, "extraction_finalization_manifest"),
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
        hash_path = temp / FINALIZATION_HASH_LEDGER
        _write_hash_ledger(hash_path, hash_rows)
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "status": FINAL_STATUS,
            "finalization_manifest_sha256": sha256_file(manifest_path),
            "finalization_hash_ledger_sha256": sha256_file(hash_path),
            "checked_one_work_corpus_sha256": sha256_file(checked_path),
            "checked_extraction_ledger_sha256": sha256_file(ledger_path),
            "merged_completed_extractions_sha256": sha256_file(merged_path),
            "source_consolidation_manifest_sha256": preparation["source"]
            ["manifest_sha256"],
            "source_one_work_corpus_sha256": preparation["source"]["corpus_sha256"],
            "frozen_preparation_manifest_sha256": preparation["manifest_sha256"],
            "analysis_specification_sha256": preparation["spec_sha256"],
            "screening_codebook_sha256": preparation["codebook_sha256"],
        }
        _write_json(temp / FINALIZATION_FROZEN_MARKER, frozen)

        if _read_exact_csv(merged_path, TEMPLATE_FIELDS) != completed["rows"]:
            raise AssertionError("Merged completed extraction rows changed")
        if _read_exact_csv(checked_path, CHECKED_CORPUS_FIELDS) != checked_rows:
            raise AssertionError("Checked corpus rows changed")
        if _read_exact_csv(ledger_path, EXTRACTION_LEDGER_FIELDS) != ledger_rows:
            raise AssertionError("Extraction ledger rows changed")
        _verify_binding(preparation["binding"], label="Frozen extraction/source input")
        _verify_binding(completed["binding"], label="Completed extraction batch")
        if sha256_file(Path(__file__)) != manifest["script"]["sha256"]:
            raise WorkExtractionError("Extraction program changed during finalization")
        if _dependency_hashes() != manifest["script"]["dependencies"]:
            raise WorkExtractionError("Extraction dependencies changed during finalization")
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
        "prepare", help="Create exact frozen blank work-extraction batches"
    )
    prepare.add_argument("--consolidation-dir", required=True, type=Path)
    prepare.add_argument("--output-dir", required=True, type=Path)
    prepare.add_argument("--batch-size", type=int, default=25)
    prepare.add_argument("--analysis-spec", type=Path, default=DEFAULT_ANALYSIS_SPEC)
    prepare.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)

    finalize = subparsers.add_parser(
        "finalize", help="Validate and merge every completed frozen extraction batch"
    )
    finalize.add_argument("--consolidation-dir", required=True, type=Path)
    finalize.add_argument("--preparation-dir", required=True, type=Path)
    finalize.add_argument("--completed-dir", required=True, type=Path)
    finalize.add_argument("--output-dir", required=True, type=Path)
    finalize.add_argument("--analysis-spec", type=Path, default=DEFAULT_ANALYSIS_SPEC)
    finalize.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            manifest = prepare_extraction_batches(
                args.consolidation_dir,
                args.output_dir,
                batch_size=args.batch_size,
                analysis_spec=args.analysis_spec,
                codebook=args.codebook,
            )
        else:
            manifest = finalize_extraction(
                args.consolidation_dir,
                args.preparation_dir,
                args.completed_dir,
                args.output_dir,
                analysis_spec=args.analysis_spec,
                codebook=args.codebook,
            )
    except WorkExtractionError as exc:
        parser.error(str(exc))
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
