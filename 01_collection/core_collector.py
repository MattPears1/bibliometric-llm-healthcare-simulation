#!/usr/bin/env python3
"""
CORE collector - requires free API key (core.ac.uk).
Provides full-text access to open access papers.
Documentation: https://api.core.ac.uk/docs/v3
"""

import os
import logging
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class CORECollector(CollectorBase):
    SOURCE_NAME = "core"

    BASE_URL = "https://api.core.ac.uk/v3/search/works"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_key = os.getenv("CORE_API_KEY", "")
        if not self._api_key:
            logger.error("[core] No API key found in .env. CORE requires authentication.")
            self.source_config["enabled"] = False
        else:
            self.session.headers["Authorization"] = f"Bearer {self._api_key}"

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        authors = []
        for a in raw.get("authors", []):
            if isinstance(a, dict):
                authors.append({"name": a.get("name", ""), "affiliation": ""})
            elif isinstance(a, str):
                authors.append({"name": a, "affiliation": ""})

        doi = ""
        for ident in raw.get("identifiers", []):
            if isinstance(ident, str) and "doi.org" in ident:
                doi = ident.split("doi.org/")[-1]
                break

        doi = doi or (raw.get("doi") or "")

        year = None
        try:
            year = int(raw.get("yearPublished", 0))
        except (ValueError, TypeError):
            pass

        return {
            "doi": doi,
            "title": raw.get("title", "") or "",
            "abstract": raw.get("abstract", "") or "",
            "authors": authors,
            "year": year,
            "journal": raw.get("publisher", "") or "",
            "source_db": self.SOURCE_NAME,
            "query_strategy": query_name,
            "citation_count": raw.get("citationCount", 0),
            "keywords": [],
            "type": raw.get("documentType", "") or "",
            "open_access": True,  # CORE is all open access
            "url": raw.get("downloadUrl", "") or raw.get("sourceFulltextUrls", [""])[0] if raw.get("sourceFulltextUrls") else "",
            "raw_id": str(raw.get("id", "")),
        }

    def _collect_query(self, query_name: str, query_string: str) -> int:
        from_year = self.search_config["date_range"]["from_year"]
        to_year = self.search_config["date_range"]["to_year"]

        checkpoint = self._load_checkpoint(query_name)
        offset = 0
        collected_count = 0
        if checkpoint:
            offset = checkpoint.get("offset", 0)
            collected_count = checkpoint.get("collected_count", 0)

        limit = min(self.batch_size, 100)

        while offset < self.max_results:
            params = {
                "q": query_string,
                "limit": limit,
                "offset": offset,
            }

            response = self._make_request(self.BASE_URL, params=params)
            if response is None:
                break

            data = response.json()
            results = data.get("results", [])
            if not results:
                break

            total = data.get("totalHits", 0)

            # Filter by year
            filtered = []
            for r in results:
                try:
                    yr = int(r.get("yearPublished", 0))
                    if from_year <= yr <= to_year:
                        filtered.append(r)
                except (ValueError, TypeError):
                    filtered.append(r)  # Keep if year unknown

            standardized = [self._standardize_record(r, query_name) for r in filtered]
            new_count = self._save_batch(standardized, query_name)
            collected_count += len(filtered)

            logger.info(
                f"[core] '{query_name}' offset {offset}: "
                f"{len(results)} results, {len(filtered)} in date range, {new_count} new "
                f"(total: {collected_count}/{total})"
            )

            offset += len(results)
            if offset >= total or offset >= self.max_results:
                break

            self._save_checkpoint(query_name, {
                "offset": offset,
                "collected_count": collected_count,
            })

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    collector = CORECollector()
    stats = collector.collect()
    print(f"\nCORE collection complete: {stats}")
