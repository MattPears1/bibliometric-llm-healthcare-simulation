#!/usr/bin/env python3
"""Create an immutable, provenance-rich metadata discovery snapshot.

This collector is deliberately separate from the frozen corpus used in the
current revision.  It never loads ``.env`` files, never writes credentials,
never appends to a previous run, and refuses output paths inside protected
source/baseline directories.

The output is raw source metadata, not an eligibility decision.  Source-level
date and language limitations are recorded in the search plan and in every
query manifest entry so downstream screening can handle unknown metadata
explicitly.
"""

from __future__ import annotations

import argparse
import dataclasses
import email.utils
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Mapping, TextIO


SCRIPT_DIR = Path(__file__).resolve().parent
ACTIVE_ROOT = SCRIPT_DIR.parent
DEFAULT_PLAN = SCRIPT_DIR / "COLLECTION_SEARCH_PLAN_V1.json"
SOURCE_ORDER = (
    "openalex",
    "pubmed",
    "europepmc",
    "crossref",
    "semantic_scholar",
    "core",
    "doaj",
)
SOURCE_ALIASES = {
    "all": "all",
    "openalex": "openalex",
    "pubmed": "pubmed",
    "europepmc": "europepmc",
    "europe_pmc": "europepmc",
    "europe-pmc": "europepmc",
    "crossref": "crossref",
    "semantic_scholar": "semantic_scholar",
    "semantic-scholar": "semantic_scholar",
    "semanticscholar": "semantic_scholar",
    "s2": "semantic_scholar",
    "core": "core",
    "doaj": "doaj",
}
PAGE_SIZE_OVERRIDE_SOURCES = {
    "openalex",
    "pubmed",
    "europepmc",
    "crossref",
    "core",
    "doaj",
}
KNOWN_ENDPOINTS = {
    "openalex": "https://api.openalex.org/works",
    "pubmed": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
    "europepmc": "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
    "crossref": "https://api.crossref.org/works",
    "semantic_scholar": "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
    "core": "https://api.core.ac.uk/v3/search/works",
    "doaj": "https://doaj.org/api/search/articles",
}
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}
SECRET_PARAM_NAMES = {
    "api_key",
    "apikey",
    "key",
    "webenv",
    "query_key",
}
SECRET_HEADER_NAMES = {
    "authorization",
    "x-api-key",
}
SAFE_RESPONSE_HEADERS = {
    "content-type",
    "retry-after",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-retry-after",
    "x-ratelimit-reset",
    "x-rate-limit-limit",
    "x-rate-limit-interval",
}


class PlanError(ValueError):
    """Raised when the versioned search plan is incomplete or unsafe."""


class CollectionRequestError(RuntimeError):
    """Raised after a request exhausts its bounded retry policy."""

    def __init__(
        self,
        source: str,
        query_id: str,
        category: str,
        status_code: int | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            f"{source}/{query_id}: request failed ({category}"
            + (f", HTTP {status_code}" if status_code is not None else "")
            + ")"
        )
        self.source = source
        self.query_id = query_id
        self.category = category
        self.status_code = status_code
        self.context = dict(context or {})


@dataclasses.dataclass(frozen=True)
class HttpResult:
    request_id: str
    status_code: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8-sig"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def utc_run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_line(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def load_plan(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PlanError(f"Cannot read search plan: {path}") from exc
    try:
        plan = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"Search plan is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(plan, dict):
        raise PlanError("Search plan root must be a JSON object")
    validate_plan(plan)
    return plan


def validate_plan(plan: Mapping[str, Any]) -> None:
    required_top = {
        "schema_version",
        "plan_id",
        "plan_version",
        "study_window",
        "contact",
        "query_profiles",
        "sources",
    }
    missing = sorted(required_top - set(plan))
    if missing:
        raise PlanError(f"Search plan is missing keys: {', '.join(missing)}")

    window = plan["study_window"]
    if not isinstance(window, Mapping):
        raise PlanError("study_window must be an object")
    try:
        start = date.fromisoformat(str(window["from"]))
        end = date.fromisoformat(str(window["through"]))
    except (KeyError, ValueError) as exc:
        raise PlanError("study_window.from/through must be ISO dates") from exc
    if start > end:
        raise PlanError("study_window.from cannot be after study_window.through")
    if window.get("inclusive") is not True:
        raise PlanError("This collector requires an explicitly inclusive study window")

    profiles = plan["query_profiles"]
    sources = plan["sources"]
    if not isinstance(profiles, Mapping) or not isinstance(sources, Mapping):
        raise PlanError("query_profiles and sources must be objects")
    if set(sources) != set(SOURCE_ORDER):
        raise PlanError(
            "sources must be exactly: " + ", ".join(SOURCE_ORDER)
        )

    for profile_name, queries in profiles.items():
        if not isinstance(queries, list) or not queries:
            raise PlanError(f"Query profile {profile_name!r} must be a non-empty list")
        seen: set[str] = set()
        for query in queries:
            if not isinstance(query, Mapping):
                raise PlanError(f"Query in {profile_name!r} must be an object")
            query_id = str(query.get("id", ""))
            query_text = str(query.get("query", ""))
            if not re.fullmatch(r"[a-z0-9_]+", query_id):
                raise PlanError(f"Unsafe query id {query_id!r} in {profile_name!r}")
            if query_id in seen:
                raise PlanError(f"Duplicate query id {query_id!r} in {profile_name!r}")
            if not query_text.strip():
                raise PlanError(f"Empty query text for {query_id!r}")
            seen.add(query_id)

    for source, config in sources.items():
        if not isinstance(config, Mapping):
            raise PlanError(f"Source {source!r} configuration must be an object")
        source_role = str(config.get("source_role", "discovery"))
        if source_role not in {
            "discovery",
            "supplementary_discovery",
            "doi_metadata_enrichment",
        }:
            raise PlanError(
                f"Source {source!r} has unsupported source_role {source_role!r}"
            )
        profile = config.get("query_profile")
        if source_role in {"discovery", "supplementary_discovery"}:
            if profile not in profiles:
                raise PlanError(
                    f"Source {source!r} references unknown profile {profile!r}"
                )
        else:
            if source != "crossref":
                raise PlanError(
                    "Only Crossref may use the DOI-metadata-enrichment role"
                )
            if profile is not None:
                raise PlanError(
                    "Crossref DOI enrichment must not declare a discovery query profile"
                )
        endpoint = str(config.get("endpoint", ""))
        if not endpoint.startswith("https://"):
            raise PlanError(f"Source {source!r} endpoint must use HTTPS")
        if endpoint != KNOWN_ENDPOINTS[source]:
            raise PlanError(
                f"Source {source!r} endpoint is not the audited official endpoint"
            )
        for numeric in ("page_size", "max_records_per_query"):
            try:
                if int(config[numeric]) <= 0:
                    raise ValueError
            except (KeyError, TypeError, ValueError) as exc:
                raise PlanError(f"Source {source!r} needs positive {numeric}") from exc
        for note in ("date_handling", "language_handling", "pagination"):
            if not str(config.get(note, "")).strip():
                raise PlanError(f"Source {source!r} needs {note}")
        env_name = config.get("key_environment_variable")
        if env_name is not None and not re.fullmatch(r"[A-Z][A-Z0-9_]+", str(env_name)):
            raise PlanError(f"Unsafe key environment-variable name for {source!r}")


