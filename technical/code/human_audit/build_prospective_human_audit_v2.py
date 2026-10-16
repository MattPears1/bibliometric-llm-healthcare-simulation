#!/usr/bin/env python3
"""Build a deterministic, blinded 100-record human-audit package.

The builder is deliberately fail-closed.  It binds the locked V2 codebook,
candidate and batch manifests, archived Reviewer A/B files, comparison package,
pre-audit model finalization, and the exact deduplicated source universe before
selecting any record.  It does not create an XLSX; the CSV is the locked data
source for the later reviewed workbook.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from typing import Any, Iterable, Mapping, Sequence

import build_fresh_screening_candidates as CANDIDATE_BUILDER
import finalize_fresh_screening_v2 as SCREEN_FINALIZER
from fresh_screening_review_common_v2 import (
    DEFAULT_CODEBOOK,
    FreshReviewError,
    canonical_json,
    file_entry,
    read_csv,
    safe_relative,
    sha256_file,
    sha256_text,
    validate_candidate_package,
    validate_file_entry,
    write_csv,
)
from prospective_human_audit_common_v2 import (
    AUDIT_SCHEMA_VERSION,
    CRITERIA_SUMMARY,
    ELIGIBILITY_QUESTION,
    EXCLUSION_SUMMARY,
    EXPECTED_SAMPLE_SIZE,
    HUMAN_RESPONSE_FIELDS,
    HUMAN_REVIEW_FIELDS,
    LOCKED_SAMPLE_SEED,
    stable_order,
    stable_rank,
)


# Keeping the accepted final decisions explicit makes this script independent
# of any future name changes in the screening helper.
VALID_MODEL_FINAL_DECISIONS = {"INCLUDE", "EXCLUDE"}

GROUP_A = "A_DIFFICULT"
GROUP_B = "B_AGREED_INCLUDE"
GROUP_C = "C_AGREED_EXCLUDE"
GROUP_D = "D_BOUNDARY_NEGATIVE"

BOUNDARY_QUOTAS = {
    "BOUNDARY_NO_SIM": 8,
    "BOUNDARY_NO_ED": 6,
    "BOUNDARY_NO_HEALTH": 6,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_output_hash_ledger(root: Path, filename: str) -> None:
    fields, rows = read_csv(root / filename)
    if fields != ["scope", "path", "role", "bytes", "sha256"]:
        raise FreshReviewError(f"{root / filename}: unexpected hash-ledger schema")
    for row in rows:
        if row["scope"] != "output":
            continue
        path = safe_relative(root, row["path"], label="finalization output ledger")
        if not path.is_file():
            raise FreshReviewError(f"Finalization output is missing: {path}")
        if (
            path.stat().st_size != int(row["bytes"])
            or sha256_file(path) != row["sha256"].casefold()
        ):
            raise FreshReviewError(f"Finalization output hash mismatch: {path}")


def _load_pre_audit_finalization(
    finalization_dir: Path,
    package: Any,
    comparison_manifest_path: Path,
    comparison_rows: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, Any], list[dict[str, str]], Path, Path]:
    root = finalization_dir.resolve()
    manifest_path = root / "SCREENING_FINALIZATION_MANIFEST_V2.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FreshReviewError(f"Missing model finalization manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise FreshReviewError(f"Invalid model finalization manifest: {manifest_path}") from exc
    if manifest.get("pipeline") != "fresh_v2_record_level_screening_finalization":
        raise FreshReviewError("Not a fresh V2 record-level finalization package")
    if manifest.get("status") != "provisional_record_level_decisions_pending_prospective_human_audit":
        raise FreshReviewError(
            "Audit sampling requires the pre-audit model finalization with no human data linked"
        )
    if int((manifest.get("counts") or {}).get("human_audited_records_linked") or 0):
        raise FreshReviewError("Pre-audit model finalization already contains human decisions")

    inputs = manifest.get("inputs") or {}
    required = {
        "candidate_build_manifest": package.candidate_manifest_sha256,
        "candidate_master": package.master_sha256,
        "comparison_manifest": sha256_file(comparison_manifest_path),
        "codebook": package.codebook_sha256,
    }
    for key, expected in required.items():
        observed = str(((inputs.get(key) or {}).get("sha256")) or "").casefold()
        if observed != expected:
            raise FreshReviewError(f"Model finalization binding mismatch for {key}")

    outputs = manifest.get("outputs") or {}
    final_path = validate_file_entry(
        root,
        outputs.get("final_record_level_screening") or {},
        label="pre-audit final record decisions",
    )
    for key, label in (
        ("final_included_records", "pre-audit included records"),
        ("post_eligibility_version_review_queue", "version review queue"),
        ("human_audit_linkage_used", "blank human-audit linkage"),
        ("summary", "pre-audit finalization summary"),
    ):
        validate_file_entry(root, outputs.get(key) or {}, label=label)
    _validate_output_hash_ledger(root, "SCREENING_FINALIZATION_HASH_MANIFEST_V2.csv")

    fields, rows = read_csv(final_path)
    if fields != SCREEN_FINALIZER.FINAL_FIELDS:
        raise FreshReviewError(f"{final_path}: unexpected final-record schema/order")
    if [row["paper_id"] for row in rows] != list(package.candidate_ids):
        raise FreshReviewError(f"{final_path}: candidate ID/order mismatch")
    comparison_by_id = {row["paper_id"]: row for row in comparison_rows}
    for row in rows:
        paper_id = row["paper_id"]
        source = package.master_by_id[paper_id]
        if any(row[field] != source[field] for field in package.master_fields):
            raise FreshReviewError(f"{final_path}: source evidence changed for {paper_id}")
        if row["human_audit_id"] or row["human_decision"]:
            raise FreshReviewError(f"{final_path}: human data present before sampling")
        if row["final_decision"] not in VALID_MODEL_FINAL_DECISIONS:
            raise FreshReviewError(f"{final_path}: unresolved model final decision for {paper_id}")
        comparison = comparison_by_id[paper_id]
        if row["audit_link_id"] != comparison["audit_link_id"]:
            raise FreshReviewError(f"{final_path}: comparison linkage mismatch for {paper_id}")
        if comparison["requires_adjudication"] == "true":
            if row["adjudication_applied"] != "true":
                raise FreshReviewError(f"{final_path}: unresolved A/B issue for {paper_id}")
        elif (
            row["adjudication_applied"] != "false"
            or row["final_decision"] != comparison["reviewer_A_decision"]
        ):
            raise FreshReviewError(f"{final_path}: model-agreement row was altered for {paper_id}")
    return manifest, rows, manifest_path, final_path


def _ranked(
    rows: Iterable[Mapping[str, Any]], *, seed: str, pool: str
) -> list[Mapping[str, Any]]:
    return sorted(rows, key=lambda row: stable_rank(seed, pool, str(row["paper_id"])))


def _take(
    rows: Sequence[Mapping[str, Any]], count: int, *, seed: str, pool: str
) -> list[Mapping[str, Any]]:
    return list(_ranked(rows, seed=seed, pool=pool)[:count])


def _selected_record(
    row: Mapping[str, Any], *, group: str, component: str, seed: str
) -> dict[str, Any]:
    selection_hash, _ = stable_rank(seed, component, str(row["paper_id"]))
    return {
        "paper_id": str(row["paper_id"]),
        "sample_group": group,
        "sample_component": component,
        "selection_hash": selection_hash,
    }


def _select_difficult(
    comparisons: Sequence[Mapping[str, str]],
    candidate_by_id: Mapping[str, Mapping[str, str]],
    *,
    seed: str,
) -> list[dict[str, Any]]:
    # Current brief defines difficult records by A/B decision disagreement or
    # either reviewer choosing UNCERTAIN. Missing abstracts are prioritised only
    # within that issue set so every Group-A record satisfies that definition.
    issues = [
        row
        for row in comparisons
        if row["uncertain_present"] == "true"
        or row["direct_include_exclude_disagreement"] == "true"
    ]
    missing = [
        row for row in issues if candidate_by_id[row["paper_id"]]["abstract_missing"] == "true"
    ]
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add(rows: Iterable[Mapping[str, Any]], count: int, component: str) -> int:
        eligible = [row for row in rows if row["paper_id"] not in selected_ids]
        chosen = _take(eligible, count, seed=seed, pool=component)
        for row in chosen:
            selected.append(
                _selected_record(row, group=GROUP_A, component=component, seed=seed)
            )
            selected_ids.add(row["paper_id"])
        return len(chosen)

    got_missing = add(missing, 10, "MISSING")
    missing_shortfall = 10 - got_missing
    uncertain_quota = 15 + (missing_shortfall + 1) // 2
    disagree_quota = 15 + missing_shortfall // 2
    uncertain = [row for row in issues if row["uncertain_present"] == "true"]
    disagree = [
        row
        for row in issues
        if row["direct_include_exclude_disagreement"] == "true"
    ]
    got_uncertain = add(uncertain, uncertain_quota, "UNCERTAIN")
    got_disagree = add(disagree, disagree_quota, "DISAGREE")
    if got_uncertain < uncertain_quota:
        add(disagree, uncertain_quota - got_uncertain, "DISAGREE")
    if got_disagree < disagree_quota:
        add(uncertain, disagree_quota - got_disagree, "UNCERTAIN")
    if len(selected) < 40:
        add(issues, 40 - len(selected), "DIFFICULT_FILL")
    return selected[:40]


def _allocate_two_pool(
    pool_one: Sequence[Mapping[str, Any]],
    pool_two: Sequence[Mapping[str, Any]],
    *,
    target: int,
    base_one: int,
    base_two: int,
    name_one: str,
    name_two: str,
    group: str,
    seed: str,
) -> list[dict[str, Any]]:
    extra = target - base_one - base_two
    quota_one = base_one + (extra + 1) // 2
    quota_two = base_two + extra // 2
    ranked_one = _ranked(pool_one, seed=seed, pool=name_one)
    ranked_two = _ranked(pool_two, seed=seed, pool=name_two)
    selected_one = list(ranked_one[:quota_one])
    selected_two = list(ranked_two[:quota_two])
    shortage_one = quota_one - len(selected_one)
    shortage_two = quota_two - len(selected_two)
    if shortage_one:
        selected_two.extend(ranked_two[len(selected_two) : len(selected_two) + shortage_one])
    if shortage_two:
        selected_one.extend(ranked_one[len(selected_one) : len(selected_one) + shortage_two])
    output = [
        _selected_record(row, group=group, component=name_one, seed=seed)
        for row in selected_one
    ] + [
        _selected_record(row, group=group, component=name_two, seed=seed)
        for row in selected_two
    ]
    if len(output) < target:
        raise FreshReviewError(
            f"Sample shortfall: {group} needs {target} records but its two pools contain "
            f"only {len(pool_one) + len(pool_two)}"
        )
    return output[:target]


def _neutral_dedup_row(record: Mapping[str, Any]) -> dict[str, Any]:
    urls = CANDIDATE_BUILDER.url_list(record)
    doi = CANDIDATE_BUILDER.clean_text(record.get("doi"))
    doi_url = f"https://doi.org/{doi}" if doi else ""
    if doi_url and doi_url.casefold() not in {value.casefold() for value in urls}:
        urls.append(doi_url)
    return {
        "paper_id": CANDIDATE_BUILDER.clean_text(record.get("dedup_id") or record.get("id")),
        "doi": doi,
        "title": CANDIDATE_BUILDER.clean_text(record.get("title")),
        "year": str(record.get("year") or ""),
        "publication_date": CANDIDATE_BUILDER.clean_text(record.get("publication_date")),
        "date_window_status": CANDIDATE_BUILDER.clean_text(record.get("date_window_status")),
        "language_status": CANDIDATE_BUILDER.clean_text(record.get("language_status")),
        "journal": CANDIDATE_BUILDER.clean_text(record.get("journal")),
        "record_type": CANDIDATE_BUILDER.clean_text(record.get("type")),
        "abstract": CANDIDATE_BUILDER.clean_text(record.get("abstract")),
        "source_keywords": "; ".join(CANDIDATE_BUILDER.source_keywords(record)),
        "url": CANDIDATE_BUILDER.clean_text(record.get("url")),
        "all_urls": "; ".join(urls),
        "abstract_missing": "true" if not CANDIDATE_BUILDER.clean_text(record.get("abstract")) else "false",
    }


def _build_boundary_pools(
    records: Sequence[Mapping[str, Any]], candidate_ids: set[str]
) -> tuple[dict[str, list[dict[str, Any]]], Mapping[str, Mapping[str, bool]]]:
    compiled = {
        name: re.compile(pattern, re.IGNORECASE)
        for name, pattern in CANDIDATE_BUILDER.DOMAIN_PATTERNS.items()
    }
    pools: dict[str, list[dict[str, Any]]] = {key: [] for key in BOUNDARY_QUOTAS}
    hit_map: dict[str, Mapping[str, bool]] = {}
    for record in records:
        row = _neutral_dedup_row(record)
        paper_id = row["paper_id"]
        if paper_id in candidate_ids:
            continue
        text = "\n".join((row["title"], row["abstract"], row["source_keywords"]))
        hits = {name: bool(pattern.search(text)) for name, pattern in compiled.items()}
        if not hits["language_model"]:
            continue
        component = ""
        if hits["healthcare"] and hits["education_training"] and not hits["simulation"]:
            component = "BOUNDARY_NO_SIM"
        elif hits["healthcare"] and hits["simulation"] and not hits["education_training"]:
            component = "BOUNDARY_NO_ED"
        elif hits["education_training"] and hits["simulation"] and not hits["healthcare"]:
            component = "BOUNDARY_NO_HEALTH"
        if component:
            pools[component].append(row)
            hit_map[paper_id] = hits
    return pools, hit_map


def _select_boundary(
    pools: Mapping[str, Sequence[Mapping[str, Any]]], *, seed: str
) -> list[dict[str, Any]]:
    ranked = {
        name: list(_ranked(rows, seed=seed, pool=name)) for name, rows in pools.items()
    }
    counts = {name: min(BOUNDARY_QUOTAS[name], len(ranked[name])) for name in BOUNDARY_QUOTAS}
    remaining_needed = 20 - sum(counts.values())
    while remaining_needed > 0:
        available = {
            name: len(ranked[name]) - counts[name] for name in BOUNDARY_QUOTAS
        }
        best = sorted(available, key=lambda name: (-available[name], name))[0]
        if available[best] <= 0:
            raise FreshReviewError(
                "Boundary sample shortfall: fewer than 20 eligible high-risk outside-frame records"
            )
        take = min(remaining_needed, available[best])
        counts[best] += take
        remaining_needed -= take
    output: list[dict[str, Any]] = []
    for name in BOUNDARY_QUOTAS:
        output.extend(
            _selected_record(row, group=GROUP_D, component=name, seed=seed)
            for row in ranked[name][: counts[name]]
        )
    return output


def _split_urls(row: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for source in (str(row.get("url") or ""), str(row.get("all_urls") or "")):
        for value in re.split(r"\s*;\s*", source):
            value = value.strip()
            if value and value.casefold() not in {item.casefold() for item in values}:
                values.append(value)
    doi = str(row.get("doi") or "").strip()
    doi_url = f"https://doi.org/{doi}" if doi else ""
    if doi_url and doi_url.casefold() not in {item.casefold() for item in values}:
        values.append(doi_url)
    return values


def _visible_row(audit_id: str, source: Mapping[str, Any]) -> dict[str, str]:
    urls = _split_urls(source)
    visible = {
        "human_audit_id": audit_id,
        "title": str(source.get("title") or ""),
        "abstract": str(source.get("abstract") or ""),
        "source_keywords": str(source.get("source_keywords") or ""),
        "publication_year": str(source.get("year") or ""),
        "publication_date": str(source.get("publication_date") or ""),
        "date_window_status": str(source.get("date_window_status") or ""),
        "language_status": str(source.get("language_status") or ""),
        "journal_or_source_title": str(source.get("journal") or ""),
        "document_type": str(source.get("record_type") or ""),
        "eligibility_question": ELIGIBILITY_QUESTION,
        "criteria_summary": CRITERIA_SUMMARY,
        "exclusion_summary": EXCLUSION_SUMMARY,
        "evidence_url_1": urls[0] if urls else "",
        "evidence_url_2": urls[1] if len(urls) > 1 else "",
    }
    return {**visible, **{field: "" for field in HUMAN_RESPONSE_FIELDS}}


def build_human_audit_package(
    candidate_dir: Path,
    comparison_dir: Path,
    model_finalization_dir: Path,
    deduplicated_dir: Path,
    output_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
    seed: str = LOCKED_SAMPLE_SEED,
) -> Mapping[str, Any]:
    if seed != LOCKED_SAMPLE_SEED:
        raise FreshReviewError(
            f"This locked protocol requires seed {LOCKED_SAMPLE_SEED!r}; observed {seed!r}"
        )
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FreshReviewError(f"Output directory already exists: {output_dir}")
    package = validate_candidate_package(candidate_dir, codebook=codebook)
    comparison_manifest, comparison_rows, comparison_manifest_path = (
        SCREEN_FINALIZER._load_and_validate_comparison(comparison_dir, package)
    )
    (
        finalization_manifest,
        final_rows,
        finalization_manifest_path,
        final_path,
    ) = _load_pre_audit_finalization(
        model_finalization_dir,
        package,
        comparison_manifest_path,
        comparison_rows,
    )

    dedup_dir = deduplicated_dir.resolve()
    dedup_records, dedup_manifest, dedup_jsonl = CANDIDATE_BUILDER.load_deduplicated_input(
        dedup_dir
    )
    candidate_input = package.candidate_manifest.get("input") or {}
    dedup_manifest_path = dedup_dir / "DEDUPLICATION_MANIFEST.json"
    if sha256_file(dedup_jsonl) != str(candidate_input.get("deduplicated_jsonl_sha256") or "").casefold():
        raise FreshReviewError("Deduplicated JSONL does not match the candidate package")
    if sha256_file(dedup_manifest_path) != str(candidate_input.get("deduplication_manifest_sha256") or "").casefold():
        raise FreshReviewError("Deduplication manifest does not match the candidate package")
    dedup_ids = {
        CANDIDATE_BUILDER.clean_text(row.get("dedup_id") or row.get("id"))
        for row in dedup_records
    }
    if not set(package.candidate_ids) <= dedup_ids:
        raise FreshReviewError("Candidate frame is not a subset of the bound source universe")

    comparison_by_id = {row["paper_id"]: row for row in comparison_rows}
    final_by_id = {row["paper_id"]: row for row in final_rows}
    selected_a = _select_difficult(
        comparison_rows, package.master_by_id, seed=seed
    )
    difficult_shortfall = 40 - len(selected_a)
    group_b_target = 20 + (difficult_shortfall + 1) // 2
    group_c_target = 20 + difficult_shortfall // 2
    selected_ids = {row["paper_id"] for row in selected_a}

    agreed_include = [
        row
        for row in comparison_rows
        if row["comparison_class"] == "AGREED_INCLUDE" and row["paper_id"] not in selected_ids
    ]
    if len(agreed_include) < group_b_target:
        raise FreshReviewError(
            f"Sample shortfall: Group B needs {group_b_target} agreed inclusions but only "
            f"{len(agreed_include)} are available"
        )
    selected_b = [
        _selected_record(row, group=GROUP_B, component="AGREED_INCLUDE", seed=seed)
        for row in _take(agreed_include, group_b_target, seed=seed, pool="AGREED_INCLUDE")
    ]

    mixed_exclude = [
        row
        for row in comparison_rows
        if row["comparison_class"] == "AGREED_EXCLUDE_DIFFERENT_CODE"
        and row["paper_id"] not in selected_ids
    ]
    same_exclude = [
        row
        for row in comparison_rows
        if row["comparison_class"] == "AGREED_EXCLUDE_SAME_CODE"
        and row["paper_id"] not in selected_ids
    ]
    selected_c = _allocate_two_pool(
        mixed_exclude,
        same_exclude,
        target=group_c_target,
        base_one=10,
        base_two=10,
        name_one="MIXED_EXCLUDE",
        name_two="SAME_EXCLUDE",
        group=GROUP_C,
        seed=seed,
    )

    boundary_pools, boundary_hit_map = _build_boundary_pools(
        dedup_records, set(package.candidate_ids)
    )
    selected_d = _select_boundary(boundary_pools, seed=seed)
    selected = selected_a + selected_b + selected_c + selected_d
    if len(selected) != EXPECTED_SAMPLE_SIZE:
        raise FreshReviewError(
            f"Internal sample-size error: expected {EXPECTED_SAMPLE_SIZE}, observed {len(selected)}"
        )
    paper_ids = [row["paper_id"] for row in selected]
    if len(paper_ids) != len(set(paper_ids)):
        raise FreshReviewError("A record was selected more than once")

    dedup_neutral = {
        CANDIDATE_BUILDER.clean_text(record.get("dedup_id") or record.get("id")): _neutral_dedup_row(record)
        for record in dedup_records
    }
    selected.sort(key=lambda row: stable_order(seed, row["paper_id"]))
    review_rows: list[dict[str, str]] = []
    mappings: list[dict[str, Any]] = []
    for index, selection in enumerate(selected, start=1):
        audit_id = f"H{index:03d}"
        paper_id = selection["paper_id"]
        is_candidate = paper_id in package.master_by_id
        source = package.master_by_id[paper_id] if is_candidate else dedup_neutral[paper_id]
        review_rows.append(_visible_row(audit_id, source))
        final = final_by_id.get(paper_id)
        comparison = comparison_by_id.get(paper_id)
        order_hash, _ = stable_order(seed, paper_id)
        mappings.append(
            {
                "human_audit_id": audit_id,
                "paper_id": paper_id,
                "record_origin": "candidate_frame" if is_candidate else "outside_candidate_frame",
                "sample_group": selection["sample_group"],
                "sample_component": selection["sample_component"],
                "selection_hash": selection["selection_hash"],
                "order_hash": order_hash,
                "candidate_batch": package.batch_by_id.get(paper_id, ""),
                "candidate_row_sha256": (
                    comparison["candidate_row_sha256"] if comparison else ""
                ),
                "comparison_class": comparison["comparison_class"] if comparison else "",
                "reviewer_A_decision": comparison["reviewer_A_decision"] if comparison else "",
                "reviewer_A_primary_code": comparison["reviewer_A_primary_code"] if comparison else "",
                "reviewer_B_decision": comparison["reviewer_B_decision"] if comparison else "",
                "reviewer_B_primary_code": comparison["reviewer_B_primary_code"] if comparison else "",
                "model_final_decision": final["final_decision"] if final else "EXCLUDE",
                "model_final_primary_code": (
                    final["final_primary_code"] if final else "OUTSIDE_CANDIDATE_FRAME"
                ),
                "source_record_sha256": sha256_text(canonical_json(dict(source))),
                "boundary_hits": boundary_hit_map.get(paper_id, {}),
            }
        )

    pool_rankings: dict[str, list[dict[str, str]]] = {}
    pool_sources: dict[str, Sequence[Mapping[str, Any]]] = {
        "DIFFICULT_ALL": [
            row
            for row in comparison_rows
            if row["uncertain_present"] == "true"
            or row["direct_include_exclude_disagreement"] == "true"
        ],
        "AGREED_INCLUDE": agreed_include,
        "MIXED_EXCLUDE": mixed_exclude,
        "SAME_EXCLUDE": same_exclude,
        **boundary_pools,
    }
    for name, rows in pool_sources.items():
        pool_rankings[name] = [
            {"paper_id": row["paper_id"], "rank_sha256": stable_rank(seed, name, row["paper_id"])[0]}
            for row in _ranked(rows, seed=seed, pool=name)
        ]

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.building-", dir=output_dir.parent)
    )
    try:
        review_path = temp_dir / "HUMAN_AUDIT_BLINDED_REVIEW_TEMPLATE.csv"
        protected_path = temp_dir / "HUMAN_AUDIT_PROTECTED_MANIFEST.json"
        package_manifest_path = temp_dir / "HUMAN_AUDIT_PACKAGE_MANIFEST.json"
        write_csv(review_path, review_rows, HUMAN_REVIEW_FIELDS)

        protected = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "warning": (
                "Protected preparer file. Do not give this file to the blinded human reviewer. "
                "The blinded CSV is sufficient for review."
            ),
            "seed": seed,
            "mappings": mappings,
            "pool_rankings": pool_rankings,
            "boundary_quota_rule": BOUNDARY_QUOTAS,
        }
        protected_path.write_text(
            json.dumps(protected, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        bindings = {
            "codebook": {"path": str(package.codebook_path), "sha256": package.codebook_sha256},
            "candidate_build_manifest": {"path": str(package.candidate_manifest_path), "sha256": package.candidate_manifest_sha256},
            "candidate_master": {"path": str(package.master_path), "sha256": package.master_sha256},
            "batch_manifest": {"path": str(package.batch_manifest_path), "sha256": package.batch_manifest_sha256},
            "review_schema": {"path": str(package.schema_path), "sha256": package.schema_sha256},
            "comparison_manifest": {"path": str(comparison_manifest_path), "sha256": sha256_file(comparison_manifest_path)},
            "comparison_csv": {
                "path": str((comparison_dir.resolve() / "REVIEW_COMPARISON_V2.csv")),
                "sha256": sha256_file(comparison_dir.resolve() / "REVIEW_COMPARISON_V2.csv"),
            },
            "locked_reviewer_inputs": comparison_manifest.get("review_inputs") or [],
            "model_finalization_manifest": {"path": str(finalization_manifest_path), "sha256": sha256_file(finalization_manifest_path)},
            "model_final_decisions": {"path": str(final_path), "sha256": sha256_file(final_path)},
            "deduplication_manifest": {"path": str(dedup_manifest_path), "sha256": sha256_file(dedup_manifest_path)},
            "deduplicated_jsonl": {"path": str(dedup_jsonl), "sha256": sha256_file(dedup_jsonl)},
        }
        counts = Counter(mapping["sample_group"] for mapping in mappings)
        component_counts = Counter(mapping["sample_component"] for mapping in mappings)
        package_manifest = {
            "schema_version": AUDIT_SCHEMA_VERSION,
            "pipeline": "fresh_v2_prospective_human_audit_sample_build",
            "generated_at_utc": utc_now(),
            "status": "blinded_100_record_template_ready_for_human_review",
            "seed": seed,
            "sample_size": len(mappings),
            "sample_group_counts": dict(sorted(counts.items())),
            "sample_component_counts": dict(sorted(component_counts.items())),
            "shortfall_rules": {
                "difficult_under_40": "take the complete issue union; transfer the deficit to B then C, with B receiving an odd extra place",
                "agreed_include_or_exclude_pool": "fail before writing output if an adjusted candidate-frame quota cannot be filled",
                "boundary_subpool": "take all available and fill from the largest remaining boundary pool; fixed alphabetic tie-break",
                "boundary_total_under_20": "fail before writing output",
                "overall": "exactly 100 unique records are mandatory",
            },
            "blinding_contract": {
                "review_csv_contains_paper_id": False,
                "review_csv_contains_sample_group_or_component": False,
                "review_csv_contains_model_or_final_decisions": False,
                "review_csv_contains_candidate_trigger_or_source_database": False,
                "complete_title_abstract_keywords_retained": True,
                "evidence_urls_visible": True,
                "all_human_response_fields_initially_blank": True,
                "protected_manifest_not_needed_during_review": True,
            },
            "bindings": bindings,
            "inputs_verified": {
                "candidate_and_batch_manifests": True,
                "locked_reviewer_A_and_B_files": True,
                "comparison_package": True,
                "pre_audit_model_finalization": True,
                "deduplicated_source_universe": True,
                "no_human_results_present_before_sampling": True,
            },
            "outputs": {
                "blinded_review_template": file_entry(review_path, temp_dir, "human_only_blinded_review_template"),
                "protected_manifest": file_entry(protected_path, temp_dir, "protected_sample_mapping_and_rankings"),
            },
            "source_manifests": {
                "comparison_schema": comparison_manifest.get("schema_version"),
                "finalization_schema": finalization_manifest.get("schema_version"),
                "deduplication_schema": dedup_manifest.get("schema_version"),
            },
            "script": {"filename": Path(__file__).name, "sha256": sha256_file(Path(__file__))},
        }
        package_manifest_path.write_text(
            json.dumps(package_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        hash_rows = []
        for path, role in (
            (review_path, "human_only_blinded_review_template"),
            (protected_path, "protected_sample_mapping_and_rankings"),
            (package_manifest_path, "audit_package_manifest"),
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
            temp_dir / "HUMAN_AUDIT_HASH_MANIFEST.csv",
            hash_rows,
            ["scope", "path", "role", "bytes", "sha256"],
        )
        temp_dir.rename(output_dir)
        return package_manifest
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--comparison-dir", required=True, type=Path)
    parser.add_argument("--model-finalization-dir", required=True, type=Path)
    parser.add_argument("--deduplicated-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    parser.add_argument("--seed", default=LOCKED_SAMPLE_SEED)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = build_human_audit_package(
            args.candidate_dir,
            args.comparison_dir,
            args.model_finalization_dir,
            args.deduplicated_dir,
            args.output_dir,
            codebook=args.codebook,
            seed=args.seed,
        )
    except (FreshReviewError, CANDIDATE_BUILDER.CandidateBuildError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
