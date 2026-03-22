#!/usr/bin/env python3
"""
Semantic Scholar collector - free API, API key optional for better rate limits.
Documentation: https://api.semanticscholar.org/api-docs/
"""

import os
import logging
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class SemanticScholarCollector(CollectorBase):
    SOURCE_NAME = "semantic_scholar"

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    FIELDS = "paperId,title,abstract,year,authors,venue,citationCount,publicationTypes,openAccessPdf,externalIds"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        if self._api_key:
            self.session.headers["x-api-key"] = self._api_key
            self.rate_limit = 1.0  # Authenticated: 1 req/sec
            logger.info("[semantic_scholar] Using authenticated access (1 req/sec)")
        else:
            logger.info("[semantic_scholar] Using unauthenticated access (1 req/3.5s)")

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        authors = []
        for a in raw.get("authors", []):
            authors.append({"name": a.get("name", ""), "affiliation": ""})

        doi = ""
        ext_ids = raw.get("externalIds", {}) or {}
        doi = ext_ids.get("DOI", "") or ""

        oa_pdf = raw.get("openAccessPdf") or {}
        is_oa = bool(oa_pdf.get("url"))
        url = oa_pdf.get("url", "")
        if not url and doi:
            url = f"https://doi.org/{doi}"

        return {
            "doi": doi,
            "title": raw.get("title", "") or "",
            "abstract": raw.get("abstract", "") or "",
            "authors": authors,
            "year": raw.get("year"),
            "journal": raw.get("venue", "") or "",
            "source_db": self.SOURCE_NAME,
            "query_strategy": query_name,
            "citation_count": raw.get("citationCount", 0),
            "keywords": [],
            "type": ", ".join(raw.get("publicationTypes", []) or []),
            "open_access": is_oa,
            "url": url,
            "raw_id": raw.get("paperId", ""),
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

        params = {
            "query": query_string,
            "year": f"{from_year}-{to_year}",
            "limit": min(self.batch_size, 100),
            "offset": offset,
            "fields": self.FIELDS,
        }

        max_results = min(self.max_results, 10000)

        while offset < max_results:
            params["offset"] = offset
            response = self._make_request(self.BASE_URL, params=params)
            if response is None:
                break

            data = response.json()
            papers = data.get("data", [])
            if not papers:
                break

            total = data.get("total", 0)

            standardized = [self._standardize_record(r, query_name) for r in papers]
            new_count = self._save_batch(standardized, query_name)
            collected_count += len(papers)

            logger.info(
                f"[semantic_scholar] '{query_name}' offset {offset}: "
                f"{len(papers)} results, {new_count} new "
                f"(total: {collected_count}/{total})"
            )

            offset += len(papers)
            if offset >= total:
                break

            self._save_checkpoint(query_name, {
                "offset": offset,
                "collected_count": collected_count,
            })

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    collector = SemanticScholarCollector()
    stats = collector.collect()
    print(f"\nSemantic Scholar collection complete: {stats}")
