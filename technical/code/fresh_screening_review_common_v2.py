#!/usr/bin/env python3
"""Shared validation primitives for the fresh V2 independent-review workflow.

This module is deliberately independent of the March 2026 review scripts.  It
validates the candidate package created by ``build_fresh_screening_candidates``
and the exact 17-field outputs required by the locked fresh-rerun codebook.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PIPELINE_DIR = Path(__file__).resolve().parent
DEFAULT_CODEBOOK = PIPELINE_DIR / "SCREENING_CODEBOOK_FULL_RERUN_V2_2026-08-13.md"
EXPECTED_CODEBOOK_SHA256 = (
    "ab74c88c27d7efbf34f0b3cb680cea62b03eaec4ef11bdd630925ee8639ab9bc"
)
REVIEW_SCHEMA_VERSION = "full-rerun-independent-review-v2.0"

VALID_DECISIONS = {"INCLUDE", "EXCLUDE", "UNCERTAIN"}
VALID_FINAL_DECISIONS = {"INCLUDE", "EXCLUDE"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_TRI_STATE = {"yes", "no", "unclear"}
EXCLUSION_CODES = {
    "E1_NOT_LLM",
    "E2_NOT_HEALTH_ED",
    "E3_NOT_SIMULATION",
    "E4_CLINICAL_ONLY",
    "E5_INELIGIBLE_TYPE",
    "E6_OUT_OF_RANGE",
    "E7_NOT_ASSESSABLE_IN_ENGLISH",
    "E9_OTHER",
}
UNCERTAIN_CODES = {
    "U1_NEED_FULL_TEXT",
    "U2_NEED_MODEL_DETAIL",
    "U3_NEED_DOCUMENT_TYPE",
    "U4_NEED_VERSION_CHECK",
    "U5_NEED_LANGUAGE_CHECK",
    "U6_NEED_DATE_CHECK",
}
RETIRED_CODES = {"E8_DUPLICATE_VERSION"}

CRITERION_FIELDS = [
    "date_eligible",
    "language_assessable",
    "llm_explicit",
    "health_professions_education",
    "simulation_central",
    "eligible_document_type",
]

REVIEW_FIELDS = [
    "paper_id",
    "decision",
    "primary_code",
    "confidence",
    "date_eligible",
    "language_assessable",
    "llm_explicit",
    "health_professions_education",
    "simulation_central",
    "eligible_document_type",
    "evidence",
    "simulation_modalities",
    "nts_domains",
    "specialty",
    "model_families",
    "study_design",
    "possible_version_of",
]

MASTER_FIELDS = [
    "paper_id",
    "doi",
    "title",
    "year",
    "publication_date",
    "date_window_status",
    "language_status",
    "journal",
    "found_in_sources",
    "record_type",
    "authors",
    "abstract",
    "source_keywords",
    "url",
    "all_urls",
    "abstract_missing",
    "candidate_trigger",
    "language_model_hit",
    "healthcare_hit",
    "education_training_hit",
    "simulation_hit",
    "screening_text_sha256",
]

BLINDED_FIELDS = [
    "paper_id",
    "doi",
    "title",
    "year",
    "publication_date",
    "date_window_status",
    "language_status",
    "journal",
    "found_in_sources",
    "record_type",
    "authors",
    "abstract",
    "source_keywords",
    "url",
    "all_urls",
    "abstract_missing",
]

BATCH_MANIFEST_FIELDS = [
    "batch",
    "file",
    "review_template_file",
    "first_master_row",
    "last_master_row",
    "records",
    "bytes",
    "sha256",
    "review_template_bytes",
    "review_template_sha256",
]

VALID_MODALITIES = {
    "virtual_patient",
    "standardized_patient",
    "scenario",
    "osce",
    "roleplay",
    "mannequin",
    "task_trainer",
    "vr_ar_xr",
    "serious_game",
    "debriefing",
    "other",
}
VALID_NTS = {
    "communication",
    "teamwork",
    "leadership",
    "decision_making",
    "situational_awareness",
    "task_management",
    "stress_management",
    "professionalism",
    "other",
}
VALID_STUDY_DESIGNS = {
    "randomized_trial",
    "nonrandomized_comparative",
    "pre_post",
    "observational",
    "survey",
    "qualitative",
    "mixed_methods",
    "development_evaluation",
    "evidence_review",
    "methods_framework",
    "other",
    "unclear",
}

CODE_GATE_REQUIREMENTS = {
    "E1_NOT_LLM": ("llm_explicit", "no"),
    "E2_NOT_HEALTH_ED": ("health_professions_education", "no"),
    "E3_NOT_SIMULATION": ("simulation_central", "no"),
    "E4_CLINICAL_ONLY": ("health_professions_education", "no"),
    "E5_INELIGIBLE_TYPE": ("eligible_document_type", "no"),
    "E6_OUT_OF_RANGE": ("date_eligible", "no"),
    "E7_NOT_ASSESSABLE_IN_ENGLISH": ("language_assessable", "no"),
    "U2_NEED_MODEL_DETAIL": ("llm_explicit", "unclear"),
    "U3_NEED_DOCUMENT_TYPE": ("eligible_document_type", "unclear"),
    "U5_NEED_LANGUAGE_CHECK": ("language_assessable", "unclear"),
    "U6_NEED_DATE_CHECK": ("date_eligible", "unclear"),
}


class FreshReviewError(ValueError):
    """Raised when a V2 review artifact violates a locked workflow contract."""


@dataclass(frozen=True)
class BatchSpec:
    number: int
    input_path: Path
    review_filename: str
    ids: tuple[str, ...]
    row: Mapping[str, str]


@dataclass(frozen=True)
class CandidatePackage:
    root: Path
    codebook_path: Path
    codebook_sha256: str
    candidate_manifest_path: Path
    candidate_manifest_sha256: str
    candidate_manifest: Mapping[str, Any]
    master_path: Path
    master_sha256: str
    master_fields: tuple[str, ...]
    master_rows: tuple[Mapping[str, str], ...]
    master_by_id: Mapping[str, Mapping[str, str]]
    schema_path: Path
    schema_sha256: str
    batch_manifest_path: Path
    batch_manifest_sha256: str
    batches: tuple[BatchSpec, ...]
    batch_by_id: Mapping[str, int]

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(row["paper_id"] for row in self.master_rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def safe_relative(root: Path, value: Any, *, label: str) -> Path:
    text = str(value or "").strip().replace("\\", "/")
    if not text:
        raise FreshReviewError(f"Missing {label} path")
    relative = Path(text)
    if relative.is_absolute() or ".." in relative.parts:
        raise FreshReviewError(f"Unsafe {label} path: {text!r}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise FreshReviewError(f"Unsafe {label} path: {text!r}") from exc
    return resolved


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FreshReviewError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    return fields, rows


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def file_entry(path: Path, root: Path, role: str) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def validate_file_entry(root: Path, entry: Mapping[str, Any], *, label: str) -> Path:
    path = safe_relative(root, entry.get("path"), label=label)
    if not path.is_file():
        raise FreshReviewError(f"Missing {label}: {path}")
    try:
        expected_bytes = int(entry.get("bytes"))
    except (TypeError, ValueError) as exc:
        raise FreshReviewError(f"{label} has invalid byte count") from exc
    observed_hash = sha256_file(path)
    expected_hash = str(entry.get("sha256") or "").casefold()
    if path.stat().st_size != expected_bytes or observed_hash.casefold() != expected_hash:
        raise FreshReviewError(
            f"{label} integrity mismatch for {path}: expected bytes/hash "
            f"{expected_bytes}/{expected_hash}, observed {path.stat().st_size}/{observed_hash}"
        )
    return path


def validate_locked_codebook(codebook: Path = DEFAULT_CODEBOOK) -> tuple[Path, str]:
    resolved = codebook.resolve()
    if not resolved.is_file():
        raise FreshReviewError(f"Missing locked screening codebook: {resolved}")
    observed = sha256_file(resolved)
    if observed.casefold() != EXPECTED_CODEBOOK_SHA256:
        raise FreshReviewError(
            "Locked V2 screening codebook SHA-256 mismatch: expected "
            f"{EXPECTED_CODEBOOK_SHA256}, observed {observed}"
        )
    text = resolved.read_text(encoding="utf-8-sig")
    if "Version: 2.0" not in text or "E8_DUPLICATE_VERSION" not in text:
        raise FreshReviewError("Locked codebook identity markers are missing")
    return resolved, observed


def _validate_hash_ledger(candidate_dir: Path) -> None:
    path = candidate_dir / "CANDIDATE_HASH_MANIFEST.csv"
    fields, rows = read_csv(path)
    expected_fields = ["scope", "path", "role", "bytes", "sha256"]
    if fields != expected_fields:
        raise FreshReviewError(f"{path}: unexpected hash-ledger schema")
    for row in rows:
        if row["scope"] != "output":
            continue
        target = safe_relative(candidate_dir, row["path"], label="candidate output ledger")
        if not target.is_file():
            raise FreshReviewError(f"Candidate output ledger target is missing: {target}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise FreshReviewError(f"{path}: invalid byte count for {row['path']}") from exc
        if target.stat().st_size != expected_bytes or sha256_file(target) != row["sha256"].casefold():
            raise FreshReviewError(f"Candidate output hash-ledger mismatch: {target}")


def validate_candidate_package(
    candidate_dir: Path,
    *,
    codebook: Path = DEFAULT_CODEBOOK,
    require_ready: bool = True,
) -> CandidatePackage:
    root = candidate_dir.resolve()
    if not root.is_dir():
        raise FreshReviewError(f"Candidate directory does not exist: {root}")
    codebook_path, codebook_sha = validate_locked_codebook(codebook)

    manifest_path = root / "CANDIDATE_BUILD_MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise FreshReviewError(f"Missing candidate manifest: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise FreshReviewError(f"Invalid candidate manifest JSON: {manifest_path}") from exc
    if manifest.get("pipeline") != "fresh_de_novo_screening_candidate_build":
        raise FreshReviewError("Candidate manifest is not the fresh de-novo builder output")
    manifest_codebook = ((manifest.get("input") or {}).get("screening_codebook") or {})
    if str(manifest_codebook.get("sha256") or "").casefold() != codebook_sha:
        raise FreshReviewError("Candidate manifest is not bound to the locked V2 codebook")
    status = ((manifest.get("workflow_status") or {}).get("status") or "").strip()
    unresolved_pairs = int(
        ((manifest.get("workflow_status") or {}).get(
            "unresolved_deduplication_review_pairs"
        ) or 0)
    )
    if require_ready and (status != "ready_for_independent_screening" or unresolved_pairs):
        raise FreshReviewError(
            "Candidate package is not ready for independent screening; resolve the "
            "deduplication review queue and regenerate the batches first"
        )

    outputs = manifest.get("outputs") or {}
    master_path = validate_file_entry(
        root, outputs.get("candidate_master_csv") or {}, label="candidate master CSV"
    )
    schema_path = validate_file_entry(
        root, outputs.get("review_output_schema") or {}, label="V2 review schema"
    )
    batch_manifest_path = validate_file_entry(
        root, outputs.get("batch_manifest") or {}, label="batch manifest"
    )
    _validate_hash_ledger(root)

    master_fields, master_rows = read_csv(master_path)
    if master_fields != MASTER_FIELDS:
        raise FreshReviewError(f"{master_path}: unexpected candidate-master schema/order")
    master_ids = [row.get("paper_id", "") for row in master_rows]
    if any(not value for value in master_ids) or len(master_ids) != len(set(master_ids)):
        raise FreshReviewError(f"{master_path}: paper_id values must be nonblank and unique")
    if master_ids != sorted(master_ids):
        raise FreshReviewError(f"{master_path}: candidate rows are not in locked paper_id order")
    expected_candidates = int((manifest.get("counts") or {}).get("candidate_records") or 0)
    if len(master_rows) != expected_candidates:
        raise FreshReviewError(
            f"Candidate count mismatch: manifest={expected_candidates}, master={len(master_rows)}"
        )

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise FreshReviewError(f"Invalid V2 review schema JSON: {schema_path}") from exc
    if schema.get("schema_version") != REVIEW_SCHEMA_VERSION:
        raise FreshReviewError(f"{schema_path}: unexpected review schema version")
    if schema.get("output_fields_in_exact_order") != REVIEW_FIELDS:
        raise FreshReviewError(f"{schema_path}: 17-field output schema/order mismatch")
    schema_codebook = schema.get("codebook") or {}
    if str(schema_codebook.get("sha256") or "").casefold() != codebook_sha:
        raise FreshReviewError(f"{schema_path}: codebook hash mismatch")
    controlled_codes = set((schema.get("controlled_values") or {}).get("primary_code") or [])
    if not ({"INCLUDE"} | EXCLUSION_CODES | UNCERTAIN_CODES) == controlled_codes:
        raise FreshReviewError(f"{schema_path}: controlled decision codes do not match V2")
    if controlled_codes & RETIRED_CODES:
        raise FreshReviewError(f"{schema_path}: retired E8 code is incorrectly active")

    batch_fields, batch_rows = read_csv(batch_manifest_path)
    if batch_fields != BATCH_MANIFEST_FIELDS:
        raise FreshReviewError(f"{batch_manifest_path}: unexpected schema/order")
    expected_batches = int((manifest.get("counts") or {}).get("batches") or 0)
    if len(batch_rows) != expected_batches:
        raise FreshReviewError(
            f"Batch count mismatch: manifest={expected_batches}, ledger={len(batch_rows)}"
        )
    batches: list[BatchSpec] = []
    concatenated_ids: list[str] = []
    batch_by_id: dict[str, int] = {}
    prior_last = 0
    for expected_number, row in enumerate(batch_rows, start=1):
        try:
            number = int(row["batch"])
            first = int(row["first_master_row"])
            last = int(row["last_master_row"])
            records = int(row["records"])
            expected_bytes = int(row["bytes"])
            expected_template_bytes = int(row["review_template_bytes"])
        except ValueError as exc:
            raise FreshReviewError(f"{batch_manifest_path}: invalid integer value") from exc
        if number != expected_number or first != prior_last + 1:
            raise FreshReviewError(f"{batch_manifest_path}: batches are not consecutive")
        if records <= 0 or last - first + 1 != records:
            raise FreshReviewError(f"{batch_manifest_path}: invalid row span for batch {number}")
        input_path = safe_relative(root, row["file"], label=f"batch {number} input")
        template_path = safe_relative(
            root, row["review_template_file"], label=f"batch {number} template"
        )
        if not input_path.is_file() or not template_path.is_file():
            raise FreshReviewError(f"Batch {number}: input/template is missing")
        if (
            input_path.stat().st_size != expected_bytes
            or sha256_file(input_path) != row["sha256"].casefold()
            or template_path.stat().st_size != expected_template_bytes
            or sha256_file(template_path) != row["review_template_sha256"].casefold()
        ):
            raise FreshReviewError(f"Batch {number}: input/template hash or size mismatch")
        input_fields, input_rows = read_csv(input_path)
        template_fields, template_rows = read_csv(template_path)
        if input_fields != BLINDED_FIELDS:
            raise FreshReviewError(f"{input_path}: reviewer input is not the blinded schema")
        if template_fields != REVIEW_FIELDS:
            raise FreshReviewError(f"{template_path}: review-template schema/order mismatch")
        ids = [record.get("paper_id", "") for record in input_rows]
        template_ids = [record.get("paper_id", "") for record in template_rows]
        if len(ids) != records or ids != template_ids:
            raise FreshReviewError(f"Batch {number}: input/template ID order mismatch")
        if any(
            value
            for template_row in template_rows
            for key, value in template_row.items()
            if key != "paper_id"
        ):
            raise FreshReviewError(f"{template_path}: template is not blank except paper_id")
        for paper_id in ids:
            if paper_id in batch_by_id:
                raise FreshReviewError(f"Candidate duplicated across batches: {paper_id}")
            batch_by_id[paper_id] = number
        concatenated_ids.extend(ids)
        batches.append(
            BatchSpec(
                number=number,
                input_path=input_path,
                review_filename=template_path.name,
                ids=tuple(ids),
                row=dict(row),
            )
        )
        prior_last = last
    if concatenated_ids != master_ids:
        raise FreshReviewError("Batches do not cover the candidate master once in locked order")

    return CandidatePackage(
        root=root,
        codebook_path=codebook_path,
        codebook_sha256=codebook_sha,
        candidate_manifest_path=manifest_path,
        candidate_manifest_sha256=sha256_file(manifest_path),
        candidate_manifest=manifest,
        master_path=master_path,
        master_sha256=sha256_file(master_path),
        master_fields=tuple(master_fields),
        master_rows=tuple(master_rows),
        master_by_id={row["paper_id"]: row for row in master_rows},
        schema_path=schema_path,
        schema_sha256=sha256_file(schema_path),
        batch_manifest_path=batch_manifest_path,
        batch_manifest_sha256=sha256_file(batch_manifest_path),
        batches=tuple(batches),
        batch_by_id=batch_by_id,
    )


def _validate_semicolon_values(
    value: str,
    allowed: set[str],
    *,
    path: Path,
    paper_id: str,
    field: str,
) -> None:
    if not value:
        return
    items = value.split(";")
    if any(not item or item != item.strip() for item in items):
        raise FreshReviewError(f"{path}: {paper_id} has malformed {field}")
    if len(items) != len(set(items)) or not set(items) <= allowed:
        raise FreshReviewError(f"{path}: {paper_id} has invalid/duplicate {field}")


def validate_decision_logic(
    row: Mapping[str, str],
    *,
    path: Path,
    paper_id: str,
    allow_uncertain: bool,
) -> None:
    decision = row["decision"]
    code = row["primary_code"]
    if decision not in (VALID_DECISIONS if allow_uncertain else VALID_FINAL_DECISIONS):
        raise FreshReviewError(f"{path}: {paper_id} has invalid decision {decision!r}")
    if code in RETIRED_CODES or code.startswith("E8"):
        raise FreshReviewError(f"{path}: {paper_id} uses retired E8 duplicate exclusion")
    expected_codes = (
        {"INCLUDE"}
        if decision == "INCLUDE"
        else EXCLUSION_CODES
        if decision == "EXCLUDE"
        else UNCERTAIN_CODES
    )
    if code not in expected_codes:
        raise FreshReviewError(f"{path}: {paper_id} decision/code mismatch")
    if any(row[field] not in VALID_TRI_STATE for field in CRITERION_FIELDS):
        raise FreshReviewError(f"{path}: {paper_id} has invalid yes/no/unclear criterion")
    if decision == "INCLUDE" and any(row[field] != "yes" for field in CRITERION_FIELDS):
        raise FreshReviewError(f"{path}: {paper_id} INCLUDE fails a required criterion")
    if decision == "EXCLUDE" and not any(row[field] == "no" for field in CRITERION_FIELDS):
        raise FreshReviewError(f"{path}: {paper_id} EXCLUDE has no failed criterion")
    if decision == "UNCERTAIN":
        if any(row[field] == "no" for field in CRITERION_FIELDS):
            raise FreshReviewError(
                f"{path}: {paper_id} UNCERTAIN contains a decisive no criterion"
            )
        if not any(row[field] == "unclear" for field in CRITERION_FIELDS):
            raise FreshReviewError(f"{path}: {paper_id} UNCERTAIN has no unclear criterion")
    requirement = CODE_GATE_REQUIREMENTS.get(code)
    if requirement and row[requirement[0]] != requirement[1]:
        raise FreshReviewError(
            f"{path}: {paper_id} {code} requires {requirement[0]}={requirement[1]}"
        )
    if code == "U1_NEED_FULL_TEXT" and not (
        row["health_professions_education"] == "unclear"
        or row["simulation_central"] == "unclear"
        or row["eligible_document_type"] == "unclear"
    ):
        raise FreshReviewError(
            f"{path}: {paper_id} U1 requires an unclear education, simulation, or type gate"
        )
    if code == "U4_NEED_VERSION_CHECK" and not row.get("possible_version_of", ""):
        raise FreshReviewError(
            f"{path}: {paper_id} U4 requires a possible_version_of record ID"
        )


def validate_review_output(
    path: Path,
    expected_ids: Sequence[str],
    all_candidate_ids: set[str],
) -> list[dict[str, str]]:
    fields, rows = read_csv(path)
    if fields != REVIEW_FIELDS:
        raise FreshReviewError(f"{path}: expected the exact 17-field V2 schema/order")
    observed_ids = [row.get("paper_id", "") for row in rows]
    if observed_ids != list(expected_ids) or len(observed_ids) != len(set(observed_ids)):
        raise FreshReviewError(
            f"{path}: IDs are missing, unexpected, duplicated, or out of input order"
        )
    for row in rows:
        paper_id = row["paper_id"]
        if None in row or any(value is None for value in row.values()):
            raise FreshReviewError(f"{path}: {paper_id} has the wrong number of CSV fields")
        if any(value != value.strip() for value in row.values()):
            raise FreshReviewError(f"{path}: {paper_id} has leading/trailing whitespace")
        if row["confidence"] not in VALID_CONFIDENCE:
            raise FreshReviewError(f"{path}: {paper_id} has invalid confidence")
        if not row["evidence"]:
            raise FreshReviewError(f"{path}: {paper_id} is missing record-specific evidence")
        if "\n" in row["evidence"] or "\r" in row["evidence"]:
            raise FreshReviewError(f"{path}: {paper_id} evidence must be one CSV-line value")
        validate_decision_logic(
            row, path=path, paper_id=paper_id, allow_uncertain=True
        )
        _validate_semicolon_values(
            row["simulation_modalities"],
            VALID_MODALITIES,
            path=path,
            paper_id=paper_id,
            field="simulation_modalities",
        )
        _validate_semicolon_values(
            row["nts_domains"],
            VALID_NTS,
            path=path,
            paper_id=paper_id,
            field="nts_domains",
        )
        if row["study_design"] not in VALID_STUDY_DESIGNS:
            raise FreshReviewError(f"{path}: {paper_id} has invalid study_design")
        if row["decision"] == "EXCLUDE" and row["simulation_modalities"]:
            raise FreshReviewError(
                f"{path}: {paper_id} excluded records must leave simulation_modalities blank"
            )
        target = row["possible_version_of"]
        if target:
            if ";" in target or target not in all_candidate_ids or target == paper_id:
                raise FreshReviewError(
                    f"{path}: {paper_id} possible_version_of must be one other candidate paper_id"
                )
    return rows


def classify_pair(a: Mapping[str, str], b: Mapping[str, str]) -> str:
    if a["decision"] == "UNCERTAIN" and b["decision"] == "UNCERTAIN":
        return (
            "BOTH_UNCERTAIN_SAME_CODE"
            if a["primary_code"] == b["primary_code"]
            else "BOTH_UNCERTAIN_DIFFERENT_CODE"
        )
    if a["decision"] == "UNCERTAIN" or b["decision"] == "UNCERTAIN":
        return "ONE_UNCERTAIN"
    if a["decision"] != b["decision"]:
        return "DIRECT_INCLUDE_EXCLUDE_DISAGREEMENT"
    if a["decision"] == "INCLUDE":
        return "AGREED_INCLUDE"
    return (
        "AGREED_EXCLUDE_SAME_CODE"
        if a["primary_code"] == b["primary_code"]
        else "AGREED_EXCLUDE_DIFFERENT_CODE"
    )


def cohen_kappa(pairs: Sequence[tuple[str, str]], labels: Sequence[str]) -> float | None:
    if not pairs:
        return None
    count = len(pairs)
    observed = sum(left == right for left, right in pairs) / count
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum(
        (left_counts[label] / count) * (right_counts[label] / count)
        for label in labels
    )
    if math.isclose(expected, 1.0):
        return 1.0 if math.isclose(observed, 1.0) else None
    return (observed - expected) / (1 - expected)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def stable_audit_link_id(master_sha256: str, paper_id: str) -> str:
    token = sha256_text(f"gse-fresh-human-audit-v2\0{master_sha256}\0{paper_id}")
    return f"HA2-{token[:24]}"


def validate_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{64}", value or ""))

