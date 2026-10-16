#!/usr/bin/env python3
"""Shared contracts for the fresh prospective human-audit workflow V2.

Only synthetic tests call this module during development.  Production audit
files are created later, after the fresh source universe and both independent
model reviews have been finalized and frozen.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from typing import Any, Iterable, Mapping, Sequence

from fresh_screening_review_common_v2 import (
    CODE_GATE_REQUIREMENTS,
    EXCLUSION_CODES,
    UNCERTAIN_CODES,
    VALID_CONFIDENCE,
    VALID_DECISIONS,
    VALID_TRI_STATE,
    FreshReviewError,
)


AUDIT_SCHEMA_VERSION = "fresh-prospective-human-audit-v2.0"
LOCKED_SAMPLE_SEED = "20260813-HV1"
LOCKED_BOOTSTRAP_SEED = 2026081305
EXPECTED_SAMPLE_SIZE = 100

ELIGIBILITY_QUESTION = (
    "Does this scholarly work substantively concern an explicit large or "
    "generative language model used in simulation-based education or training "
    "for healthcare professionals or health-professions learners?"
)
CRITERIA_SUMMARY = (
    "Include only if all are supported: publication from 2020-01-01 through "
    "2026-08-13 and enough English evidence; an explicit large/generative "
    "language model; health-professions education or training; simulation is "
    "central; and a substantive research, review, methods, or framework paper."
)
EXCLUSION_SUMMARY = (
    "Exclude when a criterion clearly fails. Use UNCERTAIN when the title and "
    "abstract are not enough; record what source check is needed instead of guessing."
)

VISIBLE_REVIEW_FIELDS = [
    "human_audit_id",
    "title",
    "abstract",
    "source_keywords",
    "publication_year",
    "publication_date",
    "date_window_status",
    "language_status",
    "journal_or_source_title",
    "document_type",
    "eligibility_question",
    "criteria_summary",
    "exclusion_summary",
    "evidence_url_1",
    "evidence_url_2",
]

HUMAN_RESPONSE_FIELDS = [
    "human_initial_decision",
    "human_primary_code",
    "human_confidence",
    "human_date_eligible",
    "human_language_assessable",
    "human_llm_explicit",
    "human_health_professions_education",
    "human_simulation_central",
    "human_eligible_document_type",
    "human_reason",
    "full_text_needed",
    "source_checked_url",
    "human_final_decision",
    "human_final_primary_code",
    "human_final_reason",
    "remains_unresolved",
    "notes",
    "minutes_spent",
]

HUMAN_REVIEW_FIELDS = VISIBLE_REVIEW_FIELDS + HUMAN_RESPONSE_FIELDS

SECOND_HUMAN_RESPONSE_FIELDS = [
    "reviewer2_initial_decision",
    "reviewer2_primary_code",
    "reviewer2_confidence",
    "reviewer2_date_eligible",
    "reviewer2_language_assessable",
    "reviewer2_llm_explicit",
    "reviewer2_health_professions_education",
    "reviewer2_simulation_central",
    "reviewer2_eligible_document_type",
    "reviewer2_reason",
    "reviewer2_full_text_needed",
    "reviewer2_source_checked_url",
    "reviewer2_final_decision",
    "reviewer2_final_primary_code",
    "reviewer2_final_reason",
    "reviewer2_remains_unresolved",
    "reviewer2_notes",
    "reviewer2_minutes_spent",
]

SECOND_HUMAN_REVIEW_FIELDS = VISIBLE_REVIEW_FIELDS + SECOND_HUMAN_RESPONSE_FIELDS

STRATUM_FIELDS = [
    "sample_group",
    "sample_component",
    "records_reviewed",
    "resolved_binary_records",
    "human_include",
    "human_exclude",
    "human_uncertain",
    "apparent_model_status_errors",
    "apparent_error_proportion",
    "exact_95pct_lower",
    "exact_95pct_upper",
    "confirmed_model_status_errors",
    "pending_second_human_or_adjudication",
    "interpretation",
]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise FreshReviewError(f"Missing CSV: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(
    path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def stable_rank(seed: str, pool: str, paper_id: str) -> tuple[str, str]:
    """Return the reproducible hash rank and its paper-ID tie breaker."""

    return sha256_text(f"{seed}-{pool}|{paper_id}"), paper_id


def stable_order(seed: str, paper_id: str) -> tuple[str, str]:
    return sha256_text(f"{seed}-ORDER|{paper_id}"), paper_id


def _binomial_cdf(k: int, n: int, probability: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(
        math.comb(n, index)
        * probability**index
        * (1.0 - probability) ** (n - index)
        for index in range(k + 1)
    )


def _bisect_monotone(
    function: Any,
    target: float,
    *,
    increasing: bool,
    iterations: int = 100,
) -> float:
    low = 0.0
    high = 1.0
    for _ in range(iterations):
        middle = (low + high) / 2.0
        value = function(middle)
        if (value < target) == increasing:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def clopper_pearson(
    successes: int, total: int, *, alpha: float = 0.05
) -> tuple[float, float]:
    """Two-sided exact Clopper-Pearson interval for a binomial proportion."""

    if total <= 0 or successes < 0 or successes > total:
        raise ValueError("successes/total must satisfy 0 <= successes <= total and total > 0")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be between 0 and 1")
    if successes == 0:
        lower = 0.0
    else:
        lower = _bisect_monotone(
            lambda p: 1.0 - _binomial_cdf(successes - 1, total, p),
            alpha / 2.0,
            increasing=True,
        )
    if successes == total:
        upper = 1.0
    else:
        upper = _bisect_monotone(
            lambda p: _binomial_cdf(successes, total, p),
            alpha / 2.0,
            increasing=False,
        )
    return lower, upper


def validate_decision_code(decision: str, code: str, *, label: str) -> None:
    if decision not in VALID_DECISIONS:
        raise FreshReviewError(f"{label}: invalid decision {decision!r}")
    valid_codes = (
        {"INCLUDE"}
        if decision == "INCLUDE"
        else EXCLUSION_CODES
        if decision == "EXCLUDE"
        else UNCERTAIN_CODES
    )
    if code not in valid_codes or code.startswith("E8"):
        raise FreshReviewError(f"{label}: decision/primary-code mismatch")


def validate_initial_response(
    row: Mapping[str, str], *, prefix: str, label: str
) -> None:
    decision = row[f"{prefix}_initial_decision"]
    code = row[f"{prefix}_primary_code"]
    confidence = row[f"{prefix}_confidence"]
    validate_decision_code(decision, code, label=label)
    if confidence not in VALID_CONFIDENCE:
        raise FreshReviewError(f"{label}: invalid confidence")
    if not row[f"{prefix}_reason"]:
        raise FreshReviewError(f"{label}: a short evidence-based reason is required")
    gates = {
        "date_eligible": row[f"{prefix}_date_eligible"],
        "language_assessable": row[f"{prefix}_language_assessable"],
        "llm_explicit": row[f"{prefix}_llm_explicit"],
        "health_professions_education": row[
            f"{prefix}_health_professions_education"
        ],
        "simulation_central": row[f"{prefix}_simulation_central"],
        "eligible_document_type": row[f"{prefix}_eligible_document_type"],
    }
    if any(value not in VALID_TRI_STATE for value in gates.values()):
        raise FreshReviewError(f"{label}: criterion fields must be yes, no, or unclear")
    if decision == "INCLUDE" and any(value != "yes" for value in gates.values()):
        raise FreshReviewError(f"{label}: INCLUDE requires every criterion to be yes")
    if decision == "EXCLUDE" and not any(value == "no" for value in gates.values()):
        raise FreshReviewError(f"{label}: EXCLUDE requires at least one criterion to be no")
    if decision == "UNCERTAIN":
        if any(value == "no" for value in gates.values()):
            raise FreshReviewError(f"{label}: UNCERTAIN cannot contain a decisive no")
        if not any(value == "unclear" for value in gates.values()):
            raise FreshReviewError(f"{label}: UNCERTAIN requires at least one unclear criterion")
    requirement = CODE_GATE_REQUIREMENTS.get(code)
    if requirement and gates[requirement[0]] != requirement[1]:
        raise FreshReviewError(
            f"{label}: {code} requires {requirement[0]}={requirement[1]}"
        )
    if code == "U1_NEED_FULL_TEXT" and not any(
        gates[field] == "unclear"
        for field in (
            "health_professions_education",
            "simulation_central",
            "eligible_document_type",
        )
    ):
        raise FreshReviewError(
            f"{label}: U1 requires unclear education, simulation, or document type"
        )


def validate_completed_response(
    row: Mapping[str, str], *, prefix: str, label: str
) -> tuple[str, str]:
    """Validate one completed response and return its effective decision/code."""

    validate_initial_response(row, prefix=prefix, label=label)
    full_text_field = "full_text_needed" if prefix == "human" else f"{prefix}_full_text_needed"
    source_url_field = "source_checked_url" if prefix == "human" else f"{prefix}_source_checked_url"
    final_decision_field = f"{prefix}_final_decision"
    final_code_field = f"{prefix}_final_primary_code"
    final_reason_field = f"{prefix}_final_reason"
    unresolved_field = "remains_unresolved" if prefix == "human" else f"{prefix}_remains_unresolved"
    notes_field = "notes" if prefix == "human" else f"{prefix}_notes"
    minutes_field = "minutes_spent" if prefix == "human" else f"{prefix}_minutes_spent"

    full_text = row[full_text_field]
    if full_text not in {"yes", "no"}:
        raise FreshReviewError(f"{label}: full-text-needed must be yes or no")
    try:
        minutes = float(row[minutes_field])
    except (TypeError, ValueError) as exc:
        raise FreshReviewError(f"{label}: minutes_spent must be a number") from exc
    if not math.isfinite(minutes) or minutes < 0:
        raise FreshReviewError(f"{label}: minutes_spent must be finite and non-negative")
    # Access these fields so a malformed mapping fails with a clear validation path.
    _ = row[notes_field]

    if full_text == "no":
        if row[f"{prefix}_initial_decision"] == "UNCERTAIN":
            raise FreshReviewError(f"{label}: an UNCERTAIN initial decision needs a source check")
        if any(
            row[field]
            for field in (
                source_url_field,
                final_decision_field,
                final_code_field,
                final_reason_field,
                unresolved_field,
            )
        ):
            raise FreshReviewError(
                f"{label}: final/source-check fields must be blank when no source check was needed"
            )
        return row[f"{prefix}_initial_decision"], row[f"{prefix}_primary_code"]

    if not row[source_url_field]:
        raise FreshReviewError(f"{label}: source_checked_url is required after a source check")
    if not row[final_reason_field]:
        raise FreshReviewError(f"{label}: final reason is required after a source check")
    validate_decision_code(
        row[final_decision_field], row[final_code_field], label=f"{label} final"
    )
    if row[unresolved_field] not in {"yes", "no"}:
        raise FreshReviewError(f"{label}: remains_unresolved must be yes or no")
    expected_unresolved = row[final_decision_field] == "UNCERTAIN"
    if (row[unresolved_field] == "yes") != expected_unresolved:
        raise FreshReviewError(
            f"{label}: remains_unresolved must be yes exactly when the final decision is UNCERTAIN"
        )
    return row[final_decision_field], row[final_code_field]


def validate_no_whitespace_or_missing(
    row: Mapping[str, str], *, required_fields: Sequence[str], label: str
) -> None:
    if None in row or any(value is None for value in row.values()):
        raise FreshReviewError(f"{label}: malformed CSV row")
    for field in required_fields:
        if field not in row:
            raise FreshReviewError(f"{label}: missing field {field}")
        if row[field] != row[field].strip():
            raise FreshReviewError(f"{label}: leading/trailing whitespace in {field}")


def proportion_record(successes: int, total: int) -> Mapping[str, Any]:
    if total == 0:
        return {
            "successes": successes,
            "total": total,
            "proportion": None,
            "exact_95pct_lower": None,
            "exact_95pct_upper": None,
        }
    lower, upper = clopper_pearson(successes, total)
    return {
        "successes": successes,
        "total": total,
        "proportion": successes / total,
        "exact_95pct_lower": lower,
        "exact_95pct_upper": upper,
    }
