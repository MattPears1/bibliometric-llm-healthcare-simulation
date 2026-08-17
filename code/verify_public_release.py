#!/usr/bin/env python3
"""Verify the public v2 release without network access or third-party packages."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


EXPECTED_ROWS = {
    "online_resources/online_resource_1_search_strategy/ONLINE_RESOURCE_1_EXACT_SOURCE_SEARCHES.csv": 18,
    "online_resources/online_resource_2_selection_and_versions/PUBLICATION_VERSION_LEDGER_REDUCED.csv": 547,
    "online_resources/online_resource_2_selection_and_versions/PUBLICATION_VERSION_FAMILY_SUMMARY.csv": 485,
    "online_resources/online_resource_4_phrases/SUPPLEMENT_PER_STUDY_PHRASE_INDICATORS.csv": 485,
    "online_resources/online_resource_5_reduced_dataset/ONLINE_RESOURCE_5_CHECKED_ONE_STUDY_DATASET.csv": 485,
    "online_resources/online_resource_5_reduced_dataset/ONLINE_RESOURCE_5_DATA_DICTIONARY.csv": 23,
    "audit/SUPPLEMENT_CLAIM_TO_SOURCE_REGISTER_V5.csv": 10279,
}

EXPECTED_COUNTS = {
    "completed_discovery_sources": 6,
    "retrieval_occurrences": 9719,
    "candidate_records": 3919,
    "eligible_publication_records": 547,
    "alternate_publication_versions": 62,
    "unique_studies": 485,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.reader(handle)) - 1


def release_files(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
        and ".git" not in path.relative_to(root).parts
        and path.name != "SHA256SUMS.csv"
    }


def verify(root: Path) -> dict[str, object]:
    ledger_path = root / "SHA256SUMS.csv"
    if not ledger_path.is_file():
        raise RuntimeError("SHA256SUMS.csv is missing")

    with ledger_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    actual_files = release_files(root)
    ledger_files = {row["relative_path"] for row in rows}
    if ledger_files != set(actual_files):
        missing = sorted(set(actual_files) - ledger_files)
        extra = sorted(ledger_files - set(actual_files))
        raise RuntimeError(f"Checksum coverage mismatch; missing={missing}, extra={extra}")

    for row in rows:
        path = actual_files[row["relative_path"]]
        if path.stat().st_size != int(row["bytes"]):
            raise RuntimeError(f"Byte-count mismatch: {row['relative_path']}")
        if sha256(path) != row["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch: {row['relative_path']}")

    observed_rows = {relative: csv_rows(root / relative) for relative in EXPECTED_ROWS}
    if observed_rows != EXPECTED_ROWS:
        raise RuntimeError(f"Row-count mismatch: {observed_rows}")

    freeze = json.loads((root / "audit" / "PUBLIC_RELEASE_FREEZE_V2.json").read_text(encoding="utf-8"))
    if freeze.get("authoritative_counts") != EXPECTED_COUNTS:
        raise RuntimeError("Frozen authoritative counts do not match v2.0.0")

    return {
        "status": "PASS",
        "release_files_verified": len(rows),
        "row_checks": observed_rows,
        "authoritative_counts": EXPECTED_COUNTS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.root.resolve())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