def plan_queries(plan: Mapping[str, Any], source: str) -> list[dict[str, str]]:
    profile = plan["sources"][source]["query_profile"]
    if profile is None:
        return []
    return [dict(query) for query in plan["query_profiles"][profile]]


def resolve_sources(values: Iterable[str] | None) -> list[str]:
    if not values:
        return list(SOURCE_ORDER)
    resolved: list[str] = []
    for raw_value in values:
        for part in raw_value.split(","):
            key = part.strip().lower()
            if key not in SOURCE_ALIASES:
                raise PlanError(f"Unknown source {part!r}")
            canonical = SOURCE_ALIASES[key]
            if canonical == "all":
                return list(SOURCE_ORDER)
            if canonical not in resolved:
                resolved.append(canonical)
    return [source for source in SOURCE_ORDER if source in resolved]


def resolve_page_size_overrides(
    values: Iterable[str] | None,
    plan: Mapping[str, Any],
    selected_sources: Iterable[str],
) -> dict[str, int]:
    """Parse audited runtime-only SOURCE=SIZE pagination overrides.

    Page size changes request chunking only; it must never broaden the locked
    scientific search. An override may therefore only lower (or equal) the
    frozen plan value and may only target a selected, page-size-aware source.
    """

    if not values:
        return {}
    selected = set(selected_sources)
    parsed: dict[str, int] = {}
    for raw_value in values:
        raw = str(raw_value).strip()
        if raw.count("=") != 1:
            raise PlanError(
                "--page-size-override must use SOURCE=SIZE exactly once"
            )
        raw_source, raw_size = (part.strip() for part in raw.split("=", 1))
        alias = raw_source.lower()
        if alias not in SOURCE_ALIASES or SOURCE_ALIASES[alias] == "all":
            raise PlanError(f"Unknown page-size override source {raw_source!r}")
        source = SOURCE_ALIASES[alias]
        if source not in selected:
            raise PlanError(
                f"Page-size override source {source!r} is not selected for this run"
            )
        if source not in PAGE_SIZE_OVERRIDE_SOURCES:
            raise PlanError(
                f"Source {source!r} does not expose a runtime page-size control"
            )
        if source in parsed:
            raise PlanError(f"Duplicate page-size override for {source!r}")
        try:
            size = int(raw_size)
        except ValueError as exc:
            raise PlanError(
                f"Page-size override for {source!r} must be an integer"
            ) from exc
        if size <= 0:
            raise PlanError(
                f"Page-size override for {source!r} must be positive"
            )
        source_role = str(
            plan["sources"][source].get("source_role", "discovery")
        )
        if source_role == "doi_metadata_enrichment":
            raise PlanError(
                f"Page-size override is not applicable to enrichment-only source {source!r}"
            )
        planned_size = int(plan["sources"][source]["page_size"])
        if size > planned_size:
            raise PlanError(
                f"Page-size override for {source!r} ({size}) cannot exceed "
                f"the frozen plan value ({planned_size})"
            )
        parsed[source] = size
    return {
        source: parsed[source]
        for source in SOURCE_ORDER
        if source in parsed
    }


