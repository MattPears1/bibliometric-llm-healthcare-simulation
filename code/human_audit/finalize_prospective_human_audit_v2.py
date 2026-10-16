#!/usr/bin/env python3
"""Validate and compare a completed fresh 100-record human audit.

The first human file is locked and hashed before model/sample labels are joined.
Any inclusion-status warning is routed to a separately blinded second-human
template.  Confirmed errors activate the prospectively specified expansion
rules; unconfirmed differences remain pending rather than being called errors.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from typing import Any, Iterable, Mapping, Sequence

from compare_fresh_independent_reviews_v2 import HUMAN_AUDIT_LINK_FIELDS
from fresh_screening_review_common_v2 import (
    FreshReviewError,
    file_entry,
    read_csv,
    safe_relative,
    sha256_file,
    validate_file_entry,
    write_csv,
)
from prospective_human_audit_common_v2 import (
    AUDIT_SCHEMA_VERSION,
    EXPECTED_SAMPLE_SIZE,
    HUMAN_RESPONSE_FIELDS,
    HUMAN_REVIEW_FIELDS,
    SECOND_HUMAN_RESPONSE_FIELDS,
    SECOND_HUMAN_REVIEW_FIELDS,
    STRATUM_FIELDS,
    VISIBLE_REVIEW_FIELDS,
    proportion_record,
    validate_completed_response,
    validate_no_whitespace_or_missing,
)


COMPARISON_RESULT_FIELDS = [
    "human_audit_id",
    "paper_id",
    "sample_group",
    "sample_component",
    "record_origin",
    "model_final_decision",
    "model_final_primary_code",
    "reviewer_A_decision",
    "reviewer_B_decision",
    "human_effective_decision",
    "human_effective_primary_code",
    "status_matches_model_final",
    "requires_second_human",
    "second_human_reason",
    "reviewer2_effective_decision",
    "reviewer2_effective_primary_code",
    "human_human_status_agreement",
    "confirmed_model_status_error",
    "requires_human_human_adjudication",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_hash_ledger(root: Path) -> None:
    fields, rows = read_csv(root / "HUMAN_AUDIT_HASH_MANIFEST.csv")
    if fields != ["scope", "path", "role", "bytes", "sha256"]:
        raise FreshReviewError("Unexpected human-audit hash-ledger schema")
    for row in rows:
        if row["scope"] != "output":
            continue
        target = safe_relative(root, row["path"], label="human-audit package output")
        if not target.is_file():
            raise FreshReviewError(f"Human-audit package output is missing: {target}")
        if (
            target.stat().st_size != int(row["bytes"])
            or sha256_file(target) != row["sha256"].casefold()
        ):
            raise FreshReviewError(f"Human-audit package output changed: {target}")


def _validate_bound_inputs(manifest: Mapping[str, Any]) -> None:
    bindings = manifest.get("bindings") or {}
    for key, entry in bindings.items():
        if key == "locked_reviewer_inputs":
            continue
        if not isinstance(entry, Mapping):
            raise FreshReviewError(f"Malformed audit binding: {key}")
        path = Path(str(entry.get("path") or "")).resolve()
        expected = str(entry.get("sha256") or "").casefold()
        if not path.is_file() or sha256_file(path) != expected:
            raise FreshReviewError(f"Bound input is missing or changed: {key}")

    comparison_manifest_path = Path(
        str((bindings.get("comparison_manifest") or {}).get("path") or "")
    ).resolve()
    comparison_root = comparison_manifest_path.parent
    for entry in bindings.get("locked_reviewer_inputs") or []:
        raw_path = Path(str(entry.get("path") or ""))
        path = raw_path.resolve() if raw_path.is_absolute() else (comparison_root / raw_path).resolve()
        if (
            not path.is_file()
            or path.stat().st_size != int(entry.get("bytes") or -1)
            or sha256_file(path) != str(entry.get("sha256") or "").casefold()
        ):
            raise FreshReviewError("A locked Reviewer A/B batch is missing or changed")


def _load_package(
    package_dir: Path,
) -> tuple[Mapping[str, Any], list[dict[str, str]], Mapping[str, Any]]:
    root = package_dir.resolve()
    manifest_path = root / "HUMAN_AUDIT_PACKAGE_MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FreshReviewError(f"Missing audit package manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise FreshReviewError(f"Invalid audit package manifest: {manifest_path}") from exc
    if (
        manifest.get("schema_version") != AUDIT_SCHEMA_VERSION
        or manifest.get("pipeline") != "fresh_v2_prospective_human_audit_sample_build"
    ):
        raise FreshReviewError("Not a fresh V2 prospective human-audit package")
    if int(manifest.get("sample_size") or 0) != EXPECTED_SAMPLE_SIZE:
        raise FreshReviewError("Audit package does not contain exactly 100 records")
    _validate_hash_ledger(root)
    _validate_bound_inputs(manifest)
    outputs = manifest.get("outputs") or {}
    review_path = validate_file_entry(
        root, outputs.get("blinded_review_template") or {}, label="blinded audit template"
    )
    protected_path = validate_file_entry(
        root, outputs.get("protected_manifest") or {}, label="protected audit manifest"
    )
    fields, template_rows = read_csv(review_path)
    if fields != HUMAN_REVIEW_FIELDS or len(template_rows) != EXPECTED_SAMPLE_SIZE:
        raise FreshReviewError("Blinded audit template has an unexpected schema or row count")
    if [row["human_audit_id"] for row in template_rows] != [
        f"H{index:03d}" for index in range(1, EXPECTED_SAMPLE_SIZE + 1)
    ]:
        raise FreshReviewError("Blinded audit IDs are not H001-H100 in order")
    for row in template_rows:
        if any(row[field] for field in HUMAN_RESPONSE_FIELDS):
            raise FreshReviewError("Original blinded template contains a human response")
    try:
        protected = json.loads(protected_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise FreshReviewError("Invalid protected audit manifest") from exc
    mappings = protected.get("mappings") or []
    if len(mappings) != EXPECTED_SAMPLE_SIZE:
        raise FreshReviewError("Protected mapping does not contain 100 records")
    if [row.get("human_audit_id") for row in mappings] != [
        row["human_audit_id"] for row in template_rows
    ]:
        raise FreshReviewError("Protected mapping and blinded template do not align")
    paper_ids = [str(row.get("paper_id") or "") for row in mappings]
    if any(not value for value in paper_ids) or len(paper_ids) != len(set(paper_ids)):
        raise FreshReviewError("Protected mapping paper IDs are blank or duplicated")
    return manifest, template_rows, protected


def _load_completed_first_review(
    path: Path, template_rows: Sequence[Mapping[str, str]]
) -> tuple[list[dict[str, str]], Mapping[str, tuple[str, str]]]:
    fields, rows = read_csv(path.resolve())
    if fields != HUMAN_REVIEW_FIELDS:
        raise FreshReviewError(f"{path}: expected the exact human-review schema/order")
    if len(rows) != EXPECTED_SAMPLE_SIZE:
        raise FreshReviewError(f"{path}: all 100 human responses are required")
    effective: dict[str, tuple[str, str]] = {}
    for template, row in zip(template_rows, rows, strict=True):
        audit_id = template["human_audit_id"]
        validate_no_whitespace_or_missing(
            row, required_fields=HUMAN_REVIEW_FIELDS, label=f"{path}:{audit_id}"
        )
        if any(row[field] != template[field] for field in VISIBLE_REVIEW_FIELDS):
            raise FreshReviewError(f"{path}: blinded evidence changed for {audit_id}")
        effective[audit_id] = validate_completed_response(
            row, prefix="human", label=f"{path}:{audit_id}"
        )
    return rows, effective


def _second_human_reason(mapping: Mapping[str, Any], human_decision: str) -> str:
    model = str(mapping["model_final_decision"])
    group = str(mapping["sample_group"])
    if group == "A_DIFFICULT" and (human_decision == "UNCERTAIN" or human_decision != model):
        return "Difficult-record human/model inclusion-status difference"
    if group == "B_AGREED_INCLUDE" and human_decision in {"EXCLUDE", "UNCERTAIN"}:
        return "Agreed-inclusion warning: human did not confirm INCLUDE"
    if group == "C_AGREED_EXCLUDE" and human_decision in {"INCLUDE", "UNCERTAIN"}:
        return "Agreed-exclusion warning: human did not confirm EXCLUDE"
    if group == "D_BOUNDARY_NEGATIVE" and human_decision in {"INCLUDE", "UNCERTAIN"}:
        return "Boundary warning: outside-frame record may be eligible"
    return ""


def _build_second_template(
    template_by_id: Mapping[str, Mapping[str, str]], flagged_ids: Sequence[str]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for audit_id in flagged_ids:
        source = template_by_id[audit_id]
        rows.append(
            {
                **{field: source[field] for field in VISIBLE_REVIEW_FIELDS},
                **{field: "" for field in SECOND_HUMAN_RESPONSE_FIELDS},
            }
        )
    return rows


def _load_second_review(
    path: Path,
    second_template: Sequence[Mapping[str, str]],
) -> tuple[list[dict[str, str]], Mapping[str, tuple[str, str]]]:
    fields, rows = read_csv(path.resolve())
    if fields != SECOND_HUMAN_REVIEW_FIELDS:
        raise FreshReviewError(f"{path}: unexpected second-human schema/order")
    expected_ids = [row["human_audit_id"] for row in second_template]
    if [row.get("human_audit_id", "") for row in rows] != expected_ids:
        raise FreshReviewError(
            f"{path}: second-human file must contain every flagged record once in blinded order"
        )
    effective: dict[str, tuple[str, str]] = {}
    for template, row in zip(second_template, rows, strict=True):
        audit_id = template["human_audit_id"]
        validate_no_whitespace_or_missing(
            row, required_fields=SECOND_HUMAN_REVIEW_FIELDS, label=f"{path}:{audit_id}"
        )
        if any(row[field] != template[field] for field in VISIBLE_REVIEW_FIELDS):
            raise FreshReviewError(f"{path}: second-human evidence changed for {audit_id}")
        effective[audit_id] = validate_completed_response(
            row, prefix="reviewer2", label=f"{path}:{audit_id}"
        )
    return rows, effective


def _agreement_metric(
    pairs: Iterable[tuple[str, str]], *, binary: bool
) -> Mapping[str, Any]:
    values = list(pairs)
    if binary:
        values = [
            (
                "INCLUDE" if left == "INCLUDE" else "NON_INCLUDE",
                "INCLUDE" if right == "INCLUDE" else "NON_INCLUDE",
            )
            for left, right in values
            if left != "UNCERTAIN"
        ]
    matches = sum(left == right for left, right in values)
    return proportion_record(matches, len(values)) if values else proportion_record(0, 0)


def _stratum_rows(
    comparison_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, Any]]:
    groups: list[tuple[str, str, list[Mapping[str, str]]]] = []
    by_group: dict[str, list[Mapping[str, str]]] = {}
    by_component: dict[tuple[str, str], list[Mapping[str, str]]] = {}
    for row in comparison_rows:
        by_group.setdefault(row["sample_group"], []).append(row)
        by_component.setdefault(
            (row["sample_group"], row["sample_component"]), []
        ).append(row)
    for group in sorted(by_group):
        groups.append((group, "ALL", by_group[group]))
        for (owner, component), rows in sorted(by_component.items()):
            if owner == group:
                groups.append((group, component, rows))

    interpretations = {
        "A_DIFFICULT": "Deliberately difficult sample; do not generalize this error proportion to ordinary records.",
        "B_AGREED_INCLUDE": "Check of model-agreed inclusions; the interval is stratum-specific, not overall sensitivity.",
        "C_AGREED_EXCLUDE": "Check of model-agreed exclusions; the interval is stratum-specific, not overall specificity.",
        "D_BOUNDARY_NEGATIVE": "Search-boundary tripwire; it does not estimate recall for the whole outside-frame universe.",
    }
    output: list[dict[str, Any]] = []
    for group, component, rows in groups:
        resolved = [row for row in rows if row["human_effective_decision"] != "UNCERTAIN"]
        errors = [
            row
            for row in resolved
            if row["human_effective_decision"] != row["model_final_decision"]
        ]
        interval = proportion_record(len(errors), len(resolved))
        output.append(
            {
                "sample_group": group,
                "sample_component": component,
                "records_reviewed": len(rows),
                "resolved_binary_records": len(resolved),
                "human_include": sum(row["human_effective_decision"] == "INCLUDE" for row in rows),
                "human_exclude": sum(row["human_effective_decision"] == "EXCLUDE" for row in rows),
                "human_uncertain": sum(row["human_effective_decision"] == "UNCERTAIN" for row in rows),
                "apparent_model_status_errors": len(errors),
                "apparent_error_proportion": interval["proportion"],
                "exact_95pct_lower": interval["exact_95pct_lower"],
                "exact_95pct_upper": interval["exact_95pct_upper"],
                "confirmed_model_status_errors": sum(row["confirmed_model_status_error"] == "true" for row in rows),
                "pending_second_human_or_adjudication": sum(
                    row["requires_second_human"] == "true"
                    and row["confirmed_model_status_error"] != "true"
                    for row in rows
                ),
                "interpretation": interpretations[group],
            }
        )
    return output


def _next_to_target(
    rankings: Sequence[Mapping[str, str]],
    selected_ids: set[str],
    target_total: int,
) -> tuple[list[str], bool]:
    ranked_ids = [row["paper_id"] for row in rankings]
    desired = ranked_ids[: min(target_total, len(ranked_ids))]
    return [paper_id for paper_id in desired if paper_id not in selected_ids], len(ranked_ids) >= target_total


def _expansion_plan(
    comparison_rows: Sequence[Mapping[str, str]], protected: Mapping[str, Any]
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    rankings = protected.get("pool_rankings") or {}
    selected_by_component: dict[str, set[str]] = {}
    for row in comparison_rows:
        selected_by_component.setdefault(row["sample_component"], set()).add(row["paper_id"])
    confirmed = [row for row in comparison_rows if row["confirmed_model_status_error"] == "true"]
    public_actions: list[dict[str, Any]] = []
    protected_actions: list[dict[str, Any]] = []

    difficult_errors = [row for row in confirmed if row["sample_group"] == "A_DIFFICULT"]
    if difficult_errors:
        all_difficult = rankings.get("DIFFICULT_ALL") or []
        selected_a = {
            row["paper_id"] for row in comparison_rows if row["sample_group"] == "A_DIFFICULT"
        }
        additional = [row["paper_id"] for row in all_difficult if row["paper_id"] not in selected_a]
        public_actions.append(
            {
                "rule": "difficult_confirmed_model_error",
                "status": "triggered",
                "action": "Review every remaining A/B disagreement or UNCERTAIN record and inspect the affected decision mechanism or codebook ambiguity.",
                "additional_records": len(additional),
            }
        )
        protected_actions.append({"rule": "difficult_confirmed_model_error", "paper_ids": additional})

    include_errors = [row for row in confirmed if row["sample_group"] == "B_AGREED_INCLUDE"]
    if include_errors:
        selected = selected_by_component.get("AGREED_INCLUDE", set())
        additional, full = _next_to_target(rankings.get("AGREED_INCLUDE") or [], selected, 100)
        public_actions.append(
            {
                "rule": "agreed_include_one_confirmed_error",
                "status": "triggered" if full else "triggered_complete_pool_short_of_100",
                "action": "Expand the model-agreed inclusion stratum to 100 records using the next locked hash ranks.",
                "additional_records": len(additional),
            }
        )
        protected_actions.append({"rule": "agreed_include_one_confirmed_error", "paper_ids": additional})
        if len(include_errors) >= 2:
            public_actions.append(
                {
                    "rule": "agreed_include_two_confirmed_errors",
                    "status": "triggered",
                    "action": "Audit the affected trigger/rule family and consider reviewing every model-agreed inclusion.",
                    "additional_records": None,
                }
            )

    exclude_errors = [row for row in confirmed if row["sample_group"] == "C_AGREED_EXCLUDE"]
    if exclude_errors:
        combined_ids: list[str] = []
        full = True
        for component in ("MIXED_EXCLUDE", "SAME_EXCLUDE"):
            additional, component_full = _next_to_target(
                rankings.get(component) or [],
                selected_by_component.get(component, set()),
                50,
            )
            full = full and component_full
            combined_ids.extend(additional)
            protected_actions.append(
                {"rule": "agreed_exclude_one_confirmed_false_exclusion", "component": component, "paper_ids": additional}
            )
        public_actions.append(
            {
                "rule": "agreed_exclude_one_confirmed_false_exclusion",
                "status": "triggered" if full else "triggered_complete_pool_short_of_50_per_component",
                "action": "Expand both agreed-exclusion code subgroups to 50 records each using the next locked hash ranks.",
                "additional_records": len(combined_ids),
            }
        )
        if len(exclude_errors) >= 2:
            public_actions.append(
                {
                    "rule": "agreed_exclude_two_confirmed_false_exclusions",
                    "status": "triggered",
                    "action": "Audit all records sharing the affected exclusion reason, trigger, or decision pattern and rerun dependent analyses.",
                    "additional_records": None,
                }
            )

    for component in ("BOUNDARY_NO_SIM", "BOUNDARY_NO_ED", "BOUNDARY_NO_HEALTH"):
        potentially_eligible = [
            row
            for row in comparison_rows
            if row["sample_component"] == component
            and row["requires_second_human"] == "true"
            and row["reviewer2_effective_decision"] in {"INCLUDE", "UNCERTAIN"}
        ]
        if not potentially_eligible:
            continue
        additional, full = _next_to_target(
            rankings.get(component) or [], selected_by_component.get(component, set()), 50
        )
        public_actions.append(
            {
                "rule": "boundary_record_remains_potentially_eligible",
                "component": component,
                "status": "triggered" if full else "triggered_complete_pool_short_of_50",
                "action": "Expand this boundary stratum to 50 records. If an eligible work is confirmed there, screen the complete stratum and revise the candidate rule.",
                "additional_records": len(additional),
            }
        )
        protected_actions.append(
            {"rule": "boundary_record_remains_potentially_eligible", "component": component, "paper_ids": additional}
        )

    pending = sum(row["requires_second_human"] == "true" and not row["reviewer2_effective_decision"] for row in comparison_rows)
    public = {
        "schema_version": "fresh-human-audit-expansion-actions-v2.0",
        "confirmed_errors": len(confirmed),
        "pending_second_human_reviews": pending,
        "actions": public_actions,
        "note": (
            "Expansion is triggered only by the prespecified confirmation rules. "
            "A first-human/model difference is a warning until independently checked."
        ),
    }
    protected_output = {
        **public,
        "warning": "Protected preparer file containing paper IDs for deterministic expansion.",
        "protected_actions": protected_actions,
    }
    return public, protected_output


def _human_linkage(
    package_manifest: Mapping[str, Any],
    mapping_by_id: Mapping[str, Mapping[str, Any]],
    effective_first: Mapping[str, tuple[str, str]],
    first_rows_by_id: Mapping[str, Mapping[str, str]],
    completed_sha: str,
    completed_utc: str,
) -> list[dict[str, str]]:
    comparison_manifest_path = Path(
        str(((package_manifest.get("bindings") or {}).get("comparison_manifest") or {}).get("path") or "")
    ).resolve()
    comparison_root = comparison_manifest_path.parent
    comparison_manifest = json.loads(comparison_manifest_path.read_text(encoding="utf-8-sig"))
    template_entry = (comparison_manifest.get("outputs") or {}).get("human_audit_linkage_template") or {}
    template_path = validate_file_entry(
        comparison_root, template_entry, label="V2 human-audit linkage template"
    )
    fields, rows = read_csv(template_path)
    if fields != HUMAN_AUDIT_LINK_FIELDS:
        raise FreshReviewError("Unexpected V2 human-audit linkage schema")
    candidate_mapping = {
        row["paper_id"]: row
        for row in mapping_by_id.values()
        if row["record_origin"] == "candidate_frame"
    }
    for row in rows:
        mapping = candidate_mapping.get(row["paper_id"])
        if not mapping:
            continue
        audit_id = mapping["human_audit_id"]
        decision, code = effective_first[audit_id]
        first = first_rows_by_id[audit_id]
        row.update(
            {
                "human_audit_id": audit_id,
                "human_decision": decision,
                "human_primary_code": code,
                "human_confidence": first["human_confidence"],
                "human_audit_source_sha256": completed_sha,
                "human_audit_completed_utc": completed_utc,
            }
        )
    return rows


def finalize_human_audit(
    package_dir: Path,
    completed_review: Path,
    output_dir: Path,
    *,
    second_human_review: Path | None = None,
) -> Mapping[str, Any]:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FreshReviewError(f"Output directory already exists: {output_dir}")
    package_manifest, template_rows, protected = _load_package(package_dir)
    first_rows, effective_first = _load_completed_first_review(
        completed_review, template_rows
    )
    completed_sha = sha256_file(completed_review.resolve())
    completed_utc = utc_now()
    template_by_id = {row["human_audit_id"]: row for row in template_rows}
    first_by_id = {row["human_audit_id"]: row for row in first_rows}
    mapping_by_id = {
        row["human_audit_id"]: row for row in protected.get("mappings") or []
    }

    flagged_ids: list[str] = []
    reasons: dict[str, str] = {}
    for audit_id in [row["human_audit_id"] for row in template_rows]:
        reason = _second_human_reason(mapping_by_id[audit_id], effective_first[audit_id][0])
        if reason:
            flagged_ids.append(audit_id)
            reasons[audit_id] = reason
    second_template = _build_second_template(template_by_id, flagged_ids)
    effective_second: Mapping[str, tuple[str, str]] = {}
    second_sha = ""
    if second_human_review:
        _, effective_second = _load_second_review(
            second_human_review, second_template
        )
        second_sha = sha256_file(second_human_review.resolve())

    comparison_rows: list[dict[str, str]] = []
    for audit_id in [row["human_audit_id"] for row in template_rows]:
        mapping = mapping_by_id[audit_id]
        human_decision, human_code = effective_first[audit_id]
        model_decision = str(mapping["model_final_decision"])
        reviewer2_decision, reviewer2_code = effective_second.get(audit_id, ("", ""))
        requires_second = audit_id in reasons
        human_human_agreement = (
            ""
            if not reviewer2_decision
            else "true"
            if reviewer2_decision == human_decision
            else "false"
        )
        confirmed_error = (
            bool(reviewer2_decision)
            and human_decision in {"INCLUDE", "EXCLUDE"}
            and reviewer2_decision == human_decision
            and human_decision != model_decision
        )
        requires_adjudication = bool(reviewer2_decision) and (
            reviewer2_decision != human_decision
            or "UNCERTAIN" in {reviewer2_decision, human_decision}
        )
        comparison_rows.append(
            {
                "human_audit_id": audit_id,
                "paper_id": str(mapping["paper_id"]),
                "sample_group": str(mapping["sample_group"]),
                "sample_component": str(mapping["sample_component"]),
                "record_origin": str(mapping["record_origin"]),
                "model_final_decision": model_decision,
                "model_final_primary_code": str(mapping["model_final_primary_code"]),
                "reviewer_A_decision": str(mapping["reviewer_A_decision"]),
                "reviewer_B_decision": str(mapping["reviewer_B_decision"]),
                "human_effective_decision": human_decision,
                "human_effective_primary_code": human_code,
                "status_matches_model_final": "true" if human_decision == model_decision else "false",
                "requires_second_human": "true" if requires_second else "false",
                "second_human_reason": reasons.get(audit_id, ""),
                "reviewer2_effective_decision": reviewer2_decision,
                "reviewer2_effective_primary_code": reviewer2_code,
                "human_human_status_agreement": human_human_agreement,
                "confirmed_model_status_error": "true" if confirmed_error else "false",
                "requires_human_human_adjudication": "true" if requires_adjudication else "false",
            }
        )

    stratum_rows = _stratum_rows(comparison_rows)
    candidate_rows = [row for row in comparison_rows if row["record_origin"] == "candidate_frame"]
    agreement = {
        "schema_version": "fresh-human-audit-agreement-summary-v2.0",
        "human_vs_model_final_three_way_raw_agreement": _agreement_metric(
            ((row["human_effective_decision"], row["model_final_decision"]) for row in comparison_rows),
            binary=False,
        ),
        "human_vs_model_final_binary_include_noninclude_agreement": _agreement_metric(
            ((row["human_effective_decision"], row["model_final_decision"]) for row in comparison_rows),
            binary=True,
        ),
        "human_vs_reviewer_A_three_way_raw_agreement_candidate_records": _agreement_metric(
            ((row["human_effective_decision"], row["reviewer_A_decision"]) for row in candidate_rows),
            binary=False,
        ),
        "human_vs_reviewer_B_three_way_raw_agreement_candidate_records": _agreement_metric(
            ((row["human_effective_decision"], row["reviewer_B_decision"]) for row in candidate_rows),
            binary=False,
        ),
        "interpretation": (
            "These are human-model audit agreement measures, not human inter-rater "
            "reliability and not sensitivity or specificity. Exact 95% binomial "
            "intervals are Clopper-Pearson intervals."
        ),
        "zero_error_warning": (
            "Zero observed errors never proves zero errors or complete search sensitivity. "
            "For 0 errors among 20 records, the two-sided exact 95% upper limit is "
            f"{proportion_record(0, 20)['exact_95pct_upper']:.6f}."
        ),
    }
    public_expansion, protected_expansion = _expansion_plan(comparison_rows, protected)
    linkage_rows = _human_linkage(
        package_manifest,
        mapping_by_id,
        effective_first,
        first_by_id,
        completed_sha,
        completed_utc,
    )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.building-", dir=output_dir.parent)
    )
    try:
        comparison_path = temp_dir / "HUMAN_AUDIT_COMPARISON_RESULTS_PROTECTED.csv"
        stratum_path = temp_dir / "HUMAN_AUDIT_STRATUM_RESULTS.csv"
        agreement_path = temp_dir / "HUMAN_AUDIT_AGREEMENT_SUMMARY.json"
        second_template_path = temp_dir / "SECOND_HUMAN_BLINDED_REVIEW_TEMPLATE.csv"
        linkage_path = temp_dir / "HUMAN_AUDIT_LINKAGE_COMPLETED_V2.csv"
        public_expansion_path = temp_dir / "EXPANSION_ACTIONS_PUBLIC.json"
        protected_expansion_path = temp_dir / "EXPANSION_PLAN_PROTECTED.json"
        write_csv(comparison_path, comparison_rows, COMPARISON_RESULT_FIELDS)
        write_csv(stratum_path, stratum_rows, STRATUM_FIELDS)
        write_csv(second_template_path, second_template, SECOND_HUMAN_REVIEW_FIELDS)
        write_csv(linkage_path, linkage_rows, HUMAN_AUDIT_LINK_FIELDS)
        agreement_path.write_text(
            json.dumps(agreement, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        public_expansion_path.write_text(
            json.dumps(public_expansion, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        protected_expansion_path.write_text(
            json.dumps(protected_expansion, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        outputs = {
            "protected_comparison": file_entry(comparison_path, temp_dir, "joined_human_model_results"),
            "stratum_results": file_entry(stratum_path, temp_dir, "stratum_specific_exact_interval_results"),
            "agreement_summary": file_entry(agreement_path, temp_dir, "human_model_agreement_summary"),
            "second_human_blinded_template": file_entry(second_template_path, temp_dir, "blinded_second_human_review_template"),
            "completed_v2_human_linkage": file_entry(linkage_path, temp_dir, "candidate_order_human_audit_linkage"),
            "public_expansion_actions": file_entry(public_expansion_path, temp_dir, "prespecified_expansion_actions_without_paper_ids"),
            "protected_expansion_plan": file_entry(protected_expansion_path, temp_dir, "deterministic_expansion_paper_ids"),
        }
        status = (
            "complete_pending_required_second_human_reviews"
            if flagged_ids and not second_human_review
            else "complete_pending_human_human_adjudication"
            if any(row["requires_human_human_adjudication"] == "true" for row in comparison_rows)
            else "complete_with_prespecified_expansion_actions_evaluated"
        )
        manifest = {
            "schema_version": "fresh-prospective-human-audit-finalization-v2.0",
            "pipeline": "fresh_v2_prospective_human_audit_finalization",
            "generated_at_utc": completed_utc,
            "status": status,
            "counts": {
                "human_responses_validated": len(first_rows),
                "candidate_frame_records": len(candidate_rows),
                "boundary_records": len(comparison_rows) - len(candidate_rows),
                "second_human_reviews_required": len(flagged_ids),
                "second_human_reviews_completed": len(effective_second),
                "confirmed_model_status_errors": sum(row["confirmed_model_status_error"] == "true" for row in comparison_rows),
                "human_human_adjudications_required": sum(row["requires_human_human_adjudication"] == "true" for row in comparison_rows),
            },
            "inputs": {
                "audit_package_manifest": {
                    "path": str((package_dir.resolve() / "HUMAN_AUDIT_PACKAGE_MANIFEST.json")),
                    "sha256": sha256_file(package_dir.resolve() / "HUMAN_AUDIT_PACKAGE_MANIFEST.json"),
                },
                "completed_first_human_review": {
                    "path": str(completed_review.resolve()),
                    "sha256": completed_sha,
                },
                "completed_second_human_review": (
                    {"path": str(second_human_review.resolve()), "sha256": second_sha}
                    if second_human_review
                    else None
                ),
            },
            "contracts": {
                "all_100_first_human_responses_validated": True,
                "first_human_file_hashed_before_label_join": True,
                "second_human_template_hides_first_human_and_model_decisions": True,
                "exact_binomial_intervals": "two-sided Clopper-Pearson 95%",
                "zero_errors_interpreted_as_proof_of_sensitivity": False,
                "unweighted_100_record_error_rate_reported_as_corpus_rate": False,
                "expansion_rules_evaluated_prospectively": True,
            },
            "outputs": outputs,
            "script": {"filename": Path(__file__).name, "sha256": sha256_file(Path(__file__))},
        }
        manifest_path = temp_dir / "HUMAN_AUDIT_FINALIZATION_MANIFEST.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        hash_rows = []
        for path, role in (
            (comparison_path, "joined_human_model_results"),
            (stratum_path, "stratum_specific_exact_interval_results"),
            (agreement_path, "human_model_agreement_summary"),
            (second_template_path, "blinded_second_human_review_template"),
            (linkage_path, "candidate_order_human_audit_linkage"),
            (public_expansion_path, "prespecified_expansion_actions_without_paper_ids"),
            (protected_expansion_path, "deterministic_expansion_paper_ids"),
            (manifest_path, "human_audit_finalization_manifest"),
        ):
            hash_rows.append(
                {
                    "scope": "output",
                    "path": path.relative_to(temp_dir).as_posix(),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        write_csv(
            temp_dir / "HUMAN_AUDIT_FINALIZATION_HASH_MANIFEST.csv",
            hash_rows,
            ["scope", "path", "role", "bytes", "sha256"],
        )
        temp_dir.rename(output_dir)
        return manifest
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", required=True, type=Path)
    parser.add_argument("--completed-review", required=True, type=Path)
    parser.add_argument("--second-human-review", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = finalize_human_audit(
            args.package_dir,
            args.completed_review,
            args.output_dir,
            second_human_review=args.second_human_review,
        )
    except FreshReviewError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
