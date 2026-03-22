#!/usr/bin/env python3
"""
OpenAlex collector - primary data source for bibliometric analysis.
Free API, no authentication required. ~5000+ records expected.
Uses polite pool (mailto parameter) for higher rate limits.
Documentation: https://docs.openalex.org/
"""

import os
import logging
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class OpenAlexCollector(CollectorBase):
    SOURCE_NAME = "openalex"

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # OpenAlex polite pool: add email to get higher rate limits
        email = os.getenv("API_CONTACT_EMAIL", "bibliometric.research@example.com")
        self._mailto = email

    def _reconstruct_abstract(self, inverted_index: Dict) -> str:
        """Reconstruct abstract text from OpenAlex's inverted index format."""
        if not inverted_index:
            return ""
        try:
            max_pos = max(pos for positions in inverted_index.values() for pos in positions)
            words = [""] * (max_pos + 1)
            for word, positions in inverted_index.items():
                for pos in positions:
                    if pos <= max_pos:
                        words[pos] = word
            return " ".join(w for w in words if w)
        except (ValueError, TypeError):
            return ""

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        """Convert OpenAlex record to standard schema."""
        # Extract authors
        authors = []
        for authorship in raw.get("authorships", []):
            author = authorship.get("author", {})
            institutions = authorship.get("institutions", [])
            affiliation = ""
            if institutions:
                affiliation = institutions[0].get("display_name", "")
            authors.append({
                "name": author.get("display_name", ""),
                "affiliation": affiliation,
            })

        # Extract DOI
        doi = raw.get("doi", "") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]

        # Extract journal
        journal = ""
        primary_loc = raw.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        journal = source.get("display_name", "")

        # Extract abstract
        abstract = raw.get("abstract", "")
        if not abstract and raw.get("abstract_inverted_index"):
            abstract = self._reconstruct_abstract(raw["abstract_inverted_index"])

        # Open access
        oa = raw.get("open_access", {}) or {}
        is_oa = oa.get("is_oa", False)

        # Keywords/concepts
        keywords = []
        for kw in raw.get("keywords", []):
            if isinstance(kw, dict):
                keywords.append(kw.get("display_name", kw.get("keyword", "")))
            elif isinstance(kw, str):
                keywords.append(kw)

        # URL
        url = raw.get("id", "")  # OpenAlex URL
        if doi:
            url = f"https://doi.org/{doi}"

        return {
            "doi": doi,
            "title": raw.get("title", "") or "",
            "abstract": abstract,
            "authors": authors,
            "year": raw.get("publication_year"),
            "journal": journal,
            "source_db": self.SOURCE_NAME,
            "query_strategy": query_name,
            "citation_count": raw.get("cited_by_count", 0),
            "keywords": keywords,
            "type": raw.get("type", ""),
            "open_access": is_oa,
            "url": url,
            "raw_id": raw.get("id", ""),
        }

    def _collect_query(self, query_name: str, query_string: str) -> int:
        """Collect from OpenAlex using cursor-based pagination."""
        from_year = self.search_config["date_range"]["from_year"]
        to_year = self.search_config["date_range"]["to_year"]

        # Check for checkpoint (resume)
        checkpoint = self._load_checkpoint(query_name)
        cursor = "*"
        collected_count = 0
        if checkpoint:
            cursor = checkpoint.get("cursor", "*")
            collected_count = checkpoint.get("collected_count", 0)
            logger.info(
                f"[openalex] Resuming '{query_name}' from cursor, "
                f"{collected_count} records already collected"
            )

        params = {
            "filter": f"publication_year:{from_year}-{to_year}",
            "search": query_string,
            "per_page": 200,
            "cursor": cursor,
            "select": "id,doi,title,publication_year,publication_date,type,"
                      "open_access,cited_by_count,authorships,primary_location,"
                      "abstract_inverted_index,keywords",
            "mailto": self._mailto,
        }

        page = 0
        max_pages = self.max_results // 200 + 1  # Safety limit

        while page < max_pages:
            response = self._make_request(self.BASE_URL, params=params)
            if response is None:
                logger.error(f"[openalex] Request failed for '{query_name}', stopping.")
                break

            data = response.json()
            results = data.get("results", [])
            if not results:
                logger.info(f"[openalex] No more results for '{query_name}'.")
                break

            # Standardize and save batch
            standardized = [
                self._standardize_record(r, query_name) for r in results
            ]
            new_count = self._save_batch(standardized, query_name)
            collected_count += len(results)
            page += 1

            logger.info(
                f"[openalex] '{query_name}' page {page}: "
                f"{len(results)} results, {new_count} new "
                f"(total: {collected_count})"
            )

            # Get next cursor
            next_cursor = data.get("meta", {}).get("next_cursor")
            if not next_cursor:
                break

            # Save checkpoint
            self._save_checkpoint(query_name, {
                "cursor": next_cursor,
                "collected_count": collected_count,
                "page": page,
            })

            params["cursor"] = next_cursor

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                CollectorBase.__init__.__code__.co_filename.replace(
                    "collector_base.py", ""
                )
                + "../logs/openalex_collection.log"
            )
            if False
            else logging.StreamHandler(),
            logging.StreamHandler(),
        ],
    )
    collector = OpenAlexCollector()
    stats = collector.collect()
    print(f"\nOpenAlex collection complete: {stats}")
