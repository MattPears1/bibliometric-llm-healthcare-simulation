#!/usr/bin/env python3
"""
Europe PMC collector - free REST API, no authentication required.
Good for biomedical literature with European coverage.
Documentation: https://europepmc.org/RestfulWebService
"""

import logging
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class EuropePMCCollector(CollectorBase):
    SOURCE_NAME = "europepmc"

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        """Convert Europe PMC record to standard schema."""
        # Authors
        authors = []
        author_list = raw.get("authorList", {}).get("author", [])
        if isinstance(author_list, list):
            for a in author_list:
                name = a.get("fullName", "")
                if not name:
                    first = a.get("firstName", "")
                    last = a.get("lastName", "")
                    name = f"{first} {last}".strip()
                affiliation = ""
                aff_list = a.get("authorAffiliationDetailsList", {}).get(
                    "authorAffiliation", []
                )
                if aff_list:
                    affiliation = aff_list[0].get("affiliation", "")
                if name:
                    authors.append({"name": name, "affiliation": affiliation})

        # DOI
        doi = raw.get("doi", "") or ""

        # Year
        year = None
        try:
            year = int(raw.get("pubYear", 0))
        except (ValueError, TypeError):
            pass

        # Keywords
        keywords = []
        kw_list = raw.get("keywordList", {}).get("keyword", [])
        if isinstance(kw_list, list):
            keywords = [k for k in kw_list if isinstance(k, str)]

        # Open access
        is_oa = raw.get("isOpenAccess", "N") == "Y"

        # URL
        pmid = raw.get("pmid", "")
        pmcid = raw.get("pmcid", "")
        url = ""
        if pmcid:
            url = f"https://europepmc.org/article/PMC/{pmcid}"
        elif pmid:
            url = f"https://europepmc.org/article/MED/{pmid}"
        elif doi:
            url = f"https://doi.org/{doi}"

        return {
            "doi": doi,
            "title": raw.get("title", "") or "",
            "abstract": raw.get("abstractText", "") or "",
            "authors": authors,
            "year": year,
            "journal": raw.get("journalTitle", "") or "",
            "source_db": self.SOURCE_NAME,
            "query_strategy": query_name,
            "citation_count": raw.get("citedByCount", 0),
            "keywords": keywords,
            "type": raw.get("pubType", "") or "",
            "open_access": is_oa,
            "url": url,
            "raw_id": raw.get("id", "") or f"PMID:{pmid}" if pmid else "",
        }

    def _collect_query(self, query_name: str, query_string: str) -> int:
        """Collect from Europe PMC using cursor-based pagination."""
        from_year = self.search_config["date_range"]["from_year"]
        to_year = self.search_config["date_range"]["to_year"]

        # Add date filter to query
        full_query = f"({query_string}) AND (PUB_YEAR:[{from_year} TO {to_year}])"

        # Check for checkpoint
        checkpoint = self._load_checkpoint(query_name)
        cursor = "*"
        collected_count = 0
        if checkpoint:
            cursor = checkpoint.get("cursor", "*")
            collected_count = checkpoint.get("collected_count", 0)

        params = {
            "query": full_query,
            "format": "json",
            "pageSize": min(self.batch_size, 1000),
            "cursorMark": cursor,
            "resultType": "core",
        }

        page = 0
        max_pages = self.max_results // params["pageSize"] + 1

        while page < max_pages:
            response = self._make_request(self.BASE_URL, params=params)
            if response is None:
                break

            data = response.json()
            results = data.get("resultList", {}).get("result", [])
            if not results:
                break

            # Standardize and save
            standardized = [
                self._standardize_record(r, query_name) for r in results
            ]
            new_count = self._save_batch(standardized, query_name)
            collected_count += len(results)
            page += 1

            hit_count = data.get("hitCount", 0)
            logger.info(
                f"[europepmc] '{query_name}' page {page}: "
                f"{len(results)} results, {new_count} new "
                f"(total: {collected_count}/{hit_count})"
            )

            # Check for next page
            next_cursor = data.get("nextCursorMark")
            if not next_cursor or next_cursor == params["cursorMark"]:
                break

            # Checkpoint
            self._save_checkpoint(query_name, {
                "cursor": next_cursor,
                "collected_count": collected_count,
            })

            params["cursorMark"] = next_cursor

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    collector = EuropePMCCollector()
    stats = collector.collect()
    print(f"\nEurope PMC collection complete: {stats}")
