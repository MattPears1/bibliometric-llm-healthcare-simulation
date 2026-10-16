#!/usr/bin/env python3
"""Corrected-only fail-closed base V4 + 30-record Scopus integration."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "scopus-final-integration-corrected-v2.0"
REMOVED_PAPER_ID = "sci_42a355e3f11b03dc7d88"
REMOVED_FAMILY_ID = "SIVF-3edd5760b254e839a39f5b03"
EXPECTED = {
    "base_publications": 517, "base_families": 458, "scopus_publications": 30,
    "eligible_publications": 547, "families": 485, "alternate_versions": 62,
    "combined_screening": 3919, "combined_include": 547, "combined_exclude": 3372,
}
OUTPUTS = {
    "version_ledger": "COMBINED_ELIGIBLE_PUBLICATION_VERSION_LEDGER_CORRECTED_V2.csv",
    "extraction": "COMBINED_CANONICAL_CHECKED_EXTRACTION_CORRECTED_V2.csv",
    "metadata": "COMBINED_CANONICAL_METADATA_CORRECTED_V2.csv",
    "openalex": "COMBINED_CANONICAL_OPENALEX_CORRECTED_V2.csv",
    "screening": "COMBINED_RECORD_LEVEL_SCREENING_CORRECTED_V2.csv",
    "selection": "COMBINED_STUDY_SELECTION_LEDGER_CORRECTED_V2.csv",
}
MANIFEST = "SCOPUS_FINAL_INTEGRATION_CORRECTED_MANIFEST_V2.json"
HASHES = "SCOPUS_FINAL_INTEGRATION_CORRECTED_HASHES_V2.csv"
FROZEN = "SCOPUS_FINAL_INTEGRATION_CORRECTED_FROZEN_V2.json"
QA = "SCOPUS_FINAL_INTEGRATION_CORRECTED_QA_V2.json"
FAMILY_MUTABLE = {
    "review_family_label", "family_status", "version_role", "preferred_for_analysis",
    "preferred_record_key", "preferred_basis", "relationship_to_preferred",
    "family_membership_rationale", "family_evidence_locator",
    "preferred_selection_rationale", "preferred_selection_evidence", "reviewed_by",
    "reviewed_at_utc",
}


class CorrectedIntegrationError(RuntimeError):
    pass


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_hash(values: Iterable[str]) -> str:
    return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()


def row_hash(row: dict[str, str], fields: Iterable[str]) -> str:
    return stable_hash(clean(row.get(field)) for field in fields)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise CorrectedIntegrationError(f"CSV has no header: {path}")
        return list(reader.fieldnames), [dict(row) for row in reader]


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field)) for field in fields})


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise CorrectedIntegrationError(f"Expected JSON object: {path}")
    return value


def require_fields(header: list[str], fields: Iterable[str], label: str) -> None:
    missing = sorted(set(fields) - set(header))
    if missing:
        raise CorrectedIntegrationError(f"{label} missing fields: {', '.join(missing)}")


def union_fields(*headers: list[str], prefix: Iterable[str] = ()) -> list[str]:
    result = list(prefix)
    for header in headers:
        for field in header:
            if field not in result:
                result.append(field)
    return result


REQUIRED_INPUTS = {
    "base_manifest", "base_version", "base_extraction", "base_metadata", "base_openalex",
    "base_screening", "scopus_correction_manifest", "scopus_corrected_included",
    "scopus_corrected_decisions", "run03_completion_manifest", "run03_pair_review",
    "run03_family_template", "run03_family_review", "corrected_extraction_manifest",
    "corrected_extraction", "metadata_manifest", "metadata_31", "openalex_31",
}


def resolve_inputs(bindings_path: Path) -> dict[str, Path]:
    items = (load_json(bindings_path).get("inputs") or {})
    if set(items) != REQUIRED_INPUTS:
        raise CorrectedIntegrationError("Bindings must contain exactly the corrected integration inputs")
    result = {}
    for key in sorted(REQUIRED_INPUTS):
        item = items.get(key) or {}
        raw, expected = clean(item.get("path")), clean(item.get("sha256")).casefold()
        if not raw or len(expected) != 64:
            raise CorrectedIntegrationError(f"Invalid binding: {key}")
        path = Path(raw)
        if not path.is_absolute():
            path = (bindings_path.parent / path).resolve()
        if not path.is_file() or sha256_file(path) != expected:
            raise CorrectedIntegrationError(f"Missing/hash-mismatched current byte: {key}")
        result[key] = path
    return result


def manifest_output_hash(manifest: dict[str, Any], key: str) -> str:
    return clean((manifest.get("outputs", {}).get(key) or {}).get("sha256"))


def validate_authorities(paths: dict[str, Path]) -> tuple[dict[str, Any], dict[str, Any]]:
    base = load_json(paths["base_manifest"])
    if base.get("pipeline") != "gse_base_corpus_correction_v4_20260816" or base.get("status") != "base_corpus_correction_v4_frozen_analysis_ready":
        raise CorrectedIntegrationError("Base V4 authority invalid")
    for manifest_key, path_key in (("version", "base_version"), ("extraction", "base_extraction"), ("metadata", "base_metadata"), ("openalex", "base_openalex"), ("screening", "base_screening")):
        if manifest_output_hash(base, manifest_key) != sha256_file(paths[path_key]):
            raise CorrectedIntegrationError(f"Base manifest does not bind {path_key}")
    correction = load_json(paths["scopus_correction_manifest"])
    if correction.get("pipeline") != "scopus_increment_eligibility_correction_v2_20260816" or correction.get("status") != "frozen_authoritative_scopus_eligibility_corrected":
        raise CorrectedIntegrationError("Corrected Scopus eligibility authority invalid")
    if correction.get("counts") != {"corrected_records": 1, "excluded_records": 1214, "included_records": 30, "records": 1244} or correction.get("corrected_paper_ids") != [REMOVED_PAPER_ID]:
        raise CorrectedIntegrationError("Corrected Scopus eligibility counts/target invalid")
    for manifest_key, path_key in (("included", "scopus_corrected_included"), ("decisions", "scopus_corrected_decisions")):
        if manifest_output_hash(correction, manifest_key) != sha256_file(paths[path_key]):
            raise CorrectedIntegrationError(f"Correction manifest does not bind {path_key}")
    completion = load_json(paths["run03_completion_manifest"])
    if completion.get("pipeline") != "scopus_increment_version_review_completion_run03" or completion.get("status") != "frozen_completed_version_review":
        raise CorrectedIntegrationError("Run03 completion authority invalid")
    expected_completion = {
        "alternate_versions": 62, "base_publications": 517, "distinct_work_pairs": 5,
        "eligible_publications": 547, "families": 485, "preferred_reports": 485,
        "reviewed_pairs": 8, "same_version_pairs": 3, "scopus_publications": 30,
    }
    if completion.get("counts") != expected_completion or completion.get("removed") != {"family_id": REMOVED_FAMILY_ID, "pair_id": "SIVP-af5c6d3bec2d096212bc22a0", "record_key": f"scopus_increment:{REMOVED_PAPER_ID}"}:
        raise CorrectedIntegrationError("Run03 completion counts/removal invalid; historical 548/486 review is rejected")
    for manifest_key, path_key in (
        ("SCOPUS_INCREMENT_VERSION_PAIR_REVIEW_COMPLETED.csv", "run03_pair_review"),
        ("SCOPUS_INCREMENT_ALL_RECORD_FAMILY_REVIEW_TEMPLATE.csv", "run03_family_template"),
        ("SCOPUS_INCREMENT_ALL_RECORD_FAMILY_REVIEW_COMPLETED.csv", "run03_family_review"),
    ):
        if manifest_output_hash(completion, manifest_key) != sha256_file(paths[path_key]):
            raise CorrectedIntegrationError(f"Run03 completion manifest does not bind {path_key}")
    extraction = load_json(paths["corrected_extraction_manifest"])
    output_name = "SCOPUS_INCREMENT_CHECKED_WORK_LEVEL_EXTRACTION_CORRECTED_V2.csv"
    if extraction.get("pipeline") != "scopus_increment_checked_extraction_eligibility_filter_20260816" or extraction.get("status") != "frozen_checked_extraction_for_corrected_eligible_scopus_records" or extraction.get("counts") != {"records": 30, "removed_records": 1} or extraction.get("removed_paper_ids") != [REMOVED_PAPER_ID]:
        raise CorrectedIntegrationError("Corrected extraction authority invalid; historical 31-row extraction is rejected")
    if manifest_output_hash(extraction, output_name) != sha256_file(paths["corrected_extraction"]):
        raise CorrectedIntegrationError("Corrected extraction manifest/file mismatch")
    metadata = load_json(paths["metadata_manifest"])
    if metadata.get("schema_version") != "scopus-include-metadata-v1.0" or metadata.get("counts", {}).get("records") != 31:
        raise CorrectedIntegrationError("Source metadata authority must be the frozen 31-row package before exact filtering")
    for manifest_key, path_key in (("SCOPUS_INCLUDE_BIBLIOGRAPHIC_METADATA.csv", "metadata_31"), ("SCOPUS_INCLUDE_METADATA_OPENALEX.csv", "openalex_31")):
        if manifest_output_hash(metadata, manifest_key) != sha256_file(paths[path_key]):
            raise CorrectedIntegrationError(f"Metadata manifest does not bind {path_key}")
    return completion, correction


def unique_index(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    result = {}
    for row in rows:
        key = clean(row.get("paper_id"))
        if not key or key in result:
            raise CorrectedIntegrationError(f"Blank/duplicate paper_id in {label}")
        result[key] = row
    return result


def validate_exact_shared_fields(authority_rows: list[dict[str, str]], candidate_rows: list[dict[str, str]], label: str) -> None:
    authority = unique_index(authority_rows, "corrected included authority")
    candidate = unique_index(candidate_rows, label)
    if list(candidate) != list(authority):
        raise CorrectedIntegrationError(f"{label} IDs/order do not equal corrected 30-ID authority")
    shared = (set(authority_rows[0]) & set(candidate_rows[0])) - {
        "source_record_row_sha256", "source_row_number", "source_checked_at_utc",
    }
    for key in authority:
        changed = [field for field in shared if clean(authority[key].get(field)) != clean(candidate[key].get(field))]
        if changed:
            raise CorrectedIntegrationError(f"Protected corrected source fields changed in {label}/{key}: {', '.join(sorted(changed))}")


def validate_reviews(
    paths: dict[str, Path], corrected_ids: list[str], base_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    pair_header, pairs = read_csv(paths["run03_pair_review"])
    require_fields(pair_header, ["pair_id", "record_key_a", "record_key_b", "relationship_decision", "reviewed_by", "reviewed_at_utc"], "run03 pairs")
    if len(pairs) != 8 or Counter(row["relationship_decision"] for row in pairs) != {"SAME_SCHOLARLY_WORK_VERSION": 3, "DISTINCT_SCHOLARLY_WORK": 5}:
        raise CorrectedIntegrationError("Run03 reviewed pair cardinality/decisions invalid")
    template_header, template = read_csv(paths["run03_family_template"])
    family_header, families = read_csv(paths["run03_family_review"])
    require_fields(family_header, ["record_key", "source_corpus", "source_record_id", "provisional_family_id", "family_size", "preferred_for_analysis", "preferred_record_key", "reviewed_by", "reviewed_at_utc"], "run03 families")
    tmap, fmap = {row["record_key"]: row for row in template}, {row["record_key"]: row for row in families}
    if len(tmap) != len(template) or len(fmap) != len(families) or set(tmap) != set(fmap):
        raise CorrectedIntegrationError("Family completed/template IDs mismatch")
    protected = set(template_header) - FAMILY_MUTABLE
    for key in tmap:
        changed = [field for field in protected if clean(tmap[key].get(field)) != clean(fmap[key].get(field))]
        if changed:
            raise CorrectedIntegrationError(f"Protected family fields changed: {key}")
    if len(families) != EXPECTED["eligible_publications"] or REMOVED_FAMILY_ID in {row["provisional_family_id"] for row in families} or f"scopus_increment:{REMOVED_PAPER_ID}" in fmap:
        raise CorrectedIntegrationError("Run03 family ledger retains historical false-positive or wrong cardinality")
    scopus_family_ids = [row["source_record_id"] for row in families if row["source_corpus"] == "scopus_increment"]
    if len(scopus_family_ids) != len(corrected_ids) or set(scopus_family_ids) != set(corrected_ids):
        raise CorrectedIntegrationError("Run03 Scopus publication IDs differ from corrected authority")
    base_family_rows = [row for row in families if row["source_corpus"] == "base_eligible_v4"]
    if len(base_family_rows) != EXPECTED["base_publications"]:
        raise CorrectedIntegrationError("Run03 did not preserve all 517 base publications")
    prior_groups, final_groups = defaultdict(set), defaultdict(set)
    for row in base_rows:
        prior_groups[row["version_family_id"]].add(row["paper_id"])
    for row in base_family_rows:
        final_groups[row["provisional_family_id"]].add(row["source_record_id"])
    if len(prior_groups) != EXPECTED["base_families"] or len(final_groups) != EXPECTED["base_families"] or set(map(frozenset, prior_groups.values())) != set(map(frozenset, final_groups.values())):
        raise CorrectedIntegrationError("The 458 base V4 family member sets were not preserved exactly")
    by_family = defaultdict(list)
    for row in families:
        by_family[row["provisional_family_id"]].append(row)
    if len(by_family) != EXPECTED["families"]:
        raise CorrectedIntegrationError("Final family count is not 485")
    for family_id, members in by_family.items():
        preferred = [row for row in members if row["preferred_for_analysis"].casefold() == "yes"]
        if len(preferred) != 1 or {row["preferred_record_key"] for row in members} != {preferred[0]["record_key"]} or {int(row["family_size"]) for row in members} != {len(members)}:
            raise CorrectedIntegrationError(f"Invalid preferred/family size contract: {family_id}")
    family_of = {row["record_key"]: row["provisional_family_id"] for row in families}
    for row in pairs:
        same = family_of[row["record_key_a"]] == family_of[row["record_key_b"]]
        if same != (row["relationship_decision"] == "SAME_SCHOLARLY_WORK_VERSION"):
            raise CorrectedIntegrationError(f"Pair/family contradiction: {row['pair_id']}")
    return pairs, families


def build_source_row(row: dict[str, str], header: list[str], source: str, family: dict[str, str]) -> dict[str, str]:
    return {
        "integration_schema_version": SCHEMA, "final_version_family_id": family["provisional_family_id"],
        "preferred_record_key": family["record_key"], "preferred_paper_id": family["source_record_id"],
        "integration_source_corpus": source, "integration_source_row_sha256": row_hash(row, header), **row,
    }


def integrate(bindings_path: Path, output: Path) -> dict[str, int]:
    if output.exists():
        raise CorrectedIntegrationError(f"No-clobber: output exists: {output}")
    paths = resolve_inputs(bindings_path)
    completion, correction = validate_authorities(paths)
    tables = {key: read_csv(paths[key]) for key in (
        "base_version", "base_extraction", "base_metadata", "base_openalex", "base_screening",
        "scopus_corrected_included", "scopus_corrected_decisions", "corrected_extraction",
        "metadata_31", "openalex_31",
    )}
    included_header, included = tables["scopus_corrected_included"]
    corrected_ids = [row["paper_id"] for row in included]
    if len(included) != 30 or len(set(corrected_ids)) != 30 or REMOVED_PAPER_ID in corrected_ids or any(row.get("final_decision") != "INCLUDE" for row in included):
        raise CorrectedIntegrationError("Corrected included authority is not exact ordered 30-record INCLUDE set")
    extraction_header, extraction = tables["corrected_extraction"]
    if len(extraction) != 30:
        raise CorrectedIntegrationError("Historical 31-row extraction rejected")
    validate_exact_shared_fields(included, extraction, "corrected extraction")
    metadata_header_31, metadata_31 = tables["metadata_31"]
    openalex_header_31, openalex_31 = tables["openalex_31"]
    metadata_map, openalex_map = unique_index(metadata_31, "31-row metadata"), unique_index(openalex_31, "31-row OpenAlex")
    if set(metadata_map) != set(openalex_map) or set(metadata_map) != set(corrected_ids) | {REMOVED_PAPER_ID}:
        raise CorrectedIntegrationError("Metadata source is not exact historical 31 IDs")
    metadata = [metadata_map[key] for key in corrected_ids]
    openalex = [openalex_map[key] for key in corrected_ids]
    validate_exact_shared_fields(included, metadata, "filtered corrected metadata")
    if [row["paper_id"] for row in openalex] != corrected_ids:
        raise CorrectedIntegrationError("Filtered OpenAlex order differs from corrected 30 IDs")
    base_header, base_rows = tables["base_version"]
    pairs, families = validate_reviews(paths, corrected_ids, base_rows)
    preferred = sorted((row for row in families if row["preferred_for_analysis"].casefold() == "yes"), key=lambda row: (row["provisional_family_id"], row["record_key"]))
    source_tables = {
        "base_eligible_v4": {
            "extraction": (tables["base_extraction"][0], unique_index(tables["base_extraction"][1], "base extraction")),
            "metadata": (tables["base_metadata"][0], unique_index(tables["base_metadata"][1], "base metadata")),
            "openalex": (tables["base_openalex"][0], unique_index(tables["base_openalex"][1], "base OpenAlex")),
        },
        "scopus_increment": {
            "extraction": (extraction_header, unique_index(extraction, "corrected Scopus extraction")),
            "metadata": (metadata_header_31, unique_index(metadata, "filtered Scopus metadata")),
            "openalex": (openalex_header_31, unique_index(openalex, "filtered Scopus OpenAlex")),
        },
    }
    prefix = ["integration_schema_version", "final_version_family_id", "preferred_record_key", "preferred_paper_id", "integration_source_corpus", "integration_source_row_sha256"]
    canonical_headers = {
        "extraction": union_fields(tables["base_extraction"][0], extraction_header, prefix=prefix),
        "metadata": union_fields(tables["base_metadata"][0], metadata_header_31, prefix=prefix),
        "openalex": union_fields(tables["base_openalex"][0], openalex_header_31, prefix=prefix),
    }
    canonical = {key: [] for key in canonical_headers}
    for family in preferred:
        source, paper_id = family["source_corpus"], family["source_record_id"]
        if source not in source_tables:
            raise CorrectedIntegrationError(f"Unknown preferred source: {source}")
        for kind in canonical:
            header, mapping = source_tables[source][kind]
            if paper_id not in mapping:
                raise CorrectedIntegrationError(f"Preferred report lacks exact {kind}: {family['record_key']}")
            canonical[kind].append(build_source_row(mapping[paper_id], header, source, family))
    family_sha = sha256_file(paths["run03_family_review"])
    version_header = union_fields(list(families[0]), prefix=["integration_schema_version", "source_completed_family_review_sha256"])
    version_rows = [{"integration_schema_version": SCHEMA, "source_completed_family_review_sha256": family_sha, **row} for row in sorted(families, key=lambda row: (row["provisional_family_id"], row["record_key"]))]
    selection_fields = ["integration_schema_version", "final_version_family_id", "family_size", "preferred_record_key", "preferred_paper_id", "preferred_source_corpus", "preferred_basis", "preferred_selection_rationale", "preferred_selection_evidence", "family_reviewed_by", "family_reviewed_at_utc", "source_family_review_row_sha256"]
    family_header = list(families[0])
    selection = [{
        "integration_schema_version": SCHEMA, "final_version_family_id": row["provisional_family_id"],
        "family_size": row["family_size"], "preferred_record_key": row["record_key"],
        "preferred_paper_id": row["source_record_id"], "preferred_source_corpus": row["source_corpus"],
        "preferred_basis": row.get("preferred_basis", ""), "preferred_selection_rationale": row.get("preferred_selection_rationale", ""),
        "preferred_selection_evidence": row.get("preferred_selection_evidence", ""), "family_reviewed_by": row["reviewed_by"],
        "family_reviewed_at_utc": row["reviewed_at_utc"], "source_family_review_row_sha256": row_hash(row, family_header),
    } for row in preferred]
    screening_prefix = ["integration_schema_version", "screening_source_corpus", "screening_source_row_number", "screening_source_row_sha256"]
    screening_header = union_fields(tables["base_screening"][0], tables["scopus_corrected_decisions"][0], prefix=screening_prefix)
    screening = []
    for source, key in (("base_v4", "base_screening"), ("scopus_increment_corrected", "scopus_corrected_decisions")):
        header, rows = tables[key]
        for number, row in enumerate(rows, 1):
            screening.append({"integration_schema_version": SCHEMA, "screening_source_corpus": source, "screening_source_row_number": str(number), "screening_source_row_sha256": row_hash(row, header), **row})
    decisions = Counter(row.get("final_decision") for row in screening)
    counts = {
        "eligible_publication_records": len(families), "unique_studies": len(preferred),
        "alternate_publication_versions": len(families) - len(preferred),
        "base_families_preserved": 458, "scopus_corrected_includes": len(included),
        "same_pair_decisions": sum(row["relationship_decision"] == "SAME_SCHOLARLY_WORK_VERSION" for row in pairs),
        "distinct_pair_decisions": sum(row["relationship_decision"] == "DISTINCT_SCHOLARLY_WORK" for row in pairs),
        "canonical_extraction_rows": len(canonical["extraction"]), "canonical_metadata_rows": len(canonical["metadata"]),
        "canonical_openalex_rows": len(canonical["openalex"]), "combined_screening_rows": len(screening),
        "combined_screening_include": decisions["INCLUDE"], "combined_screening_exclude": decisions["EXCLUDE"],
    }
    required_counts = {
        "eligible_publication_records": 547, "unique_studies": 485, "alternate_publication_versions": 62,
        "base_families_preserved": 458, "scopus_corrected_includes": 30, "same_pair_decisions": 3,
        "distinct_pair_decisions": 5, "canonical_extraction_rows": 485, "canonical_metadata_rows": 485,
        "canonical_openalex_rows": 485, "combined_screening_rows": 3919,
        "combined_screening_include": 547, "combined_screening_exclude": 3372,
    }
    if counts != required_counts:
        raise CorrectedIntegrationError(f"Corrected derived counts disagree: {counts}")
    temp = Path(tempfile.mkdtemp(prefix="scopus-corrected-integration-", dir=str(output.parent.resolve())))
    try:
        write_csv(temp / OUTPUTS["version_ledger"], version_header, version_rows)
        write_csv(temp / OUTPUTS["extraction"], canonical_headers["extraction"], canonical["extraction"])
        write_csv(temp / OUTPUTS["metadata"], canonical_headers["metadata"], canonical["metadata"])
        write_csv(temp / OUTPUTS["openalex"], canonical_headers["openalex"], canonical["openalex"])
        write_csv(temp / OUTPUTS["screening"], screening_header, screening)
        write_csv(temp / OUTPUTS["selection"], selection_fields, selection)
        generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        qa = {
            "schema_version": SCHEMA, "status": "PASS", "validated_at_utc": generated,
            "checks": {
                "corrected_authority_only": True, "historical_31_row_extraction_rejected": True,
                "historical_548_486_review_rejected": True, "removed_false_positive_absent": True,
                "corrected_30_ids_order_exact": True, "protected_fields_exact": True,
                "base_458_family_member_sets_preserved": True, "one_preferred_per_485_families": True,
                "canonical_source_rows_exact": True, "screening_counts_exact": True,
            }, "counts": counts,
        }
        (temp / QA).write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest = {
            "schema_version": SCHEMA, "pipeline": "corrected_scopus_base_v4_final_integration_20260816",
            "status": "frozen_corrected_combined_corpus_analysis_not_performed", "generated_at_utc": generated,
            "contracts": {
                "corrected_authorities_only": True, "all_547_publications_preserved": True,
                "all_458_base_families_preserved": True, "one_preferred_per_485_families": True,
                "false_positive_family_removed": True, "metadata_filtered_to_corrected_30_ids": True,
                "analysis_performed": False, "manuscript_modified": False, "output_no_clobber": True,
            }, "removed": {"paper_id": REMOVED_PAPER_ID, "family_id": REMOVED_FAMILY_ID},
            "derived_counts": counts,
            "bound_inputs": {key: {"path": str(path.resolve()), "sha256": sha256_file(path)} for key, path in paths.items()},
            "outputs": {},
        }
        for key, name in {**OUTPUTS, "qa": QA}.items():
            candidate = temp / name
            manifest["outputs"][key] = {"path": name, "bytes": candidate.stat().st_size, "sha256": sha256_file(candidate)}
        manifest_path = temp / MANIFEST
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        hash_rows = []
        for candidate in sorted([temp / name for name in OUTPUTS.values()] + [temp / QA, manifest_path], key=lambda path: path.name):
            hash_rows.append({"scope": "output", "path": candidate.name, "bytes": candidate.stat().st_size, "sha256": sha256_file(candidate)})
        hash_path = temp / HASHES
        write_csv(hash_path, ["scope", "path", "bytes", "sha256"], hash_rows)
        frozen = {"schema_version": SCHEMA, "pipeline": manifest["pipeline"], "status": "frozen", "generated_at_utc": generated, "manifest": MANIFEST, "manifest_sha256": sha256_file(manifest_path), "hash_manifest": HASHES, "hash_manifest_sha256": sha256_file(hash_path)}
        (temp / FROZEN).write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp.replace(output)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    return counts


def validate_combined_screening_source_rows(
    combined_header: list[str], combined_rows: list[dict[str, str]], paths: dict[str, Path],
) -> None:
    prefix = [
        "integration_schema_version", "screening_source_corpus",
        "screening_source_row_number", "screening_source_row_sha256",
    ]
    base_header, base_rows = read_csv(paths["base_screening"])
    scopus_header, scopus_rows = read_csv(paths["scopus_corrected_decisions"])
    expected_header = union_fields(base_header, scopus_header, prefix=prefix)
    if combined_header != expected_header:
        raise CorrectedIntegrationError("Combined screening source schema changed")
    blocks = (
        ("base_v4", base_header, base_rows),
        ("scopus_increment_corrected", scopus_header, scopus_rows),
    )
    if len(combined_rows) != sum(len(rows) for _, _, rows in blocks):
        raise CorrectedIntegrationError("Combined screening source cardinality changed")
    offset = 0
    for source_name, source_header, source_rows in blocks:
        source_fields = set(source_header)
        unused_union_fields = [
            field for field in combined_header if field not in prefix and field not in source_fields
        ]
        for source_number, source_row in enumerate(source_rows, 1):
            combined = combined_rows[offset]
            offset += 1
            if (
                combined.get("integration_schema_version") != SCHEMA
                or combined.get("screening_source_corpus") != source_name
                or combined.get("screening_source_row_number") != str(source_number)
                or combined.get("screening_source_row_sha256") != row_hash(source_row, source_header)
            ):
                raise CorrectedIntegrationError(
                    f"Combined screening source identity/order/hash changed: "
                    f"{source_name} row {source_number}"
                )
            changed = [
                field for field in source_header
                if combined.get(field, "") != source_row.get(field, "")
            ]
            if changed:
                raise CorrectedIntegrationError(
                    f"Combined screening source protected fields changed: "
                    f"{source_name} row {source_number}: {', '.join(changed)}"
                )
            populated = [
                field for field in unused_union_fields if combined.get(field, "") != ""
            ]
            if populated:
                raise CorrectedIntegrationError(
                    f"Combined screening source-only union fields populated: "
                    f"{source_name} row {source_number}: {', '.join(populated)}"
                )


def validate_package(path: Path) -> dict[str, int]:
    manifest_path, hash_path, frozen_path = path / MANIFEST, path / HASHES, path / FROZEN
    manifest, frozen = load_json(manifest_path), load_json(frozen_path)
    if manifest.get("pipeline") != "corrected_scopus_base_v4_final_integration_20260816" or manifest.get("status") != "frozen_corrected_combined_corpus_analysis_not_performed":
        raise CorrectedIntegrationError("Corrected integration manifest invalid")
    if frozen.get("status") != "frozen" or frozen.get("manifest_sha256") != sha256_file(manifest_path) or frozen.get("hash_manifest_sha256") != sha256_file(hash_path):
        raise CorrectedIntegrationError("FROZEN hashes invalid")
    _, hash_rows = read_csv(hash_path)
    expected = set(OUTPUTS.values()) | {QA, MANIFEST}
    if {row["path"] for row in hash_rows} != expected or len(hash_rows) != len(expected):
        raise CorrectedIntegrationError("Hash ledger coverage invalid")
    for row in hash_rows:
        candidate = path / row["path"]
        if not candidate.is_file() or str(candidate.stat().st_size) != row["bytes"] or sha256_file(candidate) != row["sha256"]:
            raise CorrectedIntegrationError(f"Output tamper: {row['path']}")
    bound_inputs = manifest.get("bound_inputs", {})
    if set(bound_inputs) != REQUIRED_INPUTS:
        raise CorrectedIntegrationError("Corrected bound-input coverage invalid")
    bound_paths = {}
    for key, item in bound_inputs.items():
        candidate = Path(item["path"])
        if not candidate.is_file() or sha256_file(candidate) != item["sha256"]:
            raise CorrectedIntegrationError(f"Bound current byte changed: {key}")
        bound_paths[key] = candidate
    validate_authorities(bound_paths)
    counts = {key: int(value) for key, value in manifest["derived_counts"].items()}
    expected_counts = {
        "version_ledger": ("eligible_publication_records", 547), "selection": ("unique_studies", 485),
        "extraction": ("canonical_extraction_rows", 485), "metadata": ("canonical_metadata_rows", 485),
        "openalex": ("canonical_openalex_rows", 485), "screening": ("combined_screening_rows", 3919),
    }
    loaded = {}
    for key, (count_key, expected_count) in expected_counts.items():
        header, rows = read_csv(path / OUTPUTS[key])
        loaded[key] = (header, rows)
        if len(rows) != expected_count or len(rows) != counts[count_key]:
            raise CorrectedIntegrationError(f"Corrected output count invalid: {key}")
    version = loaded["version_ledger"][1]
    if version != sorted(version, key=lambda row: (row["provisional_family_id"], row["record_key"])) or any(row.get("source_record_id") == REMOVED_PAPER_ID or row.get("provisional_family_id") == REMOVED_FAMILY_ID for row in version):
        raise CorrectedIntegrationError("Version ledger order/removal invariant invalid")
    if Counter(row["source_corpus"] for row in version) != {"base_eligible_v4": 517, "scopus_increment": 30}:
        raise CorrectedIntegrationError("Version ledger source cardinality invalid")
    by_family = defaultdict(list)
    for row in version:
        by_family[row["provisional_family_id"]].append(row)
    if len(by_family) != 485:
        raise CorrectedIntegrationError("Version ledger family cardinality invalid")
    for family_id, members in by_family.items():
        preferred = [row for row in members if row["preferred_for_analysis"].casefold() == "yes"]
        if len(preferred) != 1 or {row["preferred_record_key"] for row in members} != {preferred[0]["record_key"]}:
            raise CorrectedIntegrationError(f"Version ledger preferred invariant invalid: {family_id}")
    base_path = Path(manifest["bound_inputs"]["base_version"]["path"])
    _, base_rows = read_csv(base_path)
    prior_groups, final_groups = defaultdict(set), defaultdict(set)
    for row in base_rows:
        prior_groups[row["version_family_id"]].add(row["paper_id"])
    for row in version:
        if row["source_corpus"] == "base_eligible_v4":
            final_groups[row["provisional_family_id"]].add(row["source_record_id"])
    if len(prior_groups) != 458 or len(final_groups) != 458 or set(map(frozenset, prior_groups.values())) != set(map(frozenset, final_groups.values())):
        raise CorrectedIntegrationError("Validated output does not preserve exact 458 base family member sets")
    selection = loaded["selection"][1]
    if selection != sorted(selection, key=lambda row: (row["final_version_family_id"], row["preferred_record_key"])):
        raise CorrectedIntegrationError("Selection order invalid")
    selected_ids = [row["final_version_family_id"] for row in selection]
    for key in ("extraction", "metadata", "openalex"):
        if [row["final_version_family_id"] for row in loaded[key][1]] != selected_ids:
            raise CorrectedIntegrationError(f"Canonical {key} family/order invalid")
    decisions = Counter(row["final_decision"] for row in loaded["screening"][1])
    if decisions != {"INCLUDE": 547, "EXCLUDE": 3372}:
        raise CorrectedIntegrationError("Combined screening decision counts invalid")
    validate_combined_screening_source_rows(
        loaded["screening"][0], loaded["screening"][1], bound_paths
    )
    qa = load_json(path / QA)
    if qa.get("status") != "PASS" or qa.get("counts") != counts:
        raise CorrectedIntegrationError("QA artifact invalid")
    return counts


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("integrate")
    command.add_argument("--bindings", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = sub.add_parser("validate")
    command.add_argument("--package", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = integrate(args.bindings, args.output) if args.command == "integrate" else validate_package(args.package)
    except (CorrectedIntegrationError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
