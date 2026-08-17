#!/usr/bin/env python3
"""Compute prespecified agreement estimates for the two fresh model reviews."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np


VALID_DECISIONS = ("EXCLUDE", "INCLUDE", "UNCERTAIN")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise ValueError("Wilson interval requires a positive denominator")
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return centre - half, centre + half


def kappa_from_matrix(matrix: np.ndarray) -> float | None:
    total = float(matrix.sum())
    if total <= 0:
        return None
    observed = float(np.trace(matrix)) / total
    expected = float(np.dot(matrix.sum(axis=1), matrix.sum(axis=0))) / (total * total)
    denominator = 1.0 - expected
    if abs(denominator) < 1e-15:
        return None
    return (observed - expected) / denominator


def analyse(
    pairs: Iterable[tuple[str, str]],
    labels: tuple[str, ...],
    *,
    replicates: int,
    seed: int,
) -> dict[str, object]:
    pairs = list(pairs)
    if not pairs:
        raise ValueError("No review pairs supplied")
    label_index = {label: index for index, label in enumerate(labels)}
    cells = [(left, right) for left in labels for right in labels]
    cell_counts = Counter(pairs)
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for (left, right), count in cell_counts.items():
        if left not in label_index or right not in label_index:
            raise ValueError(f"Unexpected review label pair: {(left, right)!r}")
        matrix[label_index[left], label_index[right]] = count

    total = len(pairs)
    agreement_count = int(np.trace(matrix))
    kappa = kappa_from_matrix(matrix)
    if kappa is None:
        raise ValueError("Observed kappa is undefined")

    probabilities = np.array([cell_counts[cell] / total for cell in cells], dtype=float)
    rng = np.random.default_rng(seed)
    bootstrap_cells = rng.multinomial(total, probabilities, size=replicates)
    bootstrap_matrices = bootstrap_cells.reshape(replicates, len(labels), len(labels))
    totals = bootstrap_matrices.sum(axis=(1, 2)).astype(float)
    observed = np.trace(bootstrap_matrices, axis1=1, axis2=2) / totals
    row_marginals = bootstrap_matrices.sum(axis=2)
    column_marginals = bootstrap_matrices.sum(axis=1)
    expected = (row_marginals * column_marginals).sum(axis=1) / (totals * totals)
    denominators = 1.0 - expected
    defined = np.abs(denominators) >= 1e-15
    bootstrap_kappas = (observed[defined] - expected[defined]) / denominators[defined]
    undefined_count = int((~defined).sum())
    if undefined_count / replicates > 0.05:
        lower = upper = None
        interval_status = "withheld_more_than_5_percent_undefined"
    else:
        lower, upper = (
            float(value)
            for value in np.percentile(bootstrap_kappas, [2.5, 97.5], method="linear")
        )
        interval_status = "reported"
    raw_lower, raw_upper = wilson(agreement_count, total)

    return {
        "labels": list(labels),
        "n": total,
        "confusion_matrix": {
            left: {right: int(matrix[label_index[left], label_index[right]]) for right in labels}
            for left in labels
        },
        "raw_agreement": agreement_count / total,
        "raw_agreement_count": agreement_count,
        "raw_agreement_wilson_95_ci": [raw_lower, raw_upper],
        "cohen_kappa": kappa,
        "cohen_kappa_percentile_bootstrap_95_ci": [lower, upper],
        "bootstrap_replicates_requested": replicates,
        "bootstrap_replicates_defined": int(defined.sum()),
        "bootstrap_replicates_undefined": undefined_count,
        "bootstrap_seed": seed,
        "kappa_interval_status": interval_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=2026081306)
    args = parser.parse_args()
    comparison = args.comparison.resolve()
    output = args.output.resolve()
    if output.exists():
        parser.error(f"Output already exists: {output}")
    if args.replicates <= 0:
        parser.error("--replicates must be positive")

    with comparison.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        required = {"paper_id", "reviewer_A_decision", "reviewer_B_decision"}
        if not required <= fields:
            parser.error(f"Comparison file lacks fields: {sorted(required - fields)}")
        rows = list(reader)
    paper_ids = [row["paper_id"] for row in rows]
    if not paper_ids or len(paper_ids) != len(set(paper_ids)):
        parser.error("Comparison must contain unique, nonblank paper IDs")
    for row in rows:
        for field in ("reviewer_A_decision", "reviewer_B_decision"):
            if row[field] not in VALID_DECISIONS:
                parser.error(f"Invalid {field} for {row['paper_id']}: {row[field]!r}")

    three_way_pairs = [
        (row["reviewer_A_decision"], row["reviewer_B_decision"])
        for row in rows
    ]
    binary_pairs = [
        (
            "INCLUDE" if left == "INCLUDE" else "NON_INCLUDE",
            "INCLUDE" if right == "INCLUDE" else "NON_INCLUDE",
        )
        for left, right in three_way_pairs
    ]
    result = {
        "schema_version": "fresh-model-review-agreement-v2.0",
        "comparison_file": str(comparison),
        "comparison_sha256": sha256_file(comparison),
        "interpretation_contract": {
            "reviewers": "two_independent_model_reviews",
            "human_interrater_reliability": False,
            "screening_accuracy": False,
            "screening_sensitivity_or_specificity": False,
        },
        "three_way": analyse(
            three_way_pairs,
            VALID_DECISIONS,
            replicates=args.replicates,
            seed=args.seed,
        ),
        "binary_include_vs_non_include": analyse(
            binary_pairs,
            ("NON_INCLUDE", "INCLUDE"),
            replicates=args.replicates,
            seed=args.seed,
        ),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
