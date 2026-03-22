#!/usr/bin/env python3
"""
Deduplicator - removes duplicate records using three-tier matching:
1. DOI exact match (highest confidence)
2. Title fuzzy match (rapidfuzz, threshold 90%)
3. Author+year+title fragment (fallback for no-DOI ambiguous titles)

Priority for keeping: PubMed > OpenAlex > Europe PMC > Crossref > Semantic Scholar > CORE > DOAJ
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# Source priority (lower = higher priority = keep this record)
SOURCE_PRIORITY = {
    "pubmed": 0,
    "openalex": 1,
    "europepmc": 2,
    "crossref": 3,
    "semantic_scholar": 4,
    "core": 5,
    "doaj": 6,
}


class Deduplicator:
    """Remove duplicate records across multiple sources."""

    def __init__(self, config_path: str = None):
        if config_path:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            config_path = Path(__file__).parent.parent / "config.yaml"
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)

        dedup_config = self.config.get("processing", {}).get("deduplication", {})
        self.fuzzy_threshold = dedup_config.get("fuzzy_title_threshold", 90)
        self.use_author_year = dedup_config.get("author_year_fragment", True)

        self.output_dir = Path(__file__).parent / "merged"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "total_input": 0,
            "duplicates_doi": 0,
            "duplicates_title": 0,
            "duplicates_author_year": 0,
            "unique_output": 0,
        }

    def _source_priority(self, source: str) -> int:
        """Get priority for a source (lower = higher priority)."""
        return SOURCE_PRIORITY.get(source, 99)

    def _pick_best_record(self, records: List[Dict]) -> Dict:
        """Given duplicate records, pick the best one based on source priority and data quality."""
        if len(records) == 1:
            return records[0]

        # Sort by: source priority (ascending), then data completeness (descending)
        def quality_score(r):
            priority = self._source_priority(r.get("source_db", ""))
            # Bonus for having more metadata
            has_abstract = 1 if r.get("abstract") and len(r.get("abstract", "")) > 50 else 0
            has_doi = 1 if r.get("doi") else 0
            has_authors = 1 if r.get("authors") else 0
            has_citations = 1 if r.get("citation_count", 0) > 0 else 0
            completeness = has_abstract + has_doi + has_authors + has_citations
            return (priority, -completeness)

        records.sort(key=quality_score)
        best = records[0]

        # Merge: take best fields from all duplicates
        for other in records[1:]:
            # Take abstract from whichever has a longer one
            if len(other.get("abstract", "") or "") > len(best.get("abstract", "") or ""):
                best["abstract"] = other["abstract"]
            # Take higher citation count
            if (other.get("citation_count", 0) or 0) > (best.get("citation_count", 0) or 0):
                best["citation_count"] = other["citation_count"]
            # Merge keywords
            existing_kw = set(best.get("keywords", []))
            for kw in other.get("keywords", []):
                if kw not in existing_kw:
                    best.setdefault("keywords", []).append(kw)
                    existing_kw.add(kw)
            # Take DOI if missing
            if not best.get("doi") and other.get("doi"):
                best["doi"] = other["doi"]

        # Track all source databases this record appeared in
        best["found_in_sources"] = list(set(r.get("source_db", "") for r in records))

        return best

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        """
        Deduplicate records using three-tier matching.
        Returns list of unique records.
        """
        self.stats["total_input"] = len(records)
        logger.info(f"Starting deduplication of {len(records)} records")

        # Tier 1: DOI exact match
        doi_groups: Dict[str, List[Dict]] = defaultdict(list)
        no_doi: List[Dict] = []

        for record in records:
            doi = (record.get("doi") or "").strip().lower()
            if doi:
                doi_groups[doi].append(record)
            else:
                no_doi.append(record)

        # Merge DOI groups
        unique_by_doi = []
        for doi, group in doi_groups.items():
            if len(group) > 1:
                self.stats["duplicates_doi"] += len(group) - 1
            unique_by_doi.append(self._pick_best_record(group))

        logger.info(
            f"Tier 1 (DOI): {len(records)} → {len(unique_by_doi)} with DOI + "
            f"{len(no_doi)} without DOI. Removed {self.stats['duplicates_doi']} DOI dupes."
        )

        # Tier 2: Fuzzy title match on remaining (no-DOI + unique DOI records)
        all_candidates = unique_by_doi + no_doi
        unique_records = self._fuzzy_title_dedup(all_candidates)

        logger.info(
            f"Tier 2 (fuzzy title): {len(all_candidates)} → {len(unique_records)}. "
            f"Removed {self.stats['duplicates_title']} title dupes."
        )

        # Tier 3: Author+year+title fragment (optional)
        if self.use_author_year:
            before = len(unique_records)
            unique_records = self._author_year_dedup(unique_records)
            self.stats["duplicates_author_year"] = before - len(unique_records)
            logger.info(
                f"Tier 3 (author+year): {before} → {len(unique_records)}. "
                f"Removed {self.stats['duplicates_author_year']} dupes."
            )

        self.stats["unique_output"] = len(unique_records)
        total_dupes = (
            self.stats["duplicates_doi"]
            + self.stats["duplicates_title"]
            + self.stats["duplicates_author_year"]
        )
        logger.info(
            f"Deduplication complete: {len(records)} → {len(unique_records)} "
            f"({total_dupes} duplicates removed, {total_dupes/len(records)*100:.1f}%)"
        )

        return unique_records

    def _fuzzy_title_dedup(self, records: List[Dict]) -> List[Dict]:
        """Deduplicate by fuzzy title matching."""
        try:
            from rapidfuzz import fuzz
        except ImportError:
            logger.warning("rapidfuzz not installed. Using exact title matching only.")
            return self._exact_title_dedup(records)

        # Group by normalized title (first pass: exact match on normalized)
        title_groups: Dict[str, List[Dict]] = defaultdict(list)
        for record in records:
            norm_title = record.get("title_normalized", "")
            if not norm_title:
                norm_title = (record.get("title", "") or "").strip().lower()[:200]
            title_groups[norm_title].append(record)

        # Merge exact title groups
        semi_unique = []
        for title, group in title_groups.items():
            if len(group) > 1:
                self.stats["duplicates_title"] += len(group) - 1
            semi_unique.append(self._pick_best_record(group))

        # Second pass: fuzzy matching between remaining records
        # Use blocking (group by first 30 chars of normalized title) to avoid O(n^2)
        if len(semi_unique) > 500000:
            logger.warning(
                f"Too many records ({len(semi_unique)}) for fuzzy matching. "
                f"Using exact title matching only."
            )
            return semi_unique

        # Build blocks: group records by first 30 chars of normalized title
        blocks: Dict[str, List[Tuple[int, Dict]]] = defaultdict(list)
        for idx, rec in enumerate(semi_unique):
            title = rec.get("title_normalized", "") or rec.get("title", "").lower()
            block_key = title[:30]
            blocks[block_key].append((idx, rec))

        logger.info(
            f"Fuzzy matching with blocking: {len(semi_unique)} records in "
            f"{len(blocks)} blocks (avg {len(semi_unique)/max(len(blocks),1):.1f} per block)"
        )

        used = set()
        final = []

        for block_key, block_records in blocks.items():
            for pos_in_block, (i, rec_a) in enumerate(block_records):
                if i in used:
                    continue

                cluster = [rec_a]
                title_a = rec_a.get("title_normalized", "") or rec_a.get("title", "").lower()

                for j, rec_b in block_records[pos_in_block + 1:]:
                    if j in used:
                        continue
                    title_b = rec_b.get("title_normalized", "") or rec_b.get("title", "").lower()

                    # Quick length check to avoid unnecessary comparisons
                    if abs(len(title_a) - len(title_b)) > len(title_a) * 0.3:
                        continue

                    score = fuzz.ratio(title_a, title_b)
                    if score >= self.fuzzy_threshold:
                        cluster.append(rec_b)
                        used.add(j)
                        self.stats["duplicates_title"] += 1

                used.add(i)
                final.append(self._pick_best_record(cluster))

        return final

    def _exact_title_dedup(self, records: List[Dict]) -> List[Dict]:
        """Fallback: exact normalized title matching only."""
        title_groups: Dict[str, List[Dict]] = defaultdict(list)
        for record in records:
            norm_title = record.get("title_normalized", "")
            if not norm_title:
                norm_title = (record.get("title", "") or "").strip().lower()[:200]
            title_groups[norm_title].append(record)

        unique = []
        for title, group in title_groups.items():
            if len(group) > 1:
                self.stats["duplicates_title"] += len(group) - 1
            unique.append(self._pick_best_record(group))
        return unique

    def _author_year_dedup(self, records: List[Dict]) -> List[Dict]:
        """
        Tier 3: Match records by first author last name + year + title fragment.
        Catches cases where DOI is missing and titles have minor variations.
        """
        def make_key(record):
            year = record.get("year", "")
            authors = record.get("authors", [])
            first_author = ""
            if authors:
                name = authors[0].get("name", "")
                # Extract last name (last word)
                parts = name.split()
                first_author = parts[-1].lower() if parts else ""
            title_fragment = (record.get("title", "") or "").lower()[:50]
            return f"{first_author}:{year}:{title_fragment}"

        key_groups: Dict[str, List[Dict]] = defaultdict(list)
        for record in records:
            key = make_key(record)
            key_groups[key].append(record)

        unique = []
        for key, group in key_groups.items():
            unique.append(self._pick_best_record(group))

        return unique

    def save(self, records: List[Dict], prefix: str = "deduplicated") -> Path:
        """Save deduplicated records."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = self.output_dir / f"{prefix}_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        # CSV
        csv_path = self.output_dir / f"{prefix}_{timestamp}.csv"
        import csv
        if records:
            fieldnames = ["id", "doi", "title", "year", "journal", "source_db",
                         "citation_count", "type", "open_access", "found_in_sources", "abstract"]
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for r in records:
                    row = dict(r)
                    row["found_in_sources"] = "; ".join(r.get("found_in_sources", []))
                    writer.writerow(row)

        # Report
        report_path = self.output_dir / f"{prefix}_report_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write("# Deduplication Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Statistics\n\n")
            f.write(f"| Metric | Count |\n|--------|-------|\n")
            for key, val in self.stats.items():
                f.write(f"| {key} | {val} |\n")
            total_dupes = self.stats["duplicates_doi"] + self.stats["duplicates_title"] + self.stats["duplicates_author_year"]
            f.write(f"| total_duplicates | {total_dupes} |\n")
            if self.stats["total_input"] > 0:
                f.write(f"| dedup_rate | {total_dupes/self.stats['total_input']*100:.1f}% |\n")

        logger.info(f"Saved {len(records)} deduplicated records to {json_path}")
        return json_path


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python deduplicator.py <normalized_records.json>")
        print("  Or run normalizer.py first to generate the input file.")
        return

    input_file = sys.argv[1]
    with open(input_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    dedup = Deduplicator()
    unique = dedup.deduplicate(records)
    dedup.save(unique)


if __name__ == "__main__":
    main()
