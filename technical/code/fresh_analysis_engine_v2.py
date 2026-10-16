#!/usr/bin/env python3
"""Generate the prespecified fresh-August V2 analysis from locked inputs.

This is a new, data-agnostic engine.  It does not call the March analysis,
does not query a network service, and never modifies an input package.  Every
run validates the complete upstream hash/status chain that it consumes, builds
in a temporary sibling directory, and atomically renames a new output only
after a final input-hash recheck.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import itertools
import json
import math
import os
import re
import shutil
import sys
import tempfile
import textwrap
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PIPELINE_DIR = Path(__file__).resolve().parent
ACTIVE_ROOT = PIPELINE_DIR.parent
BUNDLED_DEPENDENCIES = ACTIVE_ROOT / "99_QA" / "python_deps"
if BUNDLED_DEPENDENCIES.is_dir() and str(BUNDLED_DEPENDENCIES) not in sys.path:
    sys.path.insert(0, str(BUNDLED_DEPENDENCIES))

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError as exc:  # pragma: no cover - exercised only in a bad runtime
    raise RuntimeError(
        "Fresh analysis figures require the bundled Python 3.12 runtime and "
        f"dependencies at {BUNDLED_DEPENDENCIES}"
    ) from exc

from compare_fresh_independent_reviews_v2 import COMPARISON_FIELDS
from compute_fresh_review_agreement_v2 import (
    VALID_DECISIONS as AGREEMENT_DECISIONS,
    analyse as analyse_agreement,
)
from finalize_fresh_screening_v2 import FINAL_FIELDS, HUMAN_AUDIT_LINK_FIELDS
from fresh_screening_review_common_v2 import MASTER_FIELDS
from fresh_work_level_extraction_v2 import (
    BINDING_FIELDS as EXTRACTION_BINDING_FIELDS,
    CHECKED_CORPUS_FIELDS,
    CHECKED_CORPUS,
    EXTRACTION_FIELDS,
    FINALIZATION_FROZEN_MARKER as EXTRACTION_FROZEN_MARKER,
    FINALIZATION_HASH_LEDGER as EXTRACTION_HASH_LEDGER,
    FINALIZATION_MANIFEST as EXTRACTION_MANIFEST,
    FINALIZATION_SUMMARY as EXTRACTION_SUMMARY,
    FINALIZE_PIPELINE as EXTRACTION_PIPELINE,
    FINAL_STATUS as EXTRACTION_STATUS,
    SOURCE_CORPUS_FIELDS,
)
from apply_fresh_metadata_corrections_v2 import (
    AUDIT_COLUMNS as METADATA_AUDIT_FIELDS,
    LEDGER_COLUMNS as METADATA_LEDGER_FIELDS,
    apply_corrections as apply_metadata_corrections,
    load_corrections as load_metadata_corrections,
)


SCHEMA_VERSION = "fresh-analysis-engine-v2.0"
PIPELINE = "fresh_august_prespecified_analysis_v2"
FINAL_STATUS = "fresh_august_analysis_v2_completed_hash_frozen"
SCREENING_FINAL_STATUS = (
    "record_level_screening_finalized_human_audit_deferred_"
    "pending_systematic_version_review"
)
HUMAN_AUDIT_DISPLAY = "not performed\N{EM DASH}deferred"
REVIEWED_METADATA_FIELDS = ("doi", "year", "publication_date")

DEFAULT_ANALYSIS_SPEC = (
    ACTIVE_ROOT / "06_AUDIT" / "FRESH_ANALYSIS_SPECIFICATION_V2_2026-08-14.json"
)
DEFAULT_AMENDMENT = (
    ACTIVE_ROOT
    / "06_AUDIT"
    / "FRESH_ANALYSIS_SPECIFICATION_V2_AMENDMENT_001_HUMAN_AUDIT_DEFERRAL_2026-08-14.json"
)
DEFAULT_CLARIFICATION = (
    ACTIVE_ROOT
    / "06_AUDIT"
    / "PROSPECTIVE_HUMAN_AUDIT_DEFERRAL_CLARIFICATION_2026-08-14.md"
)
DEFAULT_AMENDMENT_002 = (
    ACTIVE_ROOT
    / "06_AUDIT"
    / "FRESH_ANALYSIS_SPECIFICATION_V2_AMENDMENT_002_SENSITIVITY_RULES_2026-08-14.json"
)
DEFAULT_AMENDMENT_003 = (
    ACTIVE_ROOT
    / "06_AUDIT"
    / "FRESH_ANALYSIS_SPECIFICATION_V2_AMENDMENT_003_TIMESTAMP_CORRECTION_2026-08-14.json"
)
DEFAULT_INPUT_CONTRACT = (
    PIPELINE_DIR / "FRESH_ANALYSIS_INPUT_CONTRACT_V2_2_2026-08-14.json"
)
LOCKED_AUTHORITY_HASHES = {
    "analysis_specification": "db0b4354352e684768734ecc7c547708642e9a4037bef74ad0b0ac1350aa804d",
    "amendment_001": "aca5d00091a9aab220d1ce0c1f4435fa19f90d7d7f452149f24e3b20ae9b9465",
    "human_audit_clarification": "b0a675410717e9136f3925790100ac1cbbb7a7878c16951e6dcff306c4c72584",
    "amendment_002": "22a45d87f623944bace2530dbd11def03776b44716584e48c8fcb6d76c79f3f5",
    "amendment_003": "8203ea9c3e04c8759dfe71729c3fd8c612143e15d9a43eff7e7d72889ebcd2df",
    "input_contract": "06b8c24b5239a50dd82ea208594998805b3676dfbe25f5c3bf05d20c1a4849d9",
}
LOCKED_SUPPORT_PROGRAM_HASHES = {
    "compute_fresh_review_agreement_v2.py": "b91a9e5d8f52e3203806f373365c31901a4a2836706bbe94e5cbabcbe560b1d3",
    "apply_fresh_metadata_corrections_v2.py": "1c1d52f2c3d669e0dbf349e2ded6a91f19f846fefeec3184810efb587aa4d842",
}

# Reference pins document the fresh production packages that were available
# when this engine was written.  They are not used to make synthetic fixtures
# look like production and do not replace dynamic manifest/hash validation.
FRESH_REFERENCE_INPUTS = {
    "metadata_corrected_corpus": {
        "path": "GSE_FULL_RERUN_2026-08-13/09A_METADATA_CORRECTED/canonical_metadata_run01/ONE_WORK_ANALYSIS_CORPUS_METADATA_CORRECTED_V2.csv",
        "sha256": "6a5d4f5ec3e24421288bc82ccfdd47fea048e13e7c6d33ed1f8679f491035062",
        "rows": 470,
        "source_corpus_sha256": "14f699562b600935668faa087f5fb83ccce06a0d6db36fcdfec20fe29f0ec675",
    },
    "openalex_locked": {
        "path": "GSE_FULL_RERUN_2026-08-13/11_OPENALEX_FIXED_SNAPSHOT/openalex_run01/OPENALEX_LOCKED.csv",
        "sha256": "082ba7a66e42b27de51190f41115719ebc32a773757eba7205f680c339a9e315",
        "rows": 470,
        "matched": 468,
        "unmatched": 2,
        "locked_at_utc": "2026-08-14T21:02:52+00:00",
        "snapshot_fingerprint": "d19d351979fa85ba96c6e9c5a8de3d868a89c946d6152ab1d3d863abb391d444",
    },
}


def validate_fresh_reference_pins(
    metadata: Mapping[str, Any], openalex: Mapping[str, Any]
) -> None:
    """Hard-gate a production run to the reviewed August reference packages."""

    workspace = ACTIVE_ROOT.parent.resolve()
    metadata_pin = FRESH_REFERENCE_INPUTS["metadata_corrected_corpus"]
    expected_metadata = (workspace / metadata_pin["path"]).resolve()
    if (
        metadata["corrected_path"].resolve() != expected_metadata
        or metadata["corrected_sha256"] != metadata_pin["sha256"]
        or metadata["source_sha256"] != metadata_pin["source_corpus_sha256"]
        or len(metadata["rows"]) != metadata_pin["rows"]
    ):
        raise FreshAnalysisError(
            "Production metadata input does not match the reviewed fresh-August reference pin"
        )
    openalex_pin = FRESH_REFERENCE_INPUTS["openalex_locked"]
    expected_openalex = (workspace / openalex_pin["path"]).resolve()
    if (
        openalex["locked_path"].resolve() != expected_openalex
        or sha256_file(openalex["locked_path"]) != openalex_pin["sha256"]
        or len(openalex["rows"]) != openalex_pin["rows"]
        or openalex["matched"] != openalex_pin["matched"]
        or openalex["unmatched"] != openalex_pin["unmatched"]
        or openalex["report"].get("generated_utc") != openalex_pin["locked_at_utc"]
        or openalex["report"].get("snapshot_fingerprint")
        != openalex_pin["snapshot_fingerprint"]
    ):
        raise FreshAnalysisError(
            "Production OpenAlex input does not match the reviewed fresh-August reference pin"
        )

OUTPUT_MANIFEST = "FRESH_ANALYSIS_OUTPUT_MANIFEST_V2.json"
OUTPUT_HASH_LEDGER = "FRESH_ANALYSIS_HASH_MANIFEST_V2.csv"
OUTPUT_FROZEN_MARKER = "FRESH_ANALYSIS_FROZEN_V2.json"
OUTPUT_SUMMARY = "FRESH_ANALYSIS_SUMMARY_V2.json"

HASH_FIELDS = ["scope", "path", "role", "bytes", "sha256"]
OPENALEX_FIELDS = [
    "paper_id",
    "input_doi",
    "resolution_doi",
    "version_override_applied",
    "input_title",
    "input_year",
    "match_status",
    "match_method",
    "title_similarity",
    "second_best_title_similarity",
    "title_similarity_margin",
    "year_difference",
    "openalex_id",
    "openalex_doi",
    "openalex_title",
    "publication_year",
    "publication_date",
    "language",
    "work_type",
    "work_type_crossref",
    "cited_by_count",
    "is_retracted",
    "is_paratext",
    "is_oa",
    "oa_status",
    "oa_url",
    "any_repository_has_fulltext",
    "best_oa_landing_page_url",
    "best_oa_pdf_url",
    "authors_count",
    "authors_json",
    "country_codes",
    "institution_ids",
    "institution_names",
    "counts_by_year_json",
    "topics_json",
    "keywords_json",
    "locations_count",
    "source_id",
    "source_name",
    "source_issn_l",
    "source_issn",
    "source_type",
    "publisher",
]

AGREEMENT_TABLE_FIELDS = [
    "section",
    "measure",
    "category",
    "numerator",
    "denominator",
    "estimate",
    "ci_lower",
    "ci_upper",
    "ci_level",
    "ci_method",
    "denominator_definition",
    "response_type",
    "value_text",
    "note",
]
DESCRIPTIVE_TABLE_FIELDS = [
    "section",
    "measure",
    "category",
    "count",
    "denominator",
    "percent",
    "value",
    "value_text",
    "unit",
    "denominator_definition",
    "response_type",
    "work_ids",
    "note",
]
PHRASE_TABLE_FIELDS = [
    "section",
    "measure",
    "category",
    "count",
    "denominator",
    "percent",
    "title_count",
    "abstract_count",
    "keyword_count",
    "value",
    "value_text",
    "unit",
    "denominator_definition",
    "response_type",
    "work_ids",
    "note",
]

COUNTRY_DISPLAY_NAMES = {
    "US": "United States",
    "CN": "China",
    "GB": "United Kingdom",
    "AU": "Australia",
    "KR": "South Korea",
    "DE": "Germany",
    "JP": "Japan",
    "IN": "India",
    "CA": "Canada",
    "ES": "Spain",
}
EXCLUSION_CODE_LABELS = {
    "E1_NOT_LLM": "No explicit large or generative language model",
    "E2_NOT_HEALTH_ED": "Not health-professions education, training or assessment",
    "E3_NOT_SIMULATION": "Simulation-based education absent or peripheral",
    "E4_CLINICAL_ONLY": "Clinical use without a simulation-training purpose",
    "E5_INELIGIBLE_TYPE": "Ineligible or inadequately reported publication type",
    "E6_OUT_OF_RANGE": "Outside the date range",
    "E7_NOT_ASSESSABLE_IN_ENGLISH": "Not assessable from available English information",
    "E9_OTHER": "Other stated reason",
}

OA_CATEGORIES = ["gold", "green", "hybrid", "bronze", "diamond", "closed", "unknown"]
PROTECTED_ROOT_NAMES = {
    "old_archive",
    "current_gse",
    "journal_route",
    "other_copies",
    "publisher",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


class FreshAnalysisError(RuntimeError):
    """Raised when an input or output violates the locked analysis contract."""


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FreshAnalysisError(f"Missing {label}: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise FreshAnalysisError(f"Invalid {label}: {path}") from exc
    if not isinstance(value, dict):
        raise FreshAnalysisError(f"{label} must be a JSON object: {path}")
    return value


def safe_relative(root: Path, value: Any, label: str) -> Path:
    raw = Path(clean(value))
    if not clean(value) or raw.is_absolute() or ".." in raw.parts:
        raise FreshAnalysisError(f"Unsafe {label} path: {value!r}")
    target = (root / raw).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise FreshAnalysisError(f"{label} path escapes package: {value!r}") from exc
    return target


def read_csv_exact(
    path: Path, expected_fields: Sequence[str] | None = None
) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            rows = list(reader)
    except OSError as exc:
        raise FreshAnalysisError(f"Cannot read CSV: {path}") from exc
    if expected_fields is not None and fields != list(expected_fields):
        raise FreshAnalysisError(
            f"{path}: unexpected CSV schema/order; expected {list(expected_fields)}, "
            f"observed {fields}"
        )
    for number, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            raise FreshAnalysisError(f"{path}:{number}: malformed CSV row")
    return fields, rows


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="raise")
        writer.writeheader()
        for raw in rows:
            row: dict[str, Any] = {}
            for field in fields:
                value = raw.get(field, "")
                if value is None:
                    value = ""
                elif isinstance(value, bool):
                    value = "true" if value else "false"
                elif isinstance(value, (list, dict)):
                    value = canonical_json(value)
                row[field] = value
            writer.writerow(row)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool):
        raise FreshAnalysisError(f"{label} is not an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise FreshAnalysisError(f"{label} is not an integer: {value!r}") from exc
    if str(parsed) != clean(value) and not isinstance(value, int):
        raise FreshAnalysisError(f"{label} is not an exact integer: {value!r}")
    if parsed < minimum:
        raise FreshAnalysisError(f"{label} must be at least {minimum}")
    return parsed


def percent(count: int | float, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    value = 100.0 * float(count) / denominator
    if value != 0.0 and round(value, 1) == 0.0:
        return value
    return round(value, 1)


def validate_entry(root: Path, entry: Mapping[str, Any], label: str) -> Path:
    if not isinstance(entry, Mapping):
        raise FreshAnalysisError(f"Missing manifested {label}")
    path = safe_relative(root, entry.get("path"), label)
    if not path.is_file():
        raise FreshAnalysisError(f"Missing manifested {label}: {path}")
    expected_hash = clean(entry.get("sha256")).casefold()
    if not SHA256_RE.fullmatch(expected_hash):
        raise FreshAnalysisError(f"Invalid manifested SHA-256 for {label}")
    expected_bytes = integer(entry.get("bytes"), f"{label} byte count")
    if path.stat().st_size != expected_bytes or sha256_file(path) != expected_hash:
        raise FreshAnalysisError(f"Manifested {label} is stale or tampered: {path}")
    return path


def validate_hash_ledger(
    root: Path,
    filename: str,
    *,
    required_output_paths: Iterable[str] = (),
) -> tuple[Path, list[dict[str, str]], list[Path]]:
    path = root / filename
    _fields, rows = read_csv_exact(path, HASH_FIELDS)
    seen: set[tuple[str, str, str]] = set()
    outputs: set[str] = set()
    bound: list[Path] = [path]
    for row in rows:
        key = (row["scope"], row["path"], row["role"])
        if key in seen:
            raise FreshAnalysisError(f"{path}: duplicate hash-ledger row {key}")
        seen.add(key)
        if not SHA256_RE.fullmatch(row["sha256"]):
            raise FreshAnalysisError(f"{path}: invalid SHA-256 for {row['path']}")
        expected_bytes = integer(row["bytes"], f"{path}/{row['path']} bytes")
        if row["scope"] != "output":
            continue
        normalized = row["path"].replace("\\", "/")
        target = safe_relative(root, normalized, "hash-ledger output")
        if not target.is_file():
            raise FreshAnalysisError(f"Hash-ledger target is missing: {target}")
        if target.stat().st_size != expected_bytes or sha256_file(target) != row["sha256"]:
            raise FreshAnalysisError(f"Hash-ledger output is stale or tampered: {target}")
        outputs.add(normalized)
        bound.append(target)
    required = {item.replace("\\", "/") for item in required_output_paths}
    if not required <= outputs:
        raise FreshAnalysisError(
            f"{path}: required output hashes missing: {sorted(required - outputs)}"
        )
    return path, rows, bound


def add_binding(bindings: dict[str, str], path: Path) -> None:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FreshAnalysisError(f"Binding target is missing: {resolved}")
    observed = sha256_file(resolved)
    prior = bindings.get(str(resolved))
    if prior is not None and prior != observed:
        raise FreshAnalysisError(f"Conflicting input binding: {resolved}")
    bindings[str(resolved)] = observed


def verify_bindings(bindings: Mapping[str, str]) -> None:
    for raw, expected in bindings.items():
        path = Path(raw)
        if not path.is_file() or sha256_file(path) != expected:
            raise FreshAnalysisError(f"Input changed during analysis: {path}")


def validate_authorities(
    spec_path: Path, amendment_path: Path, clarification_path: Path
) -> tuple[dict[str, Any], dict[str, Any], list[Path]]:
    paths = [
        spec_path.resolve(),
        amendment_path.resolve(),
        clarification_path.resolve(),
        DEFAULT_AMENDMENT_002.resolve(),
        DEFAULT_AMENDMENT_003.resolve(),
        DEFAULT_INPUT_CONTRACT.resolve(),
    ]
    keys = [
        "analysis_specification",
        "amendment_001",
        "human_audit_clarification",
        "amendment_002",
        "amendment_003",
        "input_contract",
    ]
    for key, path in zip(keys, paths, strict=True):
        if not path.is_file():
            raise FreshAnalysisError(f"Missing locked authority: {path}")
        if sha256_file(path) != LOCKED_AUTHORITY_HASHES[key]:
            raise FreshAnalysisError(f"Locked authority SHA-256 mismatch: {path}")
    for filename, expected in LOCKED_SUPPORT_PROGRAM_HASHES.items():
        program = PIPELINE_DIR / filename
        if not program.is_file() or sha256_file(program) != expected:
            raise FreshAnalysisError(f"Locked support program SHA-256 mismatch: {program}")
    spec = load_json(paths[0], "analysis specification")
    amendment = load_json(paths[1], "analysis amendment")
    amendment_002 = load_json(paths[3], "fresh analysis sensitivity amendment")
    amendment_003 = load_json(paths[4], "fresh analysis timestamp correction")
    input_contract = load_json(paths[5], "fresh analysis input contract")
    if (
        spec.get("schema_version") != "2.0"
        or spec.get("specification_id") != "gse_fresh_analysis_v2_2026-08-14"
        or spec.get("status")
        != "prespecified_before_final_screening_and_outcome_analysis"
    ):
        raise FreshAnalysisError("Locked analysis specification identity/status changed")
    change = amendment.get("change") or {}
    reporting = amendment.get("reporting_contracts") or {}
    if (
        amendment.get("amendment_id")
        != "gse_fresh_analysis_v2_amendment_001_human_audit_deferral"
        or change.get("prospective_human_audit_for_this_revision")
        != "deferred_by_corresponding_author"
        or change.get("accepted_record_finalization_status") != SCREENING_FINAL_STATUS
        or reporting.get("human_audit_result_display") != "not_performed_deferred"
        or reporting.get("fresh_boundary_negative_sample_completed") is not False
    ):
        raise FreshAnalysisError("Amendment 001 deferral contract changed")
    clarification = paths[2].read_text(encoding="utf-8-sig")
    required_clarification = (
        "No prospective human review",
        "not imply that a human checked",
        "will not be used as validation",
    )
    if any(text not in clarification for text in required_clarification):
        raise FreshAnalysisError("Human-audit clarification content changed")
    sensitivity_change = amendment_002.get("change") or {}
    if (
        amendment_002.get("amendment_id")
        != "gse_fresh_analysis_v2_amendment_002_sensitivity_rules"
        or amendment_002.get("whether_outcome_counts_seen") is not True
        or amendment_002.get("primary_corpus_or_primary_counts_changed") is not False
        or "family_size is 1" not in clean(
            sensitivity_change.get("standalone_preprint_or_repository_only_rule")
        )
        or "doi_exact or openalex_id_exact" not in clean(
            sensitivity_change.get("exact_identifier_metadata_rule")
        )
    ):
        raise FreshAnalysisError("Sensitivity-rule amendment changed")
    corrected_authority = amendment_003.get("corrected_authority") or {}
    if (
        amendment_003.get("amendment_id")
        != "gse_fresh_analysis_v2_amendment_003_timestamp_correction"
        or amendment_003.get("classification")
        != "provenance_correction_before_replacement_final_run"
        or amendment_003.get("supersedes_no_scientific_rule") is not True
        or amendment_003.get("primary_corpus_or_primary_counts_changed") is not False
        or amendment_003.get("sensitivity_rules_changed") is not False
        or corrected_authority.get("sha256") != LOCKED_AUTHORITY_HASHES["amendment_002"]
        or corrected_authority.get("filesystem_creation_utc") != "2026-08-14T22:10:25Z"
        or corrected_authority.get("first_analysis_run_using_it_utc") != "2026-08-14T22:19:40Z"
    ):
        raise FreshAnalysisError("Sensitivity timestamp-correction amendment changed")
    contract_authorities = input_contract.get("analysis_authorities") or {}
    contract_metadata = input_contract.get("metadata_correction") or {}
    contract_openalex = input_contract.get("openalex") or {}
    contract_extraction = input_contract.get("checked_extraction") or {}
    contract_versions = input_contract.get("publication_version_consolidation") or {}
    if (
        input_contract.get("status")
        != "production_input_chain_finalized_ready_for_analysis"
        or input_contract.get("schema_version") != "fresh-analysis-input-contract-v2.2"
        or input_contract.get("contract_id")
        != "gse_fresh_august_analysis_input_freeze_v2_2_2026-08-14"
        or input_contract.get("production_run_performed_at_contract_freeze") is not False
        or (contract_authorities.get("sensitivity_timestamp_correction") or {}).get("sha256")
        != LOCKED_AUTHORITY_HASHES["amendment_003"]
        or contract_extraction.get("checked_corpus_sha256")
        != "fc27f8a76145b41ea7a33770e31facd6e57a6b18121a6d1d057fbaaf286f55dd"
        or contract_extraction.get("rows") != 470
        or contract_extraction.get("human_reference_standard_available") is not False
        or contract_versions.get("manifest_sha256")
        != "61805ac471f377f8e16181f57fd0594f800f14b9952890ead9b15b4dd9d83cc1"
        or contract_versions.get("eligible_version_ledger_sha256")
        != "c0b7a570ee7290cc1c639eda6880fb7e6f43b736de5b4f379ddda5f8597612c7"
        or contract_versions.get("eligible_publication_records") != 530
        or contract_versions.get("unique_studies") != 470
        or contract_metadata.get("corrected_sha256")
        != FRESH_REFERENCE_INPUTS["metadata_corrected_corpus"]["sha256"]
        or contract_metadata.get("source_corpus_sha256")
        != FRESH_REFERENCE_INPUTS["metadata_corrected_corpus"]["source_corpus_sha256"]
        or contract_openalex.get("locked_sha256")
        != FRESH_REFERENCE_INPUTS["openalex_locked"]["sha256"]
        or contract_openalex.get("locked_at_utc")
        != FRESH_REFERENCE_INPUTS["openalex_locked"]["locked_at_utc"]
        or contract_openalex.get("snapshot_fingerprint")
        != FRESH_REFERENCE_INPUTS["openalex_locked"]["snapshot_fingerprint"]
        or contract_openalex.get("march_snapshot_allowed") is not False
    ):
        raise FreshAnalysisError("Fresh analysis input contract changed")
    uncertainty = spec.get("uncertainty") or {}
    raw_ci = uncertainty.get("model_raw_agreement_ci") or {}
    kappa_ci = uncertainty.get("model_kappa_ci") or {}
    if (
        raw_ci != {"method": "wilson", "level": 0.95}
        or kappa_ci.get("method") != "record_level_percentile_bootstrap"
        or kappa_ci.get("replicates") != 10_000
        or kappa_ci.get("seed") != 2026081306
        or kappa_ci.get("level") != 0.95
    ):
        raise FreshAnalysisError("Prespecified agreement uncertainty contract changed")
    window = spec.get("study_window") or {}
    if (
        window.get("from") != "2020-01-01"
        or window.get("through") != "2026-08-13"
        or window.get("inclusive") is not True
        or window.get("complete_calendar_years") != list(range(2020, 2026))
        or (window.get("partial_period") or {}).get("year") != 2026
    ):
        raise FreshAnalysisError("Prespecified study window changed")
    return spec, amendment, paths


def validate_raw_manifests(
    manifest_paths: Sequence[Path], *, synthetic_test_mode: bool
) -> dict[str, Any]:
    if not manifest_paths:
        raise FreshAnalysisError("At least one raw collector run manifest is required")
    run_ids: set[str] = set()
    sources: Counter[str] = Counter()
    retrieval_occurrences = 0
    bindings: dict[str, str] = {}
    manifests: list[dict[str, Any]] = []
    for raw_path in manifest_paths:
        path = raw_path.resolve()
        root = path.parent
        manifest = load_json(path, "raw collector run manifest")
        run_id = clean(manifest.get("run_id"))
        if not run_id or run_id in run_ids:
            raise FreshAnalysisError("Raw manifests require distinct nonblank run IDs")
        run_ids.add(run_id)
        if manifest.get("schema_version") != "1.0":
            raise FreshAnalysisError(f"Unsupported raw manifest schema: {path}")
        allowed_modes = {"snapshot", "synthetic_test"} if synthetic_test_mode else {"snapshot"}
        if manifest.get("mode") not in allowed_modes or manifest.get("run_status") != "completed":
            raise FreshAnalysisError(f"Raw collector input is not a completed snapshot: {path}")
        if integer(manifest.get("query_errors"), f"{path} query_errors") != 0:
            raise FreshAnalysisError(f"Raw collector input has query errors: {path}")
        if manifest.get("frozen_source_modified") is not False:
            raise FreshAnalysisError(f"Raw collector reports a modified frozen source: {path}")
        credential = manifest.get("credential_policy") or {}
        if credential.get("values_written_to_outputs") is not False:
            raise FreshAnalysisError(f"Raw collector credential-output contract failed: {path}")
        selected = manifest.get("selected_sources")
        if not isinstance(selected, list) or not selected or any(not clean(x) for x in selected):
            raise FreshAnalysisError(f"Raw collector selected_sources is invalid: {path}")
        result_map = manifest.get("source_results") or {}
        if not isinstance(result_map, Mapping):
            raise FreshAnalysisError(f"Raw collector source_results is invalid: {path}")
        run_records = 0
        for source in selected:
            result = result_map.get(source) or {}
            if integer(result.get("errors", 0), f"{path}/{source} errors") != 0:
                raise FreshAnalysisError(f"Raw collector source has errors: {path}/{source}")
            queries = result.get("queries") or []
            if not isinstance(queries, list):
                raise FreshAnalysisError(f"Raw collector queries are invalid: {path}/{source}")
            observed_source_records = 0
            for query in queries:
                if not isinstance(query, Mapping) or query.get("status") == "error":
                    raise FreshAnalysisError(f"Raw collector query failed: {path}/{source}")
                records = integer(
                    query.get("records_written"), f"{path}/{source} records_written"
                )
                raw_file = safe_relative(root, query.get("raw_file"), "raw query file")
                if not raw_file.is_file() or sha256_file(raw_file) != clean(
                    query.get("raw_file_sha256")
                ).casefold():
                    raise FreshAnalysisError(f"Raw query file is stale or tampered: {raw_file}")
                with raw_file.open("r", encoding="utf-8-sig") as handle:
                    observed_lines = sum(bool(line.strip()) for line in handle)
                if observed_lines != records:
                    raise FreshAnalysisError(f"Raw query record count mismatch: {raw_file}")
                add_binding(bindings, raw_file)
                observed_source_records += records
            if integer(
                result.get("records_written", observed_source_records),
                f"{path}/{source} source records",
            ) != observed_source_records:
                raise FreshAnalysisError(f"Raw source record count mismatch: {path}/{source}")
            sources[source] += observed_source_records
            run_records += observed_source_records
        provenance = manifest.get("provenance_files") or {}
        for key in ("queries", "requests"):
            entry = provenance.get(key) or {}
            target = safe_relative(root, entry.get("path"), f"raw provenance {key}")
            if not target.is_file() or sha256_file(target) != clean(entry.get("sha256")).casefold():
                raise FreshAnalysisError(f"Raw provenance is stale or tampered: {target}")
            add_binding(bindings, target)
        plan_copy = root / "search_plan_used.json"
        if not plan_copy.is_file():
            raise FreshAnalysisError(f"Raw snapshot lacks search_plan_used.json: {root}")
        plan = load_json(plan_copy, "saved raw search plan")
        window = plan.get("study_window") or {}
        if (
            window.get("from") != "2020-01-01"
            or window.get("through") != "2026-08-13"
            or window.get("inclusive") is not True
        ):
            raise FreshAnalysisError(f"Raw snapshot study window is stale: {plan_copy}")
        plan_entry = manifest.get("plan") or {}
        plan_claim = clean(plan_entry.get("sha256")).casefold()
        plan_source_text = clean(plan_entry.get("path"))
        saved_plan_hash = sha256_file(plan_copy)
        if plan_source_text:
            plan_source = Path(plan_source_text)
            if not plan_source.is_absolute():
                plan_source = (root / plan_source).resolve()
            if not plan_source.is_file():
                raise FreshAnalysisError(
                    f"Collector-claimed source search plan is missing: {plan_source}"
                )
            if not plan_claim or sha256_file(plan_source) != plan_claim:
                raise FreshAnalysisError(
                    f"Collector-claimed source search plan hash mismatch: {plan_source}"
                )
            source_plan = load_json(plan_source, "collector source search plan")
            if canonical_json(source_plan) != canonical_json(plan):
                raise FreshAnalysisError(
                    f"Saved raw search plan is not semantically identical to its source: {plan_copy}"
                )
            add_binding(bindings, plan_source)
        elif plan_claim and saved_plan_hash != plan_claim:
            raise FreshAnalysisError(f"Saved raw search plan hash mismatch: {plan_copy}")
        add_binding(bindings, plan_copy)
        add_binding(bindings, path)
        retrieval_occurrences += run_records
        manifests.append(manifest)
    return {
        "run_ids": sorted(run_ids),
        "retrieval_occurrences": retrieval_occurrences,
        "by_source": dict(sorted(sources.items())),
        "manifests": manifests,
        "bindings": bindings,
    }


def count_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8-sig") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FreshAnalysisError(f"Invalid JSONL at {path}:{number}") from exc
            if not isinstance(value, dict):
                raise FreshAnalysisError(f"Expected JSON object at {path}:{number}")
            count += 1
    return count


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration as exc:
            raise FreshAnalysisError(f"CSV is empty: {path}") from exc
        return sum(1 for _row in reader)


def validate_normalization(
    root_value: Path, raw: Mapping[str, Any], *, synthetic_test_mode: bool
) -> dict[str, Any]:
    root = root_value.resolve()
    manifest_path = root / "normalization_manifest.json"
    manifest = load_json(manifest_path, "normalization manifest")
    if manifest.get("schema_version") != "1.0":
        raise FreshAnalysisError("Unsupported normalization schema")
    readiness = manifest.get("integration_readiness") or {}
    if readiness.get("status") not in {"ready_for_deduplication", "requires_cap_disclosure"}:
        raise FreshAnalysisError("Normalization is incomplete or not analysis-ready")
    window = manifest.get("search_plan", {}).get("study_window") or {}
    if (
        window.get("from") != "2020-01-01"
        or window.get("through") != "2026-08-13"
        or window.get("inclusive") is not True
    ):
        raise FreshAnalysisError("Normalization study window is stale")
    provenance = manifest.get("provenance_contract") or {}
    if provenance.get("credential_values_written") is not False:
        raise FreshAnalysisError("Normalization credential provenance contract failed")
    outputs = manifest.get("outputs") or {}
    jsonl = validate_entry(root, outputs.get("normalized_jsonl") or {}, "normalized JSONL")
    csv_path = validate_entry(root, outputs.get("normalized_csv") or {}, "normalized CSV")
    hash_path, _ledger, bound = validate_hash_ledger(
        root,
        "NORMALIZATION_HASH_MANIFEST.csv",
        required_output_paths=(jsonl.name, csv_path.name, manifest_path.name),
    )
    count = count_jsonl(jsonl)
    counts = manifest.get("counts") or {}
    if integer(counts.get("retrieval_occurrences"), "normalized retrieval occurrences") != count:
        raise FreshAnalysisError("Normalization retrieval count mismatch")
    if count != raw["retrieval_occurrences"]:
        raise FreshAnalysisError(
            "Raw collector and normalization retrieval-occurrence counts disagree"
        )
    snapshot = manifest.get("input_snapshot") or {}
    if manifest.get("artifact_type") == "normalized_snapshot_union":
        observed_runs = set(snapshot.get("constituent_run_ids") or [])
    else:
        observed_runs = {clean(snapshot.get("run_id"))}
        raw_hash = clean(snapshot.get("run_manifest_sha256")).casefold()
        matching = [
            path for path in raw["bindings"] if Path(path).name == "run_manifest.json"
        ]
        if raw_hash and raw_hash not in {raw["bindings"][item] for item in matching}:
            raise FreshAnalysisError("Normalization is bound to a different raw manifest")
    if observed_runs != set(raw["run_ids"]):
        raise FreshAnalysisError("Normalization and supplied raw run IDs disagree")
    bindings: dict[str, str] = {}
    for path in [manifest_path, jsonl, csv_path, hash_path, *bound]:
        add_binding(bindings, path)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "retrieval_occurrences": count,
        "counts": counts,
        "bindings": bindings,
    }


def _validate_dedup_manifest_files(root: Path, manifest: Mapping[str, Any]) -> list[Path]:
    outputs = manifest.get("outputs") or {}
    required_keys = ("deduplicated_jsonl", "deduplicated_csv", "merge_ledger", "review_queue")
    paths = [validate_entry(root, outputs.get(key) or {}, f"deduplication {key}") for key in required_keys]
    manifest_path = root / "DEDUPLICATION_MANIFEST.json"
    hash_path, _rows, bound = validate_hash_ledger(
        root,
        "DEDUPLICATION_HASH_MANIFEST.csv",
        required_output_paths=tuple(path.name for path in paths) + (manifest_path.name,),
    )
    return [manifest_path, hash_path, *paths, *bound]


def validate_deduplication(root_value: Path, normalization: Mapping[str, Any]) -> dict[str, Any]:
    root = root_value.resolve()
    manifest_path = root / "DEDUPLICATION_MANIFEST.json"
    manifest = load_json(manifest_path, "deduplication manifest")
    pipeline = manifest.get("pipeline")
    if pipeline not in {
        "fresh_snapshot_deduplication",
        "fresh_snapshot_deduplication_review_adjudication",
    }:
        raise FreshAnalysisError("Unsupported fresh deduplication package")
    all_paths = _validate_dedup_manifest_files(root, manifest)
    source_manifest: dict[str, Any]
    source_path: Path
    if pipeline == "fresh_snapshot_deduplication_review_adjudication":
        status = (manifest.get("workflow_status") or {}).get("status")
        if status != "resolved_ready_for_screening":
            raise FreshAnalysisError("Deduplication review is not fully resolved")
        source_name = clean((manifest.get("input") or {}).get("source_directory_name"))
        source_path = root.parent / source_name / "DEDUPLICATION_MANIFEST.json"
        source_manifest = load_json(source_path, "source deduplication manifest")
        expected = clean(
            (manifest.get("input") or {}).get("source_deduplication_manifest_sha256")
        ).casefold()
        if sha256_file(source_path) != expected:
            raise FreshAnalysisError("Resolved deduplication source manifest is stale")
        all_paths.extend(_validate_dedup_manifest_files(source_path.parent, source_manifest))
    else:
        source_manifest = manifest
        source_path = manifest_path
    source_input = source_manifest.get("input") or {}
    if clean(source_input.get("normalization_manifest_sha256")).casefold() != normalization[
        "manifest_sha256"
    ]:
        raise FreshAnalysisError("Deduplication is bound to a different normalization")
    counts = manifest.get("counts") or {}
    source_counts = source_manifest.get("counts") or {}
    occurrences = integer(counts.get("retrieval_occurrences"), "dedup retrieval occurrences")
    deduplicated = integer(counts.get("deduplicated_records"), "deduplicated records")
    pre_review_deduplicated = integer(
        source_counts.get("deduplicated_records"), "pre-review deduplicated records"
    )
    automatic_reduction = integer(
        source_counts.get(
            "occurrences_removed_by_exact_deduplication",
            occurrences - pre_review_deduplicated,
        ),
        "automatic duplicate reduction",
    )
    reviewed_reduction = integer(
        counts.get(
            "records_removed_by_reviewed_same_work_merges",
            pre_review_deduplicated - deduplicated,
        ),
        "separately checked same-record reduction",
    )
    unresolved = integer(counts.get("ambiguous_review_pairs", 0), "unresolved dedup pairs")
    if occurrences != normalization["retrieval_occurrences"]:
        raise FreshAnalysisError("Normalization and deduplication occurrence counts disagree")
    if unresolved != 0:
        raise FreshAnalysisError("Deduplication contains unresolved ambiguous pairs")
    if (
        occurrences - automatic_reduction != pre_review_deduplicated
        or pre_review_deduplicated - reviewed_reduction != deduplicated
    ):
        raise FreshAnalysisError("Automatic and separately checked duplicate reductions do not reconcile")
    dedup_jsonl = validate_entry(
        root, (manifest.get("outputs") or {}).get("deduplicated_jsonl") or {}, "deduplicated JSONL"
    )
    if count_jsonl(dedup_jsonl) != deduplicated:
        raise FreshAnalysisError("Deduplicated JSONL count mismatch")
    bindings: dict[str, str] = {}
    for path in all_paths + [source_path, dedup_jsonl]:
        add_binding(bindings, path)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "retrieval_occurrences": occurrences,
        "automatic_duplicate_reduction": automatic_reduction,
        "pre_review_deduplicated_records": pre_review_deduplicated,
        "reviewed_same_record_reduction": reviewed_reduction,
        "deduplicated_records": deduplicated,
        "bindings": bindings,
    }


def validate_candidate_package(root_value: Path, dedup: Mapping[str, Any]) -> dict[str, Any]:
    root = root_value.resolve()
    manifest_path = root / "CANDIDATE_BUILD_MANIFEST.json"
    manifest = load_json(manifest_path, "candidate-build manifest")
    if manifest.get("pipeline") != "fresh_de_novo_screening_candidate_build":
        raise FreshAnalysisError("Input is not the fresh candidate-build package")
    status = (manifest.get("workflow_status") or {}).get("status")
    if status != "ready_for_independent_screening":
        raise FreshAnalysisError("Candidate package is provisional or stale")
    input_info = manifest.get("input") or {}
    if clean(input_info.get("deduplication_manifest_sha256")).casefold() != dedup[
        "manifest_sha256"
    ]:
        raise FreshAnalysisError("Candidate package is bound to a different deduplication")
    outputs = manifest.get("outputs") or {}
    master = validate_entry(root, outputs.get("candidate_master_csv") or {}, "candidate master")
    master_jsonl = validate_entry(
        root, outputs.get("candidate_master_jsonl") or {}, "candidate master JSONL"
    )
    batch_manifest = validate_entry(
        root, outputs.get("batch_manifest") or {}, "candidate batch manifest"
    )
    review_schema = validate_entry(
        root, outputs.get("review_output_schema") or {}, "candidate review schema"
    )
    _fields, rows = read_csv_exact(master, MASTER_FIELDS)
    ids = [row["paper_id"] for row in rows]
    if not ids or any(not item for item in ids) or len(ids) != len(set(ids)):
        raise FreshAnalysisError("Candidate master IDs are blank, duplicated, or empty")
    counts = manifest.get("counts") or {}
    if (
        integer(counts.get("deduplicated_records"), "candidate deduplicated count")
        != dedup["deduplicated_records"]
        or integer(counts.get("candidate_records"), "candidate record count") != len(rows)
        or integer(counts.get("noncandidate_records"), "noncandidate record count")
        != dedup["deduplicated_records"] - len(rows)
    ):
        raise FreshAnalysisError("Candidate manifest counts are stale")
    hash_path, _ledger, bound = validate_hash_ledger(
        root,
        "CANDIDATE_HASH_MANIFEST.csv",
        required_output_paths=(
            master.name,
            master_jsonl.name,
            batch_manifest.name,
            review_schema.name,
            manifest_path.name,
        ),
    )
    bindings: dict[str, str] = {}
    for path in [manifest_path, master, master_jsonl, batch_manifest, review_schema, hash_path, *bound]:
        add_binding(bindings, path)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "master_path": master,
        "master_sha256": sha256_file(master),
        "rows": rows,
        "ids": ids,
        "bindings": bindings,
    }


def validate_comparison_package(root_value: Path, candidate: Mapping[str, Any]) -> dict[str, Any]:
    root = root_value.resolve()
    manifest_path = root / "REVIEW_COMPARISON_MANIFEST_V2.json"
    manifest = load_json(manifest_path, "review-comparison manifest")
    if manifest.get("pipeline") != "fresh_v2_independent_review_comparison":
        raise FreshAnalysisError("Input is not the fresh V2 comparison package")
    package = manifest.get("candidate_package") or {}
    if (
        clean(package.get("candidate_build_manifest_sha256")).casefold()
        != candidate["manifest_sha256"]
        or clean(package.get("candidate_master_sha256")).casefold()
        != candidate["master_sha256"]
    ):
        raise FreshAnalysisError("Comparison package is bound to different candidates")
    outputs = manifest.get("outputs") or {}
    required_keys = (
        "comparison",
        "adjudication_input",
        "adjudication_decisions_template",
        "human_audit_linkage_template",
        "version_relationship_review_input",
        "agreement_summary",
    )
    output_paths = [validate_entry(root, outputs.get(key) or {}, f"comparison {key}") for key in required_keys]
    comparison_path = output_paths[0]
    _fields, rows = read_csv_exact(comparison_path, COMPARISON_FIELDS)
    ids = [row["paper_id"] for row in rows]
    if ids != candidate["ids"]:
        raise FreshAnalysisError("Comparison candidate ID/order mismatch")
    for row in rows:
        for field in ("reviewer_A_decision", "reviewer_B_decision"):
            if row[field] not in AGREEMENT_DECISIONS:
                raise FreshAnalysisError(f"Invalid model-review decision for {row['paper_id']}")
    summary = load_json(output_paths[-1], "comparison agreement summary")
    if integer(summary.get("records"), "comparison summary records") != len(rows):
        raise FreshAnalysisError("Comparison agreement summary count mismatch")
    review_paths: list[Path] = []
    review_keys: set[tuple[str, int]] = set()
    for entry in manifest.get("review_inputs") or []:
        reviewer = clean(entry.get("reviewer"))
        batch = integer(entry.get("batch"), "locked review batch", minimum=1)
        if reviewer not in {"A", "B"} or (reviewer, batch) in review_keys:
            raise FreshAnalysisError("Comparison locked-review input set is invalid")
        review_keys.add((reviewer, batch))
        path = safe_relative(root, entry.get("path"), "locked reviewer input")
        if (
            not path.is_file()
            or path.stat().st_size != integer(entry.get("bytes"), "locked review bytes")
            or sha256_file(path) != clean(entry.get("sha256")).casefold()
        ):
            raise FreshAnalysisError(f"Locked reviewer input is stale or tampered: {path}")
        review_paths.append(path)
    if not review_paths:
        raise FreshAnalysisError("Comparison package has no locked reviewer inputs")
    hash_path, _ledger, bound = validate_hash_ledger(
        root,
        "REVIEW_COMPARISON_HASH_MANIFEST_V2.csv",
        required_output_paths=tuple(path.relative_to(root).as_posix() for path in output_paths)
        + (manifest_path.name,),
    )
    bindings: dict[str, str] = {}
    for path in [manifest_path, *output_paths, *review_paths, hash_path, *bound]:
        add_binding(bindings, path)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "comparison_path": comparison_path,
        "rows": rows,
        "bindings": bindings,
    }


def validate_screening_finalization(
    root_value: Path,
    candidate: Mapping[str, Any],
    comparison: Mapping[str, Any],
) -> dict[str, Any]:
    root = root_value.resolve()
    manifest_path = root / "SCREENING_FINALIZATION_MANIFEST_V2.json"
    manifest = load_json(manifest_path, "screening-finalization manifest")
    if (
        manifest.get("pipeline") != "fresh_v2_record_level_screening_finalization"
        or manifest.get("status") != SCREENING_FINAL_STATUS
    ):
        raise FreshAnalysisError("Screening finalization is provisional, stale, or wrong-version")
    contracts = manifest.get("contracts") or {}
    required_true = (
        "all_model_disagreements_and_uncertain_rows_resolved",
        "agreed_exclusions_with_different_codes_resolved",
        "prospective_human_audit_deferred_by_author",
        "systematic_version_review_still_required",
    )
    if any(contracts.get(field) is not True for field in required_true):
        raise FreshAnalysisError("Screening-finalization resolution/deferral contracts failed")
    if (
        contracts.get("prospective_human_audit_linked") is not False
        or contracts.get("human_reference_standard_available") is not False
        or contracts.get("model_agreement_may_be_reported_as_human_reliability") is not False
        or contracts.get("analysis_unit_ready") is not False
    ):
        raise FreshAnalysisError("Screening finalization permits an unsupported claim")
    inputs = manifest.get("inputs") or {}
    if (
        clean((inputs.get("candidate_build_manifest") or {}).get("sha256")).casefold()
        != candidate["manifest_sha256"]
        or clean((inputs.get("comparison_manifest") or {}).get("sha256")).casefold()
        != comparison["manifest_sha256"]
    ):
        raise FreshAnalysisError("Screening finalization input hashes are stale")
    outputs = manifest.get("outputs") or {}
    required_keys = (
        "final_record_level_screening",
        "final_included_records",
        "post_eligibility_version_review_queue",
        "human_audit_linkage_used",
        "human_audit_deferral_used",
        "human_audit_deferral_source_note_used",
        "summary",
    )
    paths = [validate_entry(root, outputs.get(key) or {}, f"screening {key}") for key in required_keys]
    final_path, included_path, _version_path, human_path, deferral_path, deferral_note, summary_path = paths
    _fields, final_rows = read_csv_exact(final_path, FINAL_FIELDS)
    _fields, included_rows = read_csv_exact(included_path, FINAL_FIELDS)
    if [row["paper_id"] for row in final_rows] != candidate["ids"]:
        raise FreshAnalysisError("Final screening candidate ID/order mismatch")
    included_expected = [row for row in final_rows if row["final_decision"] == "INCLUDE"]
    if included_rows != included_expected:
        raise FreshAnalysisError("Included-record file does not match final decisions")
    if any(row["final_decision"] not in {"INCLUDE", "EXCLUDE"} for row in final_rows):
        raise FreshAnalysisError("Final screening contains an unresolved decision")
    _fields, human_rows = read_csv_exact(human_path, HUMAN_AUDIT_LINK_FIELDS)
    if [row["paper_id"] for row in human_rows] != candidate["ids"]:
        raise FreshAnalysisError("Human-audit linkage candidate ID/order mismatch")
    human_result_fields = HUMAN_AUDIT_LINK_FIELDS[4:]
    if any(any(row[field] for field in human_result_fields) for row in human_rows):
        raise FreshAnalysisError("Human-audit results are present despite the author deferral")
    deferral = load_json(deferral_path, "copied human-audit deferral")
    if (
        deferral.get("decision") != "deferred_by_corresponding_author"
        or deferral.get("human_audit_completed") is not False
        or deferral.get("human_reference_standard_available") is not False
    ):
        raise FreshAnalysisError("Copied human-audit deferral is invalid")
    summary = load_json(summary_path, "screening-finalization summary")
    counts = manifest.get("counts") or {}
    if (
        integer(counts.get("records"), "final screening records") != len(final_rows)
        or integer(counts.get("included_records"), "final included records")
        != len(included_rows)
        or integer(counts.get("human_audited_records_linked"), "human audited records") != 0
        or integer(counts.get("human_audit_deferred_by_author"), "human audit deferral") != 1
        or summary.get("status") != SCREENING_FINAL_STATUS
    ):
        raise FreshAnalysisError("Screening-finalization counts/status are stale")
    hash_path, _ledger, bound = validate_hash_ledger(
        root,
        "SCREENING_FINALIZATION_HASH_MANIFEST_V2.csv",
        required_output_paths=tuple(path.relative_to(root).as_posix() for path in paths)
        + (manifest_path.name,),
    )
    bindings: dict[str, str] = {}
    for path in [manifest_path, *paths, hash_path, *bound]:
        add_binding(bindings, path)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "rows": final_rows,
        "included_rows": included_rows,
        "summary": summary,
        "bindings": bindings,
    }


def validate_version_consolidation_package(
    manifest_path_value: Path,
    expected_corpus_path: Path,
    *,
    synthetic_test_mode: bool = False,
) -> dict[str, Any]:
    """Validate the complete publication-version package used by extraction."""

    manifest_path = manifest_path_value.resolve()
    root = manifest_path.parent
    manifest = load_json(manifest_path, "publication-version consolidation manifest")
    if (
        manifest.get("schema_version") != "fresh-publication-version-consolidation-v2.0"
        or manifest.get("pipeline") != "fresh_v2_publication_version_consolidation"
        or manifest.get("status")
        != "publication_version_consolidation_finalized_analysis_unit_ready"
    ):
        raise FreshAnalysisError("Publication-version consolidation is not analysis-ready")
    contracts = manifest.get("contracts") or {}
    required_true = (
        "all_eligible_versions_preserved_in_ledger",
        "all_record_level_rows_preserved",
        "analysis_unit_ready",
        "one_preferred_version_per_family",
        "record_level_eligibility_unchanged",
    )
    if any(contracts.get(field) is not True for field in required_true):
        raise FreshAnalysisError("Publication-version consolidation contracts failed")
    outputs = manifest.get("outputs") or {}
    required_keys: tuple[str, ...] = (
        "all_record_level_screening_preserved",
        "eligible_version_ledger",
        "one_work_analysis_corpus",
        "summary",
    )
    if not synthetic_test_mode:
        required_keys += ("family_decisions_used", "pair_decisions_used")
    validated = {
        key: validate_entry(root, outputs.get(key) or {}, f"version consolidation {key}")
        for key in required_keys
    }
    paths = list(validated.values())
    corpus_path = validated["one_work_analysis_corpus"]
    if corpus_path.resolve() != expected_corpus_path.resolve():
        raise FreshAnalysisError("Extraction and version consolidation use different one-work corpora")
    counts = manifest.get("counts") or {}
    eligible_versions = integer(counts.get("eligible_record_versions"), "eligible versions")
    unique_studies = integer(counts.get("one_work_analysis_rows"), "one-work rows")
    if (
        count_csv_rows(validated["eligible_version_ledger"]) != eligible_versions
        or count_csv_rows(corpus_path) != unique_studies
    ):
        raise FreshAnalysisError("Publication-version ledgers do not match their manifested counts")
    hash_path, _ledger, bound = validate_hash_ledger(
        root,
        "PUBLICATION_VERSION_CONSOLIDATION_HASH_MANIFEST_V2.csv",
        required_output_paths=tuple(path.relative_to(root).as_posix() for path in paths)
        + (manifest_path.name,),
    )
    frozen_path = root / "PUBLICATION_VERSION_CONSOLIDATION_FROZEN_V2.json"
    frozen = load_json(frozen_path, "publication-version consolidation frozen marker")
    frozen_expected = {
        "status": "publication_version_consolidation_finalized_analysis_unit_ready",
        "consolidation_manifest_sha256": sha256_file(manifest_path),
        "consolidation_hash_ledger_sha256": sha256_file(hash_path),
        "eligible_version_ledger_sha256": sha256_file(validated["eligible_version_ledger"]),
        "one_work_analysis_corpus_sha256": sha256_file(corpus_path),
    }
    for field, expected in frozen_expected.items():
        if clean(frozen.get(field)).casefold() != expected.casefold():
            raise FreshAnalysisError(f"Publication-version frozen marker mismatch: {field}")
    bindings: dict[str, str] = {}
    for path in [manifest_path, *paths, hash_path, frozen_path, *bound]:
        add_binding(bindings, path)
    for entry in (() if synthetic_test_mode else (manifest.get("inputs") or {}).values()):
        if not isinstance(entry, Mapping) or not entry.get("path") or not entry.get("sha256"):
            continue
        source = Path(str(entry["path"])).resolve()
        if not source.is_file() or sha256_file(source) != clean(entry["sha256"]).casefold():
            raise FreshAnalysisError(f"Publication-version upstream input is stale: {source}")
        add_binding(bindings, source)
    return {
        "manifest": manifest,
        "eligible_versions": eligible_versions,
        "unique_studies": unique_studies,
        "eligible_ledger_path": validated["eligible_version_ledger"],
        "bindings": bindings,
    }


def validate_extraction_package(
    root_value: Path,
    spec: Mapping[str, Any],
    spec_path: Path,
    finalization: Mapping[str, Any],
    *,
    synthetic_test_mode: bool = False,
) -> dict[str, Any]:
    root = root_value.resolve()
    manifest_path = root / EXTRACTION_MANIFEST
    manifest = load_json(manifest_path, "checked-extraction finalization manifest")
    if (
        manifest.get("schema_version") != "fresh-work-level-extraction-v2.0"
        or manifest.get("pipeline") != EXTRACTION_PIPELINE
        or manifest.get("status") != EXTRACTION_STATUS
    ):
        raise FreshAnalysisError("Checked work-level extraction is not finalized/analysis-ready")
    contracts = manifest.get("contracts") or {}
    required_true = (
        "source_corpus_unchanged",
        "source_order_preserved",
        "every_canonical_work_source_checked",
        "final_fields_come_only_from_checked_extraction",
        "analysis_ready_checked_work_extraction",
    )
    if any(contracts.get(field) is not True for field in required_true):
        raise FreshAnalysisError("Checked extraction readiness contracts failed")
    if contracts.get("human_validation_claims_permitted") is not False:
        raise FreshAnalysisError("Checked extraction permits unsupported human-validation claims")
    inputs = manifest.get("inputs") or {}
    if clean((inputs.get("analysis_specification") or {}).get("sha256")).casefold() != sha256_file(
        spec_path
    ):
        raise FreshAnalysisError("Checked extraction used a different analysis specification")
    source_entry = inputs.get("one_work_analysis_corpus") or {}
    consolidation_entry = inputs.get("publication_version_consolidation_manifest") or {}
    source_corpus_path = Path(str(source_entry.get("path") or "")).resolve()
    consolidation_manifest_path = Path(str(consolidation_entry.get("path") or "")).resolve()
    if (
        not source_corpus_path.is_file()
        or sha256_file(source_corpus_path) != clean(source_entry.get("sha256")).casefold()
        or not consolidation_manifest_path.is_file()
        or sha256_file(consolidation_manifest_path)
        != clean(consolidation_entry.get("sha256")).casefold()
    ):
        raise FreshAnalysisError("Checked extraction version-consolidation inputs are stale")
    consolidation = validate_version_consolidation_package(
        consolidation_manifest_path,
        source_corpus_path,
        synthetic_test_mode=synthetic_test_mode,
    )
    outputs = manifest.get("outputs") or {}
    required_keys = (
        "merged_completed_extractions",
        "checked_one_work_corpus",
        "checked_extraction_ledger",
        "summary",
    )
    paths = [validate_entry(root, outputs.get(key) or {}, f"extraction {key}") for key in required_keys]
    checked_path = paths[1]
    if checked_path.name != CHECKED_CORPUS:
        raise FreshAnalysisError("Checked analysis corpus filename changed")
    _fields, rows = read_csv_exact(checked_path, CHECKED_CORPUS_FIELDS)
    if not rows:
        raise FreshAnalysisError("Checked analysis corpus is empty")
    ids = [row["paper_id"] for row in rows]
    families = [row["version_family_id"] for row in rows]
    if (
        any(not item for item in ids + families)
        or len(ids) != len(set(ids))
        or len(families) != len(set(families))
    ):
        raise FreshAnalysisError("Checked corpus work/family IDs are blank or duplicated")
    if rows != sorted(rows, key=lambda row: (row["version_family_id"], row["paper_id"])):
        raise FreshAnalysisError("Checked corpus row order is stale")
    included_ids = {row["paper_id"] for row in finalization["included_rows"]}
    if not set(ids) <= included_ids:
        raise FreshAnalysisError("Checked corpus contains a non-included record version")
    labels = spec.get("study_level_labels") or {}
    for number, row in enumerate(rows, start=2):
        if (
            row["final_decision"] != "INCLUDE"
            or row["preferred_for_analysis"] != "yes"
            or row["preferred_paper_id"] != row["paper_id"]
            or row["human_audit_mode"] != "explicit_author_deferral"
            or row["source_row_number"] != str(number - 1)
        ):
            raise FreshAnalysisError(f"{checked_path}:{number}: invalid canonical-work binding")
        for field, group, required in (
            ("final_model_families", "model_families", True),
            ("final_simulation_modalities", "simulation_methods", True),
            ("final_nts_domains", "nts_domains", False),
        ):
            values = split_semicolon(row[field])
            if required and not values:
                raise FreshAnalysisError(f"{checked_path}:{number}: blank {field}")
            if any(value not in labels[group] for value in values):
                raise FreshAnalysisError(f"{checked_path}:{number}: unlocked {field}")
        if row["final_study_design"] not in labels["study_designs"]:
            raise FreshAnalysisError(f"{checked_path}:{number}: unlocked study design")
        if row["source_check_attestation"] != "independent_source_check_completed":
            raise FreshAnalysisError(f"{checked_path}:{number}: source check is unattested")
        if row["screening_suggestions_role"] != "suggestions_only_not_evidence":
            raise FreshAnalysisError(f"{checked_path}:{number}: suggestions/evidence role changed")
    counts = manifest.get("counts") or {}
    if integer(counts.get("canonical_works"), "checked canonical works") != len(rows):
        raise FreshAnalysisError("Checked extraction manifest count mismatch")
    summary = load_json(paths[-1], "checked-extraction summary")
    if (
        summary.get("status") != EXTRACTION_STATUS
        or integer(summary.get("canonical_works_checked"), "checked summary works") != len(rows)
        or summary.get("prospective_human_audit_deferred_by_author") is not True
        or summary.get("human_reference_standard_available") is not False
    ):
        raise FreshAnalysisError("Checked extraction summary contract mismatch")
    hash_path, _ledger, bound = validate_hash_ledger(
        root,
        EXTRACTION_HASH_LEDGER,
        required_output_paths=tuple(path.relative_to(root).as_posix() for path in paths)
        + (manifest_path.name,),
    )
    frozen_path = root / EXTRACTION_FROZEN_MARKER
    frozen = load_json(frozen_path, "checked-extraction frozen marker")
    frozen_expected = {
        "status": EXTRACTION_STATUS,
        "finalization_manifest_sha256": sha256_file(manifest_path),
        "finalization_hash_ledger_sha256": sha256_file(hash_path),
        "checked_one_work_corpus_sha256": sha256_file(checked_path),
        "analysis_specification_sha256": sha256_file(spec_path),
    }
    for field, expected in frozen_expected.items():
        if clean(frozen.get(field)).casefold() != expected.casefold():
            raise FreshAnalysisError(f"Checked-extraction frozen marker mismatch: {field}")
    script = manifest.get("script") or {}
    extraction_script = PIPELINE_DIR / "fresh_work_level_extraction_v2.py"
    if (
        script.get("filename") != extraction_script.name
        or clean(script.get("sha256")).casefold() != sha256_file(extraction_script)
    ):
        raise FreshAnalysisError("Checked extraction was produced by stale extraction code")
    bindings: dict[str, str] = {}
    for path in [manifest_path, *paths, hash_path, frozen_path, extraction_script, *bound]:
        add_binding(bindings, path)
    for path, digest in consolidation["bindings"].items():
        prior = bindings.get(path)
        if prior is not None and prior != digest:
            raise FreshAnalysisError(f"Conflicting version-consolidation binding: {path}")
        bindings[path] = digest
    for entry in inputs.values():
        if not isinstance(entry, Mapping) or not entry.get("path") or not entry.get("sha256"):
            continue
        source = Path(str(entry["path"])).resolve()
        if not source.is_file() or sha256_file(source) != clean(entry["sha256"]).casefold():
            raise FreshAnalysisError(f"Checked-extraction upstream input is stale: {source}")
        add_binding(bindings, source)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "checked_path": checked_path,
        "rows": rows,
        "ids": ids,
        "version_consolidation": consolidation,
        "bindings": bindings,
    }


def validate_metadata_correction_package(
    root_value: Path, extraction: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate and join the separate reviewed bibliographic correction view.

    The checked extraction remains bound to the original 112-column one-work
    corpus.  This validator proves that the correction view has the same exact
    rows/order, changes only its reviewed fields, and then overlays those
    corrected source values plus the eight audit fields for analysis.
    """

    root = root_value.resolve()
    manifest_path = root / "METADATA_CORRECTION_MANIFEST_V2.json"
    ledger_path = root / "METADATA_CORRECTION_LEDGER_V2.csv"
    corrected_path = root / "ONE_WORK_ANALYSIS_CORPUS_METADATA_CORRECTED_V2.csv"
    manifest = load_json(manifest_path, "metadata-correction manifest")
    if (
        manifest.get("schema_version") != "fresh_metadata_corrections_v2.0"
        or manifest.get("status") != "metadata_corrections_applied_analysis_view_ready"
        or manifest.get("paper_id_order_preserved") is not True
        or manifest.get("source_fields_preserved_except_reviewed_corrections") is not True
    ):
        raise FreshAnalysisError("Metadata-correction package is not finalized/analysis-ready")
    if not corrected_path.is_file() or sha256_file(corrected_path) != clean(
        manifest.get("corrected_corpus_sha256")
    ).casefold():
        raise FreshAnalysisError("Metadata-corrected corpus is stale or tampered")
    if not ledger_path.is_file() or sha256_file(ledger_path) != clean(
        manifest.get("correction_ledger_sha256")
    ).casefold():
        raise FreshAnalysisError("Metadata-correction ledger is stale or tampered")
    source_path = Path(clean(manifest.get("source_corpus_path"))).resolve()
    source_sha = clean(manifest.get("source_corpus_sha256")).casefold()
    if not source_path.is_file() or sha256_file(source_path) != source_sha:
        raise FreshAnalysisError("Metadata-correction source corpus is stale or missing")
    decisions_path = Path(clean(manifest.get("correction_decisions_path"))).resolve()
    if not decisions_path.is_file() or sha256_file(decisions_path) != clean(
        manifest.get("correction_decisions_sha256")
    ).casefold():
        raise FreshAnalysisError("Metadata-correction decisions are stale or tampered")
    _source_fields, source_rows = read_csv_exact(source_path, SOURCE_CORPUS_FIELDS)
    expected_corrected_fields = list(SOURCE_CORPUS_FIELDS) + list(METADATA_AUDIT_FIELDS)
    _corrected_fields, corrected_rows = read_csv_exact(
        corrected_path, expected_corrected_fields
    )
    _ledger_fields, ledger_rows = read_csv_exact(ledger_path, METADATA_LEDGER_FIELDS)
    try:
        expected_fields, expected_rows, expected_ledger_rows, _expected_report = (
            apply_metadata_corrections(
                _source_fields,
                source_rows,
                load_metadata_corrections(decisions_path),
                source_sha,
            )
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FreshAnalysisError(
            "Metadata-correction decisions cannot reproduce the reviewed analysis view"
        ) from exc
    if (
        expected_fields != expected_corrected_fields
        or expected_rows != corrected_rows
        or expected_ledger_rows != ledger_rows
    ):
        raise FreshAnalysisError(
            "Metadata-correction view/ledger is not exactly reproducible from its reviewed decisions"
        )
    if (
        len(source_rows) != len(corrected_rows)
        or [row["paper_id"] for row in source_rows]
        != [row["paper_id"] for row in corrected_rows]
        or [row["paper_id"] for row in source_rows] != extraction["ids"]
    ):
        raise FreshAnalysisError(
            "Metadata source, corrected view and checked extraction IDs/order disagree"
        )
    extraction_source_sha = clean(
        (
            extraction["manifest"].get("inputs", {}).get("one_work_analysis_corpus")
            or {}
        ).get("sha256")
    ).casefold()
    if extraction_source_sha != source_sha:
        raise FreshAnalysisError(
            "Checked extraction and metadata correction are not bound to the same original one-work corpus"
        )
    corrected_record_count = 0
    corrected_field_count = 0
    ledger_index: dict[tuple[str, str], dict[str, str]] = {}
    for ledger in ledger_rows:
        key = (ledger["paper_id"], ledger["field"])
        if key in ledger_index:
            raise FreshAnalysisError(f"Duplicate metadata-correction ledger row: {key}")
        ledger_index[key] = ledger
        if ledger["source_corpus_sha256"] != source_sha:
            raise FreshAnalysisError("Metadata-correction ledger source hash changed")
    analysis_rows: list[dict[str, str]] = []
    for source_row, corrected_row, checked_row in zip(
        source_rows, corrected_rows, extraction["rows"], strict=True
    ):
        paper_id = source_row["paper_id"]
        for field in SOURCE_CORPUS_FIELDS:
            if checked_row[field] != source_row[field]:
                raise FreshAnalysisError(
                    f"Checked extraction source value differs from its original corpus: {paper_id}/{field}"
                )
        source_row_sha = sha256_text(canonical_json(dict(source_row)))
        if corrected_row["metadata_source_row_sha256"] != source_row_sha:
            raise FreshAnalysisError(
                f"Metadata source-row hash mismatch for {paper_id}"
            )
        changed = split_semicolon(corrected_row["metadata_corrected_fields"])
        if any(field not in REVIEWED_METADATA_FIELDS for field in changed):
            raise FreshAnalysisError(
                f"Metadata correction changes a non-authorized analysis field for {paper_id}"
            )
        applied = corrected_row["metadata_correction_applied"]
        if applied not in {"true", "false"} or (applied == "true") != bool(changed):
            raise FreshAnalysisError(f"Metadata correction-applied flag mismatch for {paper_id}")
        if changed:
            corrected_record_count += 1
        corrected_field_count += len(changed)
        for field in SOURCE_CORPUS_FIELDS:
            if field not in changed and corrected_row[field] != source_row[field]:
                raise FreshAnalysisError(
                    f"Unreviewed metadata field changed for {paper_id}/{field}"
                )
            if field in changed:
                ledger = ledger_index.get((paper_id, field))
                if (
                    ledger is None
                    or ledger["old_value"] != source_row[field]
                    or ledger["new_value"] != corrected_row[field]
                    or ledger["source_row_sha256"] != source_row_sha
                ):
                    raise FreshAnalysisError(
                        f"Metadata correction lacks a matching ledger decision: {paper_id}/{field}"
                    )
        corrected_hash = sha256_text(
            canonical_json(
                {
                    key: value
                    for key, value in corrected_row.items()
                    if key != "metadata_corrected_row_sha256"
                }
            )
        )
        if corrected_row["metadata_corrected_row_sha256"] != corrected_hash:
            raise FreshAnalysisError(
                f"Metadata corrected-row hash mismatch for {paper_id}"
            )
        for field in changed:
            if ledger_index[(paper_id, field)]["corrected_row_sha256"] != corrected_hash:
                raise FreshAnalysisError(
                    f"Metadata ledger corrected-row hash mismatch: {paper_id}/{field}"
                )
        joined = dict(checked_row)
        joined.update({field: corrected_row[field] for field in REVIEWED_METADATA_FIELDS})
        joined.update({field: corrected_row[field] for field in METADATA_AUDIT_FIELDS})
        analysis_rows.append(joined)
    if set(ledger_index) != {
        (row["paper_id"], field)
        for row in corrected_rows
        for field in split_semicolon(row["metadata_corrected_fields"])
    }:
        raise FreshAnalysisError("Metadata-correction ledger has missing or extra decisions")
    if (
        integer(manifest.get("source_rows"), "metadata source rows") != len(source_rows)
        or integer(manifest.get("output_rows"), "metadata output rows") != len(corrected_rows)
        or integer(manifest.get("corrected_records"), "metadata corrected records")
        != corrected_record_count
        or integer(manifest.get("corrected_fields"), "metadata corrected fields")
        != corrected_field_count
        or integer(manifest.get("source_column_count"), "metadata source columns")
        != len(SOURCE_CORPUS_FIELDS)
        or integer(manifest.get("output_column_count"), "metadata output columns")
        != len(expected_corrected_fields)
    ):
        raise FreshAnalysisError("Metadata-correction manifest counts are stale")
    bindings: dict[str, str] = {}
    for path in (
        manifest_path,
        ledger_path,
        corrected_path,
        source_path,
        decisions_path,
        PIPELINE_DIR / "apply_fresh_metadata_corrections_v2.py",
    ):
        add_binding(bindings, path)
    return {
        "root": root,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "corrected_path": corrected_path,
        "corrected_sha256": sha256_file(corrected_path),
        "source_path": source_path,
        "source_sha256": source_sha,
        "rows": corrected_rows,
        "analysis_rows": analysis_rows,
        "ids": [row["paper_id"] for row in corrected_rows],
        "bindings": bindings,
    }


def _report_path(root: Path, value: Any, fallback: str) -> Path:
    raw = Path(clean(value) or fallback)
    if raw.is_absolute():
        candidate = raw.resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            candidate = root / raw.name
        return candidate
    return safe_relative(root, raw.as_posix(), "OpenAlex report")


def validate_openalex_package(
    root_value: Path, corrected_rows: Sequence[Mapping[str, str]]
) -> dict[str, Any]:
    root = root_value.resolve()
    report_path = root / "OPENALEX_LOCK_REPORT.json"
    report = load_json(report_path, "OpenAlex lock report")
    if report.get("status") != "LOCKED":
        raise FreshAnalysisError("OpenAlex snapshot is not LOCKED")
    if report.get("raw_snapshot_modified") is not False or report.get("network_access") is not False:
        raise FreshAnalysisError("OpenAlex lock report does not preserve the fixed snapshot")
    generated_utc = clean(report.get("generated_utc"))
    try:
        generated_at = datetime.fromisoformat(generated_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshAnalysisError("OpenAlex lock report lacks a valid lock timestamp") from exc
    if generated_at.utcoffset() is None or not SHA256_RE.fullmatch(
        clean(report.get("snapshot_fingerprint"))
    ):
        raise FreshAnalysisError("OpenAlex lock timestamp/fingerprint is incomplete")
    locked_path = _report_path(root, report.get("locked_file"), "OPENALEX_LOCKED.csv")
    if not locked_path.is_file() or sha256_file(locked_path) != clean(
        report.get("locked_sha256")
    ).casefold():
        raise FreshAnalysisError("OpenAlex locked file is stale or tampered")
    _fields, rows = read_csv_exact(locked_path, OPENALEX_FIELDS)
    ids = [row["paper_id"] for row in rows]
    corrected_ids = [row["paper_id"] for row in corrected_rows]
    if ids != corrected_ids or len(ids) != len(set(ids)):
        raise FreshAnalysisError("OpenAlex locked rows do not match checked works in order")
    for locked, corrected in zip(rows, corrected_rows, strict=True):
        if (
            locked["input_doi"].casefold() != corrected["doi"].casefold()
            or locked["input_title"] != corrected["title"]
            or locked["input_year"] != corrected["year"]
        ):
            raise FreshAnalysisError(
                "OpenAlex locked input metadata differs from the reviewed corrected view: "
                f"{locked['paper_id']}"
            )
    if integer(report.get("locked_records"), "OpenAlex locked records") != len(rows):
        raise FreshAnalysisError("OpenAlex lock-report count mismatch")
    matched = sum(row["match_status"] == "MATCHED" for row in rows)
    unmatched = sum(row["match_status"] == "UNMATCHED" for row in rows)
    if matched + unmatched != len(rows):
        raise FreshAnalysisError("OpenAlex lock contains an unresolved match status")
    if (
        integer(report.get("locked_matched"), "OpenAlex matched records") != matched
        or integer(report.get("locked_unmatched"), "OpenAlex unmatched records") != unmatched
    ):
        raise FreshAnalysisError("OpenAlex match counts are stale")
    bindings: dict[str, str] = {}
    for filename, expected in (report.get("input_hashes") or {}).items():
        path = safe_relative(root, filename, "OpenAlex input")
        if not path.is_file() or sha256_file(path) != clean(expected).casefold():
            raise FreshAnalysisError(f"OpenAlex snapshot input is stale or tampered: {path}")
        add_binding(bindings, path)
    for key, fallback, hash_key in (
        ("completed_review", "OPENALEX_MATCH_REVIEW_COMPLETED.csv", "completed_review_sha256"),
        ("ledger_file", "OPENALEX_MATCH_ADJUDICATION_LEDGER.csv", "ledger_sha256"),
    ):
        path = _report_path(root, report.get(key), fallback)
        if not path.is_file() or sha256_file(path) != clean(report.get(hash_key)).casefold():
            raise FreshAnalysisError(f"OpenAlex {key} is stale or tampered")
        add_binding(bindings, path)
    for path in (report_path, locked_path):
        add_binding(bindings, path)
    return {
        "root": root,
        "report": report,
        "report_path": report_path,
        "locked_path": locked_path,
        "rows": rows,
        "by_id": {row["paper_id"]: row for row in rows},
        "matched": matched,
        "unmatched": unmatched,
        "bindings": bindings,
    }


def split_semicolon(value: Any) -> list[str]:
    text = clean(value)
    if not text:
        return []
    values = [item.strip() for item in text.split(";")]
    if any(not item for item in values):
        raise FreshAnalysisError(f"Malformed semicolon-delimited value: {text!r}")
    if len(values) != len(set(values)):
        raise FreshAnalysisError(f"Duplicate semicolon-delimited value: {text!r}")
    return values


def plain_label(value: str) -> str:
    special = {
        "ChatGPT_unspecified": "ChatGPT (version unspecified)",
        "OpenAI_o_series": "OpenAI o-series",
        "T5_FLAN": "T5 / FLAN",
        "vr_ar_xr": "Virtual, augmented or extended reality",
        "osce": "Objective structured clinical examination",
        "roleplay": "Role-play",
        "decision_making": "Decision-making",
        "situational_awareness": "Situational awareness",
        "task_management": "Task management",
        "stress_management": "Stress management",
        "no_explicit_nts": "No explicit NTS domain",
        "no_explicit_simulation_method": "No explicit simulation method identified",
        "randomized_trial": "Randomized trial",
        "nonrandomized_comparative": "Non-randomized comparative",
        "pre_post": "Pre-post",
        "mixed_methods": "Mixed methods",
        "development_evaluation": "Development/evaluation",
        "evidence_review": "Evidence review",
        "methods_framework": "Methods/framework",
        "other_named": "Other named model",
        "unspecified_generative_model": "Unspecified generative model",
        "virtual_patient": "Virtual patient",
        "standardized_patient": "Standardized patient",
        "task_trainer": "Task trainer",
        "serious_game": "Serious game",
        "openalex": "OpenAlex",
        "pubmed": "PubMed",
        "europepmc": "Europe PMC",
        "semantic_scholar": "Semantic Scholar",
        "doaj": "DOAJ",
    }
    if value in special:
        return special[value]
    display = value.replace("_", " ").strip()
    # Preserve established brand/model capitalization such as GPT-4,
    # DeepSeek, Med-PaLM and BioGPT.  Ordinary controlled labels remain
    # sentence-cased for reader-facing tables and figures.
    return display if any(character.isupper() for character in display) else display.capitalize()


def country_label(code: str) -> str:
    """Return a plain reader-facing country label while retaining the ISO code."""

    normalized = clean(code).upper()
    name = COUNTRY_DISPLAY_NAMES.get(normalized)
    return f"{name} ({normalized})" if name else normalized


def descriptive_row(**values: Any) -> dict[str, Any]:
    row = {field: "" for field in DESCRIPTIVE_TABLE_FIELDS}
    row.update(values)
    if not clean(row["denominator_definition"]):
        raise AssertionError("Every descriptive row requires a denominator definition")
    if not clean(row["response_type"]):
        raise AssertionError("Every descriptive row requires a response-type note")
    return row


def agreement_row(**values: Any) -> dict[str, Any]:
    row = {field: "" for field in AGREEMENT_TABLE_FIELDS}
    row.update(values)
    if not clean(row["denominator_definition"]):
        raise AssertionError("Every agreement row requires a denominator definition")
    if not clean(row["response_type"]):
        raise AssertionError("Every agreement row requires a response-type note")
    return row


def frequency_rows(
    rows: Sequence[Mapping[str, str]],
    field: str,
    labels: Sequence[str],
    *,
    section: str,
    denominator_definition: str,
    blank_label: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    work_ids: dict[str, list[str]] = {label: [] for label in labels}
    if blank_label is not None:
        work_ids[blank_label] = []
    for row in rows:
        values = split_semicolon(row[field])
        if not values and blank_label is not None:
            values = [blank_label]
        for value in values:
            if value not in work_ids:
                raise FreshAnalysisError(f"Unexpected checked label in {field}: {value}")
            work_ids[value].append(row["paper_id"])
    n = len(rows)
    output_labels = [*labels, blank_label] if blank_label is not None else list(labels)
    output = [
        descriptive_row(
            section=section,
            measure="Work frequency",
            category=plain_label(label),
            count=len(work_ids[label]),
            denominator=n,
            percent=percent(len(work_ids[label]), n),
            unit="canonical works",
            denominator_definition=denominator_definition,
            response_type=(
                "single response; categories are mutually exclusive"
                if field == "final_study_design"
                else "multiple response; percentages may sum to more than 100%"
            ),
            work_ids=";".join(work_ids[label]),
            note=(
                "A zero is an observed zero category count, not a missing value."
                if not work_ids[label]
                else "Counted at most once per canonical work for this label."
            ),
        )
        for label in output_labels
    ]
    return output, work_ids


def phrase_pattern(variants: Sequence[str]) -> re.Pattern[str]:
    patterns: list[str] = []
    for raw in variants:
        normalized = unicodedata.normalize("NFKC", raw).casefold()
        pieces = re.split(r"[\s\-\u2010-\u2015]+", normalized)
        body = r"[\s\-\u2010-\u2015]+".join(re.escape(piece) for piece in pieces if piece)
        patterns.append(r"(?<!\w)" + body + r"(?!\w)")
    return re.compile("(?:" + "|".join(patterns) + ")", re.IGNORECASE)


def phrase_text(value: Any) -> str:
    text = html.unescape(clean(value))
    text = re.sub(r"<[^>]*>", " ", text)
    return unicodedata.normalize("NFKC", text).casefold()


def phrase_analysis(
    works: Sequence[Mapping[str, str]], spec: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, set[str]]]:
    dictionary = (spec.get("phrase_matching") or {}).get("dictionary") or []
    compiled = {
        item["label"]: (item["group"], phrase_pattern(item["variants"]))
        for item in dictionary
    }
    hits: dict[str, set[str]] = {label: set() for label in compiled}
    title_hits: dict[str, set[str]] = {label: set() for label in compiled}
    abstract_hits: dict[str, set[str]] = {label: set() for label in compiled}
    keyword_hits: dict[str, set[str]] = {label: set() for label in compiled}
    work_labels: dict[str, set[str]] = {}
    with_abstract = [row for row in works if clean(row["abstract"])]
    with_abstract_ids = {row["paper_id"] for row in with_abstract}
    for row in works:
        paper_id = row["paper_id"]
        title = phrase_text(row["title"])
        abstract = phrase_text(row["abstract"])
        keywords = phrase_text(row["source_keywords"])
        full = "\n".join((title, abstract, keywords))
        matched: set[str] = set()
        for label, (_group, pattern) in compiled.items():
            title_match = bool(pattern.search(title))
            abstract_match = bool(abstract and pattern.search(abstract))
            keyword_match = bool(pattern.search(keywords))
            if pattern.search(full):
                hits[label].add(paper_id)
                matched.add(label)
            if title_match:
                title_hits[label].add(paper_id)
            if abstract_match:
                abstract_hits[label].add(paper_id)
            if keyword_match:
                keyword_hits[label].add(paper_id)
        work_labels[paper_id] = matched
    n = len(works)
    abstract_n = len(with_abstract)
    frequency: list[dict[str, Any]] = []
    for item in dictionary:
        label = item["label"]
        frequency.append(
            descriptive_row(
                section=item["group"],
                measure="Predefined phrase frequency",
                category=label,
                count=len(hits[label]),
                denominator=n,
                percent=percent(len(hits[label]), n),
                title_count=len(title_hits[label]),
                abstract_count=len(abstract_hits[label]),
                keyword_count=len(keyword_hits[label]),
                unit="unique studies",
                denominator_definition="all unique studies",
                response_type="multiple response; each phrase label counted at most once per work",
                work_ids=";".join(sorted(hits[label])),
                note="Exact prespecified variants only; NFKC, case-insensitive, whole phrase, hyphen/space equivalent; no stemming or added synonyms.",
            )
        )
        frequency.append(
            descriptive_row(
                section=item["group"],
                measure="Retained-abstract sensitivity frequency",
                category=label,
                count=len(hits[label] & with_abstract_ids),
                denominator=abstract_n,
                percent=percent(len(hits[label] & with_abstract_ids), abstract_n),
                title_count=len(title_hits[label] & with_abstract_ids),
                abstract_count=len(abstract_hits[label]),
                keyword_count=len(keyword_hits[label] & with_abstract_ids),
                unit="unique studies with a retained abstract",
                denominator_definition="unique studies with a retained abstract",
                response_type="multiple response; each phrase label counted at most once per work",
                work_ids=";".join(sorted(abstract_hits[label])),
                note=(
                    "Not estimable because no canonical work retained an abstract."
                    if abstract_n == 0
                    else "The same title, abstract and keyword search, restricted to studies with a retained abstract."
                ),
            )
        )
    pair_rows: list[dict[str, Any]] = []
    for left, right in itertools.combinations([item["label"] for item in dictionary], 2):
        shared = sorted(hits[left] & hits[right])
        if len(shared) < 3:
            continue
        pair_rows.append(
            descriptive_row(
                section="Phrase co-occurrence",
                measure="Same-work phrase pair",
                category=f"{left} + {right}",
                count=len(shared),
                denominator=n,
                percent=percent(len(shared), n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="multiple response pair; minimum pair count 3",
                work_ids=";".join(shared),
                note="Descriptive same-work co-occurrence only.",
            )
        )
    pair_rows.sort(key=lambda row: (-int(row["count"]), row["category"]))
    groups = {item["label"]: item["group"] for item in dictionary}
    network_rows = [
        row
        for row in pair_rows
        if all(
            groups[label] != "scope_check" and len(hits[label]) >= 5
            for label in row["category"].split(" + ")
        )
    ][:25]
    return frequency, pair_rows, network_rows, hits


def quantile(values: Sequence[int], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=float), q * 100.0, method="linear"))


def citation_statistics(values: Sequence[int]) -> dict[str, Any]:
    if not values:
        return {
            "n": 0,
            "sum": None,
            "mean": None,
            "median": None,
            "q1": None,
            "q3": None,
            "minimum": None,
            "maximum": None,
            "zero_count": 0,
        }
    return {
        "n": len(values),
        "sum": int(sum(values)),
        "mean": float(sum(values) / len(values)),
        "median": quantile(values, 0.5),
        "q1": quantile(values, 0.25),
        "q3": quantile(values, 0.75),
        "minimum": int(min(values)),
        "maximum": int(max(values)),
        "zero_count": int(sum(value == 0 for value in values)),
    }


def normalize_source_key(
    row: Mapping[str, str], documented_name_fallback: str = ""
) -> tuple[str, str]:
    fallback = clean(documented_name_fallback)
    if clean(row["source_id"]):
        return (
            "openalex:" + row["source_id"].casefold(),
            clean(row["source_name"]) or fallback or row["source_id"],
        )
    if clean(row["source_issn_l"]):
        return (
            "issn-l:" + row["source_issn_l"].casefold(),
            clean(row["source_name"]) or fallback or row["source_issn_l"],
        )
    display = clean(row["source_name"]) or fallback
    name = " ".join(unicodedata.normalize("NFKC", display).casefold().split())
    if name:
        return "name:" + name, display
    return "unknown", "Unknown source"


def build_analysis(
    *,
    spec: Mapping[str, Any],
    raw: Mapping[str, Any],
    normalization: Mapping[str, Any],
    dedup: Mapping[str, Any],
    candidate: Mapping[str, Any],
    comparison: Mapping[str, Any],
    finalization: Mapping[str, Any],
    extraction: Mapping[str, Any],
    metadata: Mapping[str, Any],
    openalex: Mapping[str, Any],
) -> dict[str, Any]:
    works = metadata["analysis_rows"]
    n = len(works)
    oa_by_id = openalex["by_id"]
    work_ids = [row["paper_id"] for row in works]

    final_decisions = Counter(row["final_decision"] for row in finalization["rows"])
    final_codes = Counter(row["final_primary_code"] for row in finalization["rows"])
    eligible_versions = len(finalization["included_rows"])
    additional_versions = eligible_versions - n
    flow = [
        ("Retrieval occurrences", raw["retrieval_occurrences"], "all saved source/query retrieval occurrences"),
        ("Automatically merged duplicate occurrences", dedup["automatic_duplicate_reduction"], "duplicate source records merged using exact or cautious automatic rules"),
        ("Records after automatic duplicate merging", dedup["pre_review_deduplicated_records"], "bibliographic records after automatic duplicate merging"),
        ("Separately checked same-record merges", dedup["reviewed_same_record_reduction"], "additional same-record duplicate merges after separate review"),
        ("Unique bibliographic records after deduplication", dedup["deduplicated_records"], "bibliographic records after automatic and separately checked duplicate merging"),
        ("Records outside the four-domain candidate trigger", dedup["deduplicated_records"] - len(candidate["rows"]), "deduplicated records not entering the review population"),
        ("Candidate records reviewed by both models", len(candidate["rows"]), "all candidate records before resolution"),
        ("Records excluded after resolution", final_decisions.get("EXCLUDE", 0), "all candidate records before resolution"),
        ("Eligible publication records", eligible_versions, "included publication records before publication-version consolidation"),
        ("Additional publications linked to another eligible version", additional_versions, "eligible publication records linked to another report of the same study"),
        ("Unique studies", n, "one preferred publication record per systematically reviewed study family"),
    ]
    if (
        raw["retrieval_occurrences"] != normalization["retrieval_occurrences"]
        or normalization["retrieval_occurrences"] != dedup["retrieval_occurrences"]
        or dedup["deduplicated_records"] > normalization["retrieval_occurrences"]
        or len(candidate["rows"]) > dedup["deduplicated_records"]
        or n > eligible_versions
    ):
        raise FreshAnalysisError("Selection-flow counts violate the validated stage ordering")
    complete_flow_rows: list[dict[str, Any]] = []
    for source, count in raw["by_source"].items():
        complete_flow_rows.append(
            descriptive_row(
                section="Selection flow",
                measure="Retrieval occurrence by source",
                category=plain_label(source),
                count=count,
                denominator=raw["retrieval_occurrences"],
                percent=percent(count, raw["retrieval_occurrences"]),
                unit="source/query retrieval occurrences",
                denominator_definition="all saved source/query retrieval occurrences",
                response_type="single response by retrieval source",
                note="Counts precede cross-source normalization and deduplication.",
            )
        )
    complete_flow_rows.extend(
        descriptive_row(
            section="Selection flow",
            measure="Stage count",
            category=label,
            count=count,
            denominator="not applicable",
            unit="stage-specific records or works",
            denominator_definition=definition,
            response_type="stage-specific count",
            note="Unit changes are stated explicitly at each stage.",
        )
        for label, count, definition in flow
    )
    for decision in sorted(final_decisions):
        complete_flow_rows.append(
            descriptive_row(
                section="Selection flow",
                measure="Final record-level decision",
                category=plain_label(decision),
                count=final_decisions[decision],
                denominator=len(candidate["rows"]),
                percent=percent(final_decisions[decision], len(candidate["rows"])),
                unit="candidate records",
                denominator_definition="all candidate records before resolution",
                response_type="single response; mutually exclusive final decisions",
                note="Decision after conflict/uncertainty resolution; no human reference standard.",
            )
        )
    for code, count in sorted(final_codes.items()):
        if code == "INCLUDE":
            continue
        complete_flow_rows.append(
            descriptive_row(
                section="Selection flow",
                measure="Final primary exclusion reason",
                category=EXCLUSION_CODE_LABELS.get(code, plain_label(code)),
                count=count,
                denominator=len(candidate["rows"]),
                percent=percent(count, len(candidate["rows"])),
                unit="candidate records",
                denominator_definition="all candidate records before resolution",
                response_type="single primary exclusion reason among mutually exclusive final decisions",
                note=f"Screening code {code}; counts sum to the final excluded total.",
            )
        )
    complete_flow_rows.append(
        descriptive_row(
            section="Selection flow",
            measure="Systematic publication-version consolidation",
            category="Eligible versions not selected as the preferred canonical representation",
            count=additional_versions,
            denominator=eligible_versions,
            percent=percent(
                additional_versions,
                eligible_versions,
            ),
            unit="eligible publication versions",
            denominator_definition="all eligible publication versions entering systematic version review",
            response_type="version-consolidation reduction count",
            note="These are alternate versions, not excluded scholarly works.",
        )
    )

    pairs_three = [
        (row["reviewer_A_decision"], row["reviewer_B_decision"])
        for row in comparison["rows"]
    ]
    pairs_binary = [
        (
            "INCLUDE" if left == "INCLUDE" else "NON_INCLUDE",
            "INCLUDE" if right == "INCLUDE" else "NON_INCLUDE",
        )
        for left, right in pairs_three
    ]
    agreement_three = analyse_agreement(
        pairs_three, AGREEMENT_DECISIONS, replicates=10_000, seed=2026081306
    )
    agreement_binary = analyse_agreement(
        pairs_binary, ("NON_INCLUDE", "INCLUDE"), replicates=10_000, seed=2026081306
    )
    table1: list[dict[str, Any]] = []
    for source, count in raw["by_source"].items():
        table1.append(
            agreement_row(
                section="Selection flow",
                measure="Retrieval occurrence by source",
                category=plain_label(source),
                numerator=count,
                denominator=raw["retrieval_occurrences"],
                estimate=percent(count, raw["retrieval_occurrences"]),
                denominator_definition="all saved source/query retrieval occurrences",
                response_type="single response by retrieval source",
                value_text="percent of retrieval occurrences",
                note="Counts precede cross-source normalization and duplicate merging.",
            )
        )
    for label, count, definition in flow:
        table1.append(
            agreement_row(
                section="Selection flow",
                measure="Stage count",
                category=label,
                numerator=count,
                denominator="not applicable",
                denominator_definition=definition,
                response_type="stage-specific count",
                note="Counts use the analysis unit stated for this stage.",
            )
        )
    for label, result in (
        ("Three-choice include/exclude/uncertain", agreement_three),
        ("Binary include versus non-include", agreement_binary),
    ):
        table1.append(
            agreement_row(
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
        table1.append(
            agreement_row(
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
                    "Record-level percentile bootstrap; 10,000 replicates; seed 2026081306"
                    if result["kappa_interval_status"] == "reported"
                    else "CI withheld because more than 5% of bootstrap replicates were undefined"
                ),
                denominator_definition="all candidate records before resolution",
                response_type="paired model-review decisions",
                note=f"Undefined bootstrap replicates: {result['bootstrap_replicates_undefined']}.",
            )
        )
    table1.append(
        agreement_row(
            section="Prospective human audit",
            measure="Audit result",
            category="Fresh candidate and boundary-negative review",
            numerator="not applicable",
            denominator="not applicable",
            denominator_definition="no prospective fresh-run human audit sample exists",
            response_type="not performed",
            value_text=HUMAN_AUDIT_DISPLAY,
            note="No human error rate or human confidence interval was calculated.",
        )
    )

    years = list(range(2020, 2027))
    year_ids: dict[str, list[str]] = {str(year): [] for year in years}
    year_ids["Missing"] = []
    for row in works:
        value = clean(row["year"])
        if value in year_ids:
            year_ids[value].append(row["paper_id"])
        elif not value:
            year_ids["Missing"].append(row["paper_id"])
        else:
            raise FreshAnalysisError(f"Canonical work year is outside the locked window: {value}")
    table2: list[dict[str, Any]] = []
    annual_rows: list[dict[str, Any]] = []
    for year in years:
        label = str(year) if year < 2026 else "2026 (1 Jan to 13 Aug; partial)"
        row = descriptive_row(
            section="Annual publications",
            measure="Observed annual count",
            category=label,
            count=len(year_ids[str(year)]),
            denominator=n,
            percent=percent(len(year_ids[str(year)]), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="single response; mutually exclusive publication-year categories",
            work_ids=";".join(year_ids[str(year)]),
            note=(
                "Partial observed period reported separately; not annualized."
                if year == 2026
                else "Complete calendar year."
            ),
        )
        annual_rows.append(row)
        table2.append(row)
    if year_ids["Missing"]:
        missing_year_row = descriptive_row(
            section="Annual publications",
            measure="Missing publication year",
            category="Missing",
            count=len(year_ids["Missing"]),
            denominator=n,
            percent=percent(len(year_ids["Missing"]), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="missingness category; not assigned to any year",
            work_ids=";".join(year_ids["Missing"]),
            note="Missing publication year is not treated as zero.",
        )
        annual_rows.append(missing_year_row)
        table2.append(missing_year_row)

    source_ids: defaultdict[str, list[str]] = defaultdict(list)
    source_display: dict[str, str] = {}
    retrieval_sources: defaultdict[str, list[str]] = defaultdict(list)
    oa_ids: defaultdict[str, list[str]] = defaultdict(list)
    citations: list[int] = []
    citation_ids: list[str] = []
    missing_citation_ids: list[str] = []
    country_ids: defaultdict[str, list[str]] = defaultdict(list)
    country_fractional: Counter[str] = Counter()
    works_with_country: list[str] = []
    international_collaboration_ids: list[str] = []
    author_works: defaultdict[str, set[str]] = defaultdict(set)
    author_display: dict[str, str] = {}
    author_identity_type: dict[str, str] = {}
    works_with_authors: list[str] = []
    oa_parsed_authors: dict[str, list[dict[str, Any]]] = {}
    for work in works:
        paper_id = work["paper_id"]
        oa = oa_by_id[paper_id]
        source_key, display = normalize_source_key(oa, work["journal"])
        source_ids[source_key].append(paper_id)
        source_display[source_key] = display
        for source in split_semicolon(work["found_in_sources"]):
            retrieval_sources[source].append(paper_id)
        category = clean(oa["oa_status"]).casefold() or "unknown"
        if oa["match_status"] == "UNMATCHED":
            category = "unknown"
        if category not in OA_CATEGORIES:
            raise FreshAnalysisError(f"Unexpected OpenAlex OA status for {paper_id}: {category}")
        oa_ids[category].append(paper_id)
        cited = clean(oa["cited_by_count"])
        if oa["match_status"] == "MATCHED" and cited:
            value = integer(cited, f"OpenAlex citations for {paper_id}")
            citations.append(value)
            citation_ids.append(paper_id)
        else:
            missing_citation_ids.append(paper_id)
        raw_authors = clean(oa["authors_json"])
        if raw_authors:
            try:
                parsed = json.loads(raw_authors)
            except json.JSONDecodeError as exc:
                raise FreshAnalysisError(f"Invalid OpenAlex authors_json for {paper_id}") from exc
            if not isinstance(parsed, list):
                raise FreshAnalysisError(f"OpenAlex authors_json is not a list for {paper_id}")
        else:
            parsed = []
        oa_parsed_authors[paper_id] = parsed
        usable_author = False
        countries: set[str] = set()
        seen_author_keys: set[str] = set()
        identified_signatures: defaultdict[tuple[str, str, tuple[str, ...]], set[str]] = (
            defaultdict(set)
        )
        for author in parsed:
            if not isinstance(author, Mapping):
                raise FreshAnalysisError(f"Malformed OpenAlex authorship for {paper_id}")
            author_id = clean(author.get("author_id"))
            name_key = " ".join(
                unicodedata.normalize("NFKC", clean(author.get("author_name")))
                .casefold()
                .split()
            )
            orcid = clean(author.get("orcid")).casefold()
            institution_ids = author.get("institution_ids") or []
            if not isinstance(institution_ids, list):
                raise FreshAnalysisError(
                    f"Malformed OpenAlex author institution IDs for {paper_id}"
                )
            signature = (
                name_key,
                orcid,
                tuple(sorted(clean(value).casefold() for value in institution_ids if clean(value))),
            )
            if author_id:
                identified_signatures[signature].add(author_id)
        for index, author in enumerate(parsed, start=1):
            if not isinstance(author, Mapping):
                raise FreshAnalysisError(f"Malformed OpenAlex authorship for {paper_id}")
            author_id = clean(author.get("author_id"))
            name = clean(author.get("author_name"))
            if not author_id and not name:
                continue
            usable_author = True
            if author_id:
                key = "openalex:" + author_id.casefold()
                identity = "OpenAlex author ID"
            else:
                name_key = " ".join(
                    unicodedata.normalize("NFKC", name).casefold().split()
                )
                orcid = clean(author.get("orcid")).casefold()
                institution_ids = author.get("institution_ids") or []
                signature = (
                    name_key,
                    orcid,
                    tuple(
                        sorted(
                            clean(value).casefold()
                            for value in institution_ids
                            if clean(value)
                        )
                    ),
                )
                identified_matches = identified_signatures.get(signature, set())
                if len(identified_matches) == 1:
                    matched_id = next(iter(identified_matches))
                    key = "openalex:" + matched_id.casefold()
                    identity = "OpenAlex author ID; duplicate name-only authorship collapsed within work"
                else:
                    signature_hash = sha256_text(canonical_json(signature))[:16]
                    key = f"name-only:{paper_id}:{signature_hash}"
                    identity = "name-only record; duplicates collapsed within work only; not merged across works"
            if key not in seen_author_keys:
                author_works[key].add(paper_id)
                author_display[key] = name or author_id
                author_identity_type[key] = identity
                seen_author_keys.add(key)
            raw_countries = author.get("countries") or []
            if not isinstance(raw_countries, list):
                raise FreshAnalysisError(f"Malformed OpenAlex author countries for {paper_id}")
            countries.update(clean(code).upper() for code in raw_countries if clean(code))
        if usable_author:
            works_with_authors.append(paper_id)
        if countries:
            works_with_country.append(paper_id)
            if len(countries) > 1:
                international_collaboration_ids.append(paper_id)
            weight = 1.0 / len(countries)
            for country in sorted(countries):
                country_ids[country].append(paper_id)
                country_fractional[country] += weight

    source_rows = [
        descriptive_row(
            section="Publication source",
            measure="Source frequency",
            category=source_display[key],
            count=len(ids),
            denominator=n,
            percent=percent(len(ids), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="single response; mutually exclusive normalized publication source",
            work_ids=";".join(ids),
            note=(
                "Unknown source is retained as a separate missingness category."
                if key == "unknown"
                else f"Normalization key: {key}."
            ),
        )
        for key, ids in source_ids.items()
    ]
    source_rows.sort(key=lambda row: (-int(row["count"]), row["category"].casefold()))
    named_source_rows = [row for row in source_rows if row["category"] != "Unknown source"]
    top_named_source_rows = named_source_rows[:10]
    other_named_source_ids = sorted(
        paper_id
        for row in named_source_rows[10:]
        for paper_id in split_semicolon(row["work_ids"])
    )
    known_source_ids = sorted(
        paper_id
        for row in named_source_rows
        for paper_id in split_semicolon(row["work_ids"])
    )
    unknown_source_ids = sorted(source_ids.get("unknown", []))
    source_summary_rows = [
        descriptive_row(
            section="Publication source",
            measure="Source frequency",
            category="Other named sources",
            count=len(other_named_source_ids),
            denominator=n,
            percent=percent(len(other_named_source_ids), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="single response; aggregate of named sources below the top ten",
            work_ids=";".join(other_named_source_ids),
            note="Each study appears in only one normalized publication-source category.",
        ),
        descriptive_row(
            section="Publication source",
            measure="Normalized-source coverage",
            category="Named source available",
            count=len(known_source_ids),
            denominator=n,
            percent=percent(len(known_source_ids), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="coverage; mutually exclusive with unknown source",
            work_ids=";".join(known_source_ids),
            note="OpenAlex source, ISSN-L, or documented source-name fallback was available.",
        ),
        descriptive_row(
            section="Publication source",
            measure="Normalized-source coverage",
            category="Unknown source",
            count=len(unknown_source_ids),
            denominator=n,
            percent=percent(len(unknown_source_ids), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="missingness; mutually exclusive with named source available",
            work_ids=";".join(unknown_source_ids),
            note="An unknown source is retained as missing and is not assigned to another journal.",
        ),
    ]
    table2.extend(top_named_source_rows + source_summary_rows)
    oa_rows = [
        descriptive_row(
            section="Open access",
            measure="OpenAlex OA status",
            category=plain_label(category),
            count=len(oa_ids[category]),
            denominator=n,
            percent=percent(len(oa_ids[category]), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="single response; mutually exclusive OA categories",
            work_ids=";".join(oa_ids[category]),
            note=(
                "Unknown is not treated as closed."
                if category == "unknown"
                else "Status from the fixed OpenAlex snapshot."
            ),
        )
        for category in OA_CATEGORIES
    ]
    known_oa_ids = sorted(
        paper_id
        for category in OA_CATEGORIES
        if category != "unknown"
        for paper_id in oa_ids[category]
    )
    oa_rows.extend(
        [
            descriptive_row(
                section="Open access",
                measure="Open-access metadata coverage",
                category="Known status",
                count=len(known_oa_ids),
                denominator=n,
                percent=percent(len(known_oa_ids), n),
                unit="unique studies",
                denominator_definition="all unique studies",
                response_type="coverage; mutually exclusive with unknown status",
                work_ids=";".join(known_oa_ids),
                note="A status was available in the fixed OpenAlex snapshot.",
            ),
            descriptive_row(
                section="Open access",
                measure="Open-access metadata coverage",
                category="Unknown status",
                count=len(oa_ids["unknown"]),
                denominator=n,
                percent=percent(len(oa_ids["unknown"]), n),
                unit="unique studies",
                denominator_definition="all unique studies",
                response_type="coverage; mutually exclusive with known status",
                work_ids=";".join(oa_ids["unknown"]),
                note="Unknown or unmatched records are not counted as closed.",
            ),
        ]
    )
    table2.extend(oa_rows)
    citation_stats = citation_statistics(citations)
    table2.append(
        descriptive_row(
            section="Citations",
            measure="Citation coverage",
            category="Fixed OpenAlex citation value available",
            count=len(citations),
            denominator=n,
            percent=percent(len(citations), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="coverage",
            work_ids=";".join(citation_ids),
            note="Missing citation values are not treated as zero.",
        )
    )
    table2.append(
        descriptive_row(
            section="Citations",
            measure="Citation missingness",
            category="Missing fixed-snapshot citation value",
            count=len(missing_citation_ids),
            denominator=n,
            percent=percent(len(missing_citation_ids), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="missingness",
            work_ids=";".join(missing_citation_ids),
            note="Missing is distinct from an explicit citation count of zero.",
        )
    )
    citation_names = ["n", "sum", "mean", "median", "q1", "q3", "minimum", "maximum", "zero_count"]
    for name in citation_names:
        value = citation_stats[name]
        table2.append(
            descriptive_row(
                section="Citations",
                measure="Citation distribution",
                category=plain_label(name),
                denominator=len(citations),
                value=value,
                value_text="not estimable" if value is None else "",
                unit="citations" if name != "n" else "canonical works with citation value",
                denominator_definition="canonical works with a value from the fixed OpenAlex snapshot",
                response_type="summary statistic",
                note=(
                    "Quartiles use linear interpolation."
                    if name in {"q1", "median", "q3"}
                    else "Explicit zeros contribute to the distribution."
                ),
            )
        )
    missing_country_ids = [paper_id for paper_id in work_ids if paper_id not in set(works_with_country)]
    missing_author_ids = [paper_id for paper_id in work_ids if paper_id not in set(works_with_authors)]
    coverage_main_rows = [
            descriptive_row(
                section="Coverage",
                measure="OpenAlex match coverage",
                category="Matched",
                count=openalex["matched"],
                denominator=n,
                percent=percent(openalex["matched"], n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="coverage",
                note="Validated fixed OpenAlex snapshot match.",
            ),
            descriptive_row(
                section="Coverage",
                measure="OpenAlex match coverage",
                category="Unmatched",
                count=openalex["unmatched"],
                denominator=n,
                percent=percent(openalex["unmatched"], n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="missingness category; mutually exclusive with matched",
                note="Confirmed unmatched records retain OpenAlex-dependent values as missing.",
            ),
            descriptive_row(
                section="Coverage",
                measure="Country-affiliation coverage",
                category="At least one usable country affiliation",
                count=len(works_with_country),
                denominator=n,
                percent=percent(len(works_with_country), n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="coverage",
                work_ids=";".join(works_with_country),
                note="No country is imputed for uncovered works.",
            ),
            descriptive_row(
                section="Coverage",
                measure="Country-affiliation coverage",
                category="No usable country affiliation",
                count=len(missing_country_ids),
                denominator=n,
                percent=percent(len(missing_country_ids), n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="missingness category; mutually exclusive with covered",
                work_ids=";".join(missing_country_ids),
                note="Missing affiliation country is not treated as zero.",
            ),
            descriptive_row(
                section="Coverage",
                measure="Authorship coverage",
                category="Usable structured OpenAlex authorship",
                count=len(works_with_authors),
                denominator=n,
                percent=percent(len(works_with_authors), n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="coverage",
                work_ids=";".join(works_with_authors),
                note="Name-only authors are not merged across works.",
            ),
            descriptive_row(
                section="Coverage",
                measure="Authorship coverage",
                category="No usable structured authorship",
                count=len(missing_author_ids),
                denominator=n,
                percent=percent(len(missing_author_ids), n),
                unit="canonical works",
                denominator_definition="all canonical works",
                response_type="missingness category; mutually exclusive with covered",
                work_ids=";".join(missing_author_ids),
                note="Missing structured authorship is not treated as zero authors.",
            ),
        ]
    table2.extend(coverage_main_rows)

    labels = spec["study_level_labels"]
    model_rows, model_ids = frequency_rows(
        works,
        "final_model_families",
        labels["model_families"],
        section="Model families",
        denominator_definition="all canonical works",
    )
    no_exact_model_ids = [
        row["paper_id"]
        for row in works
        if set(split_semicolon(row["final_model_families"]))
        == {"unspecified_generative_model"}
    ]
    model_rows.append(
        descriptive_row(
            section="Model families",
            measure="Model-family evidence coverage",
            category="No exact model family established",
            count=len(no_exact_model_ids),
            denominator=n,
            percent=percent(len(no_exact_model_ids), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="summary coverage row; separate from multiple-response family frequencies",
            work_ids=";".join(no_exact_model_ids),
            note="The study named only a generative model in general; a family was not inferred.",
        )
    )
    simulation_rows, simulation_ids = frequency_rows(
        works,
        "final_simulation_modalities",
        labels["simulation_methods"],
        section="Simulation methods",
        denominator_definition="all canonical works",
        blank_label="no_explicit_simulation_method",
    )
    design_rows, design_ids = frequency_rows(
        works,
        "final_study_design",
        labels["study_designs"],
        section="Study designs",
        denominator_definition="all canonical works",
    )
    table3 = model_rows + simulation_rows + design_rows
    nts_blank = "no_explicit_nts"
    nts_rows, nts_ids = frequency_rows(
        works,
        "final_nts_domains",
        labels["nts_domains"],
        section="Non-technical skills domains",
        denominator_definition="all canonical works",
        blank_label=nts_blank,
    )
    explicit_nts_ids = sorted(
        {paper_id for label in labels["nts_domains"] for paper_id in nts_ids[label]}
    )
    table4: list[dict[str, Any]] = [
        descriptive_row(
            section="Non-technical skills domains",
            measure="NTS evidence coverage",
            category="At least one explicit NTS domain",
            count=len(explicit_nts_ids),
            denominator=n,
            percent=percent(len(explicit_nts_ids), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="coverage; mutually exclusive with no explicit NTS domain",
            work_ids=";".join(explicit_nts_ids),
            note="Based only on the final checked study-level extraction.",
        )
    ]
    for row in nts_rows:
        raw_label = next(
            label for label in [*labels["nts_domains"], nts_blank] if plain_label(label) == row["category"]
        )
        row["note"] = (
            "No explicit checked NTS domain; blank is not treated as zero evidence."
            if raw_label == nts_blank
            else "Final checked extraction only; phrase matches do not create NTS labels."
        )
        table4.append(row)
        if raw_label != nts_blank:
            count = len(nts_ids[raw_label])
            table4.append(
                descriptive_row(
                    section="Non-technical skills domains",
                    measure="Frequency among NTS-explicit works",
                    category=plain_label(raw_label),
                    count=count,
                    denominator=len(explicit_nts_ids),
                    percent=percent(count, len(explicit_nts_ids)),
                    unit="canonical works",
                    denominator_definition="canonical works with at least one explicit checked NTS domain",
                    response_type="multiple response; percentages may sum to more than 100%",
                    work_ids=";".join(nts_ids[raw_label]),
                    note="Secondary prespecified denominator.",
                )
            )

    specialty_ids: defaultdict[str, list[str]] = defaultdict(list)
    specialty_display: dict[str, str] = {}
    no_specialty: list[str] = []
    for row in works:
        values = split_semicolon(row["final_specialty"])
        if not values:
            no_specialty.append(row["paper_id"])
        seen_specialties: set[str] = set()
        for value in values:
            key = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
            if key in seen_specialties:
                continue
            seen_specialties.add(key)
            specialty_ids[key].append(row["paper_id"])
            specialty_display.setdefault(key, plain_label(value))
    specialty_rows = [
        descriptive_row(
            section="Specialties and professions",
            measure="Checked specialty/profession frequency",
            category=specialty_display[key],
            count=len(ids),
            denominator=n,
            percent=percent(len(ids), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="multiple response; percentages may sum to more than 100%",
            work_ids=";".join(ids),
            note="Source-grounded checked free-text category; counted once per work.",
        )
        for key, ids in specialty_ids.items()
    ]
    specialty_rows.sort(key=lambda row: (-int(row["count"]), row["category"].casefold()))
    specialty_rows.append(
        descriptive_row(
            section="Specialties and professions",
            measure="Checked specialty/profession missingness",
            category="No explicit specialty or profession identified",
            count=len(no_specialty),
            denominator=n,
            percent=percent(len(no_specialty), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="missingness category",
            work_ids=";".join(no_specialty),
            note="Missing specialty/profession is not treated as zero.",
        )
    )

    general_specialty_keys = {
        "medicine",
        "general medical education",
        "health professions",
        "health professions education",
        "healthcare professionals",
        "healthcare education",
        "interprofessional",
        "simulation education",
        "medical education faculty development",
        "undergraduate medical education",
    }
    surgical_specialty_keys = {
        "surgery",
        "general surgery",
        "urology",
        "orthopaedic surgery",
        "neurosurgery",
        "otolaryngology",
        "plastic surgery",
        "cardiothoracic surgery",
        "vascular surgery",
        "paediatric surgery",
        "transplant surgery",
        "bariatric surgery",
        "spine surgery",
        "obstetrics gynaecology",
    }
    specialty_row_by_key = {
        " ".join(row["category"].casefold().split()): row
        for row in specialty_rows
        if row["measure"] == "Checked specialty/profession frequency"
    }
    general_rows = [
        specialty_row_by_key[key]
        for key in general_specialty_keys
        if key in specialty_row_by_key
    ]
    surgical_rows = [
        specialty_row_by_key[key]
        for key in surgical_specialty_keys
        if key in specialty_row_by_key and int(specialty_row_by_key[key]["count"]) > 0
    ]
    selected_specialty_keys = {
        " ".join(row["category"].casefold().split()) for row in [*general_rows, *surgical_rows]
    }
    remaining_rows = [
        row
        for key, row in specialty_row_by_key.items()
        if key not in selected_specialty_keys
    ][:10]
    specialty_plot_rows = [*general_rows, *surgical_rows, *remaining_rows]
    specialty_plot_rows.sort(key=lambda row: (-int(row["count"]), row["category"].casefold()))

    country_rows = [
        descriptive_row(
            section="Geography",
            measure="Whole-count country affiliation",
            category=country,
            count=len(ids),
            denominator=len(works_with_country),
            percent=percent(len(ids), len(works_with_country)),
            unit="country-affiliated canonical works",
            denominator_definition="canonical works with at least one usable country affiliation",
            response_type="multiple response whole counting; percentages may sum to more than 100%",
            work_ids=";".join(ids),
            note="Each represented country receives one whole count per work.",
        )
        for country, ids in country_ids.items()
    ]
    country_rows.sort(key=lambda row: (-int(row["count"]), row["category"]))
    fractional_rows = [
        descriptive_row(
            section="Geography",
            measure="Fractional country affiliation",
            category=country,
            denominator=len(works_with_country),
            value=round(country_fractional[country], 6),
            unit="fractional canonical works",
            denominator_definition="canonical works with at least one usable country affiliation",
            response_type="fractional response; each covered work contributes total weight 1 across its countries",
            work_ids=";".join(country_ids[country]),
            note="No missing country was imputed.",
        )
        for country in sorted(country_fractional, key=lambda x: (-country_fractional[x], x))
    ]
    country_all_n_rows = [
        descriptive_row(
            section="Geography",
            measure="Whole-count country affiliation (all-study denominator)",
            category=country,
            count=len(ids),
            denominator=n,
            percent=percent(len(ids), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="multiple response whole counting; percentages may sum to more than 100%",
            work_ids=";".join(ids),
            note="Supplementary all-study percentage; missing countries are not imputed.",
        )
        for country, ids in sorted(
            country_ids.items(), key=lambda item: (-len(item[1]), item[0])
        )
    ]
    geography_coverage_rows = [
        descriptive_row(
            section="Geography",
            measure="Country-affiliation coverage",
            category="Covered",
            count=len(works_with_country),
            denominator=n,
            percent=percent(len(works_with_country), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="coverage",
            work_ids=";".join(works_with_country),
            note="Works without a usable country remain missing, not zero-country works.",
        ),
        descriptive_row(
            section="Geography",
            measure="Country-affiliation coverage",
            category="No usable country affiliation",
            count=len(missing_country_ids),
            denominator=n,
            percent=percent(len(missing_country_ids), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="missingness category; mutually exclusive with covered",
            work_ids=";".join(missing_country_ids),
            note="Missing country affiliation is retained as missing and is never imputed.",
        ),
        descriptive_row(
            section="Geography",
            measure="International collaboration",
            category="More than one country affiliation",
            count=len(international_collaboration_ids),
            denominator=len(works_with_country),
            percent=percent(len(international_collaboration_ids), len(works_with_country)),
            unit="country-affiliated unique studies",
            denominator_definition="unique studies with at least one usable country affiliation",
            response_type="binary within covered studies",
            work_ids=";".join(international_collaboration_ids),
            note="Works without country data are not classified as domestic or international.",
        ),
    ]
    top_country_codes = [row["category"] for row in country_rows[:10]]
    whole_by_country = {row["category"]: row for row in country_rows}
    fractional_by_country = {row["category"]: row for row in fractional_rows}
    table5: list[dict[str, Any]] = []
    for code in top_country_codes:
        whole = dict(whole_by_country[code])
        fractional = dict(fractional_by_country[code])
        whole["category"] = country_label(code)
        fractional["category"] = country_label(code)
        table5.extend((whole, fractional))
    table5.extend(geography_coverage_rows)

    phrase_rows, pair_rows, network_rows, phrase_hits = phrase_analysis(works, spec)
    table6 = [row for row in phrase_rows if row["measure"] == "Predefined phrase frequency"]
    network_node_labels = sorted(
        {
            label
            for row in network_rows
            for label in row["category"].split(" + ")
        },
        key=str.casefold,
    )
    network_node_rows = [
        descriptive_row(
            section="Conditional phrase network",
            measure="Node work frequency",
            category=label,
            count=len(phrase_hits[label]),
            denominator=n,
            percent=percent(len(phrase_hits[label]), n),
            unit="unique studies",
            denominator_definition="all unique studies",
            response_type="multiple response; each phrase counted at most once per study",
            work_ids=";".join(sorted(phrase_hits[label])),
            note="Node size in the supplementary figure uses this work count.",
        )
        for label in network_node_labels
    ]
    phrase_dictionary = (spec.get("phrase_matching") or {}).get("dictionary") or []
    phrase_indicator_fields = ["paper_id", *[item["label"] for item in phrase_dictionary]]
    phrase_indicator_rows = [
        {
            "paper_id": paper_id,
            **{
                item["label"]: "1" if paper_id in phrase_hits[item["label"]] else "0"
                for item in phrase_dictionary
            },
        }
        for paper_id in work_ids
    ]
    phrase_dictionary_fields = ["group", "label", "variants"]
    phrase_dictionary_rows = [
        {
            "group": item["group"],
            "label": item["label"],
            "variants": " | ".join(item["variants"]),
        }
        for item in phrase_dictionary
    ]

    # Sensitivity 1: remove records that are available only as a standalone
    # preprint or other repository version.  This rule is fixed in Amendment
    # 002 and never changes the primary 470-study corpus.
    preprint_repository_excluded_ids = {
        row["paper_id"]
        for row in works
        if integer(row["family_size"], f"family size/{row['paper_id']}") == 1
        and (
            clean(row["version_role"]).casefold() in {"preprint", "other_version"}
            or "preprint" in clean(row["record_type"]).casefold()
        )
    }
    preprint_sensitivity_works = [
        row for row in works if row["paper_id"] not in preprint_repository_excluded_ids
    ]
    preprint_n = len(preprint_sensitivity_works)
    preprint_sensitivity_rows: list[dict[str, Any]] = [
        descriptive_row(
            section="Preprint/repository sensitivity",
            measure="Cohort coverage",
            category="Studies retained",
            count=preprint_n,
            denominator=n,
            percent=percent(preprint_n, n),
            unit="unique studies",
            denominator_definition="all unique studies in the primary corpus",
            response_type="sensitivity cohort coverage",
            work_ids=";".join(row["paper_id"] for row in preprint_sensitivity_works),
            note="Primary results are unchanged; this is a secondary sensitivity cohort.",
        ),
        descriptive_row(
            section="Preprint/repository sensitivity",
            measure="Cohort coverage",
            category="Standalone preprint or repository-only studies excluded",
            count=len(preprint_repository_excluded_ids),
            denominator=n,
            percent=percent(len(preprint_repository_excluded_ids), n),
            unit="unique studies",
            denominator_definition="all unique studies in the primary corpus",
            response_type="sensitivity cohort exclusion",
            work_ids=";".join(sorted(preprint_repository_excluded_ids)),
            note="Rule: family size 1 and preprint/other-version role or explicit preprint record type.",
        ),
    ]
    for year in years:
        ids = [
            row["paper_id"]
            for row in preprint_sensitivity_works
            if clean(row["year"]) == str(year)
        ]
        preprint_sensitivity_rows.append(
            descriptive_row(
                section="Preprint/repository sensitivity: annual counts",
                measure="Observed annual count",
                category=str(year) if year < 2026 else "2026 (partial to 13 Aug)",
                count=len(ids),
                denominator=preprint_n,
                percent=percent(len(ids), preprint_n),
                unit="unique studies",
                denominator_definition="studies retained in the preprint/repository sensitivity cohort",
                response_type="single response publication-year category",
                work_ids=";".join(ids),
                note="2026 is observed only through 13 August and is not annualized.",
            )
        )
    for field, group, section, blank_label in (
        ("final_model_families", "model_families", "Model families", None),
        (
            "final_simulation_modalities",
            "simulation_methods",
            "Simulation methods",
            "no_explicit_simulation_method",
        ),
        ("final_nts_domains", "nts_domains", "Non-technical skills domains", "no_explicit_nts"),
        ("final_study_design", "study_designs", "Study designs", None),
    ):
        rows_for_field, _ids = frequency_rows(
            preprint_sensitivity_works,
            field,
            labels[group],
            section=f"Preprint/repository sensitivity: {section}",
            denominator_definition="studies retained in the preprint/repository sensitivity cohort",
            blank_label=blank_label,
        )
        preprint_sensitivity_rows.extend(rows_for_field)
    for row in specialty_rows:
        if row["measure"] != "Checked specialty/profession frequency":
            continue
        retained_ids = sorted(
            set(split_semicolon(row["work_ids"]))
            - preprint_repository_excluded_ids
        )
        sensitivity_row = dict(row)
        sensitivity_row.update(
            {
                "section": "Preprint/repository sensitivity: specialties and professions",
                "count": len(retained_ids),
                "denominator": preprint_n,
                "percent": percent(len(retained_ids), preprint_n),
                "unit": "unique studies",
                "denominator_definition": "studies retained in the preprint/repository sensitivity cohort",
                "work_ids": ";".join(retained_ids),
                "note": "Secondary sensitivity result; primary specialty counts remain based on all studies.",
            }
        )
        preprint_sensitivity_rows.append(sensitivity_row)
    preprint_phrase_rows, _preprint_pairs, _preprint_network, _preprint_hits = phrase_analysis(
        preprint_sensitivity_works, spec
    )

    # Sensitivity 2: retain only fixed-snapshot metadata matches made through
    # an exact DOI or exact OpenAlex work identifier.  Title-search matches
    # remain in the primary analysis but are excluded from this stricter view.
    exact_metadata_ids = {
        paper_id
        for paper_id in work_ids
        if clean(oa_by_id[paper_id]["match_method"]).casefold()
        in {"doi_exact", "openalex_id_exact"}
    }
    exact_n = len(exact_metadata_ids)
    exact_metadata_rows: list[dict[str, Any]] = [
        descriptive_row(
            section="Exact-identifier metadata sensitivity",
            measure="Cohort coverage",
            category="Exact DOI or OpenAlex-ID match",
            count=exact_n,
            denominator=n,
            percent=percent(exact_n, n),
            unit="unique studies",
            denominator_definition="all unique studies in the primary corpus",
            response_type="metadata sensitivity cohort coverage",
            work_ids=";".join(sorted(exact_metadata_ids)),
            note="Title-search matches and confirmed unmatched records are excluded only from this sensitivity view.",
        )
    ]
    for row in source_rows:
        retained_ids = sorted(set(split_semicolon(row["work_ids"])) & exact_metadata_ids)
        sensitivity_row = dict(row)
        sensitivity_row.update(
            {
                "section": "Exact-identifier metadata sensitivity: publication sources",
                "count": len(retained_ids),
                "denominator": exact_n,
                "percent": percent(len(retained_ids), exact_n),
                "unit": "unique studies",
                "denominator_definition": "studies with an exact DOI or OpenAlex-ID match",
                "work_ids": ";".join(retained_ids),
            }
        )
        exact_metadata_rows.append(sensitivity_row)
    for category in OA_CATEGORIES:
        retained_ids = sorted(set(oa_ids[category]) & exact_metadata_ids)
        exact_metadata_rows.append(
            descriptive_row(
                section="Exact-identifier metadata sensitivity: open access",
                measure="OpenAlex OA status",
                category=plain_label(category),
                count=len(retained_ids),
                denominator=exact_n,
                percent=percent(len(retained_ids), exact_n),
                unit="unique studies",
                denominator_definition="studies with an exact DOI or OpenAlex-ID match",
                response_type="single response; mutually exclusive OA categories",
                work_ids=";".join(retained_ids),
                note="Point-in-time status from the fixed OpenAlex snapshot.",
            )
        )
    exact_country_covered = sorted(set(works_with_country) & exact_metadata_ids)
    exact_author_covered = sorted(set(works_with_authors) & exact_metadata_ids)
    for label, ids in (
        ("Usable country affiliation", exact_country_covered),
        ("Usable structured authorship", exact_author_covered),
    ):
        exact_metadata_rows.append(
            descriptive_row(
                section="Exact-identifier metadata sensitivity: coverage",
                measure=label,
                category="Available",
                count=len(ids),
                denominator=exact_n,
                percent=percent(len(ids), exact_n),
                unit="unique studies",
                denominator_definition="studies with an exact DOI or OpenAlex-ID match",
                response_type="metadata coverage",
                work_ids=";".join(ids),
                note="Missing metadata remains missing and is not set to zero.",
            )
        )
    for country, ids in sorted(
        country_ids.items(), key=lambda item: (-len(set(item[1]) & exact_metadata_ids), item[0])
    ):
        retained_ids = sorted(set(ids) & exact_metadata_ids)
        exact_metadata_rows.append(
            descriptive_row(
                section="Exact-identifier metadata sensitivity: geography",
                measure="Whole-count country affiliation",
                category=country,
                count=len(retained_ids),
                denominator=len(exact_country_covered),
                percent=percent(len(retained_ids), len(exact_country_covered)),
                unit="country-affiliated unique studies",
                denominator_definition="exact-identifier studies with at least one usable country affiliation",
                response_type="multiple response whole counting; percentages may sum to more than 100%",
                work_ids=";".join(retained_ids),
                note="No country is inferred or imputed.",
            )
        )
    exact_international_ids = sorted(
        set(international_collaboration_ids) & exact_metadata_ids
    )
    exact_metadata_rows.append(
        descriptive_row(
            section="Exact-identifier metadata sensitivity: geography",
            measure="International collaboration",
            category="More than one country affiliation",
            count=len(exact_international_ids),
            denominator=len(exact_country_covered),
            percent=percent(len(exact_international_ids), len(exact_country_covered)),
            unit="country-affiliated unique studies",
            denominator_definition="exact-identifier studies with at least one usable country affiliation",
            response_type="binary within covered studies",
            work_ids=";".join(exact_international_ids),
            note="Studies without country data are not classified as domestic or international.",
        )
    )
    for author_key, ids in sorted(
        author_works.items(),
        key=lambda item: (-len(set(item[1]) & exact_metadata_ids), author_display[item[0]].casefold()),
    ):
        retained_ids = sorted(set(ids) & exact_metadata_ids)
        exact_metadata_rows.append(
            descriptive_row(
                section="Exact-identifier metadata sensitivity: authors",
                measure="Unique-author study count",
                category=author_display[author_key],
                count=len(retained_ids),
                denominator=len(exact_author_covered),
                percent=percent(len(retained_ids), len(exact_author_covered)),
                unit="authorship-covered unique studies",
                denominator_definition="exact-identifier studies with usable structured authorship",
                response_type="multiple response; one count per unique author per study",
                work_ids=";".join(retained_ids),
                note=author_identity_type[author_key],
            )
        )
    exact_citations = [
        integer(oa_by_id[paper_id]["cited_by_count"], f"exact-ID citations/{paper_id}")
        for paper_id in sorted(exact_metadata_ids)
        if clean(oa_by_id[paper_id]["cited_by_count"])
    ]
    exact_citation_stats = citation_statistics(exact_citations)
    for name in ("n", "sum", "mean", "median", "q1", "q3", "minimum", "maximum", "zero_count"):
        exact_metadata_rows.append(
            descriptive_row(
                section="Exact-identifier metadata sensitivity: citations",
                measure="Citation distribution",
                category=plain_label(name),
                denominator=len(exact_citations),
                value=exact_citation_stats[name],
                value_text="not estimable" if exact_citation_stats[name] is None else "",
                unit="citations" if name != "n" else "unique studies with a citation value",
                denominator_definition="exact-identifier studies with a fixed-snapshot citation value",
                response_type="summary statistic",
                note="Explicit zero values are retained; missing values are omitted.",
            )
        )

    author_rows = [
        descriptive_row(
            section="Author productivity",
            measure="Canonical work count",
            category=author_display[key],
            count=len(ids),
            denominator=len(works_with_authors),
            percent=percent(len(ids), len(works_with_authors)),
            value_text=key,
            unit="authorship-covered canonical works",
            denominator_definition="canonical works with usable structured OpenAlex authorship",
            response_type="multiple response; one count per unique author per work",
            work_ids=";".join(sorted(ids)),
            note=author_identity_type[key],
        )
        for key, ids in author_works.items()
    ]
    author_rows.sort(key=lambda row: (-int(row["count"]), row["category"].casefold()))
    author_productivity_distribution = Counter(len(ids) for ids in author_works.values())
    author_distribution_rows: list[dict[str, Any]] = []
    for label, author_count in (
        ("1 study", author_productivity_distribution.get(1, 0)),
        ("2 studies", author_productivity_distribution.get(2, 0)),
        ("3 studies", author_productivity_distribution.get(3, 0)),
        (">=4 studies", sum(count for works_count, count in author_productivity_distribution.items() if works_count >= 4)),
    ):
        author_distribution_rows.append(
            descriptive_row(
                section="Author productivity distribution",
                measure="Number of studies per unique author identity",
                category=label,
                count=author_count,
                denominator=len(author_works),
                percent=percent(author_count, len(author_works)),
                unit="unique author identities",
                denominator_definition="all usable structured author identities in the fixed OpenAlex snapshot",
                response_type="single response; mutually exclusive productivity bands",
                note="OpenAlex author IDs are used when available; unresolved name-only records are not merged across studies.",
            )
        )
    table2.extend(author_rows[:10])

    retrieval_source_rows = [
        descriptive_row(
            section="Retrieval-source coverage",
            measure="Canonical works found in source",
            category=source,
            count=len(ids),
            denominator=n,
            percent=percent(len(ids), n),
            unit="canonical works",
            denominator_definition="all canonical works",
            response_type="multiple response; percentages may sum to more than 100%",
            work_ids=";".join(ids),
            note="Source occurrence derived from preserved found_in_sources; counted once per work/source.",
        )
        for source, ids in sorted(retrieval_sources.items())
    ]
    all_work_id_set = set(work_ids)
    coverage_rows: list[dict[str, Any]] = []
    coverage_inputs = [
        ("Publication date", {row["paper_id"] for row in works if clean(row["publication_date"])}),
        ("Retained abstract", {row["paper_id"] for row in works if clean(row["abstract"])}),
        ("Normalized publication source", set(known_source_ids)),
        ("Structured authorship", set(works_with_authors)),
        ("Country affiliation", set(works_with_country)),
        ("Open-access status", set(known_oa_ids)),
        ("Citation value", set(citation_ids)),
        ("Checked model field", {row["paper_id"] for row in works if split_semicolon(row["final_model_families"])}),
        ("Checked simulation field", {row["paper_id"] for row in works if split_semicolon(row["final_simulation_modalities"])}),
        ("Explicit NTS domain", set(explicit_nts_ids)),
        ("Specialty or profession", all_work_id_set - set(no_specialty)),
        ("Study-design label", {row["paper_id"] for row in works if clean(row["final_study_design"])}),
    ]
    for label, present_ids in coverage_inputs:
        missing_ids = all_work_id_set - present_ids
        for category, ids, response in (
            ("Present", sorted(present_ids), "coverage"),
            ("Missing or not explicitly identified", sorted(missing_ids), "missingness"),
        ):
            coverage_rows.append(
                descriptive_row(
                    section="Complete field coverage",
                    measure=label,
                    category=category,
                    count=len(ids),
                    denominator=n,
                    percent=percent(len(ids), n),
                    unit="unique studies",
                    denominator_definition="all unique studies",
                    response_type=f"{response}; mutually exclusive within field",
                    work_ids=";".join(ids),
                    note="Missing information is retained as missing and is never converted to zero.",
                )
            )
    citation_by_year: list[dict[str, Any]] = []
    for year in years:
        ids = set(year_ids[str(year)])
        values = [
            integer(oa_by_id[paper_id]["cited_by_count"], f"citation/{paper_id}")
            for paper_id in ids
            if clean(oa_by_id[paper_id]["cited_by_count"])
        ]
        stats = citation_statistics(values)
        citation_by_year.append(
            descriptive_row(
                section="Citations by publication year",
                measure="Coverage and distribution",
                category=(str(year) if year < 2026 else "2026 (partial to 13 Aug)"),
                count=len(values),
                denominator=len(ids),
                percent=percent(len(values), len(ids)),
                value=stats,
                unit="canonical works / citations",
                denominator_definition=f"canonical works published in {year}",
                response_type="coverage plus descriptive distribution",
                work_ids=";".join(sorted(ids)),
                note="Missing citation values are excluded from distribution statistics, not set to zero.",
            )
        )

    confusion_rows: list[dict[str, Any]] = []
    for form, result in (("three-choice", agreement_three), ("binary include versus non-include", agreement_binary)):
        for left in result["labels"]:
            for right in result["labels"]:
                confusion_rows.append(
                    descriptive_row(
                        section="Model-review confusion matrix",
                        measure=form,
                        category=f"Reviewer A: {plain_label(left)} | Reviewer B: {plain_label(right)}",
                        count=result["confusion_matrix"][left][right],
                        denominator=result["n"],
                        percent=percent(result["confusion_matrix"][left][right], result["n"]),
                        unit="candidate records",
                        denominator_definition="all candidate records before resolution",
                        response_type="paired model-review decision cell",
                        note="Model-review consistency only.",
                    )
                )

    work_classifications = []
    classification_fields = [
        "paper_id",
        "version_family_id",
        "doi",
        "year",
        "publication_date",
        *METADATA_AUDIT_FIELDS,
        "final_model_families",
        "final_model_description_raw",
        "final_simulation_modalities",
        "final_nts_domains",
        "final_specialty",
        "final_study_design",
        "source_checked_by",
        "source_checked_at_utc",
        "evidence_url_1",
        "evidence_url_2",
    ]
    for row in works:
        work_classifications.append({field: row[field] for field in classification_fields})

    return {
        "n": n,
        "work_ids": work_ids,
        "flow": flow,
        "agreement": {"three_way": agreement_three, "binary": agreement_binary},
        "tables": {
            "TABLE_1_SELECTION_AGREEMENT_HUMAN_AUDIT": (table1, AGREEMENT_TABLE_FIELDS),
            "TABLE_2_PUBLICATION_SOURCE_OA_CITATION_COVERAGE": (table2, DESCRIPTIVE_TABLE_FIELDS),
            "TABLE_3_MODEL_SIMULATION_STUDY_DESIGN": (table3, DESCRIPTIVE_TABLE_FIELDS),
            "TABLE_4_RECONCILED_NTS": (table4, DESCRIPTIVE_TABLE_FIELDS),
            "TABLE_5_GEOGRAPHY_WITH_MISSINGNESS": (table5, DESCRIPTIVE_TABLE_FIELDS),
            "TABLE_6_PREDEFINED_PHRASE_FREQUENCIES": (table6, PHRASE_TABLE_FIELDS),
        },
        "supplements": {
            "SUPPLEMENT_SELECTION_FLOW_COMPLETE": (
                complete_flow_rows,
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_MODEL_REVIEW_CONFUSION_MATRICES": (confusion_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_ANNUAL_COUNTS_COMPLETE": (annual_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_PUBLICATION_SOURCES_COMPLETE": (
                source_rows + source_summary_rows,
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_RETRIEVAL_SOURCE_COVERAGE_COMPLETE": (retrieval_source_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_OPEN_ACCESS_COMPLETE": (oa_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_CITATIONS_BY_YEAR": (citation_by_year, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_COVERAGE_COMPLETE": (coverage_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_AUTHOR_PRODUCTIVITY_COMPLETE": (
                author_rows
                + author_distribution_rows
                + [
                    row
                    for row in coverage_main_rows
                    if row["measure"] == "Authorship coverage"
                ],
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_GEOGRAPHY_WHOLE_AND_FRACTIONAL_COMPLETE": (
                country_rows + fractional_rows + country_all_n_rows + geography_coverage_rows,
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_PREDEFINED_PHRASE_FREQUENCY_COMPLETE": (phrase_rows, PHRASE_TABLE_FIELDS),
            "SUPPLEMENT_PHRASE_COOCCURRENCE_COMPLETE": (pair_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_PHRASE_NETWORK_EDGES_CONDITIONAL": (network_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_PHRASE_NETWORK_NODES_CONDITIONAL": (
                network_node_rows,
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_PREDEFINED_PHRASE_DICTIONARY": (
                phrase_dictionary_rows,
                phrase_dictionary_fields,
            ),
            "SUPPLEMENT_PER_STUDY_PHRASE_INDICATORS": (
                phrase_indicator_rows,
                phrase_indicator_fields,
            ),
            "SUPPLEMENT_MODEL_FAMILIES_COMPLETE": (model_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_SIMULATION_METHODS_COMPLETE": (simulation_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_NTS_DOMAINS_COMPLETE": (table4, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_SPECIALTY_PROFESSION_COMPLETE": (specialty_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_STUDY_DESIGNS_COMPLETE": (design_rows, DESCRIPTIVE_TABLE_FIELDS),
            "SUPPLEMENT_SENSITIVITY_EXCLUDE_STANDALONE_PREPRINTS_REPOSITORY_ONLY": (
                preprint_sensitivity_rows,
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_SENSITIVITY_PREPRINT_REPOSITORY_PHRASES": (
                preprint_phrase_rows,
                PHRASE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_SENSITIVITY_EXACT_IDENTIFIER_METADATA": (
                exact_metadata_rows,
                DESCRIPTIVE_TABLE_FIELDS,
            ),
            "SUPPLEMENT_CHECKED_WORK_CLASSIFICATIONS": (work_classifications, classification_fields),
        },
        "plot_data": {
            "retrieval_sources": [
                {"category": plain_label(source), "count": count}
                for source, count in raw["by_source"].items()
            ],
            "years": years,
            "year_counts": [len(year_ids[str(year)]) for year in years],
            "models": [row for row in model_rows if row["measure"] == "Work frequency"],
            "simulations": simulation_rows,
            "nts": [row for row in nts_rows if row["category"] != plain_label(nts_blank)],
            "designs": design_rows,
            "specialties": specialty_plot_rows,
            "phrase_network_edges": network_rows,
            "phrase_counts": {label: len(ids) for label, ids in phrase_hits.items()},
        },
        "summary_values": {
            "candidate_records": len(candidate["rows"]),
            "included_publication_versions": len(finalization["included_rows"]),
            "canonical_works": n,
            "openalex_matched": openalex["matched"],
            "citation_values_available": len(citations),
            "citation_values_missing": len(missing_citation_ids),
            "works_with_country": len(works_with_country),
            "works_with_authors": len(works_with_authors),
            "works_with_abstract": sum(bool(clean(row["abstract"])) for row in works),
            "partial_2026_count": len(year_ids["2026"]),
            "preprint_repository_sensitivity_excluded": len(preprint_repository_excluded_ids),
            "preprint_repository_sensitivity_n": preprint_n,
            "exact_identifier_metadata_sensitivity_n": exact_n,
        },
    }


def _barh(ax: Any, rows: Sequence[Mapping[str, Any]], *, max_rows: int | None = None) -> None:
    observed = [row for row in rows if int(row.get("count") or 0) > 0]
    observed.sort(key=lambda row: (int(row["count"]), row["category"].casefold()))
    if max_rows is not None:
        observed = observed[-max_rows:]
    if not observed:
        observed = [{"category": "No observed category", "count": 0}]
    labels = [row["category"] for row in observed]
    counts = [int(row["count"]) for row in observed]
    positions = np.arange(len(labels))
    bars = ax.barh(positions, counts, color="#315b7d", edgecolor="black", linewidth=0.5)
    ax.set_yticks(positions, labels)
    ax.set_xlabel("Unique studies")
    ax.bar_label(bars, padding=3, fontsize=8)
    if counts:
        ax.set_xlim(0, max(counts) * 1.08 + 1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(False)


def save_figure_pair(fig: Any, directory: Path, stem: str) -> list[Path]:
    png = directory / f"{stem}.png"
    eps = directory / f"{stem}.eps"
    fig.savefig(png, dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(eps, format="eps", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [png, eps]


def create_figures(directory: Path, analysis: Mapping[str, Any]) -> list[Path]:
    directory.mkdir()
    paths: list[Path] = []
    fig, ax = plt.subplots(figsize=(9.2, 10.2))
    ax.axis("off")
    flow_by_label = {label: count for label, count, _definition in analysis["flow"]}
    source_lines = [
        f"{row['category']}: {int(row['count']):,}"
        for row in analysis["plot_data"]["retrieval_sources"]
    ]
    main_flow = [
        (
            "Records retrieved from five databases\n"
            + " | ".join(source_lines[:3])
            + "\n"
            + " | ".join(source_lines[3:]),
            flow_by_label["Retrieval occurrences"],
        ),
        ("Records after automatic duplicate merging", flow_by_label["Records after automatic duplicate merging"]),
        ("Unique records after all duplicate removal", flow_by_label["Unique bibliographic records after deduplication"]),
        ("Records reviewed by both model reviewers", flow_by_label["Candidate records reviewed by both models"]),
        ("Eligible publication records", flow_by_label["Eligible publication records"]),
        (
            "Unique studies included\n(after linking publications from the same study)",
            flow_by_label["Unique studies"],
        ),
    ]
    side_flow = [
        (
            0,
            "Automatically merged duplicate occurrences",
            flow_by_label["Automatically merged duplicate occurrences"],
        ),
        (
            1,
            "Additional same-record merges after separate checking",
            flow_by_label["Separately checked same-record merges"],
        ),
        (
            2,
            "Records outside the broad review rule",
            flow_by_label["Records outside the four-domain candidate trigger"],
        ),
        (
            3,
            "Records excluded after separate reviews and resolution",
            flow_by_label["Records excluded after resolution"],
        ),
        (
            4,
            "Additional publications describing the same study",
            flow_by_label["Additional publications linked to another eligible version"],
        ),
    ]
    y_positions = np.linspace(0.94, 0.07, len(main_flow))
    for index, (label, count) in enumerate(main_flow):
        y = y_positions[index]
        ax.text(
            0.33,
            y,
            f"{label}\n{count:,}",
            ha="center",
            va="center",
            fontsize=9.4 if index == 0 else 10,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "#eef4f8", "edgecolor": "#315b7d"},
        )
        if index < len(main_flow) - 1:
            ax.annotate(
                "",
                xy=(0.33, y_positions[index + 1] + 0.052),
                xytext=(0.33, y - 0.052),
                arrowprops={"arrowstyle": "->", "color": "black", "linewidth": 0.8},
            )
    for source_index, label, count in side_flow:
        source_y = y_positions[source_index]
        side_y = source_y - 0.075
        ax.annotate(
            "",
            xy=(0.70, side_y),
            xytext=(0.51, source_y - 0.015),
            arrowprops={"arrowstyle": "->", "color": "black", "linewidth": 0.8},
        )
        ax.text(
            0.79,
            side_y,
            f"{label}\n{count:,}",
            ha="center",
            va="center",
            fontsize=8.6,
            bbox={"boxstyle": "round,pad=0.4", "facecolor": "#f7f7f7", "edgecolor": "#666666"},
        )
    paths.extend(save_figure_pair(fig, directory, "FIGURE_1_SELECTION_FLOW"))

    plot = analysis["plot_data"]
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    colours = ["#315b7d"] * 6 + ["#a65f2b"]
    bars = ax.bar(range(7), plot["year_counts"], color=colours, edgecolor="black", linewidth=0.5)
    ax.set_xticks(range(7), [str(year) for year in range(2020, 2026)] + ["2026\n(to 13 Aug)"])
    ax.set_ylabel("Unique studies")
    ax.spines[["top", "right"]].set_visible(False)
    ax.bar_label(bars, padding=2, fontsize=8)
    ax.grid(False)
    paths.extend(save_figure_pair(fig, directory, "FIGURE_2_ANNUAL_COUNTS"))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 7.2))
    _barh(axes[0], plot["models"], max_rows=12)
    _barh(axes[1], plot["simulations"])
    axes[0].text(-0.14, 1.02, "A", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.14, 1.02, "B", transform=axes[1].transAxes, fontweight="bold")
    fig.tight_layout()
    paths.extend(save_figure_pair(fig, directory, "FIGURE_3_MODEL_FAMILIES_AND_SIMULATION_METHODS"))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 6.6))
    _barh(axes[0], plot["nts"])
    _barh(axes[1], plot["designs"])
    axes[0].text(-0.14, 1.02, "A", transform=axes[0].transAxes, fontweight="bold")
    axes[1].text(-0.14, 1.02, "B", transform=axes[1].transAxes, fontweight="bold")
    fig.tight_layout()
    paths.extend(save_figure_pair(fig, directory, "FIGURE_4_NTS_DOMAINS_AND_STUDY_DESIGNS"))

    specialty_height = max(7.2, 1.8 + 0.34 * len(plot["specialties"]))
    fig, ax = plt.subplots(figsize=(10.0, specialty_height))
    _barh(ax, plot["specialties"])
    fig.tight_layout()
    paths.extend(save_figure_pair(fig, directory, "FIGURE_5_SPECIALTIES_AND_PROFESSIONS"))
    return paths


def create_supplementary_phrase_network(
    directory: Path, analysis: Mapping[str, Any]
) -> list[Path]:
    """Render the prespecified co-occurrence network only when edges qualify."""

    edges = list(analysis["plot_data"]["phrase_network_edges"])
    if not edges:
        return []
    parsed: list[tuple[str, str, int]] = []
    nodes: set[str] = set()
    for row in edges:
        pair = clean(row["category"]).split(" + ")
        count = integer(row["count"], "phrase-network edge count")
        if len(pair) != 2 or count < 3:
            raise FreshAnalysisError("Malformed conditional phrase-network edge")
        left, right = pair
        nodes.update((left, right))
        parsed.append((left, right, count))
    ordered = sorted(nodes, key=str.casefold)
    node_counts = analysis["plot_data"].get("phrase_counts") or {}
    if any(integer(node_counts.get(label, 0), f"phrase count/{label}") < 5 for label in ordered):
        raise FreshAnalysisError("Phrase-network node does not meet the minimum work count")

    # Deterministic force-directed layout.  The network is supplementary and
    # descriptive only; the layout is used solely to reduce crossing and label
    # collisions, not to calculate any inferential network statistic.
    rng = np.random.default_rng(2026081405)
    matrix = rng.uniform(-0.8, 0.8, size=(len(ordered), 2))
    index = {label: position for position, label in enumerate(ordered)}
    max_edge = max(count for _left, _right, count in parsed)
    ideal = math.sqrt(4.0 / max(len(ordered), 1))
    for iteration in range(500):
        displacement = np.zeros_like(matrix)
        for left_index in range(len(ordered)):
            for right_index in range(left_index + 1, len(ordered)):
                delta = matrix[left_index] - matrix[right_index]
                distance = max(float(np.linalg.norm(delta)), 1e-4)
                force = ideal * ideal / distance
                vector = delta / distance * force
                displacement[left_index] += vector
                displacement[right_index] -= vector
        for left, right, count in parsed:
            left_index = index[left]
            right_index = index[right]
            delta = matrix[left_index] - matrix[right_index]
            distance = max(float(np.linalg.norm(delta)), 1e-4)
            weight = 0.65 + 0.70 * count / max_edge
            force = distance * distance / ideal * weight
            vector = delta / distance * force
            displacement[left_index] -= vector
            displacement[right_index] += vector
        temperature = 0.12 * (1.0 - iteration / 500.0) + 0.005
        lengths = np.linalg.norm(displacement, axis=1)
        scale = np.minimum(lengths, temperature) / np.maximum(lengths, 1e-9)
        matrix += displacement * scale[:, None]
        matrix -= matrix.mean(axis=0)
    radius = max(float(np.max(np.linalg.norm(matrix, axis=1))), 1e-9)
    matrix = matrix / radius
    positions = {label: matrix[index[label]] for label in ordered}

    fig, ax = plt.subplots(figsize=(12.0, 10.0))
    ax.set_aspect("equal")
    ax.axis("off")
    for left, right, count in parsed:
        start, end = positions[left], positions[right]
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            color="#6e7f8d",
            linewidth=0.6 + 3.0 * count / max_edge,
            alpha=0.55,
            zorder=1,
        )
    max_count = max(integer(node_counts[label], f"phrase count/{label}") for label in ordered)
    for label in ordered:
        point = positions[label]
        count = integer(node_counts[label], f"phrase count/{label}")
        size = 180.0 + 1250.0 * count / max_count
        ax.scatter(
            [point[0]],
            [point[1]],
            s=size,
            color="#d7e6f0",
            edgecolor="#315b7d",
            linewidth=1.0,
            zorder=3,
        )
        direction = 1.0 if point[0] >= 0 else -1.0
        ax.text(
            point[0] + direction * 0.045,
            point[1] + 0.012,
            textwrap.fill(label, width=18),
            ha="left" if direction > 0 else "right",
            va="center",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.78, "pad": 0.5},
            zorder=4,
        )
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.25, 1.25)
    return save_figure_pair(
        fig, directory, "SUPPLEMENT_FIGURE_PHRASE_NETWORK_CONDITIONAL"
    )


def write_table_pair(
    directory: Path,
    stem: str,
    rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    *,
    table_kind: str,
) -> list[Path]:
    csv_path = directory / f"{stem}.csv"
    json_path = directory / f"{stem}.json"
    write_csv(csv_path, rows, fields)
    write_json(
        json_path,
        {
            "schema_version": SCHEMA_VERSION,
            "table_id": stem,
            "table_kind": table_kind,
            "fields": list(fields),
            "rows": list(rows),
            "denominator_contract": (
                "Every analytical row states its denominator definition and response type."
                if "denominator_definition" in fields
                else "Not applicable to this dictionary or per-study indicator resource."
            ),
            "missingness_contract": "Missing metadata is reported as missing and is never converted to zero.",
        },
    )
    return [csv_path, json_path]


def ensure_output_path(output: Path, immutable_roots: Sequence[Path]) -> Path:
    resolved = output.resolve()
    if resolved.exists():
        raise FreshAnalysisError(f"Output already exists; refusing to overwrite: {resolved}")
    lowered = {part.casefold() for part in resolved.parts}
    if lowered & PROTECTED_ROOT_NAMES:
        raise FreshAnalysisError(f"Output is inside protected historical material: {resolved}")
    for root in immutable_roots:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise FreshAnalysisError(f"Output must not be inside immutable input: {root}")
    return resolved


def run_analysis(
    *,
    extraction_dir: Path,
    metadata_correction_dir: Path,
    openalex_dir: Path,
    screening_finalization_dir: Path,
    comparison_dir: Path,
    candidate_dir: Path,
    dedup_dir: Path,
    normalization_dir: Path,
    raw_manifests: Sequence[Path],
    output_dir: Path,
    analysis_spec: Path = DEFAULT_ANALYSIS_SPEC,
    amendment: Path = DEFAULT_AMENDMENT,
    clarification: Path = DEFAULT_CLARIFICATION,
    synthetic_test_mode: bool = False,
    confirm_production_run: bool = False,
) -> Mapping[str, Any]:
    if not synthetic_test_mode and not confirm_production_run:
        raise FreshAnalysisError(
            "Production execution requires --confirm-production-run; this prevents an accidental early run"
        )
    spec, _amendment, authority_paths = validate_authorities(
        analysis_spec, amendment, clarification
    )
    raw = validate_raw_manifests(raw_manifests, synthetic_test_mode=synthetic_test_mode)
    normalization = validate_normalization(
        normalization_dir, raw, synthetic_test_mode=synthetic_test_mode
    )
    dedup = validate_deduplication(dedup_dir, normalization)
    candidate = validate_candidate_package(candidate_dir, dedup)
    comparison = validate_comparison_package(comparison_dir, candidate)
    finalization = validate_screening_finalization(
        screening_finalization_dir, candidate, comparison
    )
    extraction = validate_extraction_package(
        extraction_dir,
        spec,
        analysis_spec.resolve(),
        finalization,
        synthetic_test_mode=synthetic_test_mode,
    )
    metadata = validate_metadata_correction_package(metadata_correction_dir, extraction)
    openalex = validate_openalex_package(openalex_dir, metadata["rows"])
    if not synthetic_test_mode:
        validate_fresh_reference_pins(metadata, openalex)

    input_roots = [
        extraction_dir.resolve(),
        metadata_correction_dir.resolve(),
        openalex_dir.resolve(),
        screening_finalization_dir.resolve(),
        comparison_dir.resolve(),
        candidate_dir.resolve(),
        dedup_dir.resolve(),
        normalization_dir.resolve(),
        *(path.resolve().parent for path in raw_manifests),
    ]
    output = ensure_output_path(output_dir, input_roots)
    bindings: dict[str, str] = {}
    for path in authority_paths:
        add_binding(bindings, path)
    for package in (
        raw,
        normalization,
        dedup,
        candidate,
        comparison,
        finalization,
        extraction,
        metadata,
        openalex,
    ):
        for path, digest in package["bindings"].items():
            prior = bindings.get(path)
            if prior is not None and prior != digest:
                raise FreshAnalysisError(f"Conflicting input hash binding: {path}")
            bindings[path] = digest
    agreement_script = PIPELINE_DIR / "compute_fresh_review_agreement_v2.py"
    add_binding(bindings, agreement_script)
    add_binding(bindings, Path(__file__))

    analysis = build_analysis(
        spec=spec,
        raw=raw,
        normalization=normalization,
        dedup=dedup,
        candidate=candidate,
        comparison=comparison,
        finalization=finalization,
        extraction=extraction,
        metadata=metadata,
        openalex=openalex,
    )
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
                write_table_pair(table_dir, stem, rows, fields, table_kind="main table")
            )
        for stem, (rows, fields) in analysis["supplements"].items():
            artifacts.extend(
                write_table_pair(
                    supplement_dir, stem, rows, fields, table_kind="complete supplement"
                )
            )
        eligible_ledger_copy = (
            supplement_dir / "SUPPLEMENT_ELIGIBLE_PUBLICATION_VERSION_LEDGER_V2.csv"
        )
        shutil.copy2(
            extraction["version_consolidation"]["eligible_ledger_path"],
            eligible_ledger_copy,
        )
        artifacts.append(eligible_ledger_copy)
        artifacts.extend(create_figures(figure_dir, analysis))
        supplementary_network_paths = create_supplementary_phrase_network(
            supplement_dir, analysis
        )
        artifacts.extend(supplementary_network_paths)

        summary = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "status": FINAL_STATUS,
            "analysis_mode": "synthetic_test" if synthetic_test_mode else "production",
            "study_window": spec["study_window"],
            "primary_analysis_unit": "one unique study represented by one preferred publication record",
            "counts": analysis["summary_values"],
            "openalex_snapshot": {
                "status": "LOCKED",
                "locked_at_utc": openalex["report"]["generated_utc"],
                "snapshot_fingerprint": openalex["report"]["snapshot_fingerprint"],
                "locked_sha256": sha256_file(openalex["locked_path"]),
                "matched": openalex["matched"],
                "confirmed_unmatched": openalex["unmatched"],
            },
            "model_review_agreement": analysis["agreement"],
            "human_audit": {
                "status": HUMAN_AUDIT_DISPLAY,
                "human_reference_standard_available": False,
                "fresh_boundary_negative_sample_completed": False,
                "interpretation": "Agreement describes consistency between two model reviews. Shared or correlated model error may remain.",
            },
            "partial_2026": {
                "through": "2026-08-13",
                "observed_count": analysis["summary_values"]["partial_2026_count"],
                "reported_separately": True,
                "annualized": False,
            },
            "missingness": "Missing metadata remains missing and is never converted to zero.",
            "multiple_response": "Model, simulation, NTS, specialty/profession, retrieval-source, author and country whole-count percentages may sum to more than 100%.",
            "figure_contract": "Figures contain plain axis/category labels and no embedded titles; PNG files are 600 dpi and EPS companions are supplied.",
            "conditional_supplementary_phrase_network": {
                "generated": bool(supplementary_network_paths),
                "minimum_phrase_count": 5,
                "minimum_pair_count": 3,
                "maximum_pairs": 25,
                "scope_check_group_excluded": True,
                "community_detection": False,
                "centrality": False,
                "node_size": "number of unique studies containing the phrase",
                "edge_width": "number of unique studies containing both phrases",
            },
            "omitted_analysis_rationale": {
                "bradford_law": "Omitted because normalized publication-source counts answer the question more directly.",
                "lotka_law": "Omitted because incomplete author identity makes a fitted productivity law unnecessarily fragile.",
                "model_licensing": "Omitted because a family name does not establish the licence of the exact model version used.",
                "word_cloud": "Omitted because exact predefined phrase tables and the threshold-conditional co-occurrence display are more auditable.",
                "urology_only_analysis": "Omitted so that every clinical field is described under the same rule."
            },
        }
        summary_path = temp / OUTPUT_SUMMARY
        write_json(summary_path, summary)
        artifacts.append(summary_path)

        artifact_entries = [
            {
                "path": path.relative_to(temp).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in sorted(artifacts, key=lambda item: item.relative_to(temp).as_posix())
        ]
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "pipeline": PIPELINE,
            "status": FINAL_STATUS,
            "analysis_mode": "synthetic_test" if synthetic_test_mode else "production",
            "counts": {
                "canonical_works": analysis["n"],
                "main_tables": 6,
                "main_figures": 5,
                "conditional_supplementary_phrase_network_figures": (
                    1 if supplementary_network_paths else 0
                ),
                "artifact_files_before_manifest": len(artifact_entries),
            },
            "locked_authorities": {
                key: {
                    "path": str(path),
                    "sha256": sha256_file(path),
                }
                for key, path in zip(LOCKED_AUTHORITY_HASHES, authority_paths, strict=True)
            },
            "inputs": [
                {
                    "path": path,
                    "bytes": Path(path).stat().st_size,
                    "sha256": digest,
                }
                for path, digest in sorted(bindings.items())
            ],
            "outputs": artifact_entries,
            "contracts": {
                "input_hashes_rechecked_before_atomic_rename": True,
                "output_created_without_overwrite": True,
                "human_audit_results_included": False,
                "human_audit_display": HUMAN_AUDIT_DISPLAY,
                "all_denominators_explicit": True,
                "multiple_response_notes_explicit": True,
                "missing_values_converted_to_zero": False,
                "partial_2026_reported_separately": True,
                "figure_titles_embedded": False,
                "png_dpi": 600,
                "eps_companions": True,
                "supplementary_phrase_network_is_threshold_conditional": True,
                "word_cloud_included": False,
            },
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "agreement_program": agreement_script.name,
                "agreement_program_sha256": sha256_file(agreement_script),
                "python_version": sys.version.split()[0],
                "numpy_version": np.__version__,
                "matplotlib_version": matplotlib.__version__,
            },
        }
        manifest_path = temp / OUTPUT_MANIFEST
        write_json(manifest_path, manifest)
        output_rows = [
            {
                "scope": "output",
                "path": path.relative_to(temp).as_posix(),
                "role": "analysis_artifact",
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifacts
        ]
        output_rows.append(
            {
                "scope": "output",
                "path": manifest_path.name,
                "role": "analysis_output_manifest",
                "bytes": manifest_path.stat().st_size,
                "sha256": sha256_file(manifest_path),
            }
        )
        input_rows = [
            {
                "scope": "input",
                "path": path,
                "role": "validated_hash_bound_input",
                "bytes": Path(path).stat().st_size,
                "sha256": digest,
            }
            for path, digest in bindings.items()
        ]
        hash_path = temp / OUTPUT_HASH_LEDGER
        write_csv(
            hash_path,
            sorted(input_rows + output_rows, key=lambda row: (row["scope"], row["path"], row["role"])),
            HASH_FIELDS,
        )
        output_set_sha = sha256_text(
            "\0".join(
                f"{row['path']}:{row['sha256']}"
                for row in sorted(output_rows, key=lambda item: item["path"])
            )
        )
        frozen = {
            "schema_version": SCHEMA_VERSION,
            "status": FINAL_STATUS,
            "analysis_output_manifest_sha256": sha256_file(manifest_path),
            "analysis_hash_manifest_sha256": sha256_file(hash_path),
            "analysis_summary_sha256": sha256_file(summary_path),
            "ordered_output_set_sha256": output_set_sha,
            "checked_one_work_corpus_sha256": sha256_file(extraction["checked_path"]),
            "metadata_corrected_corpus_sha256": metadata["corrected_sha256"],
            "openalex_locked_sha256": sha256_file(openalex["locked_path"]),
            "comparison_manifest_sha256": comparison["manifest_sha256"],
            "screening_finalization_manifest_sha256": finalization["manifest_sha256"],
        }
        frozen_path = temp / OUTPUT_FROZEN_MARKER
        write_json(frozen_path, frozen)

        verify_bindings(bindings)
        for row in output_rows:
            path = safe_relative(temp, row["path"], "generated output")
            if path.stat().st_size != int(row["bytes"]) or sha256_file(path) != row["sha256"]:
                raise FreshAnalysisError(f"Generated output changed before freeze: {path}")
        if sha256_file(manifest_path) != frozen["analysis_output_manifest_sha256"]:
            raise FreshAnalysisError("Analysis manifest changed before atomic rename")
        if sha256_file(hash_path) != frozen["analysis_hash_manifest_sha256"]:
            raise FreshAnalysisError("Analysis hash ledger changed before atomic rename")
        temp.rename(output)
        return manifest
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extraction-dir", required=True, type=Path)
    parser.add_argument("--metadata-correction-dir", required=True, type=Path)
    parser.add_argument("--openalex-dir", required=True, type=Path)
    parser.add_argument("--screening-finalization-dir", required=True, type=Path)
    parser.add_argument("--comparison-dir", required=True, type=Path)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--dedup-dir", required=True, type=Path)
    parser.add_argument("--normalization-dir", required=True, type=Path)
    parser.add_argument("--raw-manifest", required=True, action="append", type=Path)
    parser.add_argument("--analysis-spec", type=Path, default=DEFAULT_ANALYSIS_SPEC)
    parser.add_argument("--amendment", type=Path, default=DEFAULT_AMENDMENT)
    parser.add_argument("--clarification", type=Path, default=DEFAULT_CLARIFICATION)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--synthetic-test-mode",
        action="store_true",
        help="Permit explicitly synthetic collector fixtures; never use for production",
    )
    parser.add_argument(
        "--confirm-production-run",
        action="store_true",
        help="Explicitly authorize analysis of validated production packages",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.synthetic_test_mode and args.confirm_production_run:
        parser.error("Synthetic-test and production-confirmation modes are mutually exclusive")
    try:
        manifest = run_analysis(
            extraction_dir=args.extraction_dir,
            metadata_correction_dir=args.metadata_correction_dir,
            openalex_dir=args.openalex_dir,
            screening_finalization_dir=args.screening_finalization_dir,
            comparison_dir=args.comparison_dir,
            candidate_dir=args.candidate_dir,
            dedup_dir=args.dedup_dir,
            normalization_dir=args.normalization_dir,
            raw_manifests=args.raw_manifest,
            output_dir=args.output_dir,
            analysis_spec=args.analysis_spec,
            amendment=args.amendment,
            clarification=args.clarification,
            synthetic_test_mode=args.synthetic_test_mode,
            confirm_production_run=args.confirm_production_run,
        )
    except FreshAnalysisError as exc:
        parser.error(str(exc))
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
