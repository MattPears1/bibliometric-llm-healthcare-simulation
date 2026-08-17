#!/usr/bin/env python3
"""Build the final six-source analysis from a hash-locked combined corpus.

V5 is deliberately fail-closed.  The checked-in input contract is a scaffold,
not permission to run the analysis.  A production run is possible only after
the contract is changed to ``ready_for_production`` and every pending final
file has a verified path, byte count, row count, and SHA-256 digest.

The engine never changes an upstream package.  It writes to a new temporary
directory, rechecks every input hash, and atomically publishes a new output
directory only after all tables, figures, ledgers, and acceptance gates pass.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import shutil
import sys
import tempfile
import textwrap
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


HERE = Path(__file__).resolve().parent
PIPELINE_DIR = HERE.parent
ACTIVE_ROOT = PIPELINE_DIR.parent
WORKSPACE = ACTIVE_ROOT.parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

import fresh_analysis_engine_v2 as v2  # noqa: E402


SCHEMA_VERSION = "gse-combined-analysis-engine-v5.0"
CONTRACT_SCHEMA_VERSION = "gse-combined-analysis-input-contract-v5.0"
PIPELINE = "gse_six_source_combined_analysis_v5"
FINAL_STATUS = "gse_six_source_combined_analysis_v5_completed_hash_frozen"
SCAFFOLD_STATUS = "scaffold_awaiting_final_inputs"
READY_STATUS = "ready_for_production"

DEFAULT_CONTRACT = HERE / "COMBINED_ANALYSIS_INPUT_CONTRACT_V5_SCAFFOLD_2026-08-16.json"

OUTPUT_MANIFEST = "COMBINED_ANALYSIS_OUTPUT_MANIFEST_V5.json"
OUTPUT_HASH_LEDGER = "COMBINED_ANALYSIS_HASH_MANIFEST_V5.csv"
OUTPUT_FROZEN_MARKER = "COMBINED_ANALYSIS_FROZEN_V5.json"
OUTPUT_SUMMARY = "COMBINED_ANALYSIS_SUMMARY_V5.json"

SIX_SOURCES = (
    "openalex",
    "pubmed",
    "europepmc",
    "semantic_scholar",
    "doaj",
    "scopus",
)
SCOPUS_CORRECTED_RECORD_ID = "sci_42a355e3f11b03dc7d88"
SCOPUS_EXTRACTION_FINALIZATION_SHA256 = (
    "1b72bcec2215f500bd2c874293249d0c3cc5f40bee06b5bf4fe5882b9651dd28"
)

LOCKED_ROLE_NAMES = {
    "analysis_specification",
    "amendment_001",
    "amendment_002",
    "amendment_003",
    "amendment_004",
    "amendment_005_superseded",
    "primary_raw_manifest",
    "primary_normalization_manifest",
    "primary_deduplication_manifest",
    "primary_candidate_manifest",
    "primary_review_comparison",
    "primary_review_comparison_manifest",
    "base_correction_manifest",
    "base_correction_hash_ledger",
    "base_final_screening",
    "base_eligible_version_ledger",
    "base_checked_corpus",
    "base_openalex",
    "metadata_correction_manifest",
    "metadata_correction_ledger",
    "human_audit_summary",
    "human_audit_finalization_manifest",
    "scopus_raw_manifest",
    "scopus_bridge_manifest",
    "scopus_review_comparison",
    "scopus_review_comparison_manifest",
    "scopus_finalization_manifest",
    "scopus_finalization_hash_ledger",
    "scopus_final_screening",
    "scopus_included_records",
    "scopus_version_review_preparation_manifest",
    "scopus_version_review_preparation_hash_ledger",
    "scopus_metadata_manifest",
    "scopus_metadata_hash_ledger",
    "scopus_openalex",
}

FINAL_ROLE_NAMES = {
    "amendment_006_final_correction_and_integration",
    "scopus_corrected_finalization_manifest",
    "scopus_corrected_finalization_hash_ledger",
    "scopus_corrected_final_screening",
    "scopus_corrected_included_records",
    "scopus_extraction_manifest",
    "scopus_checked_extraction",
    "scopus_extraction_hash_ledger",
    "scopus_completed_version_decisions",
    "scopus_version_decision_manifest",
    "scopus_version_decision_hash_ledger",
    "combined_package_manifest",
    "combined_package_hash_ledger",
    "combined_package_frozen_marker",
    "combined_eligible_version_ledger",
    "combined_study_selection_ledger",
    "combined_checked_corpus",
    "combined_metadata",
    "combined_openalex",
    "combined_record_level_screening",
}

WORK_REQUIRED_COLUMNS = {
    "paper_id",
    "version_family_id",
    "doi",
    "title",
    "year",
    "publication_date",
    "journal",
    "found_in_sources",
    "record_type",
    "abstract",
    "source_keywords",
    "family_size",
    "version_role",
    "final_model_families",
    "final_simulation_modalities",
    "final_nts_domains",
    "final_specialty",
    "final_study_design",
    "source_checked_by",
    "source_checked_at_utc",
    "evidence_url_1",
    "evidence_url_2",
}

VERSION_REQUIRED_COLUMNS = {
    "integration_schema_version",
    "source_completed_family_review_sha256",
    "provisional_family_id",
    "family_size",
    "record_key",
    "source_record_id",
    "source_corpus",
    "preferred_for_analysis",
    "preferred_record_key",
    "relationship_to_preferred",
}

AUTHOR_LEDGER_FIELDS = [
    "author_key",
    "openalex_author_id",
    "display_name",
    "identity_type",
    "unresolved_name_flag",
    "work_count",
    "work_ids",
]

SPECIALTY_LEDGER_FIELDS = [
    "raw_label",
    "plain_label",
    "display_group",
    "work_count",
    "included_in_figure_5",
    "classification_rule",
    "work_ids",
]

CLAIM_REGISTER_FIELDS = [
    "claim_id",
    "artifact",
    "row_number",
    "section",
    "measure",
    "category",
    "reported_value",
    "denominator",
    "input_bundle_sha256",
    "source_table_row_sha256",
]

INPUT_BINDING_FIELDS = ["role", "path", "bytes", "rows", "sha256", "state"]
FIGURE_MANIFEST_FIELDS = [
    "figure_stem",
    "png_path",
    "eps_path",
    "png_width_px",
    "png_height_px",
    "png_dpi_x",
    "png_dpi_y",
    "png_sha256",
    "eps_sha256",
]


class CombinedAnalysisError(v2.FreshAnalysisError):
    """Raised when the V5 input or output contract is violated."""


def _clean(value: Any) -> str:
    return v2.clean(value)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_row_sha(row: Mapping[str, Any]) -> str:
    return v2.sha256_text(v2.canonical_json({str(k): row[k] for k in sorted(row)}))


def read_csv_any(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise CombinedAnalysisError(f"Invalid or duplicated CSV header: {path}")
        fields = list(reader.fieldnames)
        rows = list(reader)
    for number, row in enumerate(rows, start=2):
        if None in row or set(row) != set(fields):
            raise CombinedAnalysisError(f"Malformed CSV row at {path}:{number}")
    return fields, rows


def _resolve_workspace_path(value: Any, label: str) -> Path:
    text = _clean(value)
    if not text:
        raise CombinedAnalysisError(f"Missing path for {label}")
    path = Path(text)
    if not path.is_absolute():
        path = WORKSPACE / path
    path = path.resolve()
    try:
        path.relative_to(WORKSPACE.resolve())
    except ValueError as exc:
        raise CombinedAnalysisError(f"{label} leaves the workspace: {path}") from exc
    return path


def _nested_value(value: Any, dotted: str) -> Any:
    current = value
    for part in dotted.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise CombinedAnalysisError(f"Expected JSON key is absent: {dotted}")
        current = current[part]
    return current


def _validate_pin(role: str, pin: Mapping[str, Any]) -> dict[str, Any]:
    if pin.get("state") != "locked":
        raise CombinedAnalysisError(f"Input role is not locked: {role}")
    path = _resolve_workspace_path(pin.get("path"), role)
    if not path.is_file():
        raise CombinedAnalysisError(f"Locked input is missing: {role}: {path}")
    expected_sha = _clean(pin.get("sha256")).casefold()
    if not v2.SHA256_RE.fullmatch(expected_sha):
        raise CombinedAnalysisError(f"Invalid SHA-256 pin for {role}")
    actual_sha = v2.sha256_file(path)
    if actual_sha != expected_sha:
        raise CombinedAnalysisError(f"SHA-256 mismatch for {role}")
    expected_bytes = pin.get("bytes")
    if expected_bytes is not None and v2.integer(expected_bytes, f"bytes/{role}") != path.stat().st_size:
        raise CombinedAnalysisError(f"Byte-count mismatch for {role}")

    fields: list[str] | None = None
    rows: list[dict[str, str]] | None = None
    expected_rows = pin.get("rows")
    required_columns = pin.get("required_columns") or []
    if path.suffix.casefold() == ".csv" and (expected_rows is not None or required_columns):
        fields, rows = read_csv_any(path)
        if expected_rows is not None and len(rows) != v2.integer(expected_rows, f"rows/{role}"):
            raise CombinedAnalysisError(f"Row-count mismatch for {role}")
        missing = set(required_columns) - set(fields)
        if missing:
            raise CombinedAnalysisError(f"Required columns missing for {role}: {sorted(missing)}")

    expected_json = pin.get("expected_json") or {}
    if expected_json:
        document = v2.load_json(path, role)
        for dotted, expected in expected_json.items():
            if _nested_value(document, dotted) != expected:
                raise CombinedAnalysisError(
                    f"JSON contract mismatch for {role}.{dotted}: "
                    f"expected {expected!r}, found {_nested_value(document, dotted)!r}"
                )
    return {
        "role": role,
        "path": path,
        "sha256": actual_sha,
        "bytes": path.stat().st_size,
        "rows": len(rows) if rows is not None else expected_rows,
        "fields": fields,
        "loaded_rows": rows,
        "state": "locked",
    }


def _validate_selection_contract(selection: Mapping[str, Any], *, production: bool) -> dict[str, int]:
    source_counts_raw = selection.get("retrieval_occurrences_by_source") or {}
    if tuple(source_counts_raw) != SIX_SOURCES:
        raise CombinedAnalysisError(
            "Retrieval sources must be the fixed ordered six-source list: " + ", ".join(SIX_SOURCES)
        )
    source_counts = {
        source: v2.integer(source_counts_raw[source], f"retrieval/{source}")
        for source in SIX_SOURCES
    }
    total_raw = v2.integer(selection.get("retrieval_occurrences_total"), "raw retrieval total")
    if sum(source_counts.values()) != total_raw:
        raise CombinedAnalysisError("Six source counts do not sum to the raw retrieval total")

    cutoff = v2.integer(selection.get("scopus_after_cutoff_removed"), "Scopus cutoff exclusions")
    after_scopus_cutoff = v2.integer(
        selection.get("retrieval_occurrences_after_scopus_cutoff"),
        "retrievals entering duplicate handling",
    )
    if source_counts["scopus"] < cutoff or total_raw - cutoff != after_scopus_cutoff:
        raise CombinedAnalysisError("Scopus cutoff arithmetic does not reconcile")

    primary_dates_raw = selection.get("primary_five_occurrence_date_status") or {}
    required_primary_date_keys = {
        "inside_window",
        "before_window",
        "after_window",
        "unknown",
        "unresolved_boundary",
    }
    if set(primary_dates_raw) != required_primary_date_keys:
        raise CombinedAnalysisError("Primary-source occurrence date-status categories changed")
    primary_dates = {
        key: v2.integer(value, f"primary occurrence date status/{key}")
        for key, value in primary_dates_raw.items()
    }
    primary_total = sum(source_counts[source] for source in SIX_SOURCES if source != "scopus")
    if sum(primary_dates.values()) != primary_total:
        raise CombinedAnalysisError("Primary-source occurrence date-status rows do not sum")

    automatic_parts_raw = selection.get("automatic_duplicate_merges") or {}
    automatic_parts = {
        key: v2.integer(value, f"automatic duplicate merges/{key}")
        for key, value in automatic_parts_raw.items()
        if key != "total"
    }
    automatic_total = v2.integer(automatic_parts_raw.get("total"), "automatic duplicate total")
    if sum(automatic_parts.values()) != automatic_total:
        raise CombinedAnalysisError("Automatic duplicate-merge components do not sum")
    after_automatic = v2.integer(selection.get("records_after_automatic_merging"), "post-automatic records")
    if after_scopus_cutoff - automatic_total != after_automatic:
        raise CombinedAnalysisError("Automatic duplicate-merge arithmetic does not reconcile")

    reviewed_parts_raw = selection.get("reviewed_same_record_merges") or {}
    reviewed_parts = {
        key: v2.integer(value, f"reviewed same-record merges/{key}")
        for key, value in reviewed_parts_raw.items()
        if key != "total"
    }
    reviewed_total = v2.integer(reviewed_parts_raw.get("total"), "reviewed same-record total")
    if sum(reviewed_parts.values()) != reviewed_total:
        raise CombinedAnalysisError("Reviewed same-record components do not sum")
    deduplicated = v2.integer(selection.get("deduplicated_records"), "deduplicated records")
    if after_automatic - reviewed_total != deduplicated:
        raise CombinedAnalysisError("Reviewed same-record arithmetic does not reconcile")

    candidates_raw = selection.get("candidate_records") or {}
    candidate_parts = {
        key: v2.integer(value, f"candidate records/{key}")
        for key, value in candidates_raw.items()
        if key != "total"
    }
    candidate_total = v2.integer(candidates_raw.get("total"), "candidate total")
    if sum(candidate_parts.values()) != candidate_total:
        raise CombinedAnalysisError("Candidate stream counts do not sum")
    outside = v2.integer(selection.get("records_outside_candidate_frame"), "outside candidate frame")
    if deduplicated - candidate_total != outside:
        raise CombinedAnalysisError("Candidate-frame arithmetic does not reconcile")

    resolution_raw = selection.get("separate_resolution_checks") or {}
    resolution_parts = {
        key: v2.integer(value, f"resolution checks/{key}")
        for key, value in resolution_raw.items()
        if key != "total"
    }
    resolution_total = v2.integer(resolution_raw.get("total"), "resolution total")
    if sum(resolution_parts.values()) != resolution_total or resolution_total > candidate_total:
        raise CombinedAnalysisError("Review-resolution components do not reconcile")

    final_out_of_range = v2.integer(
        selection.get("final_out_of_range_exclusions"),
        "final out-of-range exclusions",
    )
    if final_out_of_range > candidate_total:
        raise CombinedAnalysisError("Out-of-range exclusions exceed the candidate frame")

    included_raw = selection.get("eligible_publication_records")
    excluded_raw = selection.get("excluded_candidate_records")
    if production:
        if included_raw is None or excluded_raw is None:
            raise CombinedAnalysisError("Production contract must record final included and excluded counts")
        included = v2.integer(included_raw, "eligible publications")
        excluded = v2.integer(excluded_raw, "excluded candidates")
        if included + excluded != candidate_total:
            raise CombinedAnalysisError("Final record decisions do not reconcile with candidates")
    else:
        if (included_raw is None) != (excluded_raw is None):
            raise CombinedAnalysisError("Final included and excluded counts must both be set or both be pending")
        included = 0 if included_raw is None else v2.integer(included_raw, "eligible publications")
        excluded = 0 if excluded_raw is None else v2.integer(excluded_raw, "excluded candidates")
        if included_raw is not None and included + excluded != candidate_total:
            raise CombinedAnalysisError("Final record decisions do not reconcile with candidates")

    final_n = selection.get("canonical_works")
    if production:
        if final_n is None:
            raise CombinedAnalysisError("Production contract must record the derived canonical-work count")
        final_n_int = v2.integer(final_n, "canonical works", minimum=1)
        if final_n_int > included:
            raise CombinedAnalysisError("Canonical works exceed eligible publication records")
    else:
        final_n_int = 0 if final_n is None else v2.integer(final_n, "canonical works", minimum=1)
    return {
        **{f"source_{key}": value for key, value in source_counts.items()},
        "raw": total_raw,
        "cutoff": cutoff,
        "after_scopus_cutoff": after_scopus_cutoff,
        "primary_date_flagged_outside": primary_dates["before_window"] + primary_dates["after_window"],
        "primary_date_unknown_or_unresolved": primary_dates["unknown"] + primary_dates["unresolved_boundary"],
        "automatic": automatic_total,
        "after_automatic": after_automatic,
        "reviewed": reviewed_total,
        "deduplicated": deduplicated,
        "candidates": candidate_total,
        "outside": outside,
        "resolution": resolution_total,
        "final_out_of_range": final_out_of_range,
        "included": included,
        "excluded": excluded,
        "canonical": final_n_int,
    }


def _validate_oversight_contract(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {
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
    }
    if dict(value) != required:
        raise CombinedAnalysisError("Lead-author oversight contract changed or is incomplete")
    return required


def validate_input_contract(
    contract_path: Path,
    *,
    production: bool,
    validate_locked_files: bool = True,
) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    contract = v2.load_json(contract_path, "V5 input contract")
    if contract.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise CombinedAnalysisError("V5 input-contract schema is wrong")
    status = contract.get("status")
    if status not in {SCAFFOLD_STATUS, READY_STATUS}:
        raise CombinedAnalysisError(f"Unknown V5 input-contract status: {status!r}")
    if production and status != READY_STATUS:
        raise CombinedAnalysisError("The V5 contract is still a scaffold; production is blocked")
    window = contract.get("study_window") or {}
    if window != {"from": "2020-01-01", "through": "2026-08-13", "inclusive": True}:
        raise CombinedAnalysisError("Study-window contract changed")
    selection = _validate_selection_contract(contract.get("selection_flow") or {}, production=production)
    oversight = _validate_oversight_contract(contract.get("lead_author_oversight") or {})

    inputs = contract.get("inputs") or {}
    missing_roles = (LOCKED_ROLE_NAMES | FINAL_ROLE_NAMES) - set(inputs)
    unexpected_roles = set(inputs) - (LOCKED_ROLE_NAMES | FINAL_ROLE_NAMES)
    if missing_roles or unexpected_roles:
        raise CombinedAnalysisError(
            f"Input roles differ from V5 contract; missing={sorted(missing_roles)}, "
            f"unexpected={sorted(unexpected_roles)}"
        )
    pending_roles = sorted(role for role, pin in inputs.items() if pin.get("state") == "pending")
    if production and pending_roles:
        raise CombinedAnalysisError(f"Production inputs remain pending: {pending_roles}")
    if any(inputs[role].get("state") != "locked" for role in LOCKED_ROLE_NAMES):
        raise CombinedAnalysisError("A previously available upstream input is no longer locked")
    if production and any(inputs[role].get("state") != "locked" for role in FINAL_ROLE_NAMES):
        raise CombinedAnalysisError("One or more final combined-corpus inputs are not locked")

    validated: dict[str, dict[str, Any]] = {}
    if validate_locked_files:
        for role, pin in inputs.items():
            if pin.get("state") == "locked":
                validated[role] = _validate_pin(role, pin)
    return {
        "contract": contract,
        "contract_path": contract_path,
        "contract_sha256": v2.sha256_file(contract_path),
        "selection": selection,
        "oversight": oversight,
        "inputs": validated,
        "pending_roles": pending_roles,
        "ready": status == READY_STATUS and not pending_roles,
    }


def _rows_for(validated: Mapping[str, Any], role: str) -> tuple[list[str], list[dict[str, str]]]:
    pin = validated["inputs"].get(role)
    if pin is None:
        raise CombinedAnalysisError(f"Required validated input role is absent: {role}")
    if pin.get("loaded_rows") is not None and pin.get("fields") is not None:
        return list(pin["fields"]), list(pin["loaded_rows"])
    return read_csv_any(pin["path"])


def _true(value: Any) -> bool:
    return _clean(value).casefold() in {"1", "true", "yes", "y"}


def _paired_agreement(
    pairs: Sequence[tuple[str, str]],
    labels: tuple[str, ...],
    *,
    replicates: int = 10_000,
    seed: int = 2026081306,
    chunk_size: int = 100,
) -> dict[str, Any]:
    """Compute agreement with an actual paired-record percentile bootstrap."""

    if not pairs:
        raise CombinedAnalysisError("No paired model-review decisions were supplied")
    label_index = {label: index for index, label in enumerate(labels)}
    width = len(labels)
    encoded: list[int] = []
    matrix = v2.np.zeros((width, width), dtype=v2.np.int64)
    for left, right in pairs:
        if left not in label_index or right not in label_index:
            raise CombinedAnalysisError(f"Unexpected model-review decision pair: {(left, right)!r}")
        left_index, right_index = label_index[left], label_index[right]
        matrix[left_index, right_index] += 1
        encoded.append(left_index * width + right_index)
    total = len(encoded)
    observed = float(v2.np.trace(matrix)) / total
    expected = float(v2.np.dot(matrix.sum(axis=1), matrix.sum(axis=0))) / (total * total)
    if abs(1.0 - expected) < 1e-15:
        raise CombinedAnalysisError("Observed model-review kappa is undefined")
    kappa = (observed - expected) / (1.0 - expected)

    z = 1.959963984540054
    denominator = 1.0 + z * z / total
    centre = (observed + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(
        observed * (1.0 - observed) / total + z * z / (4.0 * total * total)
    ) / denominator

    encoded_array = v2.np.asarray(encoded, dtype=v2.np.int16)
    rng = v2.np.random.default_rng(seed)
    bootstrap_values: list[float] = []
    undefined = 0
    for start in range(0, replicates, chunk_size):
        size = min(chunk_size, replicates - start)
        indices = rng.integers(0, total, size=(size, total))
        sampled = encoded_array[indices]
        matrices = v2.np.zeros((size, width, width), dtype=v2.np.int64)
        for left_index in range(width):
            for right_index in range(width):
                cell = left_index * width + right_index
                matrices[:, left_index, right_index] = (sampled == cell).sum(axis=1)
        totals = matrices.sum(axis=(1, 2)).astype(float)
        observed_values = v2.np.trace(matrices, axis1=1, axis2=2) / totals
        row_marginals = matrices.sum(axis=2)
        column_marginals = matrices.sum(axis=1)
        expected_values = (row_marginals * column_marginals).sum(axis=1) / (totals * totals)
        denominators = 1.0 - expected_values
        defined = v2.np.abs(denominators) >= 1e-15
        undefined += int((~defined).sum())
        bootstrap_values.extend(
            ((observed_values[defined] - expected_values[defined]) / denominators[defined]).tolist()
        )
    if undefined / replicates > 0.05:
        lower = upper = None
        interval_status = "withheld_more_than_5_percent_undefined"
    else:
        lower, upper = (
            float(value)
            for value in v2.np.percentile(bootstrap_values, [2.5, 97.5], method="linear")
        )
        interval_status = "reported"
    return {
        "labels": list(labels),
        "n": total,
        "confusion_matrix": {
            left: {
                right: int(matrix[label_index[left], label_index[right]])
                for right in labels
            }
            for left in labels
        },
        "raw_agreement": observed,
        "raw_agreement_count": int(v2.np.trace(matrix)),
        "raw_agreement_wilson_95_ci": [centre - half, centre + half],
        "cohen_kappa": kappa,
        "cohen_kappa_percentile_bootstrap_95_ci": [lower, upper],
        "bootstrap_replicates_requested": replicates,
        "bootstrap_replicates_defined": replicates - undefined,
        "bootstrap_replicates_undefined": undefined,
        "bootstrap_seed": seed,
        "bootstrap_unit": "paired candidate record",
        "kappa_interval_status": interval_status,
    }


def _agreement_rows_v5(agreement: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, result in (
        ("Three-choice include/exclude/uncertain", agreement["three_way"]),
        ("Binary include versus non-include", agreement["binary"]),
    ):
        rows.append(
            v2.agreement_row(
                section="Model-review agreement",
                measure="Raw agreement",
                category=label,
                numerator=result["raw_agreement_count"],
                denominator=result["n"],
                estimate=result["raw_agreement"],
                ci_lower=result["raw_agreement_wilson_95_ci"][0],
                ci_upper=result["raw_agreement_wilson_95_ci"][1],
                ci_level=0.95,
                ci_method="Wilson",
                denominator_definition="all candidate records before resolution",
                response_type="paired model-review decisions",
                note="Consistency between two model reviews; no human reference standard.",
            )
        )
        kappa_ci = result["cohen_kappa_percentile_bootstrap_95_ci"]
        rows.append(
            v2.agreement_row(
                section="Model-review agreement",
                measure="Cohen kappa",
                category=label,
                numerator="not applicable",
                denominator=result["n"],
                estimate=result["cohen_kappa"],
                ci_lower=kappa_ci[0],
                ci_upper=kappa_ci[1],
                ci_level=0.95,
                ci_method=(
                    "Paired-record percentile bootstrap; 10,000 replicates; seed 2026081306"
                    if result["kappa_interval_status"] == "reported"
                    else "CI withheld because more than 5% of bootstrap replicates were undefined"
                ),
                denominator_definition="all candidate records before resolution",
                response_type="paired model-review decisions",
                note=f"Undefined bootstrap replicates: {result['bootstrap_replicates_undefined']}.",
            )
        )
    return rows


def _validate_final_rows(validated: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    selection = validated["selection"]
    correction_fields, correction_rows = _rows_for(
        validated, "metadata_correction_ledger"
    )
    version_fields, version_rows = _rows_for(validated, "combined_eligible_version_ledger")
    selection_fields, study_selection_rows = _rows_for(
        validated, "combined_study_selection_ledger"
    )
    extraction_fields, extraction_rows = _rows_for(validated, "combined_checked_corpus")
    metadata_fields, metadata_rows = _rows_for(validated, "combined_metadata")
    oa_fields, openalex_raw_rows = _rows_for(validated, "combined_openalex")
    combined_screening_fields, combined_screening = _rows_for(
        validated, "combined_record_level_screening"
    )
    completed_version_fields, completed_version_rows = _rows_for(
        validated, "scopus_completed_version_decisions"
    )
    _base_inc_fields, base_versions = _rows_for(validated, "base_eligible_version_ledger")
    _scopus_inc_fields, scopus_included = _rows_for(
        validated, "scopus_corrected_included_records"
    )
    _base_final_fields, base_final = _rows_for(validated, "base_final_screening")
    _scopus_final_fields, scopus_final = _rows_for(
        validated, "scopus_corrected_final_screening"
    )
    _primary_comp_fields, primary_comparison = _rows_for(validated, "primary_review_comparison")
    _scopus_comp_fields, scopus_comparison = _rows_for(validated, "scopus_review_comparison")
    base_checked_fields, base_checked_rows = _rows_for(validated, "base_checked_corpus")
    scopus_checked_fields, scopus_checked_rows = _rows_for(validated, "scopus_checked_extraction")
    base_oa_fields, base_oa_rows = _rows_for(validated, "base_openalex")
    scopus_oa_fields, scopus_oa_rows = _rows_for(validated, "scopus_openalex")

    if not VERSION_REQUIRED_COLUMNS <= set(version_fields):
        raise CombinedAnalysisError(
            f"Combined version ledger is missing columns: {sorted(VERSION_REQUIRED_COLUMNS - set(version_fields))}"
        )
    study_selection_required = {
        "integration_schema_version",
        "final_version_family_id",
        "family_size",
        "preferred_record_key",
        "preferred_paper_id",
        "preferred_source_corpus",
        "preferred_basis",
        "preferred_selection_rationale",
        "preferred_selection_evidence",
        "family_reviewed_by",
        "family_reviewed_at_utc",
        "source_family_review_row_sha256",
    }
    if not study_selection_required <= set(selection_fields):
        raise CombinedAnalysisError(
            "Combined study-selection ledger is missing columns: "
            f"{sorted(study_selection_required - set(selection_fields))}"
        )
    if not set(completed_version_fields) <= set(version_fields):
        raise CombinedAnalysisError(
            "Combined version ledger does not retain every completed version-review field"
        )
    if len(completed_version_rows) != len(version_rows):
        raise CombinedAnalysisError("Completed and integrated version ledgers differ in length")
    for completed, integrated in zip(completed_version_rows, version_rows, strict=True):
        if any(integrated[field] != completed[field] for field in completed_version_fields):
            raise CombinedAnalysisError(
                f"Integrated version row differs from completed version review: {completed['record_key']}"
            )
    completed_version_sha = validated["inputs"]["scopus_completed_version_decisions"].get("sha256")
    if not completed_version_sha or any(
        row["source_completed_family_review_sha256"] != completed_version_sha
        for row in version_rows
    ):
        raise CombinedAnalysisError(
            "Integrated version rows are not bound to the completed version-review ledger hash"
        )
    if not WORK_REQUIRED_COLUMNS <= set(extraction_fields):
        raise CombinedAnalysisError(
            f"Combined checked corpus is missing columns: {sorted(WORK_REQUIRED_COLUMNS - set(extraction_fields))}"
        )
    metadata_required = {
        "paper_id",
        "final_version_family_id",
        "preferred_record_key",
        "doi",
        "title",
        "year",
        "publication_date",
        "journal",
        "found_in_sources",
        "record_type",
        "authors",
        "abstract",
        "source_keywords",
        "url",
    }
    if not metadata_required <= set(metadata_fields):
        raise CombinedAnalysisError(
            f"Combined metadata is missing columns: {sorted(metadata_required - set(metadata_fields))}"
        )
    if not set(v2.OPENALEX_FIELDS) <= set(oa_fields):
        raise CombinedAnalysisError("Combined OpenAlex view lacks the locked work-level schema")
    if not set(v2.OPENALEX_FIELDS) <= set(base_oa_fields) or not set(v2.OPENALEX_FIELDS) <= set(scopus_oa_fields):
        raise CombinedAnalysisError("A source OpenAlex view lacks the locked work-level schema")
    if not {
        "paper_id",
        "screening_source_corpus",
        "reviewer_A_decision",
        "reviewer_B_decision",
        "comparison_class",
        "final_decision",
        "final_primary_code",
    } <= set(combined_screening_fields):
        raise CombinedAnalysisError("Combined record-level screening schema is incomplete")

    base_ids = {row["paper_id"] for row in base_versions}
    scopus_ids = {row["paper_id"] for row in scopus_included}
    if base_ids & scopus_ids:
        raise CombinedAnalysisError("Base and Scopus eligible publication IDs overlap")
    expected_version_ids = base_ids | scopus_ids
    version_ids = [row["source_record_id"] for row in version_rows]
    if len(version_ids) != len(set(version_ids)) or set(version_ids) != expected_version_ids:
        raise CombinedAnalysisError("Combined version ledger does not equal base plus Scopus inclusions")
    if len(version_rows) != selection["included"]:
        raise CombinedAnalysisError("Combined version ledger count does not match the selection contract")

    families: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in version_rows:
        family = _clean(row["provisional_family_id"])
        if not family:
            raise CombinedAnalysisError("Version family ID is blank")
        families[family].append(row)
    preferred_ids: list[str] = []
    preferred_keys: list[str] = []
    family_by_preferred_id: dict[str, list[dict[str, str]]] = {}
    for family, members in families.items():
        preferred = [row for row in members if _true(row["preferred_for_analysis"])]
        if len(preferred) != 1:
            raise CombinedAnalysisError(f"Version family must have exactly one preferred record: {family}")
        preferred_id = preferred[0]["source_record_id"]
        preferred_key = preferred[0]["record_key"]
        if any(row["preferred_record_key"] != preferred_key for row in members):
            raise CombinedAnalysisError(f"Preferred-record key is inconsistent within family: {family}")
        if any(not _clean(row["relationship_to_preferred"]) for row in members):
            raise CombinedAnalysisError(f"Relationship-to-preferred is blank within family: {family}")
        if any(v2.integer(row["family_size"], f"family size/{family}", minimum=1) != len(members) for row in members):
            raise CombinedAnalysisError(f"Family-size value is inconsistent: {family}")
        preferred_ids.append(preferred_id)
        preferred_keys.append(preferred_key)
        family_by_preferred_id[preferred_id] = members
    if len(preferred_keys) != len(set(preferred_keys)):
        raise CombinedAnalysisError("Preferred record keys are not unique across version families")
    if len(families) != selection["canonical"]:
        raise CombinedAnalysisError("Version-family count differs from the contract canonical-work count")

    extraction_ids = [row["paper_id"] for row in extraction_rows]
    metadata_ids = [row["paper_id"] for row in metadata_rows]
    if extraction_ids != metadata_ids:
        raise CombinedAnalysisError(
            "Combined checked extraction and metadata must have the same paper-ID order"
        )
    if len(extraction_ids) != len(set(extraction_ids)):
        raise CombinedAnalysisError("Combined checked extraction contains duplicate paper IDs")
    selection_ids = [row["preferred_paper_id"] for row in study_selection_rows]
    if selection_ids != extraction_ids:
        raise CombinedAnalysisError(
            "Combined study-selection ledger and checked corpus must have the same preferred-paper order"
        )
    if len(selection_ids) != selection["canonical"]:
        raise CombinedAnalysisError(
            "Combined study-selection ledger count differs from the contract canonical-work count"
        )
    for selection_row in study_selection_rows:
        preferred_id = selection_row["preferred_paper_id"]
        members = family_by_preferred_id.get(preferred_id)
        if members is None:
            raise CombinedAnalysisError(
                f"Study-selection row is absent from the final version ledger: {preferred_id}"
            )
        preferred_member = next(
            member for member in members if member["source_record_id"] == preferred_id
        )
        expected_values = {
            "final_version_family_id": members[0]["provisional_family_id"],
            "family_size": str(len(members)),
            "preferred_record_key": preferred_member["record_key"],
            "preferred_source_corpus": preferred_member["source_corpus"],
            "preferred_basis": preferred_member["preferred_basis"],
            "preferred_selection_rationale": preferred_member["preferred_selection_rationale"],
            "preferred_selection_evidence": preferred_member["preferred_selection_evidence"],
            "family_reviewed_by": preferred_member["reviewed_by"],
            "family_reviewed_at_utc": preferred_member["reviewed_at_utc"],
        }
        changed = {
            field
            for field, expected in expected_values.items()
            if selection_row[field] != expected
        }
        if changed:
            raise CombinedAnalysisError(
                f"Study-selection row differs from completed version review for {preferred_id}: "
                f"{sorted(changed)}"
            )

    base_checked_by_id = {row["paper_id"]: row for row in base_checked_rows}
    scopus_checked_by_id = {row["paper_id"]: row for row in scopus_checked_rows}
    if len(base_checked_by_id) != len(base_checked_rows):
        raise CombinedAnalysisError("Base checked corpus contains duplicate paper IDs")
    if len(scopus_checked_by_id) != len(scopus_checked_rows) or set(scopus_checked_by_id) != scopus_ids:
        raise CombinedAnalysisError(
            "Corrected Scopus checked extraction does not equal corrected Scopus inclusions"
        )
    correction_required = {"paper_id", "field", "old_value", "new_value"}
    if not correction_required <= set(correction_fields):
        raise CombinedAnalysisError(
            "Metadata-correction ledger lacks its exact old/new cell schema"
        )
    common_fields = set(extraction_fields) & set(metadata_fields)
    if not {
        "integration_source_corpus",
        "integration_source_row_sha256",
        "source_finalization_manifest_sha256",
    } <= common_fields:
        raise CombinedAnalysisError(
            "Combined extraction and metadata lack the locked integration provenance fields"
        )
    extraction_by_id = {row["paper_id"]: row for row in extraction_rows}
    metadata_by_id = {row["paper_id"]: row for row in metadata_rows}
    if len(extraction_by_id) != len(extraction_rows) or len(metadata_by_id) != len(metadata_rows):
        raise CombinedAnalysisError("A combined canonical view contains duplicate paper IDs")

    # The integration row digests are role-specific: one hashes a checked
    # extraction source row and the other hashes a bibliographic source row.
    # They are validated as SHA-256 values but are not treated as shared data.
    for extraction, metadata in zip(extraction_rows, metadata_rows, strict=True):
        for view, value in (
            ("extraction", extraction["integration_source_row_sha256"]),
            ("metadata", metadata["integration_source_row_sha256"]),
        ):
            if not v2.SHA256_RE.fullmatch(_clean(value).casefold()):
                raise CombinedAnalysisError(
                    f"Invalid {view} integration source-row hash: {extraction['paper_id']}"
                )

    correction_differences = {
        (row["paper_id"], row["field"], row["old_value"], row["new_value"])
        for row in correction_rows
    }
    if len(correction_differences) != len(correction_rows):
        raise CombinedAnalysisError("Metadata-correction ledger contains a duplicate cell decision")
    if any(
        paper_id not in extraction_by_id or field not in common_fields
        for paper_id, field, _old, _new in correction_differences
    ):
        raise CombinedAnalysisError(
            "Metadata-correction ledger names a record or field outside the combined canonical views"
        )

    scopus_integrated_ids = {
        row["paper_id"]
        for row in extraction_rows
        if row["integration_source_corpus"] == "scopus_increment"
    }
    if scopus_integrated_ids != scopus_ids:
        raise CombinedAnalysisError(
            "Scopus provenance rows do not equal the corrected eligible Scopus publication IDs"
        )
    provenance_differences = {
        (
            paper_id,
            "source_finalization_manifest_sha256",
            SCOPUS_EXTRACTION_FINALIZATION_SHA256,
            "",
        )
        for paper_id in scopus_integrated_ids
    }
    expected_differences = correction_differences | provenance_differences
    actual_differences = {
        (extraction["paper_id"], field, extraction[field], metadata[field])
        for extraction, metadata in zip(extraction_rows, metadata_rows, strict=True)
        for field in common_fields - {"integration_source_row_sha256"}
        if extraction[field] != metadata[field]
    }
    if actual_differences != expected_differences:
        missing = sorted(expected_differences - actual_differences)[:10]
        extra = sorted(actual_differences - expected_differences)[:10]
        raise CombinedAnalysisError(
            "Combined extraction/metadata differences are outside the exact frozen allow-list; "
            f"missing={missing}, extra={extra}"
        )

    permitted_source_integration_changes = {
        "integration_schema_version",
        "integration_source_row_sha256",
        "final_version_family_id",
        "preferred_record_key",
        "preferred_paper_id",
        "family_size",
        "version_family_id",
        "version_role",
        "found_in_sources",
    }
    for preferred_id, members in family_by_preferred_id.items():
        preferred_member = next(
            member for member in members if member["source_record_id"] == preferred_id
        )
        source_corpus = preferred_member["source_corpus"]
        if source_corpus == "base_eligible_v4":
            source_row = base_checked_by_id.get(preferred_id)
            source_fields = base_checked_fields
        elif source_corpus == "scopus_increment":
            source_row = scopus_checked_by_id.get(preferred_id)
            source_fields = scopus_checked_fields
        else:
            raise CombinedAnalysisError(
                f"Unknown source corpus in the completed version ledger: {source_corpus}"
            )
        if source_row is None:
            raise CombinedAnalysisError(
                f"Preferred publication lacks its checked source extraction: {preferred_id}"
            )
        integrated = extraction_by_id.get(preferred_id)
        if integrated is None:
            raise CombinedAnalysisError(
                f"Preferred publication is absent from the combined checked extraction: {preferred_id}"
            )
        changed = {
            field
            for field in set(source_fields) & set(extraction_fields)
            if field not in permitted_source_integration_changes
            and source_row[field] != integrated[field]
        }
        if changed:
            raise CombinedAnalysisError(
                f"Integrated extraction changes checked source cells for {preferred_id}: {sorted(changed)}"
            )

    # Metadata supplies the checked preferred-report bibliography.  Extraction
    # supplies the checked classifications and their source evidence.  Final
    # family size and Scopus discovery coverage are overlaid from the final
    # final publication-version ledger rather than inherited from an older family.
    works: list[dict[str, str]] = []
    for extraction, metadata in zip(extraction_rows, metadata_rows, strict=True):
        row = dict(metadata)
        for field, value in extraction.items():
            if field not in row or field.startswith("final_") or field in {
                "extraction_schema_version",
                "extraction_rationale",
                "evidence_url_1",
                "evidence_url_2",
                "source_checked_by",
                "source_checked_at_utc",
                "source_check_attestation",
                "screening_suggestions_role",
            }:
                row[field] = value
        paper_id = row["paper_id"]
        members = family_by_preferred_id.get(paper_id)
        if members is None:
            raise CombinedAnalysisError(
                f"Preferred checked record is absent from the final version ledger: {paper_id}"
            )
        row["version_family_id"] = members[0]["provisional_family_id"]
        if _clean(row.get("final_version_family_id")) != row["version_family_id"]:
            raise CombinedAnalysisError(
                f"Combined corpus carries the wrong final version family: {paper_id}"
            )
        if _clean(row.get("preferred_record_key")) != members[0]["preferred_record_key"]:
            raise CombinedAnalysisError(
                f"Combined corpus carries the wrong preferred record key: {paper_id}"
            )
        row["family_size"] = str(len(members))
        row["version_role"] = next(
            member.get("version_role", "")
            for member in members
            if member["source_record_id"] == paper_id
        )
        sources = set(v2.split_semicolon(row["found_in_sources"]))
        if any(member.get("source_corpus") == "scopus_increment" for member in members):
            sources.add("scopus")
        row["found_in_sources"] = ";".join(
            source for source in SIX_SOURCES if source in sources
        )
        works.append(row)

    work_fields = list(dict.fromkeys([*metadata_fields, *extraction_fields, "version_family_id"]))
    work_ids = [row["paper_id"] for row in works]
    if len(work_ids) != len(set(work_ids)) or set(work_ids) != set(preferred_ids):
        raise CombinedAnalysisError("Combined checked corpus is not one row per preferred version family")
    if selection["canonical"] != len(works):
        raise CombinedAnalysisError("Contract canonical-work count differs from the checked corpus")
    openalex_rows = [
        {field: raw[field] for field in v2.OPENALEX_FIELDS}
        for raw in openalex_raw_rows
    ]
    oa_ids = [row["paper_id"] for row in openalex_rows]
    if len(oa_ids) != len(set(oa_ids)) or set(oa_ids) != set(work_ids):
        raise CombinedAnalysisError("Combined OpenAlex rows do not match the final checked corpus")
    base_oa_by_id = {row["paper_id"]: row for row in base_oa_rows}
    scopus_oa_by_id = {row["paper_id"]: row for row in scopus_oa_rows}
    integrated_oa_by_id = {row["paper_id"]: row for row in openalex_rows}
    if len(base_oa_by_id) != len(base_oa_rows) or len(scopus_oa_by_id) != len(scopus_oa_rows):
        raise CombinedAnalysisError("A source OpenAlex view contains duplicate paper IDs")
    for preferred_id, members in family_by_preferred_id.items():
        preferred_member = next(
            member for member in members if member["source_record_id"] == preferred_id
        )
        source_oa = (
            base_oa_by_id.get(preferred_id)
            if preferred_member["source_corpus"] == "base_eligible_v4"
            else scopus_oa_by_id.get(preferred_id)
        )
        if source_oa is None:
            raise CombinedAnalysisError(
                f"Preferred publication lacks its source OpenAlex row: {preferred_id}"
            )
        integrated_oa = integrated_oa_by_id[preferred_id]
        if any(integrated_oa[field] != source_oa[field] for field in v2.OPENALEX_FIELDS):
            raise CombinedAnalysisError(
                f"Integrated OpenAlex row changes the locked source metadata: {preferred_id}"
            )

    labels = spec["study_level_labels"]
    allowed_multi = {
        "final_model_families": set(labels["model_families"]),
        "final_simulation_modalities": set(labels["simulation_methods"]),
        "final_nts_domains": set(labels["nts_domains"]),
    }
    for row in works:
        paper_id = row["paper_id"]
        year = v2.integer(row["year"], f"year/{paper_id}")
        if year < 2020 or year > 2026:
            raise CombinedAnalysisError(f"Work year is outside the locked window: {paper_id}")
        if year == 2026:
            date = _clean(row["publication_date"])
            if not date or date > "2026-08-13":
                raise CombinedAnalysisError(f"2026 work lacks an in-window date: {paper_id}")
        for field, allowed in allowed_multi.items():
            values = v2.split_semicolon(row[field])
            if field == "final_model_families" and not values:
                raise CombinedAnalysisError(f"Checked model field is blank: {paper_id}")
            unknown = set(values) - allowed
            if unknown:
                raise CombinedAnalysisError(f"Unknown {field} labels for {paper_id}: {sorted(unknown)}")
        if _clean(row["final_study_design"]) not in labels["study_designs"]:
            raise CombinedAnalysisError(f"Invalid single study-design label: {paper_id}")
        source_values = set(v2.split_semicolon(row["found_in_sources"]))
        if source_values - set(SIX_SOURCES):
            raise CombinedAnalysisError(
                f"Unrecognized discovery source on {paper_id}: {sorted(source_values - set(SIX_SOURCES))}"
            )

    oa_by_id = {row["paper_id"]: row for row in openalex_rows}
    for paper_id, row in oa_by_id.items():
        status = _clean(row["match_status"]).upper()
        citation = _clean(row["cited_by_count"])
        if status == "MATCHED":
            if not citation:
                raise CombinedAnalysisError(f"Matched OpenAlex row lacks a citation value: {paper_id}")
            v2.integer(citation, f"citation/{paper_id}")
        elif status == "UNMATCHED":
            if citation:
                raise CombinedAnalysisError(f"Unmatched OpenAlex row contains a citation value: {paper_id}")
        else:
            raise CombinedAnalysisError(f"Invalid OpenAlex match status: {paper_id}: {status}")

    source_final_rows = [*base_final, *scopus_final]
    source_comparison_rows = [*primary_comparison, *scopus_comparison]
    final_rows = combined_screening
    comparison_rows = combined_screening
    if (
        len(final_rows) != selection["candidates"]
        or len(source_final_rows) != selection["candidates"]
        or len(source_comparison_rows) != selection["candidates"]
    ):
        raise CombinedAnalysisError("Combined screening or comparison rows do not match candidate count")
    final_ids = [row["paper_id"] for row in final_rows]
    source_final_by_id = {row["paper_id"]: row for row in source_final_rows}
    source_comparison_by_id = {row["paper_id"]: row for row in source_comparison_rows}
    if (
        len(final_ids) != len(set(final_ids))
        or set(final_ids) != set(source_final_by_id)
        or set(final_ids) != set(source_comparison_by_id)
    ):
        raise CombinedAnalysisError("Integrated and source screening record IDs differ")
    for row in final_rows:
        paper_id = row["paper_id"]
        source_final = source_final_by_id[paper_id]
        source_comparison = source_comparison_by_id[paper_id]
        if any(
            row[field] != source_final[field]
            for field in ("final_decision", "final_primary_code")
        ):
            raise CombinedAnalysisError(
                f"Integrated final decision differs from corrected source screening: {paper_id}"
            )
        if any(
            row[field] != source_comparison[field]
            for field in ("reviewer_A_decision", "reviewer_B_decision", "comparison_class")
        ):
            raise CombinedAnalysisError(
                f"Integrated pre-resolution decisions differ from source comparison: {paper_id}"
            )
    final_counts = Counter(_clean(row["final_decision"]).upper() for row in final_rows)
    if final_counts != Counter({"INCLUDE": selection["included"], "EXCLUDE": selection["excluded"]}):
        raise CombinedAnalysisError("Combined final decisions do not match the selection contract")
    final_include_ids = {
        row["paper_id"]
        for row in final_rows
        if _clean(row["final_decision"]).upper() == "INCLUDE"
    }
    if final_include_ids != set(version_ids):
        raise CombinedAnalysisError(
            "Final INCLUDE decisions do not equal the eligible publication-version ledger"
        )
    corrected = next(
        (row for row in scopus_final if row["paper_id"] == SCOPUS_CORRECTED_RECORD_ID),
        None,
    )
    if (
        corrected is None
        or _clean(corrected["final_decision"]).upper() != "EXCLUDE"
        or _clean(corrected["final_primary_code"]) != "E2_NOT_HEALTH_ED"
        or SCOPUS_CORRECTED_RECORD_ID in scopus_ids
        or SCOPUS_CORRECTED_RECORD_ID in set(version_ids)
        or SCOPUS_CORRECTED_RECORD_ID in set(work_ids)
    ):
        raise CombinedAnalysisError(
            "The locked Scopus health-education eligibility correction is not fully applied"
        )

    return {
        "version_rows": version_rows,
        "version_fields": version_fields,
        "works": works,
        "work_fields": work_fields,
        "openalex_rows": openalex_rows,
        "openalex_by_id": oa_by_id,
        "final_rows": final_rows,
        "comparison_rows": comparison_rows,
    }


def _selection_rows_v5(
    contract: Mapping[str, Any],
    analysis: Mapping[str, Any],
    final_rows: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[tuple[str, int, str]]]:
    selection = contract["selection_flow"]
    n = int(analysis["n"])
    sources = selection["retrieval_occurrences_by_source"]
    auto = selection["automatic_duplicate_merges"]
    reviewed = selection["reviewed_same_record_merges"]
    candidate = selection["candidate_records"]
    resolution = selection["separate_resolution_checks"]
    version_total = int(selection["eligible_publication_records"])
    version_reduction = version_total - n
    stages = [
        ("Retrieval occurrences", int(selection["retrieval_occurrences_total"]), "all six-source query occurrences before date and duplicate handling"),
        ("Scopus results after the cutoff", int(selection["scopus_after_cutoff_removed"]), "Scopus occurrences published after 13 August 2026 and removed before matching"),
        ("Primary-source results before or after the date window", int(selection["primary_five_occurrence_date_status"]["before_window"]) + int(selection["primary_five_occurrence_date_status"]["after_window"]), "date flags found in the five-source retrieval; these records continued to duplicate handling and candidate screening, where the final date rule was applied"),
        ("Primary-source results with an unknown or unresolved date", int(selection["primary_five_occurrence_date_status"]["unknown"]) + int(selection["primary_five_occurrence_date_status"]["unresolved_boundary"]), "date flags found in the five-source retrieval; these records continued to duplicate handling and candidate screening so that uncertain dates were not discarded automatically"),
        ("Occurrences entering duplicate handling", int(selection["retrieval_occurrences_after_scopus_cutoff"]), "all five-source occurrences plus Scopus occurrences remaining after its cutoff check; this is not a claim that every primary-source occurrence was already date-eligible"),
        ("Automatically merged duplicate occurrences", int(auto["total"]), "within-source and cross-source records merged by fixed automatic identity rules"),
        ("Records after automatic duplicate merging", int(selection["records_after_automatic_merging"]), "records after automatic duplicate handling"),
        ("Separately confirmed same-record merges", int(reviewed["total"]), "additional identity matches confirmed separately"),
        ("Unique bibliographic records after deduplication", int(selection["deduplicated_records"]), "records after automatic and separately checked duplicate handling"),
        ("Records outside the four-domain candidate frame", int(selection["records_outside_candidate_frame"]), "records not entering model review"),
        ("Candidate records reviewed by both models", int(candidate["total"]), "all records receiving two independent decisions"),
        ("Separate source checks: direct include/exclude decisions", int(resolution["direct_include_exclude"]), "directly different include/exclude decisions checked against available sources"),
        ("Separate source checks: one or both decisions uncertain", int(resolution["one_or_both_uncertain"]), "records with at least one uncertain decision checked against available sources"),
        ("Separate source checks: exclusion reason differed", int(resolution["exclusion_code_only"]), "agreed exclusions whose primary reason differed and was resolved"),
        ("All separately resolved review records", int(resolution["total"]), "union of the three mutually exclusive review-resolution groups"),
        ("Records excluded after resolution", int(selection["excluded_candidate_records"]), "one final primary reason per excluded candidate"),
        ("Eligible publication records", version_total, "eligible records before publication-version consolidation"),
        ("Alternate publication versions", version_reduction, "eligible publication records linked to another report of the same scholarly work"),
        ("Canonical unique works", n, "one preferred publication per reviewed work family"),
    ]

    complete: list[dict[str, Any]] = []
    table1: list[dict[str, Any]] = []
    total_raw = int(selection["retrieval_occurrences_total"])
    for source in SIX_SOURCES:
        count = int(sources[source])
        label = v2.plain_label(source)
        complete.append(
            v2.descriptive_row(
                section="Selection flow",
                measure="Retrieval occurrence by source",
                category=label,
                count=count,
                denominator=total_raw,
                percent=v2.percent(count, total_raw),
                unit="source/query retrieval occurrences",
                denominator_definition="all six-source retrieval occurrences before the Scopus cutoff check",
                response_type="single response by discovery source",
                note="Counts precede cross-source deduplication; Scopus post-cutoff results are shown separately.",
            )
        )
        table1.append(
            v2.agreement_row(
                section="Selection flow",
                measure="Retrieval occurrence by source",
                category=label,
                numerator=count,
                denominator=total_raw,
                estimate=v2.percent(count, total_raw),
                denominator_definition="all six-source retrieval occurrences before the Scopus cutoff check",
                response_type="single response by discovery source",
                value_text="percent of raw retrieval occurrences",
                note="Counts precede cross-source deduplication.",
            )
        )
    for label, count, definition in stages:
        complete.append(
            v2.descriptive_row(
                section="Selection flow",
                measure="Stage count",
                category=label,
                count=count,
                denominator="not applicable",
                unit="stage-specific records or works",
                denominator_definition=definition,
                response_type="stage-specific count; side checks are not serial losses",
                note="The unit and relationship to the main flow are stated explicitly.",
            )
        )
        table1.append(
            v2.agreement_row(
                section="Selection flow",
                measure="Stage count",
                category=label,
                numerator=count,
                denominator="not applicable",
                denominator_definition=definition,
                response_type="stage-specific count; side checks are not serial losses",
                note="Counts use the stated stage-specific unit.",
            )
        )

    final_codes = Counter(
        row["final_primary_code"]
        for row in final_rows
        if _clean(row["final_decision"]).upper() == "EXCLUDE"
    )
    if sum(final_codes.values()) != int(selection["excluded_candidate_records"]):
        raise CombinedAnalysisError("Exclusion-reason rows do not sum to final exclusions")
    expected_out_of_range = int(selection["final_out_of_range_exclusions"])
    if final_codes.get("E6_OUT_OF_RANGE", 0) != expected_out_of_range:
        raise CombinedAnalysisError(
            "Final E6_OUT_OF_RANGE decisions do not match the locked selection-flow count"
        )
    for code, count in sorted(final_codes.items()):
        complete.append(
            v2.descriptive_row(
                section="Selection flow",
                measure="Final primary exclusion reason",
                category=v2.EXCLUSION_CODE_LABELS.get(code, v2.plain_label(code)),
                count=count,
                denominator=int(selection["candidate_records"]["total"]),
                percent=_publication_percent(
                    count, int(selection["candidate_records"]["total"])
                ),
                unit="candidate records",
                denominator_definition="all candidate records before resolution",
                response_type="one primary reason per final excluded record",
                note=f"Screening code {code}; reason counts reconcile to all excluded records.",
            )
        )

    old_table1 = analysis["tables"]["TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT"][0]
    table1.extend(row for row in old_table1 if row["section"] == "Model-review agreement")
    oversight = _validate_oversight_contract(contract["lead_author_oversight"])
    table1.append(
        v2.agreement_row(
            section="Lead-author oversight",
            measure="Concordance with the five-source pipeline decision",
            category="Deliberately stratified 100-record oversight sample",
            numerator=oversight["successes"],
            denominator=oversight["total"],
            estimate=oversight["successes"] / oversight["total"],
            ci_lower=oversight["exact_95pct_lower"],
            ci_upper=oversight["exact_95pct_upper"],
            ci_level=0.95,
            ci_method="Exact two-sided Clopper-Pearson interval",
            denominator_definition="the deliberately stratified lead-author sample from the five-source pipeline at the time of audit",
            response_type="lead-author oversight concordance; not a representative random sample",
            note=(
                "This check predates the Scopus extension and later objective eligibility corrections; "
                "it does not validate the final six-source corpus or the 1,244 Scopus records. Fifteen "
                "human-pipeline differences did not receive the planned second-human resolution. It is "
                "not accuracy, sensitivity, specificity, or an independent reference standard."
            ),
        )
    )
    return table1, complete, stages


def _publication_percent(count: int, denominator: int) -> float | str | None:
    """Return a reader-facing percentage without displaying a positive value as zero.

    The general V2 helper deliberately retains an unrounded sub-0.05 percentage.
    That is useful for computation but not for publication display.  V5 therefore
    uses the conventional ``<0.1%`` label for any positive value below 0.1%.
    """

    value = v2.percent(count, denominator)
    if denominator > 0 and count > 0 and 100.0 * count / denominator < 0.1:
        return "<0.1%"
    return value


def _repair_phrase_table_abstract_sensitivity(
    rows: list[dict[str, Any]], works: Sequence[Mapping[str, str]]
) -> None:
    """Bind every retained-abstract phrase count to its exact union ID set."""

    abstract_ids = {row["paper_id"] for row in works if _clean(row["abstract"])}
    main_by_label = {
        row["category"]: set(v2.split_semicolon(row["work_ids"]))
        for row in rows
        if row["measure"] == "Predefined phrase frequency"
    }
    for row in rows:
        if row["measure"] != "Retained-abstract sensitivity frequency":
            continue
        if row["category"] not in main_by_label:
            raise CombinedAnalysisError(
                f"Retained-abstract phrase lacks a matching main row: {row['category']}"
            )
        # The main work-ID set is the title/abstract/keyword union.  Intersecting
        # it with the retained-abstract cohort preserves that exact search scope.
        expected = sorted(main_by_label[row["category"]] & abstract_ids)
        row["work_ids"] = ";".join(expected)
        row["count"] = len(expected)
        row["denominator"] = len(abstract_ids)
        row["percent"] = v2.percent(len(expected), len(abstract_ids))
        row["note"] = (
            "The same title, abstract and keyword search, restricted to studies with a retained abstract."
            if abstract_ids
            else "Not estimable because no canonical work retained an abstract."
        )


def _repair_phrase_sensitivity(analysis: dict[str, Any], works: Sequence[Mapping[str, str]]) -> None:
    rows, fields = analysis["supplements"]["SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE"]
    _repair_phrase_table_abstract_sensitivity(rows, works)
    analysis["supplements"]["SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE"] = (rows, fields)

    sensitivity_works = [
        row
        for row in works
        if not (
            int(row["family_size"]) == 1
            and (
                _clean(row["version_role"]).casefold() in {"preprint", "other_version"}
                or "preprint" in _clean(row["record_type"]).casefold()
            )
        )
    ]
    sensitivity_rows, sensitivity_fields = analysis["supplements"][
        "SUPPLEMENT_SENSITIVITY_PREPRINT_REPOSITORY_PHRASES"
    ]
    _repair_phrase_table_abstract_sensitivity(sensitivity_rows, sensitivity_works)
    analysis["supplements"]["SUPPLEMENT_SENSITIVITY_PREPRINT_REPOSITORY_PHRASES"] = (
        sensitivity_rows,
        sensitivity_fields,
    )


def _author_signature(author: Mapping[str, Any], paper_id: str) -> tuple[str, str, tuple[str, ...]]:
    """Build the exact within-work signature used to reconcile duplicate authorships."""

    institution_ids = author.get("institution_ids") or []
    if not isinstance(institution_ids, list):
        raise CombinedAnalysisError(f"Malformed author institution IDs for {paper_id}")
    return (
        " ".join(
            unicodedata.normalize("NFKC", _clean(author.get("author_name")))
            .casefold()
            .split()
        ),
        _clean(author.get("orcid")).casefold(),
        tuple(sorted(_clean(value).casefold() for value in institution_ids if _clean(value))),
    )


def _author_identity_ledger(
    works: Sequence[Mapping[str, str]], oa_by_id: Mapping[str, Mapping[str, str]]
) -> list[dict[str, Any]]:
    work_sets: defaultdict[str, set[str]] = defaultdict(set)
    display: dict[str, str] = {}
    openalex_id: dict[str, str] = {}
    identity_type: dict[str, str] = {}
    collapsed_to_openalex: set[str] = set()
    for work in works:
        paper_id = work["paper_id"]
        raw = _clean(oa_by_id[paper_id].get("authors_json"))
        try:
            authors = json.loads(raw) if raw else []
        except json.JSONDecodeError as exc:
            raise CombinedAnalysisError(f"Invalid authors_json for {paper_id}") from exc
        if not isinstance(authors, list):
            raise CombinedAnalysisError(f"authors_json is not a list for {paper_id}")
        identified_signatures: defaultdict[tuple[str, str, tuple[str, ...]], set[str]] = (
            defaultdict(set)
        )
        for author in authors:
            if not isinstance(author, Mapping):
                raise CombinedAnalysisError(f"Malformed authorship for {paper_id}")
            author_id = _clean(author.get("author_id"))
            if author_id:
                identified_signatures[_author_signature(author, paper_id)].add(author_id)
        seen: set[str] = set()
        for author in authors:
            if not isinstance(author, Mapping):
                raise CombinedAnalysisError(f"Malformed authorship for {paper_id}")
            author_id = _clean(author.get("author_id"))
            name = _clean(author.get("author_name"))
            if not author_id and not name:
                continue
            if author_id:
                key = "openalex:" + author_id.casefold()
                kind = "OpenAlex author ID"
            else:
                signature = _author_signature(author, paper_id)
                identified_matches = identified_signatures.get(signature, set())
                if len(identified_matches) == 1:
                    author_id = next(iter(identified_matches))
                    key = "openalex:" + author_id.casefold()
                    kind = "OpenAlex author ID; exact duplicate name-only authorship collapsed within work"
                    collapsed_to_openalex.add(key)
                else:
                    signature_hash = v2.sha256_text(v2.canonical_json(signature))[:16]
                    key = f"name-only:{paper_id}:{signature_hash}"
                    kind = "Name-only record; duplicates collapsed within work only; not merged across works"
            if key in seen:
                continue
            seen.add(key)
            work_sets[key].add(paper_id)
            display.setdefault(key, name or author_id)
            openalex_id.setdefault(key, author_id)
            identity_type.setdefault(key, kind)
    for key in collapsed_to_openalex:
        identity_type[key] = (
            "OpenAlex author ID; exact within-work duplicate collapsed using normalized name, ORCID and institution IDs"
        )
    rows = [
        {
            "author_key": key,
            "openalex_author_id": openalex_id[key],
            "display_name": display[key],
            "identity_type": identity_type[key],
            "unresolved_name_flag": "0" if openalex_id[key] else "1",
            "work_count": len(ids),
            "work_ids": ";".join(sorted(ids)),
        }
        for key, ids in work_sets.items()
    ]
    rows.sort(key=lambda row: (-int(row["work_count"]), row["display_name"].casefold(), row["author_key"]))
    return rows


def _repair_no_explicit_nts_response_types(analysis: dict[str, Any]) -> None:
    """Treat absence of an explicit NTS domain as coverage, never multi-response."""

    corrected = 0
    for collection_name in ("tables", "supplements"):
        for stem, (rows, fields) in list(analysis[collection_name].items()):
            changed = False
            for row in rows:
                if row.get("category") != "No explicit NTS domain":
                    continue
                row["response_type"] = (
                    "coverage status; mutually exclusive with at least one explicit NTS domain"
                )
                changed = True
                corrected += 1
            if changed:
                analysis[collection_name][stem] = (rows, fields)
    if corrected == 0:
        raise CombinedAnalysisError("No no-explicit-NTS coverage row was available to correct")


def _specialty_grouping(
    works: Sequence[Mapping[str, str]], spec: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ids: defaultdict[str, set[str]] = defaultdict(set)
    raw_display: dict[str, str] = {}
    for work in works:
        for raw in v2.split_semicolon(work["final_specialty"]):
            key = " ".join(unicodedata.normalize("NFKC", raw).casefold().replace("_", " ").split())
            ids[key].add(work["paper_id"])
            raw_display.setdefault(key, raw)

    fixed_surgical = {
        " ".join(str(value).casefold().replace("_", " ").split())
        for value in spec.get("surgical_grouping") or []
    }
    fixed_surgical |= {
        "surgery",
        "general surgery",
        "orthopaedic surgery",
        "neurosurgery",
        "otolaryngology",
        "plastic surgery",
        "cardiothoracic surgery",
        "vascular surgery",
        "paediatric surgery",
        "pediatric surgery",
        "transplant surgery",
        "bariatric surgery",
        "spine surgery",
        "urology",
        "operative obstetrics and gynaecology",
        "operative obstetrics and gynecology",
    }
    general_terms = {
        "medicine",
        "general medical education",
        "health professions",
        "health professions education",
        "healthcare professionals",
        "healthcare education",
        "interprofessional",
        "simulation education",
        "undergraduate medical education",
        "medical education faculty development",
    }

    grouped: dict[str, str] = {}
    rules: dict[str, str] = {}
    for key in ids:
        if key in fixed_surgical or " surgery" in f" {key}" or "surgical" in key:
            grouped[key] = "surgical specialty"
            rules[key] = "fixed surgical label or explicit surgery/surgical wording"
        elif key in general_terms:
            grouped[key] = "general or multi-professional"
            rules[key] = "fixed general or multi-professional label"
        else:
            grouped[key] = "other clinical specialty or profession"
            rules[key] = "remaining checked category"

    ordered = sorted(ids, key=lambda key: (-len(ids[key]), v2.plain_label(raw_display[key]).casefold(), key))
    required = [key for key in ordered if grouped[key] in {"general or multi-professional", "surgical specialty"}]
    remaining = [key for key in ordered if grouped[key] == "other clinical specialty or profession"][:10]
    selected = set(required + remaining)
    plot_rows = [
        v2.descriptive_row(
            section="Specialties and professions",
            measure="Checked specialty/profession frequency",
            category=v2.plain_label(raw_display[key]),
            count=len(ids[key]),
            denominator=len(works),
            percent=v2.percent(len(ids[key]), len(works)),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="multiple response; percentages may sum to more than 100%",
            work_ids=";".join(sorted(ids[key])),
            note=f"{grouped[key]}; plain reader-facing label.",
        )
        for key in ordered
        if key in selected
    ]
    ledger = [
        {
            "raw_label": raw_display[key],
            "plain_label": v2.plain_label(raw_display[key]),
            "display_group": grouped[key],
            "work_count": len(ids[key]),
            "included_in_figure_5": "1" if key in selected else "0",
            "classification_rule": rules[key],
            "work_ids": ";".join(sorted(ids[key])),
        }
        for key in ordered
    ]
    if any(row["included_in_figure_5"] != "1" for row in ledger if row["display_group"] == "surgical specialty"):
        raise CombinedAnalysisError("At least one represented surgical category was omitted from Figure 5")
    if any("_" in row["category"] for row in plot_rows):
        raise CombinedAnalysisError("Figure 5 contains raw underscore labels")
    return plot_rows, ledger


def _input_binding_rows(validated: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for role, pin in sorted(validated["inputs"].items()):
        rows.append(
            {
                "role": role,
                "path": str(pin["path"]),
                "bytes": pin["bytes"],
                "rows": "" if pin.get("rows") is None else pin["rows"],
                "sha256": pin["sha256"],
                "state": "locked",
            }
        )
    return rows


def _input_bundle_sha(validated: Mapping[str, Any]) -> str:
    payload = "\0".join(
        f"{role}:{pin['sha256']}" for role, pin in sorted(validated["inputs"].items())
    )
    return v2.sha256_text(payload)


def _claim_register(analysis: Mapping[str, Any], input_bundle_sha: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    collections = [("tables", analysis["tables"]), ("supplements", analysis["supplements"])]
    for directory, artifacts in collections:
        for stem, (artifact_rows, _fields) in sorted(artifacts.items()):
            if stem == "SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5":
                continue
            for index, row in enumerate(artifact_rows, start=2):
                reported = row.get("count")
                if reported in {None, ""}:
                    reported = row.get("value")
                if reported in {None, ""}:
                    reported = row.get("numerator")
                source_sha = _canonical_row_sha(row)
                rows.append(
                    {
                        "claim_id": "claim-" + v2.sha256_text(f"{directory}/{stem}:{index}:{source_sha}")[:20],
                        "artifact": f"{directory}/{stem}.csv",
                        "row_number": index,
                        "section": row.get("section", ""),
                        "measure": row.get("measure", ""),
                        "category": row.get("category", ""),
                        "reported_value": reported,
                        "denominator": row.get("denominator", ""),
                        "input_bundle_sha256": input_bundle_sha,
                        "source_table_row_sha256": source_sha,
                    }
                )
    return rows


def build_analysis_from_rows(
    *,
    spec: Mapping[str, Any],
    contract: Mapping[str, Any],
    final_data: Mapping[str, Any],
    input_bundle_sha256: str,
) -> dict[str, Any]:
    """Build all calculations from already validated in-memory rows.

    This entry point is used by strict synthetic tests.  Production callers
    must use :func:`run_production`, which performs all file/hash gates first.
    """

    selection = _validate_selection_contract(contract["selection_flow"], production=True)
    _validate_oversight_contract(contract["lead_author_oversight"])
    works = list(final_data["works"])
    if len(works) != selection["canonical"]:
        raise CombinedAnalysisError("In-memory final works do not match the contract N")
    comparison_rows = list(final_data["comparison_rows"])
    final_rows = list(final_data["final_rows"])
    version_rows = list(final_data["version_rows"])
    oa_rows = list(final_data["openalex_rows"])
    analysis = v2.build_analysis(
        spec=spec,
        raw={
            # V2's validated statistical helpers require one serial retrieval
            # denominator.  V5 therefore passes the post-Scopus-cutoff stream
            # here and replaces V2's selection table with the complete V5 flow,
            # which also reports all 9,719 raw occurrences and the 150 removed.
            "retrieval_occurrences": selection["after_scopus_cutoff"],
            "by_source": {
                source: (
                    int(contract["selection_flow"]["retrieval_occurrences_by_source"][source])
                    - (selection["cutoff"] if source == "scopus" else 0)
                )
                for source in SIX_SOURCES
            },
        },
        normalization={"retrieval_occurrences": selection["after_scopus_cutoff"]},
        dedup={
            "retrieval_occurrences": selection["after_scopus_cutoff"],
            "automatic_duplicate_reduction": selection["automatic"],
            "pre_review_deduplicated_records": selection["after_automatic"],
            "reviewed_same_record_reduction": selection["reviewed"],
            "deduplicated_records": selection["deduplicated"],
        },
        candidate={"rows": comparison_rows},
        comparison={"rows": comparison_rows},
        finalization={"rows": final_rows, "included_rows": version_rows},
        extraction={},
        metadata={"analysis_rows": works},
        openalex={
            "rows": oa_rows,
            "by_id": {row["paper_id"]: row for row in oa_rows},
            "matched": sum(_clean(row["match_status"]).upper() == "MATCHED" for row in oa_rows),
            "unmatched": sum(_clean(row["match_status"]).upper() == "UNMATCHED" for row in oa_rows),
        },
    )
    three_way_pairs = [
        (row["reviewer_A_decision"], row["reviewer_B_decision"])
        for row in comparison_rows
    ]
    binary_pairs = [
        (
            "INCLUDE" if left == "INCLUDE" else "NON_INCLUDE",
            "INCLUDE" if right == "INCLUDE" else "NON_INCLUDE",
        )
        for left, right in three_way_pairs
    ]
    analysis["agreement"] = {
        "three_way": _paired_agreement(three_way_pairs, v2.AGREEMENT_DECISIONS),
        "binary": _paired_agreement(binary_pairs, ("NON_INCLUDE", "INCLUDE")),
    }
    analysis["tables"]["TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT"] = (
        _agreement_rows_v5(analysis["agreement"]),
        v2.AGREEMENT_TABLE_FIELDS,
    )
    table1, complete_flow, stages = _selection_rows_v5(contract, analysis, final_rows)
    analysis["tables"]["TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT"] = (
        table1,
        v2.AGREEMENT_TABLE_FIELDS,
    )
    analysis["supplements"]["SUPPLEMENT_SELECTION_FLOW_COMPLETE"] = (
        complete_flow,
        v2.DESCRIPTIVE_TABLE_FIELDS,
    )
    analysis["flow_v5"] = stages
    analysis["plot_data"]["retrieval_sources"] = [
        {
            "category": v2.plain_label(source),
            "count": int(contract["selection_flow"]["retrieval_occurrences_by_source"][source]),
        }
        for source in SIX_SOURCES
    ]
    _repair_phrase_sensitivity(analysis, works)
    _repair_no_explicit_nts_response_types(analysis)

    author_rows = _author_identity_ledger(works, {row["paper_id"]: row for row in oa_rows})
    analysis["supplements"]["SUPPLEMENT_AUTHOR_IDENTITY_LEDGER_V5"] = (
        author_rows,
        AUTHOR_LEDGER_FIELDS,
    )
    specialties, specialty_ledger = _specialty_grouping(works, spec)
    analysis["plot_data"]["specialties"] = specialties
    analysis["supplements"]["SUPPLEMENT_SPECIALTY_GROUPING_DICTIONARY_V5"] = (
        specialty_ledger,
        SPECIALTY_LEDGER_FIELDS,
    )
    analysis["supplements"]["SUPPLEMENT_INPUT_BINDINGS_V5"] = (
        list(final_data.get("input_binding_rows") or []),
        INPUT_BINDING_FIELDS,
    )
    oversight_rows = [
        dict(row)
        for row in table1
        if row["section"] == "Lead-author oversight"
    ]
    analysis["supplements"]["SUPPLEMENT_LEAD_AUTHOR_OVERSIGHT_AUDIT_V5"] = (
        oversight_rows,
        v2.AGREEMENT_TABLE_FIELDS,
    )
    claims = _claim_register(analysis, input_bundle_sha256)
    analysis["supplements"]["SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5"] = (
        claims,
        CLAIM_REGISTER_FIELDS,
    )
    analysis["version_rows"] = version_rows
    analysis["version_fields"] = list(final_data["version_fields"])
    validate_analysis_contract(analysis, spec, contract)
    return analysis


def _rows_by_category(rows: Sequence[Mapping[str, Any]], measure: str) -> dict[str, Mapping[str, Any]]:
    return {str(row["category"]): row for row in rows if row.get("measure") == measure}


def validate_analysis_contract(
    analysis: Mapping[str, Any], spec: Mapping[str, Any], contract: Mapping[str, Any]
) -> None:
    n = int(analysis["n"])
    required_tables = {
        "TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT",
        "TABLE_2_PUBLICATION_SOURCE_OA_CITATION_COVERAGE",
        "TABLE_3_MODEL_SIMULATION_STUDY_DESIGN",
        "TABLE_4_RECONCILED_NTS",
        "TABLE_5_GEOGRAPHY_WITH_MISSINGNESS",
        "TABLE_6_PREDEFINED_PHRASE_FREQUENCIES",
    }
    if set(analysis["tables"]) != required_tables:
        raise CombinedAnalysisError("Main-table set differs from the V5 publication contract")
    required_supplements = {
        "SUPPLEMENT_SELECTION_FLOW_COMPLETE",
        "SUPPLEMENT_PUBLICATION_SOURCES_COMPLETE",
        "SUPPLEMENT_COVERAGE_COMPLETE",
        "SUPPLEMENT_AUTHOR_IDENTITY_LEDGER_V5",
        "SUPPLEMENT_GEOGRAPHY_WHOLE_AND_FRACTIONAL_COMPLETE",
        "SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE",
        "SUPPLEMENT_PHRASE_NETWORK_NODES_CONDITIONAL",
        "SUPPLEMENT_PREDEFINED_PHRASE_DICTIONARY",
        "SUPPLEMENT_PER_STUDY_PHRASE_INDICATORS",
        "SUPPLEMENT_MODEL_FAMILIES_COMPLETE",
        "SUPPLEMENT_SIMULATION_METHODS_COMPLETE",
        "SUPPLEMENT_NTS_DOMAINS_COMPLETE",
        "SUPPLEMENT_SPECIALTY_PROFESSION_COMPLETE",
        "SUPPLEMENT_SPECIALTY_GROUPING_DICTIONARY_V5",
        "SUPPLEMENT_INPUT_BINDINGS_V5",
        "SUPPLEMENT_LEAD_AUTHOR_OVERSIGHT_AUDIT_V5",
        "SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5",
    }
    if required_supplements - set(analysis["supplements"]):
        raise CombinedAnalysisError(
            f"Mandatory V5 supplements are absent: {sorted(required_supplements - set(analysis['supplements']))}"
        )

    table1 = analysis["tables"]["TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT"][0]
    if any("not performed" in str(value).casefold() for row in table1 for value in row.values()):
        raise CombinedAnalysisError("The stale prospective-human-audit deferral row remains in Table 1")
    oversight_rows = [row for row in table1 if row["section"] == "Lead-author oversight"]
    if len(oversight_rows) != 1:
        raise CombinedAnalysisError("Table 1 must contain exactly one lead-author oversight row")
    oversight = oversight_rows[0]
    if (
        int(oversight["numerator"]) != 85
        or int(oversight["denominator"]) != 100
        or float(oversight["ci_lower"]) != 0.7646924998510451
        or float(oversight["ci_upper"]) != 0.9135456143583514
        or "predates the scopus extension" not in oversight["note"].casefold()
        or "not accuracy" not in oversight["note"].casefold()
    ):
        raise CombinedAnalysisError("Lead-author oversight scope or values changed")

    table4 = analysis["tables"]["TABLE_4_RECONCILED_NTS"][0]
    nts_coverage = _rows_by_category(table4, "NTS evidence coverage")
    explicit = nts_coverage.get("At least one explicit NTS domain")
    blank = next((row for row in table4 if row["category"] == "No explicit NTS domain"), None)
    if explicit is None or blank is None or int(explicit["count"]) + int(blank["count"]) != n:
        raise CombinedAnalysisError("Explicit/no-explicit NTS rows do not reconcile to N")
    no_explicit_rows = [
        row
        for collection_name in ("tables", "supplements")
        for rows, _fields in analysis[collection_name].values()
        for row in rows
        if row.get("category") == "No explicit NTS domain"
        and "response_type" in row
    ]
    if not no_explicit_rows or any(
        "mutually exclusive" not in str(row.get("response_type", "")).casefold()
        or "multiple response" in str(row.get("response_type", "")).casefold()
        for row in no_explicit_rows
    ):
        raise CombinedAnalysisError(
            "No-explicit-NTS rows must be coverage/mutually exclusive, never multiple-response"
        )

    table3 = analysis["tables"]["TABLE_3_MODEL_SIMULATION_STUDY_DESIGN"][0]
    if not any(row["category"] == "No exact model family established" for row in table3):
        raise CombinedAnalysisError("No-exact-model summary row is missing")
    if not any(row["category"] == "No explicit simulation method identified" for row in table3):
        raise CombinedAnalysisError("No-explicit-simulation-method row is missing")

    table2 = analysis["tables"]["TABLE_2_PUBLICATION_SOURCE_OA_CITATION_COVERAGE"][0]
    oa_categories = {
        row["category"].casefold()
        for row in table2
        if row["measure"] == "OpenAlex OA status"
    }
    if oa_categories != {v2.plain_label(value).casefold() for value in v2.OA_CATEGORIES}:
        raise CombinedAnalysisError("Open-access categories are incomplete")
    source_categories = {
        row["category"] for row in table2 if row["section"] == "Publication source"
    }
    if not {"Other named sources", "Named source available", "Unknown source"} <= source_categories:
        raise CombinedAnalysisError("Publication-source coverage/top named/other rows are incomplete")

    coverage_rows = analysis["supplements"]["SUPPLEMENT_COVERAGE_COMPLETE"][0]
    expected_coverage = {
        "Publication date",
        "Retained abstract",
        "Normalized publication source",
        "Structured authorship",
        "Country affiliation",
        "Open-access status",
        "Citation value",
        "Checked model field",
        "Checked simulation field",
        "Explicit NTS domain",
        "Specialty or profession",
        "Study-design label",
    }
    by_measure: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in coverage_rows:
        by_measure[str(row["measure"])].append(row)
    if set(by_measure) != expected_coverage:
        raise CombinedAnalysisError("The full 12-field missingness ledger is incomplete")
    for measure, rows in by_measure.items():
        if len(rows) != 2 or sum(int(row["count"]) for row in rows) != n:
            raise CombinedAnalysisError(f"Coverage rows do not reconcile for {measure}")

    geography = analysis["tables"]["TABLE_5_GEOGRAPHY_WITH_MISSINGNESS"][0]
    if not any(row["measure"] == "International collaboration" for row in geography):
        raise CombinedAnalysisError("International-collaboration row is missing")
    complete_geo = analysis["supplements"]["SUPPLEMENT_GEOGRAPHY_WHOLE_AND_FRACTIONAL_COMPLETE"][0]
    if not any("all-study denominator" in row["measure"] for row in complete_geo):
        raise CombinedAnalysisError("Country all-work percentages are missing")
    top_whole = [row["category"] for row in geography if row["measure"] == "Whole-count country affiliation"]
    paired_fractional = [row["category"] for row in geography if row["measure"] == "Fractional country affiliation"]
    if top_whole != paired_fractional:
        raise CombinedAnalysisError("Fractional country values are not paired to the whole-count top ten")

    phrase_rows = analysis["supplements"]["SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE"][0]
    for phrase_stem in (
        "SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE",
        "SUPPLEMENT_SENSITIVITY_PREPRINT_REPOSITORY_PHRASES",
    ):
        for row in analysis["supplements"][phrase_stem][0]:
            if row["measure"] in {
                "Predefined phrase frequency",
                "Retained-abstract sensitivity frequency",
            }:
                if any(
                    field not in row
                    for field in ("title_count", "abstract_count", "keyword_count")
                ):
                    raise CombinedAnalysisError("Phrase field-specific counts are missing")
                ids = v2.split_semicolon(row["work_ids"])
                if len(ids) != int(row["count"]):
                    raise CombinedAnalysisError(
                        f"Phrase work-ID ledger does not match count: {phrase_stem} / "
                        f"{row['measure']} / {row['category']}"
                    )
    main_phrase_counts = {
        row["category"]: int(row["count"])
        for row in phrase_rows
        if row["measure"] == "Predefined phrase frequency"
    }
    for row in analysis["supplements"]["SUPPLEMENT_PHRASE_NETWORK_NODES_CONDITIONAL"][0]:
        if int(row["count"]) != main_phrase_counts[row["category"]]:
            raise CombinedAnalysisError("Phrase-network node size is not the unique-work phrase count")

    specialty_ledger = analysis["supplements"]["SUPPLEMENT_SPECIALTY_GROUPING_DICTIONARY_V5"][0]
    if any(row["included_in_figure_5"] != "1" for row in specialty_ledger if row["display_group"] == "surgical specialty"):
        raise CombinedAnalysisError("Figure 5 omits a represented surgical category")
    if any("_" in row["plain_label"] for row in specialty_ledger):
        raise CombinedAnalysisError("Specialty dictionary contains a raw underscore display label")

    author_rows = analysis["supplements"]["SUPPLEMENT_AUTHOR_IDENTITY_LEDGER_V5"][0]
    if any(not row["author_key"] or row["unresolved_name_flag"] not in {"0", "1"} for row in author_rows):
        raise CombinedAnalysisError("Author stable keys or unresolved-name flags are incomplete")
    productivity_rows = [
        row
        for row in analysis["supplements"]["SUPPLEMENT_AUTHOR_PRODUCTIVITY_COMPLETE"][0]
        if row["section"] == "Author productivity"
    ]
    author_by_key = {row["author_key"]: row for row in author_rows}
    productivity_by_key = {row["value_text"]: row for row in productivity_rows}
    if len(author_by_key) != len(author_rows) or len(productivity_by_key) != len(productivity_rows):
        raise CombinedAnalysisError("Duplicate stable keys remain in an author output")
    if set(author_by_key) != set(productivity_by_key):
        raise CombinedAnalysisError(
            "Author identity ledger and productivity output do not contain the same identities"
        )
    for key, identity_row in author_by_key.items():
        productivity_row = productivity_by_key[key]
        if (
            int(identity_row["work_count"]) != int(productivity_row["count"])
            or set(v2.split_semicolon(identity_row["work_ids"]))
            != set(v2.split_semicolon(productivity_row["work_ids"]))
        ):
            raise CombinedAnalysisError(
                f"Author identity ledger/productivity work set differs for {key}"
            )

    selection_rows = analysis["supplements"]["SUPPLEMENT_SELECTION_FLOW_COMPLETE"][0]
    tiny_exclusion_rows = [
        row
        for row in selection_rows
        if row["measure"] == "Final primary exclusion reason"
        and int(row["count"]) > 0
        and 100.0 * int(row["count"]) / int(row["denominator"]) < 0.1
    ]
    if any(row["percent"] != "<0.1%" for row in tiny_exclusion_rows):
        raise CombinedAnalysisError("A positive sub-0.1% exclusion was not publication-formatted")
    if len(analysis["version_rows"]) != int(contract["selection_flow"]["eligible_publication_records"]):
        raise CombinedAnalysisError("Version ledger count changed during analysis")

    artifact_names = [*analysis["tables"], *analysis["supplements"]]
    prohibited = [name for name in artifact_names if "word_cloud" in name.casefold() or "wordcloud" in name.casefold() or "urology_only" in name.casefold()]
    if prohibited:
        raise CombinedAnalysisError(f"Prohibited output artifacts are present: {prohibited}")
    claims = analysis["supplements"]["SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5"][0]
    if not claims or any(not v2.SHA256_RE.fullmatch(row["input_bundle_sha256"]) for row in claims):
        raise CombinedAnalysisError("Claim-to-source register is missing or unbound")


def _stage_map(analysis: Mapping[str, Any]) -> dict[str, int]:
    return {label: int(count) for label, count, _definition in analysis["flow_v5"]}


def _phrase_network_crossing_count(
    order: Sequence[str], edges: Sequence[tuple[str, str, int]]
) -> int:
    """Count straight-chord crossings for a circular node order."""

    positions = {label: index for index, label in enumerate(order)}
    if len(positions) != len(order):
        raise CombinedAnalysisError("Phrase-network circular order contains duplicate nodes")

    def on_clockwise_arc(point: int, start: int, end: int) -> bool:
        if start < end:
            return start < point < end
        return point > start or point < end

    crossings = 0
    for (left_a, right_a, _count_a), (left_b, right_b, _count_b) in itertools.combinations(
        edges, 2
    ):
        if len({left_a, right_a, left_b, right_b}) < 4:
            continue
        a, b = positions[left_a], positions[right_a]
        c, d = positions[left_b], positions[right_b]
        if on_clockwise_arc(c, a, b) != on_clockwise_arc(d, a, b):
            crossings += 1
    return crossings


def _optimise_phrase_network_circular_order(
    nodes: Sequence[str], edges: Sequence[tuple[str, str, int]]
) -> tuple[list[str], int]:
    """Choose a deterministic low-crossing circular order from fixed multistarts."""

    unique = sorted(set(nodes), key=str.casefold)
    if len(unique) != len(nodes):
        raise CombinedAnalysisError("Phrase-network node list contains duplicates")
    edge_nodes = {label for left, right, _count in edges for label in (left, right)}
    if edge_nodes != set(unique):
        raise CombinedAnalysisError("Phrase-network node and edge sets differ")

    degree = Counter()
    for left, right, count in edges:
        degree[left] += count
        degree[right] += count
    starts: list[list[str]] = [
        list(unique),
        sorted(unique, key=lambda label: (-degree[label], label.casefold())),
    ]
    rng = random.Random(2026081702)
    for _ in range(64):
        candidate = list(unique)
        rng.shuffle(candidate)
        starts.append(candidate)

    def improve(order: list[str]) -> tuple[list[str], int]:
        current = list(order)
        current_cost = _phrase_network_crossing_count(current, edges)
        while True:
            best_order = current
            best_cost = current_cost
            for left_index in range(len(current) - 1):
                for right_index in range(left_index + 1, len(current)):
                    candidate = list(current)
                    candidate[left_index], candidate[right_index] = (
                        candidate[right_index],
                        candidate[left_index],
                    )
                    cost = _phrase_network_crossing_count(candidate, edges)
                    if cost < best_cost or (
                        cost == best_cost
                        and tuple(item.casefold() for item in candidate)
                        < tuple(item.casefold() for item in best_order)
                    ):
                        best_order, best_cost = candidate, cost
            if best_cost >= current_cost:
                return current, current_cost
            current, current_cost = best_order, best_cost

    candidates = [improve(start) for start in starts]
    return min(
        candidates,
        key=lambda item: (item[1], tuple(label.casefold() for label in item[0])),
    )


def create_supplementary_phrase_network_v5(
    directory: Path, analysis: Mapping[str, Any]
) -> list[Path]:
    """Render a print-legible network with numbered nodes and a separate legend."""

    edges = list(analysis["plot_data"]["phrase_network_edges"])
    if not edges:
        return []
    parsed: list[tuple[str, str, int]] = []
    nodes: set[str] = set()
    for row in edges:
        pair = _clean(row["category"]).split(" + ")
        count = int(row["count"])
        if len(pair) != 2 or count < 3:
            raise CombinedAnalysisError("Malformed conditional phrase-network edge")
        left, right = pair
        parsed.append((left, right, count))
        nodes.update((left, right))

    node_counts = analysis["plot_data"].get("phrase_counts") or {}
    if any(int(node_counts.get(label, 0)) < 5 for label in nodes):
        raise CombinedAnalysisError("Phrase-network node does not meet the minimum work count")
    order, crossing_count = _optimise_phrase_network_circular_order(
        sorted(nodes, key=str.casefold), parsed
    )
    positions = {
        label: v2.np.array(
            [
                math.cos(math.pi / 2.0 - 2.0 * math.pi * index / len(order)),
                math.sin(math.pi / 2.0 - 2.0 * math.pi * index / len(order)),
            ]
        )
        for index, label in enumerate(order)
    }
    legend_order = sorted(nodes, key=lambda label: (-int(node_counts[label]), label.casefold()))
    legend_number = {label: index for index, label in enumerate(legend_order, start=1)}

    directory.mkdir(parents=True, exist_ok=True)
    fig = v2.plt.figure(figsize=(13.0, 8.6))
    grid = fig.add_gridspec(1, 2, width_ratios=(1.85, 1.15), wspace=0.02)
    ax = fig.add_subplot(grid[0, 0])
    legend_ax = fig.add_subplot(grid[0, 1])
    ax.set_aspect("equal")
    ax.axis("off")
    legend_ax.axis("off")

    for left, right, count in parsed:
        start, end = positions[left], positions[right]
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color="#a9b5bf",
            linewidth=0.035 * count,
            alpha=1.0,
            solid_capstyle="round",
            zorder=1,
        )
    for label in order:
        point = positions[label]
        count = int(node_counts[label])
        ax.scatter(
            [point[0]],
            [point[1]],
            s=8.5 * count,
            color="#d7e6f0",
            edgecolor="#315b7d",
            linewidth=1.2,
            zorder=3,
        )
        ax.text(
            point[0],
            point[1],
            str(legend_number[label]),
            ha="center",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            color="#173a55",
            zorder=4,
        )
    ax.set_xlim(-1.18, 1.18)
    ax.set_ylim(-1.18, 1.18)
    ax.set_title("Same-study phrase co-occurrence", fontsize=12.0, pad=10)
    ax.text(
        0.5,
        -0.035,
        "Node area is proportional to study count; edge width is proportional to co-occurrence count.\n"
        "Circular placement is descriptive only.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8.2,
        color="#333333",
    )

    legend_ax.text(
        0.0,
        0.985,
        "Phrase key",
        ha="left",
        va="top",
        fontsize=11.0,
        fontweight="bold",
    )
    y = 0.935
    for label in legend_order:
        wrapped = textwrap.wrap(f"{legend_number[label]}. {label} (n={int(node_counts[label])})", width=36)
        legend_ax.text(
            0.0,
            y,
            "\n".join(wrapped),
            ha="left",
            va="top",
            fontsize=8.5,
            linespacing=1.12,
        )
        y -= 0.037 * len(wrapped) + 0.014
    legend_ax.text(
        0.0,
        0.015,
        f"Deterministic circular ordering; {crossing_count} straight-edge crossings.",
        ha="left",
        va="bottom",
        fontsize=7.4,
        color="#555555",
    )
    return v2.save_figure_pair(
        fig, directory, "SUPPLEMENT_FIGURE_PHRASE_NETWORK_CONDITIONAL"
    )


def create_figures_v5(directory: Path, analysis: Mapping[str, Any]) -> list[Path]:
    directory.mkdir()
    paths: list[Path] = []
    stage = _stage_map(analysis)
    source_lines = [
        f"{row['category']}: {int(row['count']):,}"
        for row in analysis["plot_data"]["retrieval_sources"]
    ]
    fig, ax = v2.plt.subplots(figsize=(10.4, 11.4))
    ax.axis("off")
    main = [
        ("Results returned by six sources\n" + " | ".join(source_lines[:3]) + "\n" + " | ".join(source_lines[3:]), stage["Retrieval occurrences"]),
        ("Occurrences entering duplicate handling", stage["Occurrences entering duplicate handling"]),
        ("Records after automatic duplicate merging", stage["Records after automatic duplicate merging"]),
        ("Unique records after separately checked identity matches", stage["Unique bibliographic records after deduplication"]),
        ("Records reviewed independently by both model reviewers", stage["Candidate records reviewed by both models"]),
        ("Eligible publication records", stage["Eligible publication records"]),
        ("Unique scholarly works analysed", stage["Canonical unique works"]),
    ]
    side = [
        (0, "Scopus results after 13 August removed", stage["Scopus results after the cutoff"]),
        (1, "Automatically merged duplicate occurrences", stage["Automatically merged duplicate occurrences"]),
        (2, "Same-record matches confirmed separately", stage["Separately confirmed same-record merges"]),
        (3, "Records outside the broad review rule", stage["Records outside the four-domain candidate frame"]),
        (4, "Review decisions checked separately", stage["All separately resolved review records"]),
        (4, "Records excluded after resolution", stage["Records excluded after resolution"]),
        (5, "Alternate publications describing the same work", stage["Alternate publication versions"]),
    ]
    ys = v2.np.linspace(0.95, 0.06, len(main))
    for index, (label, count) in enumerate(main):
        y = ys[index]
        ax.text(
            0.34,
            y,
            f"{label}\n{count:,}",
            ha="center",
            va="center",
            fontsize=9.0 if index == 0 else 9.7,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "#eef4f8", "edgecolor": "#315b7d"},
        )
        if index < len(main) - 1:
            ax.annotate("", xy=(0.34, ys[index + 1] + 0.043), xytext=(0.34, y - 0.043), arrowprops={"arrowstyle": "->", "linewidth": 0.8})
    offsets: defaultdict[int, int] = defaultdict(int)
    for source_index, label, count in side:
        offset = offsets[source_index]
        offsets[source_index] += 1
        y = ys[source_index] - 0.048 - offset * 0.078
        ax.annotate("", xy=(0.69, y), xytext=(0.52, ys[source_index] - 0.01), arrowprops={"arrowstyle": "->", "linewidth": 0.75})
        ax.text(
            0.81,
            y,
            f"{label}\n{count:,}",
            ha="center",
            va="center",
            fontsize=8.1,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "#f7f7f7", "edgecolor": "#666666"},
        )
    ax.text(
        0.64,
        0.015,
        "Five-source date audit (reported separately, not serial losses): "
        f"{stage['Primary-source results before or after the date window']:,} before/after the window; "
        f"{stage['Primary-source results with an unknown or unresolved date']:,} unknown/unresolved.",
        ha="left",
        va="bottom",
        fontsize=7.7,
        wrap=True,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#fff8e8", "edgecolor": "#9a7b3f"},
    )
    paths.extend(v2.save_figure_pair(fig, directory, "FIGURE_1_SELECTION_FLOW"))

    plot = analysis["plot_data"]
    fig, ax = v2.plt.subplots(figsize=(8.2, 5.0))
    colours = ["#315b7d"] * 6 + ["#a65f2b"]
    bars = ax.bar(range(7), plot["year_counts"], color=colours, edgecolor="black", linewidth=0.5)
    ax.set_xticks(range(7), [str(year) for year in range(2020, 2026)] + ["2026\n(to 13 Aug)"])
    ax.set_ylabel("Unique studies")
    ax.spines[["top", "right"]].set_visible(False)
    ax.bar_label(bars, padding=2, fontsize=8)
    ax.grid(False)
    paths.extend(v2.save_figure_pair(fig, directory, "FIGURE_2_ANNUAL_COUNTS"))

    fig, axes = v2.plt.subplots(1, 2, figsize=(13.0, 7.2))
    v2._barh(axes[0], plot["models"], max_rows=12)
    v2._barh(axes[1], plot["simulations"])
    axes[0].text(-0.14, 1.02, "A", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.14, 1.02, "B", transform=axes[1].transAxes, fontweight="bold")
    fig.tight_layout()
    paths.extend(v2.save_figure_pair(fig, directory, "FIGURE_3_MODEL_FAMILIES_AND_SIMULATION_METHODS"))

    fig, axes = v2.plt.subplots(1, 2, figsize=(13.0, 6.6))
    v2._barh(axes[0], plot["nts"])
    v2._barh(axes[1], plot["designs"])
    axes[0].text(-0.14, 1.02, "A", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.14, 1.02, "B", transform=axes[1].transAxes, fontweight="bold")
    fig.tight_layout()
    paths.extend(v2.save_figure_pair(fig, directory, "FIGURE_4_NTS_DOMAINS_AND_STUDY_DESIGNS"))

    specialty_height = max(7.2, 1.8 + 0.34 * len(plot["specialties"]))
    fig, ax = v2.plt.subplots(figsize=(10.0, specialty_height))
    v2._barh(ax, plot["specialties"])
    fig.tight_layout()
    paths.extend(v2.save_figure_pair(fig, directory, "FIGURE_5_SPECIALTIES_AND_PROFESSIONS"))
    return paths


def _figure_manifest(figure_paths: Sequence[Path], root: Path) -> list[dict[str, Any]]:
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise CombinedAnalysisError("Pillow is required for figure DPI QA") from exc
    by_stem: defaultdict[str, dict[str, Path]] = defaultdict(dict)
    for path in figure_paths:
        by_stem[path.stem][path.suffix.casefold()] = path
    rows: list[dict[str, Any]] = []
    for stem, pair in sorted(by_stem.items()):
        if set(pair) != {".png", ".eps"}:
            raise CombinedAnalysisError(f"Figure lacks PNG/EPS pair: {stem}")
        png, eps = pair[".png"], pair[".eps"]
        with Image.open(png) as image:
            dpi = image.info.get("dpi") or (0.0, 0.0)
            x_dpi, y_dpi = float(dpi[0]), float(dpi[1])
            if abs(x_dpi - 600.0) > 1.0 or abs(y_dpi - 600.0) > 1.0:
                raise CombinedAnalysisError(f"PNG is not 600 dpi: {png}: {dpi}")
            width, height = image.size
        rows.append(
            {
                "figure_stem": stem,
                "png_path": png.relative_to(root).as_posix(),
                "eps_path": eps.relative_to(root).as_posix(),
                "png_width_px": width,
                "png_height_px": height,
                "png_dpi_x": round(x_dpi, 3),
                "png_dpi_y": round(y_dpi, 3),
                "png_sha256": v2.sha256_file(png),
                "eps_sha256": v2.sha256_file(eps),
            }
        )
    return rows


def _ensure_output(output: Path, input_paths: Iterable[Path]) -> Path:
    output = output.resolve()
    try:
        output.relative_to(WORKSPACE.resolve())
    except ValueError as exc:
        raise CombinedAnalysisError("V5 output must remain inside the workspace") from exc
    if output.exists():
        raise CombinedAnalysisError(f"V5 output already exists; no-clobber is mandatory: {output}")
    for path in input_paths:
        try:
            output.relative_to(path.resolve())
        except ValueError:
            pass
        else:
            raise CombinedAnalysisError("V5 output cannot be placed inside an input directory")
    return output


def _verify_all_bindings(validated: Mapping[str, Any]) -> None:
    for role, pin in validated["inputs"].items():
        if not pin["path"].is_file() or v2.sha256_file(pin["path"]) != pin["sha256"]:
            raise CombinedAnalysisError(f"Input changed during analysis: {role}")


def run_production(
    *,
    contract_path: Path,
    output_dir: Path,
    confirm_production_run: bool,
) -> Mapping[str, Any]:
    if not confirm_production_run:
        raise CombinedAnalysisError("Production V5 execution requires --confirm-production-run")
    validated = validate_input_contract(contract_path, production=True, validate_locked_files=True)
    spec = v2.load_json(validated["inputs"]["analysis_specification"]["path"], "analysis specification")
    final_data = _validate_final_rows(validated, spec)
    final_data["input_binding_rows"] = _input_binding_rows(validated)
    analysis = build_analysis_from_rows(
        spec=spec,
        contract=validated["contract"],
        final_data=final_data,
        input_bundle_sha256=_input_bundle_sha(validated),
    )

    output = _ensure_output(output_dir, (pin["path"].parent for pin in validated["inputs"].values()))
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        table_dir = temp / "tables"
        supplement_dir = temp / "supplements"
        figure_dir = temp / "figures"
        table_dir.mkdir()
        supplement_dir.mkdir()
        artifacts: list[Path] = []
        for stem, (rows, fields) in analysis["tables"].items():
            artifacts.extend(
                v2.write_table_pair(
                    table_dir, stem, rows, fields, table_kind="main table"
                )
            )
        for stem, (rows, fields) in analysis["supplements"].items():
            artifacts.extend(
                v2.write_table_pair(
                    supplement_dir, stem, rows, fields, table_kind="supplement"
                )
            )

        version_copy = supplement_dir / "SUPPLEMENT_ELIGIBLE_PUBLICATION_VERSION_LEDGER_V5.csv"
        v2.write_csv(version_copy, analysis["version_rows"], analysis["version_fields"])
        artifacts.append(version_copy)
        figure_paths = create_figures_v5(figure_dir, analysis)
        artifacts.extend(figure_paths)
        network_paths = create_supplementary_phrase_network_v5(supplement_dir, analysis)
        artifacts.extend(network_paths)
        figure_rows = _figure_manifest([*figure_paths, *network_paths], temp)
        figure_manifest = figure_dir / "FIGURE_MANIFEST_V5.csv"
        v2.write_csv(figure_manifest, figure_rows, FIGURE_MANIFEST_FIELDS)
        artifacts.append(figure_manifest)

        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": v2.utc_now(),
            "status": FINAL_STATUS,
            "study_window": validated["contract"]["study_window"],
            "canonical_works": analysis["n"],
            "eligible_publication_records": len(analysis["version_rows"]),
            "alternate_publication_versions": len(analysis["version_rows"]) - analysis["n"],
            "candidate_records": validated["selection"]["candidates"],
            "six_source_retrieval_occurrences": validated["selection"]["raw"],
            "scopus_after_cutoff_removed": validated["selection"]["cutoff"],
            "separate_review_resolution_checks": validated["selection"]["resolution"],
            "model_review_agreement": analysis["agreement"],
            "human_reference_standard_available": False,
            "interpretation": "Agreement measures consistency between two model reviewers; it is not screening accuracy.",
            "partial_2026": {"through": "2026-08-13", "annualized": False},
            "output_contracts": {
                "all_denominators_explicit": True,
                "missing_values_converted_to_zero": False,
                "png_dpi": 600,
                "eps_companions": True,
                "word_cloud_included": False,
                "urology_only_analysis_included": False,
            },
        }
        summary_path = temp / OUTPUT_SUMMARY
        v2.write_json(summary_path, summary)
        artifacts.append(summary_path)

        input_entries = [
            {
                "role": role,
                "path": str(pin["path"]),
                "bytes": pin["bytes"],
                "sha256": pin["sha256"],
            }
            for role, pin in sorted(validated["inputs"].items())
        ]
        output_entries = [
            {
                "path": path.relative_to(temp).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": v2.sha256_file(path),
            }
            for path in sorted(artifacts, key=lambda item: item.relative_to(temp).as_posix())
        ]
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "pipeline": PIPELINE,
            "status": FINAL_STATUS,
            "generated_at_utc": v2.utc_now(),
            "contract_path": str(validated["contract_path"]),
            "contract_sha256": validated["contract_sha256"],
            "input_bundle_sha256": _input_bundle_sha(validated),
            "counts": {
                "canonical_works": analysis["n"],
                "eligible_publication_records": len(analysis["version_rows"]),
                "main_tables": len(analysis["tables"]),
                "main_figures": 5,
                "supplementary_phrase_network": 1 if network_paths else 0,
            },
            "inputs": input_entries,
            "outputs": output_entries,
            "contracts": {
                "six_completed_discovery_sources": list(SIX_SOURCES),
                "base_correction_bound": True,
                "scopus_finalization_version_extraction_metadata_bound": True,
                "combined_version_ledger_bound": True,
                "combined_checked_corpus_bound": True,
                "input_hashes_rechecked_before_publish": True,
                "output_no_clobber": True,
                "word_cloud_included": False,
                "urology_only_analysis_included": False,
            },
            "script": {
                "path": str(Path(__file__).resolve()),
                "sha256": v2.sha256_file(Path(__file__).resolve()),
                "validated_helper": str(Path(v2.__file__).resolve()),
                "validated_helper_sha256": v2.sha256_file(Path(v2.__file__).resolve()),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp / OUTPUT_MANIFEST
        v2.write_json(manifest_path, manifest)
        artifacts.append(manifest_path)

        hash_rows = [
            {
                "scope": "input",
                "path": str(pin["path"]),
                "role": role,
                "bytes": pin["bytes"],
                "sha256": pin["sha256"],
            }
            for role, pin in validated["inputs"].items()
        ]
        hash_rows.extend(
            {
                "scope": "output",
                "path": path.relative_to(temp).as_posix(),
                "role": "analysis_artifact",
                "bytes": path.stat().st_size,
                "sha256": v2.sha256_file(path),
            }
            for path in artifacts
        )
        hash_path = temp / OUTPUT_HASH_LEDGER
        v2.write_csv(
            hash_path,
            sorted(hash_rows, key=lambda row: (row["scope"], row["path"], row["role"])),
            v2.HASH_FIELDS,
        )
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "status": FINAL_STATUS,
            "analysis_manifest_sha256": v2.sha256_file(manifest_path),
            "analysis_hash_ledger_sha256": v2.sha256_file(hash_path),
            "analysis_summary_sha256": v2.sha256_file(summary_path),
            "contract_sha256": validated["contract_sha256"],
            "combined_version_ledger_sha256": validated["inputs"]["combined_eligible_version_ledger"]["sha256"],
            "combined_checked_corpus_sha256": validated["inputs"]["combined_checked_corpus"]["sha256"],
            "combined_openalex_sha256": validated["inputs"]["combined_openalex"]["sha256"],
        }
        frozen_path = temp / OUTPUT_FROZEN_MARKER
        v2.write_json(frozen_path, frozen)

        _verify_all_bindings(validated)
        if any("wordcloud" in path.name.casefold() or "word_cloud" in path.name.casefold() or "urology_only" in path.name.casefold() for path in temp.rglob("*")):
            raise CombinedAnalysisError("A prohibited output appeared in the package")
        for row in output_entries:
            path = temp / row["path"]
            if path.stat().st_size != row["bytes"] or v2.sha256_file(path) != row["sha256"]:
                raise CombinedAnalysisError(f"Generated output changed before freeze: {path}")
        temp.rename(output)
        return manifest
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise


def preflight(contract_path: Path) -> Mapping[str, Any]:
    validated = validate_input_contract(contract_path, production=False, validate_locked_files=True)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "READY" if validated["ready"] else "BLOCKED_AWAITING_FINAL_INPUTS",
        "contract_sha256": validated["contract_sha256"],
        "locked_inputs_validated": len(validated["inputs"]),
        "pending_roles": validated["pending_roles"],
        "production_analysis_run": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--confirm-production-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.preflight:
            print(json.dumps(preflight(args.input_contract), indent=2, sort_keys=True))
            return 0
        if args.output_dir is None:
            raise CombinedAnalysisError("--output-dir is required for production execution")
        manifest = run_production(
            contract_path=args.input_contract,
            output_dir=args.output_dir,
            confirm_production_run=args.confirm_production_run,
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    except CombinedAnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
