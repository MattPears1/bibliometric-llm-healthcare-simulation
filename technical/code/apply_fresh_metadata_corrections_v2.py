#!/usr/bin/env python3
"""Apply reviewed bibliographic corrections to the fresh one-work corpus.

The source consolidation is never edited.  This program creates a new,
hash-bound analysis view plus a field-level correction ledger.  Corrections
must state the expected old value, so stale or misdirected decisions fail
before any output is published.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "fresh_metadata_corrections_v2.0"
CORRECTED_NAME = "ONE_WORK_ANALYSIS_CORPUS_METADATA_CORRECTED_V2.csv"
LEDGER_NAME = "METADATA_CORRECTION_LEDGER_V2.csv"
MANIFEST_NAME = "METADATA_CORRECTION_MANIFEST_V2.json"

AUDIT_COLUMNS = [
    "metadata_correction_applied",
    "metadata_correction_ids",
    "metadata_corrected_fields",
    "metadata_source_row_sha256",
    "metadata_corrected_row_sha256",
    "metadata_evidence_urls",
    "metadata_correction_rationale",
    "metadata_reviewed_at_utc",
]

LEDGER_COLUMNS = [
    "correction_id",
    "paper_id",
    "field",
    "old_value",
    "new_value",
    "rationale",
    "evidence_url_1",
    "evidence_url_2",
    "reviewed_by",
    "reviewed_at_utc",
    "source_corpus_sha256",
    "source_row_sha256",
    "corrected_row_sha256",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_obj(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Missing CSV header: {path}")
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError(f"CSV has extra fields: {path}")
        return list(reader.fieldnames), rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def load_corrections(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "fresh_metadata_correction_decisions_v2.0":
        raise ValueError("Unexpected correction-decision schema_version")
    reviewed_by = str(data.get("reviewed_by", "")).strip()
    reviewed_at = str(data.get("reviewed_at_utc", "")).strip()
    if not reviewed_by or not reviewed_at:
        raise ValueError("reviewed_by and reviewed_at_utc are required")
    parsed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("reviewed_at_utc must include a timezone")
    corrections = data.get("corrections")
    if not isinstance(corrections, list) or not corrections:
        raise ValueError("At least one correction is required")
    return data


def validate_and_index_corrections(
    data: dict[str, Any], source_columns: list[str]
) -> dict[str, dict[str, Any]]:
    by_paper: dict[str, dict[str, Any]] = {}
    correction_ids: set[str] = set()
    for correction in data["corrections"]:
        correction_id = str(correction.get("correction_id", "")).strip()
        paper_id = str(correction.get("paper_id", "")).strip()
        rationale = str(correction.get("rationale", "")).strip()
        evidence_urls = correction.get("evidence_urls", [])
        fields = correction.get("fields")
        if not correction_id or correction_id in correction_ids:
            raise ValueError(f"Missing or duplicate correction_id: {correction_id!r}")
        if not paper_id or paper_id in by_paper:
            raise ValueError(f"Missing or duplicate paper_id: {paper_id!r}")
        if not rationale:
            raise ValueError(f"Missing rationale for {correction_id}")
        if not isinstance(evidence_urls, list) or not evidence_urls:
            raise ValueError(f"Missing evidence_urls for {correction_id}")
        if any(not str(url).startswith(("https://", "http://")) for url in evidence_urls):
            raise ValueError(f"Invalid evidence URL for {correction_id}")
        if not isinstance(fields, dict) or not fields:
            raise ValueError(f"Missing fields for {correction_id}")
        for field, decision in fields.items():
            if field not in source_columns:
                raise ValueError(f"Unknown field {field!r} for {correction_id}")
            if field == "paper_id" or field in AUDIT_COLUMNS:
                raise ValueError(f"Protected field {field!r} for {correction_id}")
            if not isinstance(decision, dict) or "expected_old" not in decision or "new" not in decision:
                raise ValueError(f"Malformed decision for {correction_id}/{field}")
            if str(decision["expected_old"]) == str(decision["new"]):
                raise ValueError(f"No-op decision for {correction_id}/{field}")
        correction_ids.add(correction_id)
        by_paper[paper_id] = correction
    return by_paper


def apply_corrections(
    source_columns: list[str],
    source_rows: list[dict[str, str]],
    corrections_data: dict[str, Any],
    source_corpus_sha256: str,
) -> tuple[list[str], list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    if "paper_id" not in source_columns:
        raise ValueError("Source corpus must contain paper_id")
    if any(column in source_columns for column in AUDIT_COLUMNS):
        raise ValueError("Source corpus already contains metadata audit columns")
    paper_ids = [row["paper_id"] for row in source_rows]
    if not all(paper_ids) or len(paper_ids) != len(set(paper_ids)):
        raise ValueError("Source paper_id values must be nonblank and unique")

    indexed = validate_and_index_corrections(corrections_data, source_columns)
    missing = sorted(set(indexed) - set(paper_ids))
    if missing:
        raise ValueError(f"Correction paper_id values not found: {missing}")

    output_columns = source_columns + AUDIT_COLUMNS
    output_rows: list[dict[str, str]] = []
    ledger_rows: list[dict[str, str]] = []
    corrected_field_count = 0

    for source_row in source_rows:
        source_copy = dict(source_row)
        source_row_sha = sha256_obj(source_copy)
        output_row = dict(source_copy)
        correction = indexed.get(source_row["paper_id"])
        changed_fields: list[str] = []
        evidence_urls: list[str] = []
        correction_ids: list[str] = []
        rationale = ""
        reviewed_at = ""

        pending_ledger: list[dict[str, str]] = []
        if correction:
            correction_id = str(correction["correction_id"])
            correction_ids.append(correction_id)
            rationale = str(correction["rationale"])
            evidence_urls = [str(url) for url in correction["evidence_urls"]]
            reviewed_at = str(corrections_data["reviewed_at_utc"])
            for field, decision in correction["fields"].items():
                expected_old = str(decision["expected_old"])
                new_value = str(decision["new"])
                if source_row[field] != expected_old:
                    raise ValueError(
                        f"Stale correction {correction_id}/{field}: expected "
                        f"{expected_old!r}, found {source_row[field]!r}"
                    )
                output_row[field] = new_value
                changed_fields.append(field)
                corrected_field_count += 1
                pending_ledger.append(
                    {
                        "correction_id": correction_id,
                        "paper_id": source_row["paper_id"],
                        "field": field,
                        "old_value": expected_old,
                        "new_value": new_value,
                        "rationale": rationale,
                        "evidence_url_1": evidence_urls[0] if evidence_urls else "",
                        "evidence_url_2": evidence_urls[1] if len(evidence_urls) > 1 else "",
                        "reviewed_by": str(corrections_data["reviewed_by"]),
                        "reviewed_at_utc": reviewed_at,
                        "source_corpus_sha256": source_corpus_sha256,
                        "source_row_sha256": source_row_sha,
                        "corrected_row_sha256": "",
                    }
                )

        output_row.update(
            {
                "metadata_correction_applied": "true" if correction else "false",
                "metadata_correction_ids": ";".join(correction_ids),
                "metadata_corrected_fields": ";".join(changed_fields),
                "metadata_source_row_sha256": source_row_sha,
                "metadata_corrected_row_sha256": "",
                "metadata_evidence_urls": ";".join(evidence_urls),
                "metadata_correction_rationale": rationale,
                "metadata_reviewed_at_utc": reviewed_at,
            }
        )
        corrected_row_sha = sha256_obj(
            {key: value for key, value in output_row.items() if key != "metadata_corrected_row_sha256"}
        )
        output_row["metadata_corrected_row_sha256"] = corrected_row_sha
        for ledger_row in pending_ledger:
            ledger_row["corrected_row_sha256"] = corrected_row_sha
            ledger_rows.append(ledger_row)
        output_rows.append(output_row)

    # Exact preservation checks.
    if [row["paper_id"] for row in output_rows] != paper_ids:
        raise AssertionError("Output paper_id order changed")
    for source_row, output_row in zip(source_rows, output_rows):
        changed = set(output_row["metadata_corrected_fields"].split(";")) - {""}
        for column in source_columns:
            if column not in changed and output_row[column] != source_row[column]:
                raise AssertionError(
                    f"Unexpected source-field change: {source_row['paper_id']}/{column}"
                )
    for row in output_rows:
        changed = set(row["metadata_corrected_fields"].split(";")) - {""}
        if changed.intersection({"year", "publication_date"}):
            if row.get("year") and row.get("publication_date") and not row["publication_date"].startswith(row["year"] + "-"):
                raise ValueError(
                    f"Corrected year does not match corrected publication_date: {row['paper_id']}"
                )
    doi_values = [row["doi"].strip().lower() for row in output_rows if row.get("doi", "").strip()]
    if len(doi_values) != len(set(doi_values)):
        raise ValueError("Corrected one-work corpus has duplicate DOI values")

    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "metadata_corrections_applied_analysis_view_ready",
        "source_rows": len(source_rows),
        "output_rows": len(output_rows),
        "corrected_records": len(indexed),
        "corrected_fields": corrected_field_count,
        "unchanged_records": len(source_rows) - len(indexed),
        "paper_id_order_preserved": True,
        "source_fields_preserved_except_reviewed_corrections": True,
        "source_corpus_sha256": source_corpus_sha256,
        "correction_decisions_sha256": "",
        "corrected_corpus_sha256": "",
        "correction_ledger_sha256": "",
        "source_column_count": len(source_columns),
        "output_column_count": len(output_columns),
    }
    return output_columns, output_rows, ledger_rows, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--corrections", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    corpus = args.corpus.resolve()
    corrections = args.corrections.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite output directory: {output_dir}")
    if not corpus.is_file() or not corrections.is_file():
        raise FileNotFoundError("Corpus and corrections must be existing files")

    source_columns, source_rows = read_csv(corpus)
    source_sha = sha256_file(corpus)
    corrections_data = load_corrections(corrections)
    output_columns, output_rows, ledger_rows, report = apply_corrections(
        source_columns, source_rows, corrections_data, source_sha
    )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=output_dir.name + ".tmp-", dir=output_dir.parent))
    try:
        corrected_path = temp_dir / CORRECTED_NAME
        ledger_path = temp_dir / LEDGER_NAME
        manifest_path = temp_dir / MANIFEST_NAME
        write_csv(corrected_path, output_columns, output_rows)
        write_csv(ledger_path, LEDGER_COLUMNS, ledger_rows)
        report["correction_decisions_sha256"] = sha256_file(corrections)
        report["corrected_corpus_sha256"] = sha256_file(corrected_path)
        report["correction_ledger_sha256"] = sha256_file(ledger_path)
        report["source_corpus_path"] = str(corpus)
        report["correction_decisions_path"] = str(corrections)
        manifest_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # Re-read disk artifacts before publication.
        disk_columns, disk_rows = read_csv(corrected_path)
        ledger_columns, disk_ledger = read_csv(ledger_path)
        if disk_columns != output_columns or len(disk_rows) != len(source_rows):
            raise AssertionError("Corrected corpus disk validation failed")
        if ledger_columns != LEDGER_COLUMNS or len(disk_ledger) != report["corrected_fields"]:
            raise AssertionError("Correction ledger disk validation failed")
        os.replace(temp_dir, output_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