def within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def ensure_safe_new_output(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    protected = (
        ACTIVE_ROOT / "00_SUBMISSION_BASELINE_EXACT",
        ACTIVE_ROOT / "02_SOURCE_DATA",
        SCRIPT_DIR / "legacy_reference",
    )
    for root in protected:
        if within(resolved, root.resolve()):
            raise PlanError(f"Output path is inside protected frozen material: {root}")
    if resolved.exists():
        raise PlanError(f"Output path already exists; refusing to append/overwrite: {resolved}")
    resolved.mkdir(parents=True, exist_ok=False)
    return resolved


def sanitized_params(params: Mapping[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in params.items():
        if key.lower() in SECRET_PARAM_NAMES:
            clean[key] = "<present:redacted>" if value not in (None, "") else "<absent>"
        else:
            clean[key] = value
    return clean


def safe_response_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        key.lower(): value
        for key, value in headers.items()
        if key.lower() in SAFE_RESPONSE_HEADERS
    }


def parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(0.0, (parsed - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return max(
                    0.0,
                    (parsed - datetime.now(timezone.utc)).total_seconds(),
                )
            except (TypeError, ValueError, OverflowError):
                return None


def response_header(headers: Mapping[str, str], name: str) -> str | None:
    wanted = name.lower()
    return next(
        (value for key, value in headers.items() if key.lower() == wanted),
        None,
    )


class RawQueryWriter:
    """Exclusive JSONL writer for one source/query raw stream."""

    def __init__(self, path: Path, source: str, query_id: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.source = source
        self.query_id = query_id
        self.handle: TextIO = path.open("x", encoding="utf-8", newline="\n")
        self.count = 0

    def write(
        self,
        raw_record: Any,
        request_id: str,
        raw_format: str = "json",
    ) -> None:
        self.count += 1
        envelope = {
            "schema_version": "1.0",
            "source": self.source,
            "query_id": self.query_id,
            "record_ordinal": self.count,
            "retrieved_at_utc": utc_now(),
            "request_id": request_id,
            "raw_format": raw_format,
            "raw_record": raw_record,
        }
        self.handle.write(json_line(envelope) + "\n")

    def close(self) -> None:
        if not self.handle.closed:
            self.handle.flush()
            self.handle.close()


class SnapshotCollector:
    def __init__(
        self,
        plan: dict[str, Any],
        plan_path: Path,
        sources: list[str],
        output_dir: Path,
        max_records: int | None,
        smoke_test: bool,
        preflight_counts: bool,
        timeout_seconds: float,
        max_attempts: int,
        page_size_overrides: Mapping[str, int] | None = None,
    ) -> None:
        self.plan = plan
        self.plan_path = plan_path.resolve()
        self.sources = sources
        self.output_dir = ensure_safe_new_output(output_dir)
        self.max_records = max_records
        self.smoke_test = smoke_test
        self.preflight_counts = preflight_counts
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.page_size_overrides = resolve_page_size_overrides(
            [f"{source}={size}" for source, size in (page_size_overrides or {}).items()],
            self.plan,
            self.sources,
        )
        self.run_id = self.output_dir.name
        self.started_at = utc_now()
        self.last_request_monotonic: dict[str, float] = {}
        self.request_sequence = 0
        self.query_sequence = 0
        self.request_log_path = self.output_dir / "provenance" / "request_manifest.jsonl"
        self.query_log_path = self.output_dir / "provenance" / "query_manifest.jsonl"
        self.request_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.request_log: TextIO = self.request_log_path.open(
            "x", encoding="utf-8", newline="\n"
        )
        self.query_log: TextIO = self.query_log_path.open(
            "x", encoding="utf-8", newline="\n"
        )
        write_json_new(self.output_dir / "search_plan_used.json", self.plan)

        contact = self.plan["contact"]
        contact_env = str(contact["email_environment_variable"])
        self.contact_email = os.environ.get(contact_env) or str(contact["fallback_email"])
        if (
            not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", self.contact_email)
            or "\r" in self.contact_email
            or "\n" in self.contact_email
        ):
            raise PlanError(
                f"{contact_env} must contain a syntactically valid contact email"
            )
        self.user_agent = (
            f"{contact['user_agent_product']}/{self.plan['plan_version']} "
            f"(mailto:{self.contact_email})"
        )

        env_names = sorted(
            {
                str(config["key_environment_variable"])
                for config in self.plan["sources"].values()
                if config.get("key_environment_variable")
            }
        )
        self.key_environment_presence = {
            name: bool(os.environ.get(name)) for name in env_names
        }
        self.source_results: dict[str, Any] = {}
        self.query_errors = 0

    def _source_key(self, source: str) -> str:
        env_name = self.plan["sources"][source].get("key_environment_variable")
        return os.environ.get(str(env_name), "") if env_name else ""

    def _rate_limit(self, source: str) -> float:
        config = self.plan["sources"][source]
        has_key = bool(self._source_key(source))
        if has_key and "rate_limit_seconds_with_key" in config:
            return float(config["rate_limit_seconds_with_key"])
        if not has_key and "rate_limit_seconds_without_key" in config:
            return float(config["rate_limit_seconds_without_key"])
        return float(config.get("rate_limit_seconds", 1.0))

    def _throttle(self, source: str) -> None:
        interval = self._rate_limit(source)
        previous = self.last_request_monotonic.get(source)
        if previous is not None:
            remaining = interval - (time.monotonic() - previous)
            if remaining > 0:
                time.sleep(remaining)
        self.last_request_monotonic[source] = time.monotonic()

    def _request_id(self, source: str) -> str:
        self.request_sequence += 1
        return f"{source}-{self.request_sequence:06d}"

    def _log_request(self, entry: Mapping[str, Any]) -> None:
        self.request_log.write(json_line(dict(entry)) + "\n")
        self.request_log.flush()

    def _log_query(self, entry: Mapping[str, Any]) -> None:
        self.query_log.write(json_line(dict(entry)) + "\n")
        self.query_log.flush()

    def http_get(
        self,
        source: str,
        query_id: str,
        endpoint: str,
        params: Mapping[str, Any],
        extra_headers: Mapping[str, str] | None = None,
    ) -> HttpResult:
        headers = {
            "Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8",
            "User-Agent": self.user_agent,
        }
        if extra_headers:
            headers.update(extra_headers)
        credential_headers = sorted(
            key for key in headers if key.lower() in SECRET_HEADER_NAMES
        )
        query_string = urllib.parse.urlencode(params, doseq=True)
        url = endpoint + ("&" if "?" in endpoint else "?") + query_string

        for attempt in range(1, self.max_attempts + 1):
            request_id = self._request_id(source)
            self._throttle(source)
            started = utc_now()
            started_clock = time.monotonic()
            request = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read()
                    response_headers = dict(response.headers.items())
                    status_code = int(response.status)
                duration_ms = round((time.monotonic() - started_clock) * 1000, 1)
                self._log_request(
                    {
                        "schema_version": "1.0",
                        "request_id": request_id,
                        "source": source,
                        "query_id": query_id,
                        "attempt": attempt,
                        "started_at_utc": started,
                        "completed_at_utc": utc_now(),
                        "duration_ms": duration_ms,
                        "method": "GET",
                        "endpoint": endpoint,
                        "params": sanitized_params(params),
                        "credential_headers_present": credential_headers,
                        "status_code": status_code,
                        "outcome": "success",
                        "response_headers": safe_response_headers(response_headers),
                        "response_bytes": len(body),
                        "response_sha256": sha256_bytes(body),
                    }
                )
                return HttpResult(request_id, status_code, response_headers, body)

            except urllib.error.HTTPError as exc:
                body = exc.read()
                response_headers = dict(exc.headers.items()) if exc.headers else {}
                status_code = int(exc.code)
                retryable = status_code in RETRYABLE_STATUS and attempt < self.max_attempts
                duration_ms = round((time.monotonic() - started_clock) * 1000, 1)
                self._log_request(
                    {
                        "schema_version": "1.0",
                        "request_id": request_id,
                        "source": source,
                        "query_id": query_id,
                        "attempt": attempt,
                        "started_at_utc": started,
                        "completed_at_utc": utc_now(),
                        "duration_ms": duration_ms,
                        "method": "GET",
                        "endpoint": endpoint,
                        "params": sanitized_params(params),
                        "credential_headers_present": credential_headers,
                        "status_code": status_code,
                        "outcome": "retry" if retryable else "error",
                        "error_category": "http_error",
                        "response_headers": safe_response_headers(response_headers),
                        "response_bytes": len(body),
                        "response_sha256": sha256_bytes(body),
                    }
                )
                if not retryable:
                    raise CollectionRequestError(
                        source, query_id, "http_error", status_code
                    ) from exc
                retry_after = parse_retry_after(
                    response_header(response_headers, "Retry-After")
                    or response_header(response_headers, "X-RateLimit-Retry-After")
                )
                delay = retry_after if retry_after is not None else float(2 ** (attempt - 1))
                time.sleep(min(max(delay, 0.25), 30.0))

            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                retryable = attempt < self.max_attempts
                duration_ms = round((time.monotonic() - started_clock) * 1000, 1)
                self._log_request(
                    {
                        "schema_version": "1.0",
                        "request_id": request_id,
                        "source": source,
                        "query_id": query_id,
                        "attempt": attempt,
                        "started_at_utc": started,
                        "completed_at_utc": utc_now(),
                        "duration_ms": duration_ms,
                        "method": "GET",
                        "endpoint": endpoint,
                        "params": sanitized_params(params),
                        "credential_headers_present": credential_headers,
                        "status_code": None,
                        "outcome": "retry" if retryable else "error",
                        "error_category": type(exc).__name__,
                        "response_headers": {},
                        "response_bytes": 0,
                        "response_sha256": None,
                    }
                )
                if not retryable:
                    raise CollectionRequestError(
                        source, query_id, type(exc).__name__
                    ) from exc
                time.sleep(min(float(2 ** (attempt - 1)), 30.0))

        raise CollectionRequestError(source, query_id, "retry_exhausted")

    def _cap_for(self, source: str) -> int:
        plan_cap = int(self.plan["sources"][source]["max_records_per_query"])
        if self.smoke_test or self.preflight_counts:
            return 1
        if self.max_records is None:
            return plan_cap
        return min(plan_cap, self.max_records)

    def _page_size(self, source: str) -> int:
        return self.page_size_overrides.get(
            source, int(self.plan["sources"][source]["page_size"])
        )

    def _raw_path(self, source: str, ordinal: int, query_id: str) -> Path:
        return self.output_dir / "raw" / source / f"{ordinal:03d}_{query_id}.jsonl"

    def _collect_openalex(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["openalex"]
        window = self.plan["study_window"]
        cursor = "*"
        pages = 0
        source_total: int | None = None
        selected_fields = (
            "id,doi,title,display_name,publication_year,publication_date,ids,language,"
            "primary_location,type,indexed_in,open_access,authorships,"
            "corresponding_author_ids,corresponding_institution_ids,cited_by_count,"
            "counts_by_year,referenced_works_count,abstract_inverted_index,keywords,"
            "topics,primary_topic,mesh,locations_count,is_retracted,is_paratext,"
            "updated_date,created_date"
        )
        while writer.count < cap:
            requested = min(self._page_size("openalex"), cap - writer.count)
            search_parameter = str(config.get("search_parameter", "search"))
            date_language_filter = (
                f"from_publication_date:{window['from']},"
                f"to_publication_date:{window['through']},language:en"
            )
            params: dict[str, Any] = {
                "per-page": requested,
                "cursor": cursor,
                "select": selected_fields,
                "mailto": self.contact_email,
            }
            if search_parameter == "search":
                params["search"] = query
                params["filter"] = date_language_filter
            elif search_parameter == "title_and_abstract.search":
                params["filter"] = (
                    f"title_and_abstract.search:{query},{date_language_filter}"
                )
            else:
                raise ValueError(
                    f"Unsupported OpenAlex search_parameter {search_parameter!r}"
                )
            key = self._source_key("openalex")
            if key:
                params["api_key"] = key
            response = self.http_get(
                "openalex", query_id, str(config["endpoint"]), params
            )
            data = response.json()
            results = data.get("results", [])
            if not isinstance(results, list):
                raise ValueError("OpenAlex response results is not a list")
            meta = data.get("meta", {}) or {}
            if source_total is None:
                source_total = int(meta.get("count", len(results)))
            pages += 1
            for record in results[: cap - writer.count]:
                writer.write(record, response.request_id)
            next_cursor = meta.get("next_cursor")
            if (
                not results
                or len(results) < requested
                or not next_cursor
                or next_cursor == cursor
                or writer.count >= cap
            ):
                break
            cursor = str(next_cursor)
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
            "selected_fields": selected_fields.split(","),
            "search_parameter": search_parameter,
        }

    def _pubmed_common_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "tool": "GSEMetadataSnapshot",
            "email": self.contact_email,
        }
        key = self._source_key("pubmed")
        if key:
            params["api_key"] = key
        return params

    def _collect_pubmed(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["pubmed"]
        window = self.plan["study_window"]
        full_query = (
            f"({query}) AND english[lang] AND "
            f"(\"{window['from']}\"[Date - Publication] : "
            f"\"{window['through']}\"[Date - Publication])"
        )
        base = str(config["endpoint"]).rstrip("/")
        search_params = {
            "db": "pubmed",
            "term": full_query,
            "retmode": "json",
            "retmax": 0,
            "usehistory": "y",
            **self._pubmed_common_params(),
        }
        search_response = self.http_get(
            "pubmed", query_id, base + "/esearch.fcgi", search_params
        )
        search_data = search_response.json().get("esearchresult", {})
        source_total = int(search_data.get("count", 0))
        webenv = str(search_data.get("webenv", ""))
        query_key = str(search_data.get("querykey", ""))
        target = min(source_total, cap)
        pages = 1
        if target and (not webenv or not query_key):
            raise ValueError("PubMed ESearch did not return WebEnv/query key")

        while writer.count < target:
            requested = min(
                self._page_size("pubmed"), target - writer.count
            )
            fetch_params = {
                "db": "pubmed",
                "WebEnv": webenv,
                "query_key": query_key,
                "retstart": writer.count,
                "retmax": requested,
                "rettype": "abstract",
                "retmode": "xml",
                **self._pubmed_common_params(),
            }
            fetch_response = self.http_get(
                "pubmed", query_id, base + "/efetch.fcgi", fetch_params
            )
            pages += 1
            root = ET.fromstring(fetch_response.body)
            records = list(root.findall("./PubmedArticle")) + list(
                root.findall("./PubmedBookArticle")
            )
            if not records:
                break
            for element in records[: target - writer.count]:
                writer.write(
                    {"xml": ET.tostring(element, encoding="unicode")},
                    fetch_response.request_id,
                    raw_format="pubmed_xml_fragment",
                )
            if len(records) < requested:
                break
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
            "esearch_history_used": True,
            "pubmed_10000_access_limit_acknowledged": True,
        }

    def _collect_europepmc(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["europepmc"]
        window = self.plan["study_window"]
        full_query = (
            f"({query}) AND FIRST_PDATE:[{window['from']} TO {window['through']}] "
            "AND LANG:eng"
        )
        cursor = "*"
        pages = 0
        source_total: int | None = None
        while writer.count < cap:
            requested = min(self._page_size("europepmc"), cap - writer.count)
            params = {
                "query": full_query,
                "format": "json",
                "resultType": "core",
                "pageSize": requested,
                "cursorMark": cursor,
                "email": self.contact_email,
            }
            response = self.http_get(
                "europepmc", query_id, str(config["endpoint"]), params
            )
            data = response.json()
            results = (data.get("resultList", {}) or {}).get("result", [])
            if not isinstance(results, list):
                raise ValueError("Europe PMC resultList.result is not a list")
            if source_total is None:
                source_total = int(data.get("hitCount", len(results)))
            pages += 1
            for record in results[: cap - writer.count]:
                writer.write(record, response.request_id)
            next_cursor = data.get("nextCursorMark")
            if (
                not results
                or len(results) < requested
                or not next_cursor
                or next_cursor == cursor
                or writer.count >= cap
            ):
                break
            cursor = str(next_cursor)
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
        }

    def _collect_crossref(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["crossref"]
        window = self.plan["study_window"]
        cursor = "*"
        pages = 0
        source_total: int | None = None
        while writer.count < cap:
            requested = min(self._page_size("crossref"), cap - writer.count)
            params = {
                "query.bibliographic": query,
                "filter": (
                    f"from-pub-date:{window['from']},"
                    f"until-pub-date:{window['through']}"
                ),
                "rows": requested,
                "cursor": cursor,
                "mailto": self.contact_email,
            }
            response = self.http_get(
                "crossref", query_id, str(config["endpoint"]), params
            )
            message = response.json().get("message", {})
            items = message.get("items", [])
            if not isinstance(items, list):
                raise ValueError("Crossref message.items is not a list")
            if source_total is None:
                source_total = int(message.get("total-results", len(items)))
            pages += 1
            for record in items[: cap - writer.count]:
                writer.write(record, response.request_id)
            next_cursor = message.get("next-cursor")
            if (
                not items
                or len(items) < requested
                or not next_cursor
                or next_cursor == cursor
                or writer.count >= cap
            ):
                break
            cursor = str(next_cursor)
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
        }

    def _semantic_fields(self) -> str:
        return (
            "paperId,corpusId,externalIds,url,title,abstract,venue,publicationVenue,"
            "year,referenceCount,citationCount,influentialCitationCount,isOpenAccess,"
            "openAccessPdf,fieldsOfStudy,s2FieldsOfStudy,publicationTypes,"
            "publicationDate,journal,authors"
        )

    def _collect_semantic_scholar(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["semantic_scholar"]
        window = self.plan["study_window"]
        headers: dict[str, str] = {}
        key = self._source_key("semantic_scholar")
        if key:
            headers["x-api-key"] = key
        date_filter = f"{window['from']}:{window['through']}"
        pages = 0
        source_total: int | None = None

        if self.smoke_test:
            endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"
            offset = 0
            while writer.count < cap:
                requested = min(100, cap - writer.count)
                params = {
                    "query": query,
                    "publicationDateOrYear": date_filter,
                    "limit": requested,
                    "offset": offset,
                    "fields": self._semantic_fields(),
                }
                response = self.http_get(
                    "semantic_scholar", query_id, endpoint, params, headers
                )
                data = response.json()
                records = data.get("data", [])
                if not isinstance(records, list):
                    raise ValueError("Semantic Scholar data is not a list")
                if source_total is None:
                    source_total = int(data.get("total", len(records)))
                pages += 1
                for record in records[: cap - writer.count]:
                    writer.write(record, response.request_id)
                next_offset = data.get("next")
                if (
                    not records
                    or next_offset is None
                    or int(next_offset) <= offset
                    or writer.count >= cap
                ):
                    break
                offset = int(next_offset)
            mode = "relevance_search_smoke_only"
        else:
            endpoint = str(config["endpoint"])
            token: str | None = None
            while writer.count < cap:
                params: dict[str, Any] = {
                    "query": query,
                    "publicationDateOrYear": date_filter,
                    "fields": self._semantic_fields(),
                    "sort": "publicationDate:asc",
                }
                if token:
                    params["token"] = token
                response = self.http_get(
                    "semantic_scholar", query_id, endpoint, params, headers
                )
                data = response.json()
                records = data.get("data", [])
                if not isinstance(records, list):
                    raise ValueError("Semantic Scholar bulk data is not a list")
                if source_total is None:
                    source_total = int(data.get("total", len(records)))
                pages += 1
                for record in records[: cap - writer.count]:
                    writer.write(record, response.request_id)
                next_token = data.get("token")
                if (
                    not records
                    or not next_token
                    or next_token == token
                    or writer.count >= cap
                ):
                    break
                token = str(next_token)
            mode = "bulk_token_search"
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
            "semantic_scholar_search_mode": mode,
            "authenticated": bool(key),
        }

    def _collect_core(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["core"]
        headers: dict[str, str] = {}
        key = self._source_key("core")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        offset = 0
        pages = 0
        source_total: int | None = None
        while writer.count < cap:
            requested = min(self._page_size("core"), cap - writer.count)
            params = {
                "q": query,
                "limit": requested,
                "offset": offset,
                "exclude": "fullText,references",
            }
            try:
                response = self.http_get(
                    "core", query_id, str(config["endpoint"]), params, headers
                )
            except CollectionRequestError as exc:
                at_advertised_tail = (
                    source_total is not None and offset == source_total - 1
                )
                if at_advertised_tail:
                    termination = "request_error_at_advertised_tail"
                elif source_total is not None and offset < source_total:
                    termination = "request_error_before_reported_end"
                else:
                    termination = "request_error_without_reported_total"
                missing = (
                    max(int(source_total) - writer.count, 0)
                    if source_total is not None
                    else None
                )
                raise CollectionRequestError(
                    exc.source,
                    exc.query_id,
                    exc.category,
                    exc.status_code,
                    context={
                        "pages": pages,
                        "source_reported_total": source_total,
                        "pagination_terminated": termination,
                        "pagination_complete": False,
                        "completion_claim_permitted": False,
                        "failed_offset": offset,
                        "failed_limit": requested,
                        "unretrieved_reported_hits": missing,
                        "core_failure_at_advertised_tail": at_advertised_tail,
                        "authenticated": bool(key),
                        "excluded_bulky_fields": ["fullText", "references"],
                        "downstream_date_filter_required": True,
                        "downstream_language_filter_required": True,
                    },
                ) from exc
            data = response.json()
            records = data.get("results", [])
            if not isinstance(records, list):
                raise ValueError("CORE results is not a list")
            if source_total is None:
                source_total = int(data.get("totalHits", len(records)))
            pages += 1
            for record in records[: cap - writer.count]:
                writer.write(record, response.request_id)
            offset += len(records)
            if (
                not records
                or len(records) < requested
                or (source_total is not None and offset >= source_total)
                or writer.count >= cap
            ):
                break
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
            "pagination_complete": writer.count < cap,
            "completion_claim_permitted": writer.count < cap,
            "authenticated": bool(key),
            "excluded_bulky_fields": ["fullText", "references"],
            "downstream_date_filter_required": True,
            "downstream_language_filter_required": True,
        }

    def _collect_doaj(
        self, query: str, query_id: str, writer: RawQueryWriter, cap: int
    ) -> dict[str, Any]:
        config = self.plan["sources"]["doaj"]
        endpoint = str(config["endpoint"]).rstrip("/") + "/" + urllib.parse.quote(
            query, safe=""
        )
        page = 1
        pages = 0
        source_total: int | None = None
        while writer.count < cap:
            requested = min(self._page_size("doaj"), cap - writer.count)
            params: dict[str, Any] = {"page": page, "pageSize": requested}
            key = self._source_key("doaj")
            if key:
                params["api_key"] = key
            response = self.http_get("doaj", query_id, endpoint, params)
            data = response.json()
            records = data.get("results", [])
            if not isinstance(records, list):
                raise ValueError("DOAJ results is not a list")
            if source_total is None:
                source_total = int(data.get("total", len(records)))
            pages += 1
            for record in records[: cap - writer.count]:
                writer.write(record, response.request_id)
            if (
                not records
                or len(records) < requested
                or (source_total is not None and writer.count >= source_total)
                or writer.count >= cap
            ):
                break
            page += 1
        return {
            "pages": pages,
            "source_reported_total": source_total,
            "pagination_terminated": "cap" if writer.count >= cap else "source_end",
            "downstream_exact_date_filter_required_for_2026": True,
            "downstream_article_language_resolution_required": True,
        }

    def _collect_one_query(
        self,
        source: str,
        query: Mapping[str, str],
        query_ordinal: int,
    ) -> dict[str, Any]:
        self.query_sequence += 1
        query_id = str(query["id"])
        query_text = str(query["query"])
        cap = self._cap_for(source)
        raw_path = self._raw_path(source, query_ordinal, query_id)
        writer = RawQueryWriter(raw_path, source, query_id)
        request_start = self.request_sequence
        started_at = utc_now()
        error: dict[str, Any] | None = None
        metadata: dict[str, Any] = {}
        try:
            collector = getattr(self, f"_collect_{source}")
            metadata = collector(query_text, query_id, writer, cap)
        except CollectionRequestError as exc:
            metadata.update(exc.context)
            error = {
                "category": exc.category,
                "status_code": exc.status_code,
            }
        except (ET.ParseError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            error = {"category": type(exc).__name__, "status_code": None}
        except Exception as exc:  # Preserve the run; never serialize exception text.
            error = {"category": type(exc).__name__, "status_code": None}
        finally:
            writer.close()

        config = self.plan["sources"][source]
        source_total = metadata.get("source_reported_total")
        plan_cap = int(config["max_records_per_query"])
        would_exceed_plan_cap = (
            source_total is not None and int(source_total) > plan_cap
        )
        if error:
            status = "error"
            self.query_errors += 1
        elif self.preflight_counts:
            status = "preflight_over_cap" if would_exceed_plan_cap else "preflight_complete"
        elif writer.count == 0:
            status = "empty"
        elif source_total is not None and writer.count < int(source_total) and writer.count >= cap:
            status = "capped"
        elif metadata.get("pagination_terminated") == "cap":
            status = "capped"
        else:
            status = "complete"

        report: dict[str, Any] = {
            "schema_version": "1.0",
            "source": source,
            "query_ordinal": query_ordinal,
            "query_id": query_id,
            "query": query_text,
            "started_at_utc": started_at,
            "completed_at_utc": utc_now(),
            "status": status,
            "error": error,
            "record_cap": cap,
            "plan_record_cap": plan_cap,
            "planned_page_size": int(config["page_size"]),
            "effective_page_size": self._page_size(source),
            "page_size_overridden": source in self.page_size_overrides,
            "would_exceed_plan_cap": would_exceed_plan_cap,
            "records_written": writer.count,
            "requests_attempted": self.request_sequence - request_start,
            "raw_file": raw_path.relative_to(self.output_dir).as_posix(),
            "raw_file_sha256": sha256_file(raw_path),
            "date_handling": config["date_handling"],
            "language_handling": config["language_handling"],
            "pagination": config["pagination"],
            **metadata,
        }
        self._log_query(report)
        return report

    def _close_logs(self) -> None:
        for handle in (self.request_log, self.query_log):
            if not handle.closed:
                handle.flush()
                handle.close()

    def run(self) -> int:
        for source in self.sources:
            config = self.plan["sources"][source]
            source_role = str(config.get("source_role", "discovery"))
            queries = plan_queries(self.plan, source)
            if source_role == "doi_metadata_enrichment":
                self.source_results[source] = {
                    "source_role": source_role,
                    "status": "skipped_pending_doi_enrichment",
                    "queries": [],
                    "queries_run": 0,
                    "records_written": 0,
                    "errors": 0,
                    "planned_page_size": int(config["page_size"]),
                    "effective_page_size": self._page_size(source),
                    "page_size_overridden": source in self.page_size_overrides,
                    "key_environment_variable": config.get(
                        "key_environment_variable"
                    ),
                    "key_present": bool(self._source_key(source)),
                }
                continue
            if self.smoke_test:
                queries = queries[:1]
            outcomes = [
                self._collect_one_query(source, query, ordinal)
                for ordinal, query in enumerate(queries, start=1)
            ]
            self.source_results[source] = {
                "source_role": source_role,
                "status": "queried",
                "queries": outcomes,
                "queries_run": len(outcomes),
                "records_written": sum(item["records_written"] for item in outcomes),
                "errors": sum(item["status"] == "error" for item in outcomes),
                "planned_page_size": int(config["page_size"]),
                "effective_page_size": self._page_size(source),
                "page_size_overridden": source in self.page_size_overrides,
                "key_environment_variable": self.plan["sources"][source].get(
                    "key_environment_variable"
                ),
                "key_present": bool(self._source_key(source)),
            }

        self._close_logs()
        completed_at = utc_now()
        preflight_over_cap = sum(
            query.get("status") == "preflight_over_cap"
            for source in self.source_results.values()
            for query in source.get("queries", [])
        )
        if self.preflight_counts:
            run_status = (
                "preflight_passed"
                if self.query_errors == 0 and preflight_over_cap == 0
                else "preflight_failed"
            )
        else:
            run_status = "completed" if self.query_errors == 0 else "completed_with_errors"
        manifest = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "run_status": run_status,
            "started_at_utc": self.started_at,
            "completed_at_utc": completed_at,
            "mode": (
                "preflight_counts"
                if self.preflight_counts
                else ("smoke_test" if self.smoke_test else "snapshot")
            ),
            "selected_sources": self.sources,
            "max_records_per_query_override": self.max_records,
            "runtime_overrides": {
                "page_size_by_source": self.page_size_overrides,
                "lower_or_equal_to_frozen_plan_required": True,
                "scientific_plan_or_query_text_modified": False,
            },
            "effective_smoke_record_cap": 1 if self.smoke_test else None,
            "timeout_seconds": self.timeout_seconds,
            "max_attempts_per_request": self.max_attempts,
            "output_directory": str(self.output_dir),
            "plan": {
                "path": str(self.plan_path),
                "plan_id": self.plan["plan_id"],
                "plan_version": self.plan["plan_version"],
                "sha256": sha256_file(self.plan_path),
            },
            "collector": {
                "path": str(Path(__file__).resolve()),
                "sha256": sha256_file(Path(__file__).resolve()),
                "python_version": sys.version.split()[0],
                "http_library": "Python standard-library urllib",
            },
            "credential_policy": {
                "environment_only": True,
                "dotenv_loading": False,
                "values_written_to_outputs": False,
                "key_environment_presence": self.key_environment_presence,
            },
            "frozen_source_modified": False,
            "query_errors": self.query_errors,
            "preflight_queries_over_plan_cap": preflight_over_cap,
            "request_attempts": self.request_sequence,
            "source_results": self.source_results,
            "provenance_files": {
                "requests": {
                    "path": self.request_log_path.relative_to(self.output_dir).as_posix(),
                    "sha256": sha256_file(self.request_log_path),
                },
                "queries": {
                    "path": self.query_log_path.relative_to(self.output_dir).as_posix(),
                    "sha256": sha256_file(self.query_log_path),
                },
            },
        }
        write_json_new(self.output_dir / "run_manifest.json", manifest)
        print(
            json.dumps(
                {
                    "run_status": run_status,
                    "output_directory": str(self.output_dir),
                    "sources": self.sources,
                    "query_errors": self.query_errors,
                    "preflight_queries_over_plan_cap": preflight_over_cap,
                    "request_attempts": self.request_sequence,
                    "records_written": sum(
                        int(item["records_written"])
                        for item in self.source_results.values()
                    ),
                },
                indent=2,
            )
        )
        return 0 if self.query_errors == 0 and preflight_over_cap == 0 else 2


def dry_run_report(
    plan: Mapping[str, Any],
    plan_path: Path,
    sources: list[str],
    max_records: int | None,
    smoke_test: bool,
    page_size_overrides: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    effective_overrides = resolve_page_size_overrides(
        [f"{source}={size}" for source, size in (page_size_overrides or {}).items()],
        plan,
        sources,
    )
    source_report: dict[str, Any] = {}
    for source in sources:
        config = plan["sources"][source]
        env_name = config.get("key_environment_variable")
        source_role = str(config.get("source_role", "discovery"))
        queries = plan_queries(plan, source)
        if smoke_test:
            queries = queries[:1]
        cap = int(config["max_records_per_query"])
        if smoke_test:
            cap = 1
        elif max_records is not None:
            cap = min(cap, max_records)
        source_report[source] = {
            "source_role": source_role,
            "discovery_queries_enabled": source_role in {
                "discovery",
                "supplementary_discovery",
            },
            "endpoint": config["endpoint"],
            "query_ids": [query["id"] for query in queries],
            "record_cap_per_query": cap,
            "planned_page_size": int(config["page_size"]),
            "effective_page_size": effective_overrides.get(
                source, int(config["page_size"])
            ),
            "page_size_overridden": source in effective_overrides,
            "pagination": config["pagination"],
            "date_handling": config["date_handling"],
            "language_handling": config["language_handling"],
            "key_environment_variable": env_name,
            "key_present": bool(os.environ.get(str(env_name))) if env_name else False,
        }
    return {
        "status": "dry_run_validated",
        "network_requests_made": 0,
        "files_written": 0,
        "plan_path": str(plan_path.resolve()),
        "plan_sha256": sha256_file(plan_path),
        "plan_id": plan["plan_id"],
        "plan_version": plan["plan_version"],
        "study_window": plan["study_window"],
        "runtime_overrides": {
            "page_size_by_source": effective_overrides,
            "lower_or_equal_to_frozen_plan_required": True,
            "scientific_plan_or_query_text_modified": False,
        },
        "sources": source_report,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Collect a new immutable raw metadata discovery snapshot and document any "
            "post-discovery enrichment sources. The frozen revision corpus is never modified."
        )
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_PLAN,
        help="Versioned JSON search plan (default: COLLECTION_SEARCH_PLAN_V1.json)",
    )
    parser.add_argument(
        "--source",
        action="append",
        help="Source name, repeatable or comma-separated (default: all seven)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        help="Maximum raw records per query, further bounded by the plan cap",
    )
    parser.add_argument(
        "--page-size-override",
        action="append",
        metavar="SOURCE=SIZE",
        help=(
            "Runtime-only pagination size, repeatable. It may only lower a "
            "selected source's frozen plan page size and is recorded in provenance."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Exact new output directory. It must not already exist. Default: "
            "03_PIPELINE/future_collection_snapshots/<UTC run id>"
        ),
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run only the first query for each source and save at most one record per source",
    )
    parser.add_argument(
        "--preflight-counts",
        action="store_true",
        help=(
            "Run every discovery query with a one-record retrieval cap, record each "
            "source-reported total, and fail if any query exceeds its plan cap. "
            "Enrichment-only sources are documented but not queried."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and display a secret-free plan; make no requests and write no files",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=45.0,
        help="Per-request timeout (default: 45)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum attempts per request, including the first attempt (default: 3)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_records is not None and args.max_records <= 0:
        parser.error("--max-records must be positive")
    if args.preflight_counts and args.smoke_test:
        parser.error("--preflight-counts cannot be combined with --smoke-test")
    if args.preflight_counts and args.max_records is not None:
        parser.error("--preflight-counts sets its own one-record retrieval cap")
    if not (1 <= args.max_attempts <= 8):
        parser.error("--max-attempts must be between 1 and 8")
    if not (1.0 <= args.timeout_seconds <= 300.0):
        parser.error("--timeout-seconds must be between 1 and 300")

    try:
        plan_path = args.plan.resolve()
        plan = load_plan(plan_path)
        sources = resolve_sources(args.source)
        page_size_overrides = resolve_page_size_overrides(
            args.page_size_override, plan, sources
        )
    except PlanError as exc:
        parser.error(str(exc))

    if args.dry_run:
        print(
            json.dumps(
                dry_run_report(
                    plan,
                    plan_path,
                    sources,
                    args.max_records,
                    args.smoke_test,
                    page_size_overrides,
                ),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = (
            SCRIPT_DIR
            / "future_collection_snapshots"
            / f"metadata_snapshot_{utc_run_stamp()}"
        )
    try:
        collector = SnapshotCollector(
            plan=plan,
            plan_path=plan_path,
            sources=sources,
            output_dir=output_dir,
            max_records=args.max_records,
            smoke_test=args.smoke_test,
            preflight_counts=args.preflight_counts,
            timeout_seconds=args.timeout_seconds,
            max_attempts=args.max_attempts,
            page_size_overrides=page_size_overrides,
        )
        return collector.run()
    except PlanError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
