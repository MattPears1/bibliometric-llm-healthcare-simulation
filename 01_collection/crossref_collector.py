#!/usr/bin/env python3
"""
Crossref collector - free API, no authentication required.
Good for DOI-based metadata with citation counts.
Documentation: https://api.crossref.org/swagger-ui/index.html
"""

import re
import logging
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class CrossrefCollector(CollectorBase):
    SOURCE_NAME = "crossref"

    BASE_URL = "https://api.crossref.org/works"

    def _clean_abstract(self, abstract: str) -> str:
        """Remove JATS XML tags from Crossref abstracts."""
        if not abstract:
            return ""
        # Remove XML/HTML tags
        clean = re.sub(r"<[^>]+>", " ", abstract)
        # Collapse whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _extract_year(self, raw: Dict) -> Optional[int]:
        """Extract publication year from various Crossref date fields."""
        # Try published-print first, then published-online, then created
        for field in ["published-print", "published-online", "published", "created"]:
            date_parts = raw.get(field, {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                try:
                    return int(date_parts[0][0])
                except (ValueError, TypeError, IndexError):
                    continue
        return None

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        """Convert Crossref record to standard schema."""
        # Authors
        authors = []
        for a in raw.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            name = f"{given} {family}".strip()
            affiliation = ""
            aff_list = a.get("affiliation", [])
            if aff_list:
                affiliation = aff_list[0].get("name", "")
            if name:
                authors.append({"name": name, "affiliation": affiliation})

        # DOI
        doi = raw.get("DOI", "") or ""

        # Title (Crossref returns as list)
        title = ""
        title_list = raw.get("title", [])
        if title_list:
            title = title_list[0] if isinstance(title_list, list) else str(title_list)

        # Journal
        journal = ""
        container = raw.get("container-title", [])
        if container:
            journal = container[0] if isinstance(container, list) else str(container)

        # Abstract
        abstract = self._clean_abstract(raw.get("abstract", ""))

        # Keywords
        keywords = raw.get("subject", [])
        if not isinstance(keywords, list):
            keywords = []

        # URL
        url = f"https://doi.org/{doi}" if doi else raw.get("URL", "")

        return {
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": self._extract_year(raw),
            "journal": journal,
            "source_db": self.SOURCE_NAME,
            "query_strategy": query_name,
            "citation_count": raw.get("is-referenced-by-count", 0),
            "keywords": keywords,
            "type": raw.get("type", ""),
            "open_access": False,  # Crossref doesn't directly report this
            "url": url,
            "raw_id": f"doi:{doi}" if doi else "",
        }

    def _collect_query(self, query_name: str, query_string: str) -> int:
        """Collect from Crossref using offset-based pagination."""
        from_year = self.search_config["date_range"]["from_year"]
        to_year = self.search_config["date_range"]["to_year"]

        # Check for checkpoint
        checkpoint = self._load_checkpoint(query_name)
        offset = 0
        collected_count = 0
        if checkpoint:
            offset = checkpoint.get("offset", 0)
            collected_count = checkpoint.get("collected_count", 0)

        rows = min(self.batch_size, 1000)
        max_offset = min(self.max_results, 10000)  # Crossref caps at 10000

        params = {
            "query": query_string,
            "filter": f"from-pub-date:{from_year}-01-01,until-pub-date:{to_year}-12-31",
            "rows": rows,
            "offset": offset,
            "select": "DOI,title,author,published,published-print,published-online,"
                      "type,container-title,abstract,is-referenced-by-count,subject,"
                      "URL,created",
        }

        while offset < max_offset:
            params["offset"] = offset
            response = self._make_request(self.BASE_URL, params=params)
            if response is None:
                break

            data = response.json()
            items = data.get("message", {}).get("items", [])
            if not items:
                break

            total = data.get("message", {}).get("total-results", 0)

            # Standardize and save
            standardized = [
                self._standardize_record(r, query_name) for r in items
            ]
            new_count = self._save_batch(standardized, query_name)
            collected_count += len(items)

            logger.info(
                f"[crossref] '{query_name}' offset {offset}: "
                f"{len(items)} results, {new_count} new "
                f"(total: {collected_count}/{total})"
            )

            offset += len(items)

            # Check if we've got everything
            if offset >= total or offset >= max_offset:
                break

            # Checkpoint
            self._save_checkpoint(query_name, {
                "offset": offset,
                "collected_count": collected_count,
            })

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    collector = CrossrefCollector()
    stats = collector.collect()
    print(f"\nCrossref collection complete: {stats}")
