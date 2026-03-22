#!/usr/bin/env python3
"""
PubMed E-utilities collector - FIXED version with multiple query strategies.
Previous version returned only 26 records because it required ALL 4 keyword
categories simultaneously in TIAB. This version runs relaxed queries and unions results.
Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from collector_base import CollectorBase

logger = logging.getLogger(__name__)


class PubMedCollector(CollectorBase):
    SOURCE_NAME = "pubmed"

    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def _parse_article_xml(self, article_elem) -> Optional[Dict]:
        """Parse a single PubMed article XML element into structured data."""
        try:
            medline = article_elem.find("MedlineCitation")
            if medline is None:
                return None

            article = medline.find("Article")
            if article is None:
                return None

            # PMID
            pmid_elem = medline.find("PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            # Title
            title_elem = article.find("ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Abstract (may have multiple AbstractText elements)
            abstract_parts = []
            abstract_elem = article.find("Abstract")
            if abstract_elem is not None:
                for text_elem in abstract_elem.findall("AbstractText"):
                    label = text_elem.get("Label", "")
                    text = text_elem.text or ""
                    # Get tail text and nested elements
                    full_text = "".join(text_elem.itertext())
                    if label:
                        abstract_parts.append(f"{label}: {full_text}")
                    else:
                        abstract_parts.append(full_text)
            abstract = " ".join(abstract_parts)

            # Authors
            authors = []
            author_list = article.find("AuthorList")
            if author_list is not None:
                for author_elem in author_list.findall("Author"):
                    last = author_elem.find("LastName")
                    first = author_elem.find("ForeName")
                    name_parts = []
                    if first is not None and first.text:
                        name_parts.append(first.text)
                    if last is not None and last.text:
                        name_parts.append(last.text)
                    name = " ".join(name_parts)

                    # Affiliation
                    aff_elem = author_elem.find("AffiliationInfo/Affiliation")
                    affiliation = aff_elem.text if aff_elem is not None else ""

                    if name:
                        authors.append({"name": name, "affiliation": affiliation})

            # Year
            year = None
            pub_date = article.find("Journal/JournalIssue/PubDate")
            if pub_date is not None:
                year_elem = pub_date.find("Year")
                if year_elem is not None:
                    try:
                        year = int(year_elem.text)
                    except (ValueError, TypeError):
                        pass
            # Fallback: ArticleDate
            if year is None:
                article_date = article.find("ArticleDate")
                if article_date is not None:
                    year_elem = article_date.find("Year")
                    if year_elem is not None:
                        try:
                            year = int(year_elem.text)
                        except (ValueError, TypeError):
                            pass

            # Journal
            journal = ""
            journal_elem = article.find("Journal/Title")
            if journal_elem is not None:
                journal = journal_elem.text or ""

            # DOI
            doi = ""
            id_list = article_elem.find("PubmedData/ArticleIdList")
            if id_list is not None:
                for id_elem in id_list.findall("ArticleId"):
                    if id_elem.get("IdType") == "doi":
                        doi = id_elem.text or ""
                        break

            # Keywords (MeSH + author keywords)
            keywords = []
            mesh_list = medline.find("MeshHeadingList")
            if mesh_list is not None:
                for mesh in mesh_list.findall("MeshHeading/DescriptorName"):
                    if mesh.text:
                        keywords.append(mesh.text)
            kw_list = medline.find("KeywordList")
            if kw_list is not None:
                for kw in kw_list.findall("Keyword"):
                    if kw.text:
                        keywords.append(kw.text)

            # Publication type
            pub_types = []
            type_list = article.find("PublicationTypeList")
            if type_list is not None:
                for pt in type_list.findall("PublicationType"):
                    if pt.text:
                        pub_types.append(pt.text)

            return {
                "doi": doi,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": year,
                "journal": journal,
                "source_db": self.SOURCE_NAME,
                "query_strategy": "",  # Filled in by caller
                "citation_count": 0,  # PubMed doesn't provide this
                "keywords": keywords,
                "type": ", ".join(pub_types) if pub_types else "article",
                "open_access": False,  # Would need PMC check
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "raw_id": f"PMID:{pmid}",
            }

        except Exception as e:
            logger.error(f"[pubmed] Error parsing article XML: {e}")
            return None

    def _standardize_record(self, raw: Dict, query_name: str = "") -> Dict:
        """PubMed records are already standardized during XML parsing."""
        raw["query_strategy"] = query_name
        return raw

    def _search_pmids(self, query: str) -> List[str]:
        """Search PubMed and return list of PMIDs."""
        from_year = self.search_config["date_range"]["from_year"]
        to_year = self.search_config["date_range"]["to_year"]

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": 10000,
            "retmode": "json",
            "datetype": "pdat",
            "mindate": f"{from_year}/01/01",
            "maxdate": f"{to_year}/12/31",
        }

        response = self._make_request(self.SEARCH_URL, params=params)
        if response is None:
            return []

        data = response.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        total = data.get("esearchresult", {}).get("count", 0)

        logger.info(f"[pubmed] Search returned {total} total, got {len(pmids)} PMIDs")
        return pmids

    def _fetch_articles(self, pmids: List[str], query_name: str) -> List[Dict]:
        """Fetch full article records for a batch of PMIDs."""
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        response = self._make_request(self.FETCH_URL, params=params, timeout=120)
        if response is None:
            return []

        # Parse XML
        articles = []
        try:
            root = ET.fromstring(response.text)
            for article_elem in root.findall("PubmedArticle"):
                record = self._parse_article_xml(article_elem)
                if record:
                    record["query_strategy"] = query_name
                    articles.append(record)
        except ET.ParseError as e:
            logger.error(f"[pubmed] XML parse error: {e}")

        return articles

    def _collect_query(self, query_name: str, query_string: str) -> int:
        """Collect from PubMed: search for PMIDs, then fetch in batches."""
        # Check for checkpoint
        checkpoint = self._load_checkpoint(query_name)
        fetched_pmids = set()
        collected_count = 0
        if checkpoint:
            fetched_pmids = set(checkpoint.get("fetched_pmids", []))
            collected_count = checkpoint.get("collected_count", 0)

        # Step 1: Search
        all_pmids = self._search_pmids(query_string)
        if not all_pmids:
            logger.info(f"[pubmed] No results for '{query_name}'")
            return 0

        # Remove already-fetched PMIDs
        remaining_pmids = [p for p in all_pmids if p not in fetched_pmids]
        logger.info(
            f"[pubmed] '{query_name}': {len(all_pmids)} PMIDs, "
            f"{len(remaining_pmids)} remaining to fetch"
        )

        # Step 2: Fetch in batches
        batch_size = self.batch_size
        for i in range(0, len(remaining_pmids), batch_size):
            batch = remaining_pmids[i : i + batch_size]

            articles = self._fetch_articles(batch, query_name)
            if articles:
                new_count = self._save_batch(articles, query_name)
                collected_count += len(articles)

            fetched_pmids.update(batch)

            logger.info(
                f"[pubmed] '{query_name}' batch {i // batch_size + 1}: "
                f"{len(articles)} articles (total: {collected_count})"
            )

            # Checkpoint
            self._save_checkpoint(query_name, {
                "fetched_pmids": list(fetched_pmids),
                "collected_count": collected_count,
            })

        return collected_count


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    collector = PubMedCollector()
    stats = collector.collect()
    print(f"\nPubMed collection complete: {stats}")
