#!/usr/bin/env python3
"""Build de-novo high-sensitivity screening candidates from fresh dedup data.

The builder evaluates the complete title, complete abstract and all retained
source keywords against the current four-domain sensitivity definitions:
language-model technology, healthcare, education/training and simulation.  It
does not read or rescue any record from the legacy 551-paper corpus.  Candidate
counts and 50-record blinded reviewer batches are generated dynamically.  The
review schema and blank output templates are locked to
SCREENING_CODEBOOK_FULL_RERUN_V2_2026-08-13.md by SHA-256.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "1.0"
DOMAIN_DEFINITION_VERSION = "fresh-four-domain-v1-2026-08-14"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CODEBOOK = SCRIPT_DIR / "SCREENING_CODEBOOK_FULL_RERUN_V2_2026-08-13.md"
EXPECTED_CODEBOOK_SHA256 = (
    "ab74c88c27d7efbf34f0b3cb680cea62b03eaec4ef11bdd630925ee8639ab9bc"
)

# These definitions intentionally match the broad, high-sensitivity domains in
# the current screening code.  Eligibility is not decided here; it is decided
# by independent review under SCREENING_CODEBOOK_FULL_RERUN_V2_2026-08-13.md.
DOMAIN_PATTERNS = {
    "language_model": r"\b(?:large\s+language\s+models?|small\s+language\s+models?|language\s+models?|generative\s+(?:artificial\s+intelligence|ai)|genai|generative\s+pre[- ]?trained\s+transformers?|foundation\s+models?|chat\s*gpt|gpt(?:[- .]?(?:[1-9](?:\.5)?|4o|o1|o3))?|claude|gemini|bard|llama\s*\d*|mistral|mixtral|copilot|med[- ]?palm|palm\s*2?|biogpt|medgpt|meditron|deepseek(?:[- ]r1)?|qwen\s*\d*|phi[- ]?\d|falcon|vicuna|alpaca|grok|command\s*r|retrieval[- ]augmented\s+generation|rag|conversational\s+ai|conversational\s+agents?|ai[- ](?:powered|based|driven|assisted)\s+(?:chatbots?|agents?|virtual\s+patients?|simulat\w*)|natural\s+language\s+processing|nlp|transformer\s+models?|ai\s+chatbots?|intelligent\s+tutoring\s+systems?)\b",
    "healthcare": r"\b(?:health(?:care|\s+care|\s+professions?|\s+professional)?|medical|medicine|clinical|patient|nurs\w*|physician|doctor|surg\w*|dental|dent\w*|pharmac\w*|an(?:a?e)sthes\w*|urolog\w*|cardiol\w*|oncol\w*|p[ae]diatr\w*|emergency|resuscitation|hospital|allied\s+health|midwi\w*|paramedic|radiograph\w*|physiotherap\w*|occupational\s+therap\w*)\b",
    "education_training": r"\b(?:educat\w*|teach\w*|train\w*|learn\w*|student\w*|resident\w*|curricul\w*|pedagog\w*|faculty|instructor\w*|competenc\w*|skills?|assessment|examin\w*|clerkship\w*|boot\s?camp\w*|continuing\s+professional\s+development|undergraduate\w*|postgraduate\w*|fellow\w*)\b",
    "simulation": r"\b(?:simulat\w*|virtual\s+patients?|standardi[sz]ed\s+patients?|osces?|objective\s+structured\s+clinical\s+examin\w*|role[- ]?plays?|debrief\w*|mannequins?|manikins?|high[- ]fidelity|low[- ]fidelity|mixed\s+reality|augmented\s+reality|virtual\s+reality|immersive|haptic|serious\s+games?|scenario[- ]based\s+(?:train\w*|learn\w*|educat\w*)|clinical\s+scenarios?|patient\s+scenarios?|skills?\s+labs?|simulation\s+cent(?:re|er)s?|task\s+trainers?|mock\s+codes?|sim\s+labs?)\b",
}

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

# Trigger flags and any upstream dedup/review decisions are deliberately absent
# from reviewer inputs.  Reviewers see only bibliographic evidence and neutral
# date/language metadata needed to apply the codebook.
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

REVIEW_OUTPUT_FIELDS = [
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

REVIEW_OUTPUT_GUIDANCE = {
    "schema_version": "full-rerun-independent-review-v2.0",
    "fields": {
        "paper_id": "Copy the neutral record ID exactly.",
        "decision": "INCLUDE, EXCLUDE, or UNCERTAIN.",
        "primary_code": "INCLUDE, one active exclusion code, or one uncertainty code.",
        "confidence": "high, medium, or low.",
        "date_eligible": "yes, no, or unclear for 2020-01-01 through 2026-08-13 inclusive.",
        "language_assessable": "yes, no, or unclear for enough English evidence to judge eligibility.",
        "llm_explicit": "yes, no, or unclear for an explicit large/generative language model.",
        "health_professions_education": "yes, no, or unclear for a health-professions learner purpose.",
        "simulation_central": "yes, no, or unclear for simulation being central.",
        "eligible_document_type": "yes, no, or unclear for a substantive scholarly contribution.",
        "evidence": "One or two ordinary-language sentences tied to the retained record; required and not a long quotation.",
        "simulation_modalities": "Semicolon-separated supported V2 modality values; blank if excluded or unsupported.",
        "nts_domains": "Semicolon-separated supported V2 NTS values; blank if unsupported.",
        "specialty": "Named specialty only when explicit; otherwise blank.",
        "model_families": "Semicolon-separated model families actually used, evaluated, or centrally examined.",
        "study_design": "One V2 study-design value.",
        "possible_version_of": "Other neutral record ID when a version relationship is suspected; otherwise blank. Never use this as an exclusion decision.",
    },
    "controlled_values": {
        "decision": ["INCLUDE", "EXCLUDE", "UNCERTAIN"],
        "primary_code": [
            "INCLUDE",
            "E1_NOT_LLM",
            "E2_NOT_HEALTH_ED",
            "E3_NOT_SIMULATION",
            "E4_CLINICAL_ONLY",
            "E5_INELIGIBLE_TYPE",
            "E6_OUT_OF_RANGE",
            "E7_NOT_ASSESSABLE_IN_ENGLISH",
            "E9_OTHER",
            "U1_NEED_FULL_TEXT",
            "U2_NEED_MODEL_DETAIL",
            "U3_NEED_DOCUMENT_TYPE",
            "U4_NEED_VERSION_CHECK",
            "U5_NEED_LANGUAGE_CHECK",
            "U6_NEED_DATE_CHECK",
        ],
        "confidence": ["high", "medium", "low"],
        "criterion_gate": ["yes", "no", "unclear"],
        "simulation_modalities": [
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
        ],
        "nts_domains": [
            "communication",
            "teamwork",
            "leadership",
            "decision_making",
            "situational_awareness",
            "task_management",
            "stress_management",
            "professionalism",
            "other",
        ],
        "study_design": [
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
        ],
    },
    "retired_primary_codes": ["E8_DUPLICATE_VERSION"],
    "version_handling": (
        "Judge record eligibility first. possible_version_of is only a flag; "
        "publication versions are linked after record-level eligibility."
    ),
}


class CandidateBuildError(RuntimeError):
    """Raised when a fresh candidate set cannot be built safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_codebook(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise CandidateBuildError(f"Missing locked full-rerun codebook: {resolved}")
    observed_hash = sha256_file(resolved)
    if observed_hash.casefold() != EXPECTED_CODEBOOK_SHA256:
        raise CandidateBuildError(
            "Full-rerun screening codebook SHA-256 mismatch: "
            f"expected {EXPECTED_CODEBOOK_SHA256}, observed {observed_hash}. "
            "Do not screen against an unversioned or silently edited codebook."
        )
    return {
        "filename": resolved.name,
        "path": str(resolved),
        "version": "2.0",
        "status": "locked_for_de_novo_full_rerun",
        "sha256": observed_hash,
        "expected_sha256": EXPECTED_CODEBOOK_SHA256,
        "bytes": resolved.stat().st_size,
    }


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def unique_texts(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_text(value)
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return sorted(output, key=lambda item: (item.casefold(), item))


def iter_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CandidateBuildError(
                    f"Invalid JSONL at {path}:{line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise CandidateBuildError(f"Expected an object at {path}:{line_number}")
            rows.append(value)
    return rows


def resolve_manifested_file(root: Path, value: Any) -> Path:
    relative = Path(clean_text(value))
    if not relative or relative.is_absolute() or ".." in relative.parts:
        raise CandidateBuildError(f"Unsafe manifested path: {value!r}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CandidateBuildError(f"Manifested path escapes input directory: {value!r}") from exc
    return path


def load_deduplicated_input(
    deduplicated_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], Path]:
    manifest_path = deduplicated_dir / "DEDUPLICATION_MANIFEST.json"
    if not manifest_path.is_file():
        raise CandidateBuildError(f"Missing deduplication manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateBuildError(f"Invalid deduplication manifest: {manifest_path}") from exc

    output_entry = (manifest.get("outputs") or {}).get("deduplicated_jsonl") or {}
    path = resolve_manifested_file(
        deduplicated_dir, output_entry.get("path") or "deduplicated_records.jsonl"
    )
    if not path.is_file():
        raise CandidateBuildError(f"Missing deduplicated JSONL: {path}")
    expected_hash = clean_text(output_entry.get("sha256")).casefold()
    observed_hash = sha256_file(path)
    if not expected_hash or observed_hash.casefold() != expected_hash:
        raise CandidateBuildError(
            f"Deduplicated JSONL SHA-256 mismatch: expected {expected_hash or '<missing>'}, "
            f"observed {observed_hash}"
        )
    rows = iter_jsonl(path)
    expected_count = (manifest.get("counts") or {}).get("deduplicated_records")
    if expected_count is not None and int(expected_count) != len(rows):
        raise CandidateBuildError(
            f"Deduplicated count mismatch: manifest={expected_count}, observed={len(rows)}"
        )
    record_ids = [clean_text(row.get("dedup_id") or row.get("id")) for row in rows]
    if any(not value for value in record_ids):
        raise CandidateBuildError("Every deduplicated row must have a dedup_id or id")
    if len(record_ids) != len(set(record_ids)):
        raise CandidateBuildError("Deduplicated record IDs are not unique")
    return sorted(rows, key=lambda row: clean_text(row.get("dedup_id") or row.get("id"))), manifest, path


def author_text(record: Mapping[str, Any]) -> str:
    authors = record.get("authors") or []
    if not isinstance(authors, list):
        return clean_text(authors)
    names: list[str] = []
    for author in authors:
        if isinstance(author, Mapping):
            names.append(clean_text(author.get("name")))
        else:
            names.append(clean_text(author))
    return "; ".join(unique_texts(names))


def source_keywords(record: Mapping[str, Any]) -> list[str]:
    values: list[Any] = []
    keywords = record.get("keywords") or []
    if isinstance(keywords, list):
        values.extend(keywords)
    elif keywords:
        values.extend(re.split(r"\s*;\s*", str(keywords)))
    # Defensive retention for compatible inputs that carry only the flat field.
    flat = clean_text(record.get("source_keywords"))
    if flat:
        values.extend(re.split(r"\s*;\s*", flat))
    return unique_texts(values)


def source_list(record: Mapping[str, Any]) -> list[str]:
    values = record.get("found_in_sources") or []
    if isinstance(values, list):
        return unique_texts(values)
    if values:
        return unique_texts(re.split(r"\s*;\s*", str(values)))
    return unique_texts([record.get("source_db")])


def url_list(record: Mapping[str, Any]) -> list[str]:
    values = record.get("urls") or []
    if isinstance(values, list):
        return unique_texts([record.get("url"), *values])
    return unique_texts([record.get("url"), values])


def build_candidate_row(
    record: Mapping[str, Any], compiled: Mapping[str, re.Pattern[str]]
) -> dict[str, Any] | None:
    title = clean_text(record.get("title"))
    abstract = clean_text(record.get("abstract"))
    keywords = source_keywords(record)
    # No truncation or sampling: the full normalized fields are considered.
    screening_text = "\n".join((title, abstract, "; ".join(keywords)))
    hits = {name: bool(pattern.search(screening_text)) for name, pattern in compiled.items()}
    if not all(hits.values()):
        return None
    urls = url_list(record)
    sources = source_list(record)
    return {
        "paper_id": clean_text(record.get("dedup_id") or record.get("id")),
        "doi": clean_text(record.get("doi")),
        "title": title,
        "year": record.get("year") or "",
        "publication_date": clean_text(record.get("publication_date")),
        "date_window_status": clean_text(record.get("date_window_status")),
        "language_status": clean_text(record.get("language_status")),
        "journal": clean_text(record.get("journal")),
        "found_in_sources": "; ".join(sources),
        "record_type": clean_text(record.get("type")),
        "authors": author_text(record),
        "abstract": abstract,
        "source_keywords": "; ".join(keywords),
        "url": clean_text(record.get("url")) or (urls[0] if urls else ""),
        "all_urls": "; ".join(urls),
        "abstract_missing": not bool(abstract),
        "candidate_trigger": "all_four_domains_full_fields",
        "language_model_hit": hits["language_model"],
        "healthcare_hit": hits["healthcare"],
        "education_training_hit": hits["education_training"],
        "simulation_hit": hits["simulation"],
        "screening_text_sha256": sha256_bytes(screening_text.encode("utf-8")),
    }


def csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return canonical_json(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return value


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fields})


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(dict(row)) + "\n")


def file_entry(path: Path, root: Path, role: str) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_screening_candidates(
    deduplicated_dir: Path,
    output_dir: Path,
    *,
    batch_size: int = 50,
    codebook: Path = DEFAULT_CODEBOOK,
) -> dict[str, Any]:
    deduplicated_dir = deduplicated_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise CandidateBuildError(f"Output directory already exists: {output_dir}")
    if batch_size <= 0:
        raise CandidateBuildError("batch_size must be a positive integer")
    codebook_info = validate_codebook(codebook)

    records, dedup_manifest, input_jsonl = load_deduplicated_input(deduplicated_dir)
    unresolved_dedup_pairs = int(
        (dedup_manifest.get("counts") or {}).get("ambiguous_review_pairs") or 0
    )
    compiled = {
        name: re.compile(pattern, re.IGNORECASE) for name, pattern in DOMAIN_PATTERNS.items()
    }
    candidates = [
        row
        for record in records
        if (row := build_candidate_row(record, compiled)) is not None
    ]
    candidates.sort(key=lambda row: row["paper_id"])
    if len(candidates) != len({row["paper_id"] for row in candidates}):
        raise CandidateBuildError("Candidate paper_id values are not unique")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.building-", dir=output_dir.parent)
    )
    try:
        batch_dir = temp_dir / "input_batches"
        batch_dir.mkdir()
        review_template_dir = temp_dir / "review_output_templates"
        review_template_dir.mkdir()
        master_csv = temp_dir / "SCREENING_CANDIDATES_MASTER.csv"
        master_jsonl = temp_dir / "SCREENING_CANDIDATES_MASTER.jsonl"
        write_csv(master_csv, candidates, MASTER_FIELDS)
        write_jsonl(master_jsonl, candidates)

        review_schema = {
            **REVIEW_OUTPUT_GUIDANCE,
            "codebook": codebook_info,
            "output_fields_in_exact_order": REVIEW_OUTPUT_FIELDS,
            "evidence_source": {
                "input_fields": BLINDED_FIELDS,
                "complete_title": True,
                "complete_abstract": True,
                "complete_source_keywords": True,
                "trigger_and_prior_decisions_hidden": True,
            },
        }
        review_schema_path = temp_dir / "REVIEW_OUTPUT_SCHEMA_V2.json"
        review_schema_path.write_text(
            json.dumps(review_schema, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        batch_count = (len(candidates) + batch_size - 1) // batch_size
        width = max(3, len(str(max(batch_count, 1))))
        batch_rows: list[dict[str, Any]] = []
        for batch_number, start in enumerate(range(0, len(candidates), batch_size), start=1):
            rows = candidates[start : start + batch_size]
            filename = f"batch_{batch_number:0{width}d}.csv"
            path = batch_dir / filename
            write_csv(path, rows, BLINDED_FIELDS)
            template_filename = (
                f"batch_{batch_number:0{width}d}_review_output.csv"
            )
            template_path = review_template_dir / template_filename
            write_csv(
                template_path,
                [{"paper_id": row["paper_id"]} for row in rows],
                REVIEW_OUTPUT_FIELDS,
            )
            batch_rows.append(
                {
                    "batch": batch_number,
                    "file": f"input_batches/{filename}",
                    "review_template_file": (
                        f"review_output_templates/{template_filename}"
                    ),
                    "first_master_row": start + 1,
                    "last_master_row": start + len(rows),
                    "records": len(rows),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "review_template_bytes": template_path.stat().st_size,
                    "review_template_sha256": sha256_file(template_path),
                }
            )
        batch_manifest = temp_dir / "BATCH_MANIFEST.csv"
        write_csv(
            batch_manifest,
            batch_rows,
            [
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
            ],
        )

        date_counts = Counter(row["date_window_status"] or "missing" for row in candidates)
        language_counts = Counter(row["language_status"] or "missing" for row in candidates)
        source_counts: Counter[str] = Counter()
        for row in candidates:
            source_counts.update(
                value.strip()
                for value in row["found_in_sources"].split(";")
                if value.strip()
            )

        outputs = {
            "candidate_master_csv": file_entry(master_csv, temp_dir, "candidate_master"),
            "candidate_master_jsonl": file_entry(
                master_jsonl, temp_dir, "candidate_master_machine_readable"
            ),
            "batch_manifest": file_entry(batch_manifest, temp_dir, "blinded_batch_manifest"),
            "review_output_schema": file_entry(
                review_schema_path, temp_dir, "locked_v2_reviewer_output_schema"
            ),
        }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "pipeline": "fresh_de_novo_screening_candidate_build",
            "input": {
                "deduplicated_directory": deduplicated_dir.name,
                "deduplicated_jsonl": input_jsonl.name,
                "deduplicated_jsonl_sha256": sha256_file(input_jsonl),
                "deduplication_manifest_sha256": sha256_file(
                    deduplicated_dir / "DEDUPLICATION_MANIFEST.json"
                ),
                "deduplicated_records": len(records),
                "screening_codebook": codebook_info,
            },
            "candidate_rule": {
                "definition_version": DOMAIN_DEFINITION_VERSION,
                "definition_sha256": sha256_bytes(
                    canonical_json(DOMAIN_PATTERNS).encode("utf-8")
                ),
                "required_domains": list(DOMAIN_PATTERNS),
                "fields_searched_in_full": ["title", "abstract", "source_keywords"],
                "patterns": DOMAIN_PATTERNS,
                "legacy_corpus_rescue": False,
                "eligibility_decided_by_trigger": False,
                "note": (
                    "The trigger only creates a high-sensitivity review population; "
                    "independent reviewers apply "
                    "SCREENING_CODEBOOK_FULL_RERUN_V2_2026-08-13.md."
                ),
            },
            "counts": {
                "deduplicated_records": len(records),
                "candidate_records": len(candidates),
                "noncandidate_records": len(records) - len(candidates),
                "missing_abstract_candidates": sum(row["abstract_missing"] for row in candidates),
                "candidate_date_window_status": dict(sorted(date_counts.items())),
                "candidate_language_status": dict(sorted(language_counts.items())),
                "candidate_source_occurrences": dict(sorted(source_counts.items())),
                "batch_size": batch_size,
                "batches": len(batch_rows),
            },
            "blinding_contract": {
                "batch_fields": BLINDED_FIELDS,
                "review_output_fields": REVIEW_OUTPUT_FIELDS,
                "review_templates_are_blank_except_paper_id": True,
                "trigger_fields_omitted": True,
                "upstream_review_decisions_omitted": True,
                "legacy_membership_omitted": True,
                "retired_E8_available_as_decision": False,
                "possible_version_of_is_non_exclusion_flag": True,
                "evidence_field_required_by_codebook": True,
            },
            "outputs": outputs,
            "provenance_contract": {
                "frozen_march_data_read_or_modified": False,
                "hard_coded_record_counts": False,
                "candidate_ids_unique": True,
                "batches_cover_master_once_in_order": sum(
                    row["records"] for row in batch_rows
                ) == len(candidates),
            },
            "workflow_status": {
                "status": (
                    "provisional_pending_deduplication_review"
                    if unresolved_dedup_pairs
                    else "ready_for_independent_screening"
                ),
                "unresolved_deduplication_review_pairs": unresolved_dedup_pairs,
                "note": (
                    "Blinded batches must be regenerated after any same-record merge "
                    "accepted from the deduplication review queue."
                    if unresolved_dedup_pairs
                    else "No unresolved deduplication pairs were reported by the input manifest."
                ),
            },
            "script": {
                "filename": Path(__file__).name,
                "sha256": sha256_file(Path(__file__)),
                "python_version": sys.version.split()[0],
            },
        }
        manifest_path = temp_dir / "CANDIDATE_BUILD_MANIFEST.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        hash_rows = [
            {
                "scope": "code",
                "path": str(Path(__file__).resolve()),
                "role": "candidate_build_program",
                "bytes": Path(__file__).stat().st_size,
                "sha256": sha256_file(Path(__file__)),
            },
            {
                "scope": "input",
                "path": codebook_info["path"],
                "role": "locked_full_rerun_screening_codebook_v2",
                "bytes": codebook_info["bytes"],
                "sha256": codebook_info["sha256"],
            },
            {
                "scope": "input",
                "path": str(input_jsonl),
                "role": "deduplicated_record_input",
                "bytes": input_jsonl.stat().st_size,
                "sha256": sha256_file(input_jsonl),
            },
            {
                "scope": "input",
                "path": str(deduplicated_dir / "DEDUPLICATION_MANIFEST.json"),
                "role": "deduplication_manifest",
                "bytes": (deduplicated_dir / "DEDUPLICATION_MANIFEST.json").stat().st_size,
                "sha256": sha256_file(deduplicated_dir / "DEDUPLICATION_MANIFEST.json"),
            },
        ]
        for path, role in (
            (master_csv, "candidate_master"),
            (master_jsonl, "candidate_master_machine_readable"),
            (batch_manifest, "blinded_batch_manifest"),
            (review_schema_path, "locked_v2_reviewer_output_schema"),
            (manifest_path, "candidate_build_manifest"),
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
        for batch in batch_rows:
            path = temp_dir / batch["file"]
            hash_rows.append(
                {
                    "scope": "output",
                    "path": batch["file"],
                    "role": "blinded_review_batch",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
            template_path = temp_dir / batch["review_template_file"]
            hash_rows.append(
                {
                    "scope": "output",
                    "path": batch["review_template_file"],
                    "role": "blank_v2_review_output_template",
                    "bytes": template_path.stat().st_size,
                    "sha256": sha256_file(template_path),
                }
            )
        hash_rows.sort(key=lambda row: (row["scope"], row["path"], row["role"]))
        hash_manifest = temp_dir / "CANDIDATE_HASH_MANIFEST.csv"
        write_csv(hash_manifest, hash_rows, ["scope", "path", "role", "bytes", "sha256"])

        temp_dir.rename(output_dir)
        return manifest
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deduplicated-dir",
        required=True,
        type=Path,
        help="New derivative created by deduplicate_fresh_snapshot.py",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="New output directory; it must not already exist",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Records per blinded input batch (default: 50)",
    )
    parser.add_argument(
        "--codebook",
        type=Path,
        default=DEFAULT_CODEBOOK,
        help=(
            "Locked full-rerun screening codebook; its SHA-256 must match "
            f"{EXPECTED_CODEBOOK_SHA256} (default: {DEFAULT_CODEBOOK.name})"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = build_screening_candidates(
            args.deduplicated_dir,
            args.output_dir,
            batch_size=args.batch_size,
            codebook=args.codebook,
        )
    except CandidateBuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
