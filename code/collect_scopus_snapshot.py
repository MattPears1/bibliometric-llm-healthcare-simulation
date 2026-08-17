#!/usr/bin/env python3
"""Collect a fail-closed, immutable Scopus STANDARD-metadata snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
RETRYABLE = {429, 500, 502, 503, 504}
SCOPUS_ENDPOINT = "https://api.elsevier.com/content/search/scopus"
SCOPUS_API_KEY_ENV = "ELSEVIER_API_KEY"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def parse_plan_bytes(data: bytes) -> dict[str, Any]:
    try:
        plan = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Scopus plan must be valid UTF-8 JSON") from exc
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported Scopus plan schema")
    source = plan.get("source")
    if not isinstance(source, dict):
        raise ValueError("Plan source must be an object")
    if source.get("name") != "scopus":
        raise ValueError("Plan source name must be scopus")
    if source.get("endpoint") != SCOPUS_ENDPOINT:
        raise ValueError(f"Scopus endpoint must be exactly {SCOPUS_ENDPOINT}")
    if source.get("api_key_environment_variable") != SCOPUS_API_KEY_ENV:
        raise ValueError(f"Scopus API key environment variable must be exactly {SCOPUS_API_KEY_ENV}")
    page_size = source.get("page_size")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size <= 0:
        raise ValueError("Scopus page_size must be a positive integer")
    if page_size > 200:
        raise ValueError("Scopus page_size cannot exceed the documented STANDARD-view maximum of 200")
    maximum_offset_window = source.get("maximum_offset_window")
    if (
        isinstance(maximum_offset_window, bool)
        or not isinstance(maximum_offset_window, int)
        or maximum_offset_window <= 0
        or maximum_offset_window > 5000
    ):
        raise ValueError("Scopus maximum_offset_window must be an integer from 1 through 5000")
    queries = plan.get("queries")
    if not isinstance(queries, list) or len(queries) != 3:
        raise ValueError("Plan must contain exactly three queries")
    ordinals = [q.get("ordinal") for q in queries]
    if ordinals != [1, 2, 3]:
        raise ValueError("Query ordinals must be exactly 1, 2, 3")
    if len({q.get("id") for q in queries}) != 3:
        raise ValueError("Query IDs must be unique")
    for query in queries:
        text = query.get("query")
        if not isinstance(text, str) or not text.startswith("TITLE-ABS-KEY("):
            raise ValueError(f"Invalid Scopus query: {query.get('id')}")
        if "PUBYEAR > 2019" not in text or "PUBYEAR < 2027" not in text:
            raise ValueError(f"Missing year guard: {query.get('id')}")
        if 'LIMIT-TO(LANGUAGE, "English")' not in text:
            raise ValueError(f"Missing English-language guard: {query.get('id')}")
    return plan


def read_plan(path: Path) -> dict[str, Any]:
    return parse_plan_bytes(path.read_bytes())


def entries_from_response(payload: dict[str, Any]) -> list[dict[str, Any]]:
    search = payload.get("search-results") or {}
    entries = search.get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list):
        raise ValueError("Scopus response entry is not a list")
    return [entry for entry in entries if isinstance(entry, dict) and entry.get("eid")]


def total_results_from_response(payload: dict[str, Any], query_id: str) -> int:
    search = payload.get("search-results")
    if not isinstance(search, dict):
        raise ValueError(f"Query {query_id} response is missing the search-results object")
    if "opensearch:totalResults" not in search:
        raise ValueError(f"Query {query_id} response is missing opensearch:totalResults")
    raw_total = search["opensearch:totalResults"]
    if isinstance(raw_total, bool):
        raise ValueError(f"Query {query_id} returned an invalid total-results value")
    if isinstance(raw_total, int):
        total = raw_total
    elif isinstance(raw_total, str) and raw_total.strip().isdigit():
        total = int(raw_total.strip())
    else:
        raise ValueError(f"Query {query_id} returned an invalid total-results value")
    if total < 0:
        raise ValueError(f"Query {query_id} returned a negative total-results value")
    return total


class ScopusClient:
    def __init__(self, api_key: str, timeout: int, max_attempts: int, delay: float):
        self.api_key = api_key
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.delay = delay
        self.request_counter = 0

    def get(self, endpoint: str, params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], bytes]:
        self.request_counter += 1
        request_id = f"scopus-{self.request_counter:06d}"
        url = endpoint + "?" + urllib.parse.urlencode(params)
        sanitized_url = endpoint + "?" + urllib.parse.urlencode(params)
        started = utc_now()
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            request = urllib.request.Request(
                url,
                headers={"X-ELS-APIKey": self.api_key, "Accept": "application/json"},
                method="GET",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    status = int(response.status)
                    headers = response.headers
                payload = json.loads(raw.decode("utf-8"))
                meta = {
                    "request_id": request_id,
                    "attempt": attempt,
                    "started_at_utc": started,
                    "completed_at_utc": utc_now(),
                    "status_code": status,
                    "request_url_without_credentials": sanitized_url,
                    "request_params": params,
                    "response_sha256": sha256_bytes(raw),
                    "response_bytes": len(raw),
                    "rate_limit": headers.get("X-RateLimit-Limit"),
                    "rate_remaining": headers.get("X-RateLimit-Remaining"),
                    "rate_reset": headers.get("X-RateLimit-Reset"),
                }
                time.sleep(self.delay)
                return payload, meta, raw
            except urllib.error.HTTPError as exc:
                last_error = exc
                status = int(exc.code)
                if status not in RETRYABLE or attempt == self.max_attempts:
                    raise RuntimeError(f"Scopus request failed with HTTP {status} after {attempt} attempt(s)") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    raise RuntimeError(f"Scopus request failed after {attempt} attempt(s): {type(exc).__name__}") from exc
            time.sleep(min(30.0, 2 ** (attempt - 1)))
        raise RuntimeError("Unreachable request failure") from last_error


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json(value))


def build_hash_manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "hash_manifest.csv"):
        rows.append({
            "relative_path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return rows


def run(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan).resolve()
    output = Path(args.output_dir).resolve()
    if output.exists():
        raise FileExistsError(f"Output directory already exists: {output}")
    plan_bytes = plan_path.read_bytes()
    plan_sha256 = sha256_bytes(plan_bytes)
    plan = parse_plan_bytes(plan_bytes)
    api_env = plan["source"]["api_key_environment_variable"]
    api_key = os.environ.get(api_env, "").strip()
    if not api_key:
        raise RuntimeError(f"Required environment variable is missing: {api_env}")
    output.mkdir(parents=True)
    try:
        (output / "raw" / "scopus").mkdir(parents=True)
        (output / "queries").mkdir()
        (output / "requests").mkdir()
        (output / "search_plan_used.json").write_bytes(plan_bytes)
        client = ScopusClient(api_key, args.timeout_seconds, args.max_attempts, plan["source"]["rate_limit_seconds"])
        endpoint = plan["source"]["endpoint"]
        page_size = int(plan["source"]["page_size"])
        max_window = int(plan["source"]["maximum_offset_window"])
        request_log = output / "requests" / "requests.jsonl"
        query_summaries: list[dict[str, Any]] = []
        total_written = 0
        with request_log.open("w", encoding="utf-8", newline="\n") as request_fh:
            for query in plan["queries"]:
                qid = query["id"]
                ordinal = int(query["ordinal"])
                preflight_params = {
                    "query": query["query"],
                    "count": page_size,
                    "start": 0,
                    "view": "STANDARD",
                }
                first_payload, first_meta, _ = client.get(endpoint, preflight_params)
                request_fh.write(json.dumps(first_meta, ensure_ascii=False, sort_keys=True) + "\n")
                expected = total_results_from_response(first_payload, qid)
                if expected > max_window:
                    raise RuntimeError(f"Query {qid} reports {expected} results, above the {max_window}-record offset window")
                first_entries = entries_from_response(first_payload)
                expected_first_page = min(page_size, expected)
                if len(first_entries) != expected_first_page:
                    raise RuntimeError(
                        f"Query {qid} preflight requested {page_size} records and expected "
                        f"{expected_first_page}, but received {len(first_entries)} EID-bearing records"
                    )
                if len({str(entry["eid"]) for entry in first_entries}) != len(first_entries):
                    raise RuntimeError(f"Query {qid} repeated an EID in the preflight page")
                if args.preflight_counts:
                    summary = {
                        "query_id": qid,
                        "query_ordinal": ordinal,
                        "reported_total": expected,
                        "requested_page_size": page_size,
                        "records_returned": len(first_entries),
                        "status": "preflight_complete",
                        "request_id": first_meta["request_id"],
                    }
                    query_summaries.append(summary)
                    write_json(output / "queries" / f"{ordinal:03d}_{qid}.json", summary)
                    continue

                raw_path = output / "raw" / "scopus" / f"{ordinal:03d}_{qid}.jsonl"
                seen_eids: set[str] = set()
                written = 0
                pages: list[dict[str, Any]] = []
                with raw_path.open("w", encoding="utf-8", newline="\n") as raw_fh:
                    for start in range(0, expected, page_size):
                        params = {"query": query["query"], "count": min(page_size, expected - start), "start": start, "view": "STANDARD"}
                        payload, meta, _ = client.get(endpoint, params)
                        request_fh.write(json.dumps(meta, ensure_ascii=False, sort_keys=True) + "\n")
                        current_total = total_results_from_response(payload, qid)
                        if current_total != expected:
                            raise RuntimeError(f"Query {qid} total changed during pagination: {expected} to {current_total}")
                        entries = entries_from_response(payload)
                        expected_page_records = min(params["count"], expected - start)
                        if len(entries) != expected_page_records:
                            raise RuntimeError(
                                f"Query {qid} returned {len(entries)} EID-bearing records at offset {start}; "
                                f"expected {expected_page_records}"
                            )
                        page_eids: list[str] = []
                        for entry in entries:
                            eid = str(entry["eid"])
                            if eid in seen_eids:
                                raise RuntimeError(f"Query {qid} repeated EID during pagination: {eid}")
                            seen_eids.add(eid)
                            page_eids.append(eid)
                            written += 1
                            envelope = {
                                "schema_version": SCHEMA_VERSION,
                                "source": "scopus",
                                "source_role": "additional_discovery",
                                "query_id": qid,
                                "query_ordinal": ordinal,
                                "query_text": query["query"],
                                "record_ordinal": written,
                                "request_id": meta["request_id"],
                                "request_status_code": meta["status_code"],
                                "request_response_sha256": meta["response_sha256"],
                                "retrieved_at_utc": meta["completed_at_utc"],
                                "raw_format": "scopus_standard_json",
                                "raw_record": entry,
                            }
                            raw_fh.write(json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n")
                        pages.append({
                            "start": start,
                            "requested": params["count"],
                            "returned": len(entries),
                            "request_id": meta["request_id"],
                            "response_sha256": meta["response_sha256"],
                            "first_eid": page_eids[0] if page_eids else None,
                            "last_eid": page_eids[-1] if page_eids else None,
                        })
                if written != expected:
                    raise RuntimeError(f"Query {qid} wrote {written} records but Scopus reported {expected}")
                total_written += written
                summary = {
                    "query_id": qid,
                    "query_ordinal": ordinal,
                    "query_text": query["query"],
                    "reported_total": expected,
                    "records_written": written,
                    "unique_eids": len(seen_eids),
                    "page_count": len(pages),
                    "pages": pages,
                    "raw_file": raw_path.relative_to(output).as_posix(),
                    "status": "complete",
                }
                query_summaries.append(summary)
                write_json(output / "queries" / f"{ordinal:03d}_{qid}.json", summary)

        run_manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": output.name,
            "status": "preflight_complete" if args.preflight_counts else "complete",
            "mode": "preflight_counts" if args.preflight_counts else "full_collection",
            "created_at_utc": utc_now(),
            "plan_path": str(plan_path),
            "plan_sha256": plan_sha256,
            "source": "scopus",
            "access_level": "STANDARD",
            "credentials_serialized": False,
            "query_count": len(query_summaries),
            "reported_total_sum": sum(int(q["reported_total"]) for q in query_summaries),
            "records_written_sum": total_written,
            "queries": query_summaries,
        }
        write_json(output / "run_manifest.json", run_manifest)
        rows = build_hash_manifest(output)
        with (output / "hash_manifest.csv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["relative_path", "bytes", "sha256"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(json.dumps({
            "status": run_manifest["status"],
            "query_count": run_manifest["query_count"],
            "reported_total_sum": run_manifest["reported_total_sum"],
            "records_written_sum": run_manifest["records_written_sum"],
            "output_dir": str(output),
        }, sort_keys=True))
        return 0
    except Exception:
        failure = {
            "schema_version": SCHEMA_VERSION,
            "status": "incomplete_error",
            "failed_at_utc": utc_now(),
            "credentials_serialized": False,
            "error_type": type(sys.exc_info()[1]).__name__,
            "error": str(sys.exc_info()[1]),
        }
        write_json(output / "FAILED_RUN.json", failure)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--preflight-counts", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--max-attempts", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
