#!/usr/bin/env python3
"""Finalize fresh V2 record-level screening after complete logged resolution.

The script never treats a suspected publication version as an eligibility
exclusion.  It emits a separate post-eligibility relationship queue and stops
at record-level finalization; canonical scholarly works are chosen later.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from compare_fresh_independent_reviews_v2 import (
    ADJUDICATION_DECISION_FIELDS,
    COMPARISON_FIELDS,
    HUMAN_AUDIT_LINK_FIELDS,
)
from fresh_screening_review_common_v2 import (
    CRITERION_FIELDS,
    DEFAULT_CODEBOOK,
    EXCLUSION_CODES,
    MASTER_FIELDS,
    REVIEW_FIELDS,
    RETIRED_CODES,
    UNCERTAIN_CODES,
    VALID_CONFIDENCE,
    VALID_DECISIONS,
    FreshReviewError,
    bool_text,
    canonical_json,
    classify_pair,
    file_entry,
    read_csv,
    safe_relative,
    sha256_file,
    sha256_text,
    stable_audit_link_id,
    validate_candidate_package,
    validate_decision_logic,
    validate_file_entry,
    validate_review_output,
    validate_sha256,
    write_csv,
)


COMPARISON_META_FIELDS = [
    "comparison_class",
    "decision_agreement",
    "primary_code_agreement",
    "uncertain_present",
    "direct_include_exclude_disagreement",
    "criterion_disagreement_fields",
    "possible_version_of_disagreement",
    "requires_eligibility_adjudication",
    "requires_primary_code_resolution",
    "requires_adjudication",
    "requires_version_review",
]

FINAL_FIELDS = (
    MASTER_FIELDS
    + ["audit_link_id", "batch", "candidate_row_sha256"]
    + [f"reviewer_A_{field}" for field in REVIEW_FIELDS[1:]]
    + [f"reviewer_B_{field}" for field in REVIEW_FIELDS[1:]]
    + COMPARISON_META_FIELDS
    + [
        "human_audit_id",
        "human_decision",
        "human_primary_code",
        "human_confidence",
        "human_audit_source_sha256",
        "human_audit_completed_utc",
        "adjudication_applied",
        "resolution_source",
        "adjudication_confidence",
        "adjudication_date_eligible",
        "adjudication_language_assessable",
        "adjudication_llm_explicit",
        "adjudication_health_professions_education",
        "adjudication_simulation_central",
        "adjudication_eligible_document_type",
        "adjudication_rationale",
        "adjudication_evidence_locator_1",
        "adjudication_evidence_locator_2",
        "final_decision",
        "final_primary_code",
        "decision_basis",
        "possible_version_of_union",
    ]
)

POST_ELIGIBILITY_VERSION_FIELDS = [
    "relationship_id",
    "source_paper_id",
    "target_paper_id",
    "source_final_decision",
    "target_final_decision",
    "source_doi",
    "source_title",
    "target_doi",
    "target_title",
    "flagged_by",
    "relationship_decision",
    "canonical_work_id",
    "relationship_rationale",
    "evidence_locator_1",
    "evidence_locator_2",
]

VALID_RESOLUTION_SOURCES = {
    "independent_adjudication",
    "human_audit_informed_adjudication",
}

FINALIZED_WITH_HUMAN_AUDIT_STATUS = (
    "record_level_screening_finalized_pending_systematic_version_review"
)
FINALIZED_WITH_HUMAN_AUDIT_DEFERRED_STATUS = (
    "record_level_screening_finalized_human_audit_deferred_"
    "pending_systematic_version_review"
)
PROVISIONAL_PENDING_HUMAN_AUDIT_STATUS = (
    "provisional_record_level_decisions_pending_prospective_human_audit"
)
HUMAN_AUDIT_DEFERRAL_SCHEMA = "fresh-human-audit-deferral-v2.0"
HUMAN_AUDIT_DEFERRAL_DECISION = "deferred_by_corresponding_author"
HUMAN_AUDIT_DEFERRAL_OUTPUT = "HUMAN_AUDIT_DEFERRAL_USED_V2.json"
REQUIRED_PROHIBITED_CLAIMS = {
    "human_interrater_reliability",
    "human_validated_screening",
    "measured_screening_sensitivity",
    "measured_screening_specificity",
    "zero_screening_errors",
    "proof_of_complete_recall",
}
REQUIRED_DEFERRAL_DISCLOSURES = {
    "Agreement measures consistency between two model reviews, not agreement between human reviewers.",
    "No prospective independent human screening sample was completed.",
    "Shared or correlated model errors may remain even when both reviews agree.",
    "Every disagreement or uncertain model decision was separately adjudicated under the same written eligibility rules.",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_human_audit_deferral(path: Path) -> tuple[dict[str, Any], Path, Path]:
    """Validate an explicit author decision to proceed without a human audit.

    This is a reporting limitation, not a substitute human review.  The
    machine-readable record must bind the accompanying human-readable note and
    must forbid every claim that the omitted audit would otherwise support.
    """

    resolved = path.resolve()
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FreshReviewError(f"Missing human-audit deferral record: {resolved}") from exc
    except json.JSONDecodeError as exc:
        raise FreshReviewError(f"Invalid human-audit deferral JSON: {resolved}") from exc
    if not isinstance(raw, dict):
        raise FreshReviewError("Human-audit deferral record must be a JSON object")
    expected_keys = {
        "schema_version",
        "decision",
        "decision_date",
        "fresh_search_end_date_inclusive",
        "human_audit_completed",
        "human_reference_standard_available",
        "model_review_design",
        "prohibited_claims",
        "required_disclosures",
        "source_note",
        "source_note_sha256",
    }
    if set(raw) != expected_keys:
        raise FreshReviewError("Human-audit deferral record has an unexpected schema")
    if raw["schema_version"] != HUMAN_AUDIT_DEFERRAL_SCHEMA:
        raise FreshReviewError("Unsupported human-audit deferral schema")
    if raw["decision"] != HUMAN_AUDIT_DEFERRAL_DECISION:
        raise FreshReviewError("Human-audit deferral decision is not author-approved")
    if raw["human_audit_completed"] is not False:
        raise FreshReviewError("Deferral record must state human_audit_completed=false")
    if raw["human_reference_standard_available"] is not False:
        raise FreshReviewError(
            "Deferral record must state human_reference_standard_available=false"
        )
    if raw["model_review_design"] != (
        "two_independent_model_reviews_plus_separate_adjudication_of_every_"
        "disagreement_or_uncertain_decision"
    ):
        raise FreshReviewError("Human-audit deferral model-review design changed")
    try:
        decision_date = datetime.fromisoformat(str(raw["decision_date"]))
        search_end = datetime.fromisoformat(str(raw["fresh_search_end_date_inclusive"]))
    except ValueError as exc:
        raise FreshReviewError("Human-audit deferral dates must use ISO format") from exc
    if decision_date.date() < search_end.date():
        raise FreshReviewError("Human-audit deferral predates the fresh search end date")
    prohibited = raw["prohibited_claims"]
    disclosures = raw["required_disclosures"]
    if not isinstance(prohibited, list) or set(prohibited) != REQUIRED_PROHIBITED_CLAIMS:
        raise FreshReviewError("Human-audit deferral prohibited-claims contract changed")
    if not isinstance(disclosures, list) or set(disclosures) != REQUIRED_DEFERRAL_DISCLOSURES:
        raise FreshReviewError("Human-audit deferral disclosure contract changed")
    if not all(isinstance(value, str) and value == value.strip() for value in prohibited):
        raise FreshReviewError("Human-audit deferral has malformed prohibited claims")
    if not all(isinstance(value, str) and value == value.strip() for value in disclosures):
        raise FreshReviewError("Human-audit deferral has malformed disclosures")
    source_note_name = str(raw["source_note"])
    if not source_note_name or Path(source_note_name).name != source_note_name:
        raise FreshReviewError("Human-audit deferral source_note must be a sibling filename")
    source_note = resolved.with_name(source_note_name)
    if not source_note.is_file():
        raise FreshReviewError(f"Human-audit deferral source note is missing: {source_note}")
    expected_note_sha = str(raw["source_note_sha256"]).casefold()
    if not validate_sha256(expected_note_sha) or sha256_file(source_note) != expected_note_sha:
        raise FreshReviewError("Human-audit deferral source-note hash mismatch")
    return raw, resolved, source_note


def _validate_comparison_hash_ledger(root: Path) -> None:
    path = root / "REVIEW_COMPARISON_HASH_MANIFEST_V2.csv"
    fields, rows = read_csv(path)
    if fields != ["scope", "path", "role", "bytes", "sha256"]:
        raise FreshReviewError(f"{path}: unexpected hash-ledger schema")
    for row in rows:
        if row["scope"] != "output":
            continue
        target = safe_relative(root, row["path"], label="comparison output ledger")
        if not target.is_file():
            raise FreshReviewError(f"Comparison output ledger target is missing: {target}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise FreshReviewError(f"{path}: invalid byte count for {row['path']}") from exc
        if target.stat().st_size != expected_bytes or sha256_file(target) != row["sha256"]:
            raise FreshReviewError(f"Comparison output hash-ledger mismatch: {target}")


def _load_and_validate_comparison(
    comparison_dir: Path,
    package: Any,
) -> tuple[Mapping[str, Any], list[dict[str, str]], Path]:
    root = comparison_dir.resolve()
    if not root.is_dir():
        raise FreshReviewError(f"Comparison directory does not exist: {root}")
    manifest_path = root / "REVIEW_COMPARISON_MANIFEST_V2.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FreshReviewError(f"Missing comparison manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise FreshReviewError(f"Invalid comparison manifest: {manifest_path}") from exc
    if manifest.get("pipeline") != "fresh_v2_independent_review_comparison":
        raise FreshReviewError("Comparison package is not the fresh V2 comparator output")
    candidate = manifest.get("candidate_package") or {}
    required_matches = {
        "candidate_build_manifest_sha256": package.candidate_manifest_sha256,
        "candidate_master_sha256": package.master_sha256,
        "batch_manifest_sha256": package.batch_manifest_sha256,
        "review_schema_sha256": package.schema_sha256,
        "codebook_sha256": package.codebook_sha256,
    }
    for field, expected in required_matches.items():
        if str(candidate.get(field) or "").casefold() != expected:
            raise FreshReviewError(
                f"Comparison/candidate binding mismatch for {field}: regenerate comparison"
            )
    outputs = manifest.get("outputs") or {}
    comparison_path = validate_file_entry(
        root, outputs.get("comparison") or {}, label="V2 review comparison"
    )
    for key, label in (
        ("adjudication_input", "adjudication input"),
        ("adjudication_decisions_template", "adjudication template"),
        ("human_audit_linkage_template", "human-audit linkage template"),
        ("version_relationship_review_input", "version-review input"),
        ("agreement_summary", "agreement summary"),
    ):
        validate_file_entry(root, outputs.get(key) or {}, label=label)
    _validate_comparison_hash_ledger(root)

    review_files: dict[tuple[str, int], Path] = {}
    for entry in manifest.get("review_inputs") or []:
        reviewer = str(entry.get("reviewer") or "")
        try:
            batch = int(entry.get("batch"))
            expected_bytes = int(entry.get("bytes"))
        except (TypeError, ValueError) as exc:
            raise FreshReviewError("Comparison manifest has malformed review input") from exc
        if reviewer not in {"A", "B"} or (reviewer, batch) in review_files:
            raise FreshReviewError("Comparison manifest has duplicate/invalid reviewer input")
        raw_path = Path(str(entry.get("path") or ""))
        path = (
            raw_path.resolve()
            if raw_path.is_absolute()
            else safe_relative(root, raw_path.as_posix(), label="locked reviewer input")
        )
        if not path.is_file():
            raise FreshReviewError(f"Completed reviewer input is no longer available: {path}")
        if (
            path.stat().st_size != expected_bytes
            or sha256_file(path) != str(entry.get("sha256") or "").casefold()
        ):
            raise FreshReviewError(f"Completed reviewer input changed after comparison: {path}")
        review_files[(reviewer, batch)] = path
    expected_review_keys = {
        (reviewer, batch.number)
        for reviewer in ("A", "B")
        for batch in package.batches
    }
    if set(review_files) != expected_review_keys:
        raise FreshReviewError("Comparison manifest does not bind both complete review sets")

    reviews: dict[tuple[str, str], Mapping[str, str]] = {}
    for batch in package.batches:
        for reviewer in ("A", "B"):
            rows = validate_review_output(
                review_files[(reviewer, batch.number)],
                batch.ids,
                set(package.candidate_ids),
            )
            reviews.update({(reviewer, row["paper_id"]): row for row in rows})

    fields, rows = read_csv(comparison_path)
    if fields != COMPARISON_FIELDS:
        raise FreshReviewError(f"{comparison_path}: unexpected comparison schema/order")
    if [row["paper_id"] for row in rows] != list(package.candidate_ids):
        raise FreshReviewError(f"{comparison_path}: candidate ID/order mismatch")
    for row in rows:
        paper_id = row["paper_id"]
        if None in row or any(value is None for value in row.values()):
            raise FreshReviewError(f"{path}: malformed human-audit linkage row")
        if any(value != value.strip() for value in row.values()):
            raise FreshReviewError(
                f"{path}: leading/trailing whitespace in human-audit row for {paper_id}"
            )
        a = reviews[("A", paper_id)]
        b = reviews[("B", paper_id)]
        if row["audit_link_id"] != stable_audit_link_id(package.master_sha256, paper_id):
            raise FreshReviewError(f"{comparison_path}: invalid audit link for {paper_id}")
        expected_row_sha = sha256_text(canonical_json(dict(package.master_by_id[paper_id])))
        if row["candidate_row_sha256"] != expected_row_sha:
            raise FreshReviewError(f"{comparison_path}: candidate row hash mismatch for {paper_id}")
        if int(row["batch"]) != package.batch_by_id[paper_id]:
            raise FreshReviewError(f"{comparison_path}: batch mismatch for {paper_id}")
        for reviewer, source in (("A", a), ("B", b)):
            for field in REVIEW_FIELDS[1:]:
                if row[f"reviewer_{reviewer}_{field}"] != source[field]:
                    raise FreshReviewError(
                        f"{comparison_path}: reviewer {reviewer} value mismatch for "
                        f"{paper_id}/{field}"
                    )
        uncertain = "UNCERTAIN" in {a["decision"], b["decision"]}
        direct = {a["decision"], b["decision"]} == {"INCLUDE", "EXCLUDE"}
        eligibility = a["decision"] != b["decision"] or uncertain
        code_resolution = (
            a["decision"] == b["decision"] == "EXCLUDE"
            and a["primary_code"] != b["primary_code"]
        )
        expected_values = {
            "comparison_class": classify_pair(a, b),
            "decision_agreement": bool_text(a["decision"] == b["decision"]),
            "primary_code_agreement": bool_text(a["primary_code"] == b["primary_code"]),
            "uncertain_present": bool_text(uncertain),
            "direct_include_exclude_disagreement": bool_text(direct),
            "criterion_disagreement_fields": ";".join(
                field for field in CRITERION_FIELDS if a[field] != b[field]
            ),
            "possible_version_of_disagreement": bool_text(
                a["possible_version_of"] != b["possible_version_of"]
            ),
            "requires_eligibility_adjudication": bool_text(eligibility),
            "requires_primary_code_resolution": bool_text(code_resolution),
            "requires_adjudication": bool_text(eligibility or code_resolution),
            "requires_version_review": bool_text(
                bool(a["possible_version_of"] or b["possible_version_of"])
            ),
        }
        for field, expected in expected_values.items():
            if row[field] != expected:
                raise FreshReviewError(
                    f"{comparison_path}: derived comparison mismatch for {paper_id}/{field}"
                )
    return manifest, rows, manifest_path


def _blank_human_links(package: Any) -> dict[str, dict[str, str]]:
    return {
        paper_id: {
            "audit_link_id": stable_audit_link_id(package.master_sha256, paper_id),
            "paper_id": paper_id,
            "batch": str(package.batch_by_id[paper_id]),
            "candidate_row_sha256": sha256_text(
                canonical_json(dict(package.master_by_id[paper_id]))
            ),
            "human_audit_id": "",
            "human_decision": "",
            "human_primary_code": "",
            "human_confidence": "",
            "human_audit_source_sha256": "",
            "human_audit_completed_utc": "",
        }
        for paper_id in package.candidate_ids
    }


def _load_human_links(path: Path | None, package: Any) -> dict[str, dict[str, str]]:
    if path is None:
        return _blank_human_links(package)
    fields, rows = read_csv(path.resolve())
    if fields != HUMAN_AUDIT_LINK_FIELDS:
        raise FreshReviewError(f"{path}: unexpected human-audit linkage schema/order")
    if [row["paper_id"] for row in rows] != list(package.candidate_ids):
        raise FreshReviewError(f"{path}: human-audit linkage must retain all candidate rows/order")
    seen_audit_ids: set[str] = set()
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        paper_id = row["paper_id"]
        if None in row or any(value is None for value in row.values()):
            raise FreshReviewError(f"{path}: malformed adjudication row")
        if any(value != value.strip() for value in row.values()):
            raise FreshReviewError(
                f"{path}: leading/trailing whitespace in adjudication for {paper_id}"
            )
        expected_audit_link = stable_audit_link_id(package.master_sha256, paper_id)
        expected_row_sha = sha256_text(canonical_json(dict(package.master_by_id[paper_id])))
        if (
            row["audit_link_id"] != expected_audit_link
            or row["batch"] != str(package.batch_by_id[paper_id])
            or row["candidate_row_sha256"] != expected_row_sha
        ):
            raise FreshReviewError(f"{path}: immutable linkage fields changed for {paper_id}")
        human_fields = HUMAN_AUDIT_LINK_FIELDS[4:]
        populated = [bool(row[field]) for field in human_fields]
        if any(populated) and not all(populated):
            raise FreshReviewError(f"{path}: incomplete human-audit linkage for {paper_id}")
        if all(populated):
            if row["human_audit_id"] in seen_audit_ids:
                raise FreshReviewError(f"{path}: duplicate human_audit_id")
            seen_audit_ids.add(row["human_audit_id"])
            decision = row["human_decision"]
            code = row["human_primary_code"]
            if decision not in VALID_DECISIONS:
                raise FreshReviewError(f"{path}: invalid human decision for {paper_id}")
            valid_codes = (
                {"INCLUDE"}
                if decision == "INCLUDE"
                else EXCLUSION_CODES
                if decision == "EXCLUDE"
                else UNCERTAIN_CODES
            )
            if code not in valid_codes or code in RETIRED_CODES or code.startswith("E8"):
                raise FreshReviewError(f"{path}: human decision/code mismatch for {paper_id}")
            if row["human_confidence"] not in VALID_CONFIDENCE:
                raise FreshReviewError(f"{path}: invalid human confidence for {paper_id}")
            if not validate_sha256(row["human_audit_source_sha256"]):
                raise FreshReviewError(f"{path}: invalid human source hash for {paper_id}")
            try:
                datetime.fromisoformat(row["human_audit_completed_utc"].replace("Z", "+00:00"))
            except ValueError as exc:
                raise FreshReviewError(
                    f"{path}: invalid human audit completion time for {paper_id}"
                ) from exc
        output[paper_id] = row
    return output


def _human_model_discrepancy(
    comparison: Mapping[str, str], human: Mapping[str, str]
) -> bool:
    if not human["human_audit_id"]:
        return False
    if comparison["requires_adjudication"] == "true":
        return False
    if human["human_decision"] == "UNCERTAIN":
        return True
    model_decision = comparison["reviewer_A_decision"]
    if human["human_decision"] != model_decision:
        return True
    return (
        model_decision == "EXCLUDE"
        and human["human_primary_code"] != comparison["reviewer_A_primary_code"]
    )


def _load_adjudications(
    path: Path | None,
    package: Any,
    comparison_by_id: Mapping[str, Mapping[str, str]],
    human_by_id: Mapping[str, Mapping[str, str]],
) -> dict[str, dict[str, str]]:
    required_ids = {
        paper_id
        for paper_id, row in comparison_by_id.items()
        if row["requires_adjudication"] == "true"
        or _human_model_discrepancy(row, human_by_id[paper_id])
    }
    if path is None:
        if required_ids:
            raise FreshReviewError(
                f"{len(required_ids)} records require adjudication; no decision file supplied"
            )
        return {}
    fields, rows = read_csv(path.resolve())
    if fields != ADJUDICATION_DECISION_FIELDS:
        raise FreshReviewError(f"{path}: unexpected adjudication schema/order")
    ids = [row["paper_id"] for row in rows]
    if len(ids) != len(set(ids)) or any(value not in package.master_by_id for value in ids):
        raise FreshReviewError(f"{path}: duplicate or unknown adjudication paper_id")
    candidate_position = {paper_id: index for index, paper_id in enumerate(package.candidate_ids)}
    if ids != sorted(ids, key=candidate_position.__getitem__):
        raise FreshReviewError(f"{path}: adjudication rows are not in candidate order")
    if not required_ids <= set(ids):
        missing = sorted(required_ids - set(ids), key=candidate_position.__getitem__)
        raise FreshReviewError(
            f"{path}: {len(missing)} required adjudications missing; first: {missing[:5]}"
        )
    decisions: dict[str, dict[str, str]] = {}
    for row in rows:
        paper_id = row["paper_id"]
        comparison = comparison_by_id[paper_id]
        human = human_by_id[paper_id]
        base_required = comparison["requires_adjudication"] == "true"
        if not base_required and not human["human_audit_id"]:
            raise FreshReviewError(
                f"{path}: {paper_id} is an unreviewed model-agreement row and cannot be overridden"
            )
        if row["audit_link_id"] != comparison["audit_link_id"]:
            raise FreshReviewError(f"{path}: audit link mismatch for {paper_id}")
        if row["resolution_source"] not in VALID_RESOLUTION_SOURCES:
            raise FreshReviewError(f"{path}: invalid resolution source for {paper_id}")
        if row["confidence"] not in VALID_CONFIDENCE:
            raise FreshReviewError(f"{path}: invalid adjudication confidence for {paper_id}")
        logical_row = {
            "decision": row["decision"],
            "primary_code": row["primary_code"],
            **{field: row[field] for field in CRITERION_FIELDS},
            "possible_version_of": "",
        }
        validate_decision_logic(
            logical_row, path=path.resolve(), paper_id=paper_id, allow_uncertain=False
        )
        if not row["adjudication_rationale"] or not row["evidence_locator_1"]:
            raise FreshReviewError(f"{path}: incomplete rationale/evidence for {paper_id}")
        if row["resolution_source"] == "human_audit_informed_adjudication":
            if (
                not human["human_audit_id"]
                or row["human_audit_id"] != human["human_audit_id"]
            ):
                raise FreshReviewError(
                    f"{path}: human-informed resolution is not linked for {paper_id}"
                )
        elif row["human_audit_id"]:
            raise FreshReviewError(
                f"{path}: independent adjudication must leave human_audit_id blank for {paper_id}"
            )
        decisions[paper_id] = row
    return decisions


def _version_targets(comparison: Mapping[str, str]) -> list[str]:
    targets = {
        comparison[field]
        for field in (
            "reviewer_A_possible_version_of",
            "reviewer_B_possible_version_of",
        )
        if comparison[field]
    }
    return sorted(targets)


def finalize_screening(
    candidate_dir: Path,
    comparison_dir: Path,
    output_dir: Path,
    *,
    adjudications: Path | None = None,
    human_audit_linkage: Path | None = None,
    human_audit_deferral: Path | None = None,
    codebook: Path = DEFAULT_CODEBOOK,
) -> Mapping[str, Any]:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FreshReviewError(f"Output directory already exists: {output_dir}")
    package = validate_candidate_package(candidate_dir, codebook=codebook)
    comparison_manifest, comparison_rows, comparison_manifest_path = (
        _load_and_validate_comparison(comparison_dir, package)
    )
    if human_audit_linkage is not None and human_audit_deferral is not None:
        raise FreshReviewError(
            "Use either a completed human-audit linkage or an explicit deferral record, "
            "not both"
        )
    deferral_record: dict[str, Any] | None = None
    deferral_source_path: Path | None = None
    deferral_note_path: Path | None = None
    if human_audit_deferral is not None:
        deferral_record, deferral_source_path, deferral_note_path = (
            load_human_audit_deferral(human_audit_deferral)
        )
    comparison_by_id = {row["paper_id"]: row for row in comparison_rows}
    human_by_id = _load_human_links(human_audit_linkage, package)
    adjudication_by_id = _load_adjudications(
        adjudications, package, comparison_by_id, human_by_id
    )

    final_rows: list[dict[str, Any]] = []
    for paper_id in package.candidate_ids:
        source = package.master_by_id[paper_id]
        comparison = comparison_by_id[paper_id]
        human = human_by_id[paper_id]
        adjudication = adjudication_by_id.get(paper_id)
        output: dict[str, Any] = dict(source)
        output.update(
            {
                "audit_link_id": comparison["audit_link_id"],
                "batch": comparison["batch"],
                "candidate_row_sha256": comparison["candidate_row_sha256"],
            }
        )
        for reviewer in ("A", "B"):
            for field in REVIEW_FIELDS[1:]:
                output[f"reviewer_{reviewer}_{field}"] = comparison[
                    f"reviewer_{reviewer}_{field}"
                ]
        output.update({field: comparison[field] for field in COMPARISON_META_FIELDS})
        output.update({field: human[field] for field in HUMAN_AUDIT_LINK_FIELDS[4:]})
        if adjudication:
            output.update(
                {
                    "adjudication_applied": "true",
                    "resolution_source": adjudication["resolution_source"],
                    "adjudication_confidence": adjudication["confidence"],
                    **{
                        f"adjudication_{field}": adjudication[field]
                        for field in CRITERION_FIELDS
                    },
                    "adjudication_rationale": adjudication["adjudication_rationale"],
                    "adjudication_evidence_locator_1": adjudication[
                        "evidence_locator_1"
                    ],
                    "adjudication_evidence_locator_2": adjudication[
                        "evidence_locator_2"
                    ],
                    "final_decision": adjudication["decision"],
                    "final_primary_code": adjudication["primary_code"],
                    "decision_basis": adjudication["resolution_source"],
                }
            )
        else:
            output.update(
                {
                    "adjudication_applied": "false",
                    "resolution_source": "",
                    "adjudication_confidence": "",
                    **{f"adjudication_{field}": "" for field in CRITERION_FIELDS},
                    "adjudication_rationale": "",
                    "adjudication_evidence_locator_1": "",
                    "adjudication_evidence_locator_2": "",
                    "final_decision": comparison["reviewer_A_decision"],
                    "final_primary_code": comparison["reviewer_A_primary_code"],
                    "decision_basis": "independent_model_agreement",
                }
            )
        output["possible_version_of_union"] = ";".join(_version_targets(comparison))
        final_rows.append(output)

    final_by_id = {row["paper_id"]: row for row in final_rows}
    version_edges: dict[tuple[str, str], dict[str, Any]] = {}
    for row in final_rows:
        if row["final_decision"] != "INCLUDE":
            continue
        source_id = row["paper_id"]
        comparison = comparison_by_id[source_id]
        for target_id in _version_targets(comparison):
            pair = tuple(sorted((source_id, target_id)))
            flags = []
            if comparison["reviewer_A_possible_version_of"] == target_id:
                flags.append(f"reviewer_A:{source_id}")
            if comparison["reviewer_B_possible_version_of"] == target_id:
                flags.append(f"reviewer_B:{source_id}")
            target = final_by_id[target_id]
            existing = version_edges.get(pair)
            if existing:
                existing_flags = set(existing["flagged_by"].split(";")) | set(flags)
                existing["flagged_by"] = ";".join(sorted(existing_flags))
                continue
            relationship_id = f"VR2-{sha256_text(chr(0).join(pair))[:24]}"
            version_edges[pair] = {
                "relationship_id": relationship_id,
                "source_paper_id": source_id,
                "target_paper_id": target_id,
                "source_final_decision": row["final_decision"],
                "target_final_decision": target["final_decision"],
                "source_doi": row["doi"],
                "source_title": row["title"],
                "target_doi": target["doi"],
                "target_title": target["title"],
                "flagged_by": ";".join(sorted(flags)),
                "relationship_decision": "",
                "canonical_work_id": "",
                "relationship_rationale": "",
                "evidence_locator_1": "",
                "evidence_locator_2": "",
            }
    version_rows = [version_edges[key] for key in sorted(version_edges)]
    included_rows = [row for row in final_rows if row["final_decision"] == "INCLUDE"]
    audited_count = sum(bool(row["human_audit_id"]) for row in human_by_id.values())
    # Reviewer flags are only leads.  The codebook requires a systematic
    # publication-version pass across all eligible records even if neither
    # model happened to flag a relationship, so this finalizer never claims
    # that the canonical-work analysis unit is ready.
    status = (
        FINALIZED_WITH_HUMAN_AUDIT_STATUS
        if audited_count
        else FINALIZED_WITH_HUMAN_AUDIT_DEFERRED_STATUS
        if deferral_record is not None
        else PROVISIONAL_PENDING_HUMAN_AUDIT_STATUS
    )
    summary = {
        "schema_version": "fresh-screening-finalization-summary-v2.0",
        "generated_at_utc": utc_now(),
        "status": status,
        "records": len(final_rows),
        "final_decision_counts": dict(
            sorted(Counter(row["final_decision"] for row in final_rows).items())
        ),
        "final_exclusion_code_counts": dict(
            sorted(
                Counter(
                    row["final_primary_code"]
                    for row in final_rows
                    if row["final_decision"] == "EXCLUDE"
                ).items()
            )
        ),
        "adjudicated_records": len(adjudication_by_id),
        "human_audited_records_linked": audited_count,
        "post_eligibility_version_relationships_pending": len(version_rows),
        "unit_note": (
            "These are final record-level screening decisions. Canonical unique works "
            "must not be counted until the separate publication-version review is complete."
        ),
        "human_audit_note": (
            "A completed human-audit linkage is present; separate audit-protocol QA "
            "must still verify the planned strata, blinding and expansion rules."
            if audited_count
            else "The corresponding author explicitly deferred the prospective human "
            "audit. These decisions therefore reflect two independent model reviews "
            "plus separate adjudication, not validation against a human reference standard."
            if deferral_record is not None
            else "No completed prospective human audit is linked, so these decisions "
            "are provisional and must not be reported as the final screened corpus."
        ),
        "human_audit_deferred_by_author": deferral_record is not None,
        "human_reference_standard_available": False,
    }

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.building-", dir=output_dir.parent)
    )
    try:
        final_path = temp_dir / "FINAL_RECORD_LEVEL_SCREENING_V2.csv"
        included_path = temp_dir / "FINAL_INCLUDED_RECORDS_V2.csv"
        version_path = temp_dir / "POST_ELIGIBILITY_VERSION_REVIEW_QUEUE_V2.csv"
        human_path = temp_dir / "HUMAN_AUDIT_LINKAGE_USED_V2.csv"
        deferral_copy_path = (
            temp_dir / HUMAN_AUDIT_DEFERRAL_OUTPUT
            if deferral_record is not None
            else None
        )
        deferral_note_copy_path = (
            temp_dir / deferral_note_path.name
            if deferral_note_path is not None
            else None
        )
        summary_path = temp_dir / "SCREENING_FINALIZATION_SUMMARY_V2.json"
        write_csv(final_path, final_rows, FINAL_FIELDS)
        write_csv(included_path, included_rows, FINAL_FIELDS)
        write_csv(version_path, version_rows, POST_ELIGIBILITY_VERSION_FIELDS)
        write_csv(
            human_path,
            [human_by_id[paper_id] for paper_id in package.candidate_ids],
            HUMAN_AUDIT_LINK_FIELDS,
        )
        if deferral_copy_path is not None:
            deferral_copy_path.write_text(
                json.dumps(deferral_record, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            if deferral_note_copy_path is None or deferral_note_path is None:
                raise AssertionError("Validated deferral note path was lost")
            shutil.copyfile(deferral_note_path, deferral_note_copy_path)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        outputs = {
            "final_record_level_screening": file_entry(
                final_path, temp_dir, "final_record_level_decisions"
            ),
            "final_included_records": file_entry(
                included_path, temp_dir, "included_record_versions"
            ),
            "post_eligibility_version_review_queue": file_entry(
                version_path, temp_dir, "unresolved_version_relationships"
            ),
            "human_audit_linkage_used": file_entry(
                human_path, temp_dir, "human_audit_linkage_audit_trail"
            ),
            "human_audit_deferral_used": (
                file_entry(
                    deferral_copy_path,
                    temp_dir,
                    "explicit_author_human_audit_deferral",
                )
                if deferral_copy_path is not None
                else None
            ),
            "human_audit_deferral_source_note_used": (
                file_entry(
                    deferral_note_copy_path,
                    temp_dir,
                    "human_readable_author_human_audit_deferral",
                )
                if deferral_note_copy_path is not None
                else None
            ),
            "summary": file_entry(summary_path, temp_dir, "finalization_summary"),
        }
        input_files = {
            "candidate_build_manifest": {
                "path": str(package.candidate_manifest_path),
                "sha256": package.candidate_manifest_sha256,
            },
            "candidate_master": {
                "path": str(package.master_path),
                "sha256": package.master_sha256,
            },
            "comparison_manifest": {
                "path": str(comparison_manifest_path),
                "sha256": sha256_file(comparison_manifest_path),
            },
            "adjudications": (
                {
                    "path": str(adjudications.resolve()),
                    "sha256": sha256_file(adjudications.resolve()),
                }
                if adjudications
                else None
            ),
            "human_audit_linkage": (
                {
                    "path": str(human_audit_linkage.resolve()),
                    "sha256": sha256_file(human_audit_linkage.resolve()),
                }
                if human_audit_linkage
                else None
            ),
            "human_audit_deferral": (
                {
                    "path": str(deferral_source_path),
                    "sha256": sha256_file(deferral_source_path),
                }
                if deferral_source_path is not None
                else None
            ),
            "human_audit_deferral_source_note": (
                {
                    "path": str(deferral_note_path),
                    "sha256": sha256_file(deferral_note_path),
                }
                if deferral_note_path is not None
                else None
            ),
            "codebook": {
                "path": str(package.codebook_path),
                "sha256": package.codebook_sha256,
            },
        }
        manifest = {
            "schema_version": "fresh-screening-finalization-manifest-v2.0",
            "generated_at_utc": utc_now(),
            "pipeline": "fresh_v2_record_level_screening_finalization",
            "status": status,
            "inputs": input_files,
            "counts": {
                "records": len(final_rows),
                "included_records": len(included_rows),
                "adjudicated_records": len(adjudication_by_id),
                "human_audited_records_linked": audited_count,
                "human_audit_deferred_by_author": int(deferral_record is not None),
                "pending_version_relationships": len(version_rows),
            },
            "contracts": {
                "all_model_disagreements_and_uncertain_rows_resolved": True,
                "agreed_exclusions_with_different_codes_resolved": True,
                "human_model_discrepancies_resolved_when_linked": True,
                "prospective_human_audit_linked": bool(audited_count),
                "prospective_human_audit_deferred_by_author": (
                    deferral_record is not None
                ),
                "human_reference_standard_available": False,
                "screening_sensitivity_or_specificity_claim_permitted": False,
                "model_agreement_may_be_reported_as_human_reliability": False,
                "human_audit_protocol_QA_performed_by_this_script": False,
                "retired_E8_allowed": False,
                "possible_version_of_used_as_exclusion": False,
                "automatic_version_collapse": False,
                "analysis_unit_ready": False,
                "systematic_version_review_still_required": True,
            },
            "outputs": outputs,
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "common_module_sha256": sha256_file(
                    Path(__file__).with_name("fresh_screening_review_common_v2.py")
                ),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp_dir / "SCREENING_FINALIZATION_MANIFEST_V2.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        hash_rows: list[dict[str, Any]] = []
        for name, entry in input_files.items():
            if entry:
                input_path = Path(entry["path"])
                hash_rows.append(
                    {
                        "scope": "input",
                        "path": entry["path"],
                        "role": name,
                        "bytes": input_path.stat().st_size,
                        "sha256": entry["sha256"],
                    }
                )
        for path, role in (
            (final_path, "final_record_level_decisions"),
            (included_path, "included_record_versions"),
            (version_path, "unresolved_version_relationships"),
            (human_path, "human_audit_linkage_audit_trail"),
            *((
                (deferral_copy_path, "explicit_author_human_audit_deferral"),
                (
                    deferral_note_copy_path,
                    "human_readable_author_human_audit_deferral",
                ),
            ) if deferral_copy_path is not None else ()),
            (summary_path, "finalization_summary"),
            (manifest_path, "finalization_manifest"),
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
        hash_rows.sort(key=lambda row: (row["scope"], row["path"], row["role"]))
        write_csv(
            temp_dir / "SCREENING_FINALIZATION_HASH_MANIFEST_V2.csv",
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
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--comparison-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--adjudications", type=Path)
    audit_group = parser.add_mutually_exclusive_group()
    audit_group.add_argument("--human-audit-linkage", type=Path)
    audit_group.add_argument("--human-audit-deferral", type=Path)
    parser.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = finalize_screening(
            args.candidate_dir,
            args.comparison_dir,
            args.output_dir,
            adjudications=args.adjudications,
            human_audit_linkage=args.human_audit_linkage,
            human_audit_deferral=args.human_audit_deferral,
            codebook=args.codebook,
        )
    except FreshReviewError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
