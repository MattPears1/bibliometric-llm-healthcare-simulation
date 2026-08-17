#!/usr/bin/env python3
"""Lock, compare, and route two complete fresh V2 independent review sets."""

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

from fresh_screening_review_common_v2 import (
    BLINDED_FIELDS,
    CRITERION_FIELDS,
    DEFAULT_CODEBOOK,
    REVIEW_FIELDS,
    FreshReviewError,
    bool_text,
    canonical_json,
    classify_pair,
    cohen_kappa,
    file_entry,
    sha256_file,
    sha256_text,
    stable_audit_link_id,
    validate_candidate_package,
    validate_review_output,
    write_csv,
)


COMPARISON_FIELDS = (
    ["audit_link_id", "paper_id", "batch", "candidate_row_sha256"]
    + [f"reviewer_A_{field}" for field in REVIEW_FIELDS[1:]]
    + [f"reviewer_B_{field}" for field in REVIEW_FIELDS[1:]]
    + [
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
)

ADJUDICATION_INPUT_FIELDS = (
    [
        "audit_link_id",
        "paper_id",
        "batch",
        "comparison_class",
        "requires_eligibility_adjudication",
        "requires_primary_code_resolution",
    ]
    + BLINDED_FIELDS[1:]
    + [f"reviewer_A_{field}" for field in REVIEW_FIELDS[1:]]
    + [f"reviewer_B_{field}" for field in REVIEW_FIELDS[1:]]
)

ADJUDICATION_DECISION_FIELDS = [
    "audit_link_id",
    "paper_id",
    "resolution_source",
    "decision",
    "primary_code",
    "confidence",
    "date_eligible",
    "language_assessable",
    "llm_explicit",
    "health_professions_education",
    "simulation_central",
    "eligible_document_type",
    "adjudication_rationale",
    "evidence_locator_1",
    "evidence_locator_2",
    "human_audit_id",
]

HUMAN_AUDIT_LINK_FIELDS = [
    "audit_link_id",
    "paper_id",
    "batch",
    "candidate_row_sha256",
    "human_audit_id",
    "human_decision",
    "human_primary_code",
    "human_confidence",
    "human_audit_source_sha256",
    "human_audit_completed_utc",
]

VERSION_REVIEW_FIELDS = [
    "audit_link_id",
    "paper_id",
    "batch",
    "doi",
    "title",
    "publication_date",
    "authors",
    "reviewer_A_decision",
    "reviewer_A_possible_version_of",
    "reviewer_B_decision",
    "reviewer_B_possible_version_of",
    "relationship_decision",
    "canonical_work_id",
    "relationship_rationale",
    "evidence_locator_1",
    "evidence_locator_2",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _review_file(reviewer_dir: Path, filename: str) -> Path:
    path = (reviewer_dir / filename).resolve()
    try:
        path.relative_to(reviewer_dir.resolve())
    except ValueError as exc:
        raise FreshReviewError(f"Unsafe reviewer output filename: {filename!r}") from exc
    return path


def compare_reviews(
    candidate_dir: Path,
    reviewer_a_dir: Path,
    reviewer_b_dir: Path,
    output_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
) -> Mapping[str, Any]:
    reviewer_a_dir = reviewer_a_dir.resolve()
    reviewer_b_dir = reviewer_b_dir.resolve()
    output_dir = output_dir.resolve()
    if reviewer_a_dir == reviewer_b_dir:
        raise FreshReviewError("Reviewer A and B must use distinct output directories")
    if output_dir.exists():
        raise FreshReviewError(f"Output directory already exists: {output_dir}")
    package = validate_candidate_package(candidate_dir, codebook=codebook)
    candidate_ids = set(package.candidate_ids)

    reviews_a: dict[str, dict[str, str]] = {}
    reviews_b: dict[str, dict[str, str]] = {}
    review_source_entries: list[dict[str, Any]] = []
    for batch in package.batches:
        path_a = _review_file(reviewer_a_dir, batch.review_filename)
        path_b = _review_file(reviewer_b_dir, batch.review_filename)
        rows_a = validate_review_output(path_a, batch.ids, candidate_ids)
        rows_b = validate_review_output(path_b, batch.ids, candidate_ids)
        reviews_a.update({row["paper_id"]: row for row in rows_a})
        reviews_b.update({row["paper_id"]: row for row in rows_b})
        for reviewer, path in (("A", path_a), ("B", path_b)):
            review_source_entries.append(
                {
                    "reviewer": reviewer,
                    "batch": batch.number,
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    if tuple(reviews_a) != package.candidate_ids or tuple(reviews_b) != package.candidate_ids:
        raise FreshReviewError("Reviewer outputs do not cover every candidate once in order")

    comparison_rows: list[dict[str, Any]] = []
    adjudication_inputs: list[dict[str, Any]] = []
    adjudication_templates: list[dict[str, Any]] = []
    human_links: list[dict[str, Any]] = []
    version_rows: list[dict[str, Any]] = []
    pairs_three: list[tuple[str, str]] = []
    pairs_binary: list[tuple[str, str]] = []

    for paper_id in package.candidate_ids:
        source = package.master_by_id[paper_id]
        a = reviews_a[paper_id]
        b = reviews_b[paper_id]
        batch = package.batch_by_id[paper_id]
        audit_id = stable_audit_link_id(package.master_sha256, paper_id)
        row_sha = sha256_text(canonical_json(dict(source)))
        comparison_class = classify_pair(a, b)
        uncertain_present = "UNCERTAIN" in {a["decision"], b["decision"]}
        direct_disagreement = {a["decision"], b["decision"]} == {"INCLUDE", "EXCLUDE"}
        eligibility_disagreement = a["decision"] != b["decision"] or uncertain_present
        primary_code_resolution = (
            a["decision"] == b["decision"] == "EXCLUDE"
            and a["primary_code"] != b["primary_code"]
        )
        criterion_disagreements = [
            field for field in CRITERION_FIELDS if a[field] != b[field]
        ]
        version_disagreement = a["possible_version_of"] != b["possible_version_of"]
        version_review = bool(a["possible_version_of"] or b["possible_version_of"])
        requires_adjudication = eligibility_disagreement or primary_code_resolution

        comparison: dict[str, Any] = {
            "audit_link_id": audit_id,
            "paper_id": paper_id,
            "batch": batch,
            "candidate_row_sha256": row_sha,
        }
        comparison.update({f"reviewer_A_{key}": a[key] for key in REVIEW_FIELDS[1:]})
        comparison.update({f"reviewer_B_{key}": b[key] for key in REVIEW_FIELDS[1:]})
        comparison.update(
            {
                "comparison_class": comparison_class,
                "decision_agreement": bool_text(a["decision"] == b["decision"]),
                "primary_code_agreement": bool_text(
                    a["primary_code"] == b["primary_code"]
                ),
                "uncertain_present": bool_text(uncertain_present),
                "direct_include_exclude_disagreement": bool_text(direct_disagreement),
                "criterion_disagreement_fields": ";".join(criterion_disagreements),
                "possible_version_of_disagreement": bool_text(version_disagreement),
                "requires_eligibility_adjudication": bool_text(
                    eligibility_disagreement
                ),
                "requires_primary_code_resolution": bool_text(
                    primary_code_resolution
                ),
                "requires_adjudication": bool_text(requires_adjudication),
                "requires_version_review": bool_text(version_review),
            }
        )
        comparison_rows.append(comparison)
        pairs_three.append((a["decision"], b["decision"]))
        pairs_binary.append(
            (
                "INCLUDE" if a["decision"] == "INCLUDE" else "NON_INCLUDE",
                "INCLUDE" if b["decision"] == "INCLUDE" else "NON_INCLUDE",
            )
        )

        human_links.append(
            {
                "audit_link_id": audit_id,
                "paper_id": paper_id,
                "batch": batch,
                "candidate_row_sha256": row_sha,
                "human_audit_id": "",
                "human_decision": "",
                "human_primary_code": "",
                "human_confidence": "",
                "human_audit_source_sha256": "",
                "human_audit_completed_utc": "",
            }
        )
        if requires_adjudication:
            adjudication = {
                "audit_link_id": audit_id,
                "paper_id": paper_id,
                "batch": batch,
                "comparison_class": comparison_class,
                "requires_eligibility_adjudication": bool_text(
                    eligibility_disagreement
                ),
                "requires_primary_code_resolution": bool_text(
                    primary_code_resolution
                ),
            }
            adjudication.update({field: source[field] for field in BLINDED_FIELDS[1:]})
            adjudication.update(
                {f"reviewer_A_{key}": a[key] for key in REVIEW_FIELDS[1:]}
            )
            adjudication.update(
                {f"reviewer_B_{key}": b[key] for key in REVIEW_FIELDS[1:]}
            )
            adjudication_inputs.append(adjudication)
            adjudication_templates.append(
                {
                    "audit_link_id": audit_id,
                    "paper_id": paper_id,
                    **{field: "" for field in ADJUDICATION_DECISION_FIELDS[2:]},
                }
            )
        if version_review:
            version_rows.append(
                {
                    "audit_link_id": audit_id,
                    "paper_id": paper_id,
                    "batch": batch,
                    "doi": source["doi"],
                    "title": source["title"],
                    "publication_date": source["publication_date"],
                    "authors": source["authors"],
                    "reviewer_A_decision": a["decision"],
                    "reviewer_A_possible_version_of": a["possible_version_of"],
                    "reviewer_B_decision": b["decision"],
                    "reviewer_B_possible_version_of": b["possible_version_of"],
                    "relationship_decision": "",
                    "canonical_work_id": "",
                    "relationship_rationale": "",
                    "evidence_locator_1": "",
                    "evidence_locator_2": "",
                }
            )

    summary = {
        "schema_version": "fresh-independent-review-comparison-v2.0",
        "generated_at_utc": utc_now(),
        "records": len(comparison_rows),
        "batches": len(package.batches),
        "reviewer_A_decision_counts": dict(
            sorted(Counter(row["decision"] for row in reviews_a.values()).items())
        ),
        "reviewer_B_decision_counts": dict(
            sorted(Counter(row["decision"] for row in reviews_b.values()).items())
        ),
        "comparison_class_counts": dict(
            sorted(Counter(row["comparison_class"] for row in comparison_rows).items())
        ),
        "requires_adjudication": len(adjudication_inputs),
        "requires_version_review": len(version_rows),
        "three_way_raw_agreement": (
            sum(left == right for left, right in pairs_three) / len(pairs_three)
            if pairs_three
            else None
        ),
        "three_way_cohen_kappa": cohen_kappa(
            pairs_three, ["INCLUDE", "EXCLUDE", "UNCERTAIN"]
        ),
        "binary_include_noninclude_raw_agreement": (
            sum(left == right for left, right in pairs_binary) / len(pairs_binary)
            if pairs_binary
            else None
        ),
        "binary_include_noninclude_cohen_kappa": cohen_kappa(
            pairs_binary, ["INCLUDE", "NON_INCLUDE"]
        ),
        "interpretation": (
            "Agreement between two independent model reviewers before resolution; "
            "this is not human inter-rater reliability or proof of screening accuracy."
        ),
    }

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.building-", dir=output_dir.parent)
    )
    try:
        # Freeze self-contained copies only after both complete review sets have
        # passed validation.  Reviewer A and B remain in separate subfolders;
        # neither source file is modified.
        review_input_entries: list[dict[str, Any]] = []
        for source_entry in review_source_entries:
            reviewer = source_entry["reviewer"]
            source_path = Path(source_entry["path"])
            locked_dir = temp_dir / "locked_reviewer_inputs" / f"reviewer_{reviewer}"
            locked_dir.mkdir(parents=True, exist_ok=True)
            locked_path = locked_dir / source_path.name
            shutil.copyfile(source_path, locked_path)
            if sha256_file(locked_path) != source_entry["sha256"]:
                raise FreshReviewError(
                    f"Reviewer {reviewer} batch {source_entry['batch']} changed while locking"
                )
            review_input_entries.append(
                {
                    "reviewer": reviewer,
                    "batch": source_entry["batch"],
                    "path": locked_path.relative_to(temp_dir).as_posix(),
                    "original_path": source_entry["path"],
                    "bytes": locked_path.stat().st_size,
                    "sha256": sha256_file(locked_path),
                }
            )
        comparison_path = temp_dir / "REVIEW_COMPARISON_V2.csv"
        adjudication_input_path = temp_dir / "ADJUDICATION_INPUT_V2.csv"
        adjudication_template_path = temp_dir / "ADJUDICATION_DECISIONS_TEMPLATE_V2.csv"
        human_link_path = temp_dir / "HUMAN_AUDIT_LINKAGE_TEMPLATE_V2.csv"
        version_path = temp_dir / "VERSION_RELATIONSHIP_REVIEW_INPUT_V2.csv"
        summary_path = temp_dir / "REVIEW_AGREEMENT_SUMMARY_V2.json"
        write_csv(comparison_path, comparison_rows, COMPARISON_FIELDS)
        write_csv(adjudication_input_path, adjudication_inputs, ADJUDICATION_INPUT_FIELDS)
        write_csv(
            adjudication_template_path,
            adjudication_templates,
            ADJUDICATION_DECISION_FIELDS,
        )
        write_csv(human_link_path, human_links, HUMAN_AUDIT_LINK_FIELDS)
        write_csv(version_path, version_rows, VERSION_REVIEW_FIELDS)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        outputs = {
            "comparison": file_entry(comparison_path, temp_dir, "complete_A_B_comparison"),
            "adjudication_input": file_entry(
                adjudication_input_path, temp_dir, "unresolved_record_evidence"
            ),
            "adjudication_decisions_template": file_entry(
                adjudication_template_path, temp_dir, "blank_resolution_template"
            ),
            "human_audit_linkage_template": file_entry(
                human_link_path, temp_dir, "blank_human_audit_linkage"
            ),
            "version_relationship_review_input": file_entry(
                version_path, temp_dir, "post_eligibility_version_flags"
            ),
            "agreement_summary": file_entry(summary_path, temp_dir, "agreement_summary"),
        }
        manifest = {
            "schema_version": "fresh-independent-review-comparison-manifest-v2.0",
            "generated_at_utc": utc_now(),
            "pipeline": "fresh_v2_independent_review_comparison",
            "candidate_package": {
                "directory": str(package.root),
                "candidate_build_manifest_path": str(package.candidate_manifest_path),
                "candidate_build_manifest_sha256": package.candidate_manifest_sha256,
                "candidate_master_path": str(package.master_path),
                "candidate_master_sha256": package.master_sha256,
                "batch_manifest_path": str(package.batch_manifest_path),
                "batch_manifest_sha256": package.batch_manifest_sha256,
                "review_schema_path": str(package.schema_path),
                "review_schema_sha256": package.schema_sha256,
                "codebook_path": str(package.codebook_path),
                "codebook_sha256": package.codebook_sha256,
            },
            "review_inputs": review_input_entries,
            "original_review_inputs": review_source_entries,
            "counts": {
                "records": len(comparison_rows),
                "batches": len(package.batches),
                "adjudication_rows": len(adjudication_inputs),
                "version_flag_rows": len(version_rows),
            },
            "structural_blinding_checks": {
                "reviewer_directories_distinct": True,
                "both_complete_review_sets_required_before_any_comparison_output": True,
                "reviewer_input_batches_exclude_trigger_fields": True,
                "reviewer_input_batches_exclude_other_reviewer_decisions": True,
                "reviewer_files_not_modified": True,
                "validated_review_sets_archived_in_separate_locked_subdirectories": True,
                "note": (
                    "These checks preserve the file-level blinding contract. The review "
                    "execution log must separately record what each reviewer was shown."
                ),
            },
            "decision_contract": {
                "retired_E8_allowed": False,
                "uncertain_always_requires_resolution": True,
                "direct_decision_disagreement_requires_resolution": True,
                "agreed_exclusion_with_different_primary_codes_requires_resolution": True,
                "possible_version_of_changes_eligibility": False,
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
        manifest_path = temp_dir / "REVIEW_COMPARISON_MANIFEST_V2.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        hash_rows: list[dict[str, Any]] = []
        for item in review_input_entries:
            hash_rows.append(
                {
                    "scope": f"reviewer_{item['reviewer']}_input",
                    "path": item["path"],
                    "role": f"completed_batch_{item['batch']:03d}",
                    "bytes": item["bytes"],
                    "sha256": item["sha256"],
                }
            )
        for path, role in (
            (comparison_path, "complete_A_B_comparison"),
            (adjudication_input_path, "unresolved_record_evidence"),
            (adjudication_template_path, "blank_resolution_template"),
            (human_link_path, "blank_human_audit_linkage"),
            (version_path, "post_eligibility_version_flags"),
            (summary_path, "agreement_summary"),
            (manifest_path, "comparison_manifest"),
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
            temp_dir / "REVIEW_COMPARISON_HASH_MANIFEST_V2.csv",
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
    parser.add_argument("--reviewer-a-dir", required=True, type=Path)
    parser.add_argument("--reviewer-b-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = compare_reviews(
            args.candidate_dir,
            args.reviewer_a_dir,
            args.reviewer_b_dir,
            args.output_dir,
            codebook=args.codebook,
        )
    except FreshReviewError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
