#!/usr/bin/env python3
"""
Base collector class for all bibliometric data sources.
Provides: checkpointing, retry with backoff, rate limiting, batch saving, progress logging.
All source-specific collectors inherit from this.
"""

import json
import time
import hashlib
import logging
import gzip
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)


class CollectorBase(ABC):
    """
    Abstract base class for all academic database collectors.

    Features:
    - Checkpointing: saves progress after each batch, resumes on restart
    - Retry with exponential backoff: retries failed requests, tries alternative queries
    - Rate limiting: configurable per-source delays
    - Batch saving: writes records to disk incrementally (never loses data on crash)
    - Dedup-aware: skips records already in raw output
    - Progress logging: detailed logs for monitoring
    """

    SOURCE_NAME: str = ""  # Override in subclass

    def __init__(self, config_path: Optional[str] = None):
        # Load config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Source-specific config
        self.source_config = self.config["sources"].get(self.SOURCE_NAME, {})
        self.search_config = self.config["search"]
        self.pipeline_config = self.config["pipeline"]

        # Paths
        self.base_dir = Path(__file__).parent
        self.raw_dir = self.base_dir / "raw"
        self.checkpoint_dir = self.base_dir / "checkpoints"
        self.log_dir = self.base_dir.parent / "logs"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.rate_limit = self.source_config.get("rate_limit_seconds", 1.0)
        self._last_request_time = 0.0

        # Retry config
        self.max_retries = self.pipeline_config.get("max_retries_per_source", 3)
        self.backoff_base = self.pipeline_config.get("retry_backoff_base", 2)
        self.backoff_max = self.pipeline_config.get("retry_backoff_max", 300)

        # Batch config
        self.batch_size = self.source_config.get("batch_size", 100)
        self.max_results = self.source_config.get("max_results_per_query", 10000)

        # Session for connection pooling
        self.session = requests.Session()
        email = self._get_email()
        self.session.headers.update({
            "User-Agent": f"BibliometricAnalysis/2.0 ({email})"
        })

        # Track collected DOIs/titles to avoid saving duplicates within a run
        self._seen_ids: set = set()

        # Statistics
        self.stats = {
            "source": self.SOURCE_NAME,
            "started_at": None,
            "completed_at": None,
            "queries_run": 0,
            "total_records": 0,
            "total_new_records": 0,
            "errors": 0,
            "retries": 0,
        }

    def _get_email(self) -> str:
        """Get contact email from .env or config."""
        import os
        email = os.getenv("API_CONTACT_EMAIL", "")
        if not email:
            email = "bibliometric.research@example.com"
        return email

    # -------------------------------------------------------------------------
    # Rate limiting
    # -------------------------------------------------------------------------

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    # -------------------------------------------------------------------------
    # HTTP requests with retry
    # -------------------------------------------------------------------------

    def _make_request(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 60,
        method: str = "GET",
    ) -> Optional[requests.Response]:
        """
        Make an HTTP request with rate limiting, retry, and exponential backoff.
        Returns the Response object or None if all retries failed.
        """
        self._wait_for_rate_limit()

        merged_headers = dict(self.session.headers)
        if headers:
            merged_headers.update(headers)

        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        url, params=params, headers=merged_headers, timeout=timeout
                    )
                elif method.upper() == "POST":
                    response = self.session.post(
                        url, json=params, headers=merged_headers, timeout=timeout
                    )
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Handle rate limiting responses
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"[{self.SOURCE_NAME}] Rate limited (429). "
                        f"Waiting {retry_after}s (attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    self.stats["retries"] += 1
                    time.sleep(retry_after)
                    continue

                # Handle server errors with backoff
                if response.status_code >= 500:
                    backoff = min(
                        self.backoff_base ** (attempt + 1), self.backoff_max
                    )
                    logger.warning(
                        f"[{self.SOURCE_NAME}] Server error {response.status_code}. "
                        f"Backing off {backoff}s (attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    self.stats["retries"] += 1
                    time.sleep(backoff)
                    continue

                # Check for other HTTP errors
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                backoff = min(self.backoff_base ** (attempt + 1), self.backoff_max)
                logger.warning(
                    f"[{self.SOURCE_NAME}] Timeout. "
                    f"Backing off {backoff}s (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                self.stats["retries"] += 1
                time.sleep(backoff)

            except requests.exceptions.ConnectionError:
                backoff = min(self.backoff_base ** (attempt + 1), self.backoff_max)
                logger.warning(
                    f"[{self.SOURCE_NAME}] Connection error. "
                    f"Backing off {backoff}s (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                self.stats["retries"] += 1
                time.sleep(backoff)

            except requests.exceptions.HTTPError as e:
                if response.status_code == 400:
                    logger.error(
                        f"[{self.SOURCE_NAME}] Bad request (400): {e}. "
                        f"Query may be malformed. Skipping."
                    )
                    self.stats["errors"] += 1
                    return None
                backoff = min(self.backoff_base ** (attempt + 1), self.backoff_max)
                logger.warning(
                    f"[{self.SOURCE_NAME}] HTTP error: {e}. "
                    f"Backing off {backoff}s (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                self.stats["retries"] += 1
                time.sleep(backoff)

            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] Unexpected error: {e}")
                self.stats["errors"] += 1
                return None

        logger.error(
            f"[{self.SOURCE_NAME}] All {self.max_retries + 1} attempts failed for {url}"
        )
        self.stats["errors"] += 1
        return None

    # -------------------------------------------------------------------------
    # Checkpointing
    # -------------------------------------------------------------------------

    def _checkpoint_path(self, query_name: str) -> Path:
        return self.checkpoint_dir / f"{self.SOURCE_NAME}_{query_name}_checkpoint.json"

    def _save_checkpoint(self, query_name: str, state: Dict):
        """Save current collection state for resume."""
        checkpoint = {
            "source": self.SOURCE_NAME,
            "query_name": query_name,
            "timestamp": datetime.now().isoformat(),
            "state": state,
        }
        path = self._checkpoint_path(query_name)
        with open(path, "w") as f:
            json.dump(checkpoint, f, indent=2)
        logger.debug(f"[{self.SOURCE_NAME}] Checkpoint saved: {query_name}")

    def _load_checkpoint(self, query_name: str) -> Optional[Dict]:
        """Load saved checkpoint for resuming. Returns None if no checkpoint."""
        path = self._checkpoint_path(query_name)
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                checkpoint = json.load(f)
            logger.info(
                f"[{self.SOURCE_NAME}] Resuming from checkpoint: {query_name} "
                f"(saved {checkpoint.get('timestamp', 'unknown')})"
            )
            return checkpoint.get("state")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[{self.SOURCE_NAME}] Corrupt checkpoint {path}: {e}")
            return None

    def _clear_checkpoint(self, query_name: str):
        """Remove checkpoint after successful completion."""
        path = self._checkpoint_path(query_name)
        if path.exists():
            path.unlink()

    # -------------------------------------------------------------------------
    # Record saving
    # -------------------------------------------------------------------------

    def _record_id(self, record: Dict) -> str:
        """Generate a unique ID for dedup. Uses DOI if available, else title hash."""
        doi = (record.get("doi") or "").strip().lower()
        if doi:
            return f"doi:{doi}"
        title = (record.get("title") or "").strip().lower()[:200]
        if title:
            return f"title:{hashlib.md5(title.encode()).hexdigest()}"
        return f"raw:{hashlib.md5(json.dumps(record, sort_keys=True).encode()).hexdigest()}"

    def _output_path(self, query_name: str) -> Path:
        """Path for the output JSONL file for a given query."""
        return self.raw_dir / f"{self.SOURCE_NAME}_{query_name}.jsonl"

    def _save_batch(self, records: List[Dict], query_name: str) -> int:
        """
        Append a batch of records to the output file.
        Skips records already seen (by DOI or title hash).
        Returns count of new records saved.
        """
        path = self._output_path(query_name)
        new_count = 0

        with open(path, "a", encoding="utf-8") as f:
            for record in records:
                rid = self._record_id(record)
                if rid in self._seen_ids:
                    continue
                self._seen_ids.add(rid)
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                new_count += 1

        self.stats["total_new_records"] += new_count
        if new_count > 0:
            logger.info(
                f"[{self.SOURCE_NAME}] Saved {new_count} new records "
                f"({len(records) - new_count} skipped as dupes) to {path.name}"
            )
        return new_count

    def _load_existing_ids(self, query_name: str):
        """Load IDs from existing output file to avoid re-saving."""
        path = self._output_path(query_name)
        if not path.exists():
            return
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    rid = self._record_id(record)
                    self._seen_ids.add(rid)
                    count += 1
                except json.JSONDecodeError:
                    continue
        if count > 0:
            logger.info(
                f"[{self.SOURCE_NAME}] Loaded {count} existing IDs from {path.name}"
            )

    # -------------------------------------------------------------------------
    # Abstract methods - subclasses must implement
    # -------------------------------------------------------------------------

    @abstractmethod
    def _collect_query(self, query_name: str, query_string: str) -> int:
        """
        Collect records for a single query strategy.
        Must use self._make_request(), self._save_batch(), self._save_checkpoint().
        Returns count of records collected.
        """
        pass

    @abstractmethod
    def _standardize_record(self, raw: Dict) -> Dict:
        """
        Convert a raw API response record to the standard schema:
        {
            "doi": str,
            "title": str,
            "abstract": str,
            "authors": [{"name": str, "affiliation": str}],
            "year": int,
            "journal": str,
            "source_db": str,
            "query_strategy": str,
            "citation_count": int,
            "keywords": [str],
            "type": str,
            "open_access": bool,
            "url": str,
            "raw_id": str,  # Source-specific ID
        }
        """
        pass

    # -------------------------------------------------------------------------
    # Main collection orchestration
    # -------------------------------------------------------------------------

    def collect(self) -> Dict:
        """
        Run all query strategies for this source.
        Returns collection statistics.
        """
        if not self.source_config.get("enabled", False):
            logger.info(f"[{self.SOURCE_NAME}] Source disabled in config. Skipping.")
            return self.stats

        strategies = self.source_config.get("query_strategies", [])
        if not strategies:
            logger.warning(f"[{self.SOURCE_NAME}] No query strategies defined.")
            return self.stats

        self.stats["started_at"] = datetime.now().isoformat()
        logger.info(
            f"[{self.SOURCE_NAME}] Starting collection: "
            f"{len(strategies)} query strategies"
        )

        for strategy in strategies:
            query_name = strategy["name"]
            query_string = strategy["query"]

            logger.info(
                f"[{self.SOURCE_NAME}] Running strategy '{query_name}': {query_string[:80]}..."
            )

            # Load existing records to avoid duplicates
            self._load_existing_ids(query_name)

            try:
                count = self._collect_query(query_name, query_string)
                self.stats["queries_run"] += 1
                self.stats["total_records"] += count
                logger.info(
                    f"[{self.SOURCE_NAME}] Strategy '{query_name}' complete: "
                    f"{count} records"
                )
                # Clear checkpoint on success
                self._clear_checkpoint(query_name)

            except KeyboardInterrupt:
                logger.warning(
                    f"[{self.SOURCE_NAME}] Interrupted during '{query_name}'. "
                    f"Checkpoint saved - will resume on next run."
                )
                raise

            except Exception as e:
                logger.error(
                    f"[{self.SOURCE_NAME}] Strategy '{query_name}' failed: {e}"
                )
                self.stats["errors"] += 1
                # Don't clear checkpoint - allows resume
                continue

        self.stats["completed_at"] = datetime.now().isoformat()

        # Save collection stats
        stats_path = self.log_dir / f"{self.SOURCE_NAME}_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_path, "w") as f:
            json.dump(self.stats, f, indent=2)

        logger.info(
            f"[{self.SOURCE_NAME}] Collection complete: "
            f"{self.stats['total_records']} total, "
            f"{self.stats['total_new_records']} new, "
            f"{self.stats['errors']} errors, "
            f"{self.stats['retries']} retries"
        )

        return self.stats

    def get_all_records(self) -> List[Dict]:
        """Read all collected records from raw output files for this source."""
        records = []
        for path in self.raw_dir.glob(f"{self.SOURCE_NAME}_*.jsonl"):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        records.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        return records
