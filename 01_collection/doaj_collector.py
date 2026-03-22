#!/usr/bin/env python3
"""
DOAJ (Directory of Open Access Journals) collector.
Free API, no authentication required.
Documentation: https://doaj.org/api/
"""

import logging
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class DOAJCollector(CollectorBase):
    SOURCE_NAME = "doaj"

    BASE_URL = "https://doaj.org/api/search/articles"

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        bibjson = raw.get("bibjson", {})

        authors = []
        for a in bibjson.get("author", []):
            name = a.get("name", "")
            affiliation = a.get("affiliation", {}).get("name", "") if isinstance(a.get("affiliation"), dict) else ""
            if name:
                authors.append({"name": name, "affiliation": affiliation})

        doi = ""
        for ident in bibjson.get("identifier", []):
            if ident.get("type") == "doi":
                doi = ident.get("id", "")
                break

        year = None
        try:
            year = int(bibjson.get("year", 0))
        except (ValueError, TypeError):
            pass

        journal_title = bibjson.get("journal", {}).get("title", "")

        keywords = bibjson.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        url = ""
        for link in bibjson.get("link", []):
            if link.get("type") == "fulltext":
                url = link.get("url", "")
                break
        if not url and doi:
            url = f"https://doi.org/{doi}"

        return {
            "doi": doi,
            "title": bibjson.get("title", "") or "",
            "abstract": bibjson.get("abstract", "") or "",
            "authors": authors,
            "year": year,
            "journal": journal_title,
            "source_db": self.SOURCE_NAME,
            "query_strategy": query_name,
            "citation_count": 0,  # DOAJ doesn't provide citation counts
            "keywords": keywords,
            "type": "article",
            "open_access": True,  # DOAJ is all open access
            "url": url,
            "raw_id": raw.get("id", ""),
        }

    def _collect_query(self, query_name: str, query_string: str) -> int:
        from_year = self.search_config["date_range"]["from_year"]
        to_year = self.search_config["date_range"]["to_year"]

        checkpoint = self._load_checkpoint(query_name)
        page = 1
        collected_count = 0
        if checkpoint:
            page = checkpoint.get("page", 1)
            collected_count = checkpoint.get("collected_count", 0)

        page_size = min(self.batch_size, 100)

        while collected_count < self.max_results:
            # DOAJ uses path-based search
            url = f"{self.BASE_URL}/{query_string}"
            params = {
                "page": page,
                "pageSize": page_size,
            }

            response = self._make_request(url, params=params)
            if response is None:
                break

            data = response.json()
            results = data.get("results", [])
            if not results:
                break

            total = data.get("total", 0)

            # Filter by year
            filtered = []
            for r in results:
                bibjson = r.get("bibjson", {})
                try:
                    yr = int(bibjson.get("year", 0))
                    if from_year <= yr <= to_year:
                        filtered.append(r)
                except (ValueError, TypeError):
                    filtered.append(r)

            standardized = [self._standardize_record(r, query_name) for r in filtered]
            new_count = self._save_batch(standardized, query_name)
            collected_count += len(filtered)

            logger.info(
                f"[doaj] '{query_name}' page {page}: "
                f"{len(results)} results, {len(filtered)} in date range, {new_count} new "
                f"(total: {collected_count}/{total})"
            )

            page += 1
            if page * page_size >= total or page * page_size >= self.max_results:
                break

            self._save_checkpoint(query_name, {
                "page": page,
                "collected_count": collected_count,
            })

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    collector = DOAJCollector()
    stats = collector.collect()
    print(f"\nDOAJ collection complete: {stats}")
