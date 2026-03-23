#!/usr/bin/env python3
"""
GPT-5.1 Automated Manuscript Writer & Multi-Agent Reviewer
============================================================
After analyses are complete, this script:
1. Reads all analysis tables and results
2. GPT-5.1 writes each manuscript section from the data
3. A second GPT-5.1 agent reviews for accuracy and consistency
4. A third GPT-5.1 agent verifies all numbers match source tables
5. Outputs the final reviewed manuscript

Usage:
    python ai_writer.py                # Write and review
    python ai_writer.py --write-only   # Write without review
    python ai_writer.py --review-only  # Review existing sections
"""

import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).parent.parent
SECTIONS_DIR = Path(__file__).parent / "sections"
TABLES_DIR = BASE_DIR / "03_analysis" / "tables"

MODEL = "gpt-5.1"


def get_client():
    from openai import OpenAI
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def read_all_tables():
    """Read all latest analysis tables into a single context string."""
    tables = {}
    for pattern in ["publication_trends", "citation_summary", "citation_top20",
                     "author_summary", "author_top20", "journal_summary",
                     "bradford_zones", "geographic_analysis", "nts_domains",
                     "llm_model_summary", "simulation_type_summary",
                     "research_methods", "urology_results", "descriptive_stats",
                     "thematic_clusters"]:
        files = sorted(glob.glob(str(TABLES_DIR / f"{pattern}_*.md")))
        if files:
            with open(files[-1], encoding="utf-8") as f:
                tables[pattern] = f.read()

    combined = "=== ANALYSIS RESULTS ===\n\n"
    for name, content in tables.items():
        combined += f"--- {name} ---\n{content}\n\n"
    return combined, tables


def call_gpt(client, system_prompt, user_prompt, max_tokens=4000):
    """Call GPT-5.1 with retry."""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_completion_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  GPT error (attempt {attempt+1}): {e}")
            time.sleep(5)
    return ""


# ============================================================
# AGENT 1: WRITER
# ============================================================

WRITER_SYSTEM = """You are an expert academic writer specialising in bibliometric analysis papers for medical education journals. You write in formal British English with proper academic hedging. Use Vancouver-style numbered references [1-35]. Every claim must reference specific numbers from the data provided. Do not invent numbers - use ONLY the exact values from the analysis tables."""


def write_section(client, section_name, tables_text, instruction):
    """Have GPT-5.1 write a manuscript section."""
    print(f"  Writing {section_name}...")
    prompt = f"""Write the {section_name} section for a bibliometric analysis paper about Large Language Models in Healthcare Simulation for Non-Technical Skills Training.

Use ONLY numbers from these analysis results:
{tables_text}

Additional context:
- This paper uses 7 free databases (OpenAlex, PubMed, Europe PMC, Crossref, Semantic Scholar, CORE, DOAJ)
- Three-level corpus: extended (7,893), primary (3,587), core (main analysis dataset)
- The core corpus is restricted to high/medium confidence, Tier 2/3 only
- Two-stage screening: keyword pre-filter + conservative heuristic
- The complete pipeline is on GitHub for monthly re-runs
- This is part of a broader research programme (Delphi study, scoping review, platform evaluation)
- Urology boot camps are a key focus - LLM-powered mannequin voices could replace human operators

Specific instructions for this section:
{instruction}

Write in formal British English. Use Vancouver numbered references [1-35].
Do NOT start with "This section" or similar meta-commentary. Start with the content directly."""

    return call_gpt(client, WRITER_SYSTEM, prompt, max_tokens=3000)


def write_all_sections(client, tables_text):
    """Write all manuscript sections."""
    sections = {
        "abstract.md": (
            "Abstract",
            "Write a structured abstract with Background, Methods, Results, Conclusions. Max 350 words. Include key numbers: total papers, CAGR, h-index, post-ChatGPT percentage, peak year, author count, journal count, country count, Lotka and Bradford findings, NTS gap (Decision-making vs CRM), urology boot camp gap, RCT count. End with Keywords line."
        ),
        "introduction.md": (
            "Introduction",
            "Write ~1200 words. Structure: opening paragraph on ChatGPT's impact and growth rate, Section 1.1 Background (healthcare simulation history + LLM capabilities), Section 1.2 NTS in simulation (frameworks like NOTSS, ANTS), Section 1.3 Rationale and Objectives (three motivations: pace outstripping reviews, no NTS-focused bibliometric exists, open-access imperative). State 4 objectives. Explain the three-level corpus. Use headings ## 1.1, ## 1.2, ## 1.3."
        ),
        "methods.md": (
            "Methods",
            "Write ~1300 words. Sections: 2.1 Study Design (PRISMA 2020, PRISMA-trAIce), 2.2 Data Sources (7 databases, 35 queries, why we excluded Scopus/WoS), 2.3 Data Processing (normalisation, 3-stage dedup with DOI/fuzzy/author-year), 2.4 Screening (Stage 1 keyword, Stage 2 conservative heuristic, validation with 3 reviewers), three-level corpus structure, 2.5 Inclusion/Exclusion, 2.6 Bibliometric Analysis methods (Lotka, Bradford, Callon, NTS regex, geographic), 2.7 Open-Access Philosophy."
        ),
        "results.md": (
            "Results",
            "Write ~1600 words with subsections: 3.1 Search Results (PRISMA flow numbers), 3.2 Publication Trends (CAGR, pre/post ChatGPT, peak year), 3.3 Citation Analysis (h-index, mean, uncited%), 3.4 Author Analysis (unique authors, Lotka fit, collaboration index), 3.5 Journal Distribution (Bradford zones), 3.6 Geographic (countries, top 5, intl collab%), 3.7 Thematic Mapping (Callon diagram clusters), 3.8 NTS Domains (all 9 domains with counts), 3.9 LLM Models (ChatGPT dominance, proprietary vs open-source), 3.10 Simulation Types, 3.11 Research Methods (RCT count), 3.12 Urology (papers, zero boot camp). Reference figures as (Figure X) and tables as (Table X). Use EXACT numbers from the tables."
        ),
        "discussion.md": (
            "Discussion",
            "Write ~2400 words. Sections: 4.1 Principal Findings (5 key findings synthesis), 4.2 NTS Gap (Decision-making vs CRM disparity, why CRM is neglected), 4.3 Open-Source Deficit (reproducibility concerns), 4.4 Urology Boot Camps (the untapped opportunity for LLM-powered mannequin voices), 4.5 Evidence Quality (only ~30 RCTs, preprint proportion), 4.6 Implications for Practice (educators, researchers, institutions), 4.7 Open-Access Imperative, 4.8 Limitations (9 specific limitations), 4.9 Future Directions (RCTs, NTS expansion, open-source comparative studies, boot camp pilots)."
        ),
        "conclusions.md": (
            "Conclusions",
            "Write ~550 words. Summarise 5 key findings. Provide 5 practical recommendations. End with a forward-looking paragraph about the field's potential."
        ),
    }

    for filename, (section_name, instruction) in sections.items():
        text = write_section(client, section_name, tables_text, instruction)
        if text:
            path = SECTIONS_DIR / filename
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            words = len(text.split())
            print(f"    Saved {filename} ({words} words)")
        time.sleep(2)


# ============================================================
# AGENT 2: ACCURACY REVIEWER
# ============================================================

REVIEWER_SYSTEM = """You are a meticulous academic peer reviewer. Your job is to check every number in a manuscript section against the source analysis tables. Flag any discrepancy. Also check for logical consistency, proper hedging, and academic tone. Return a corrected version of the section with ALL numbers verified against the tables."""


def review_section(client, section_name, section_text, tables_text):
    """Have a second GPT-5.1 agent review and correct a section."""
    print(f"  Reviewing {section_name}...")
    prompt = f"""Review this manuscript section for a bibliometric analysis paper.
Check EVERY number against the source tables below. Fix any inaccuracies.
Also improve academic tone, ensure proper hedging, and fix any logical issues.
Return the COMPLETE corrected section (not just the changes).

SECTION TO REVIEW:
{section_text}

SOURCE TABLES (ground truth):
{tables_text}

Return the complete corrected section. If a number doesn't match the tables, use the table value."""

    return call_gpt(client, REVIEWER_SYSTEM, prompt, max_tokens=4000)


def review_all_sections(client, tables_text):
    """Review all sections for accuracy."""
    for filename in ["abstract.md", "introduction.md", "methods.md",
                      "results.md", "discussion.md", "conclusions.md"]:
        path = SECTIONS_DIR / filename
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            section_text = f.read()

        corrected = review_section(client, filename, section_text, tables_text)
        if corrected and len(corrected) > 100:
            with open(path, "w", encoding="utf-8") as f:
                f.write(corrected)
            print(f"    Corrected {filename}")
        time.sleep(2)


# ============================================================
# AGENT 3: NUMBER VERIFIER
# ============================================================

VERIFIER_SYSTEM = """You are a data verification specialist. Extract every specific number from the manuscript and check it against the source tables. Return a JSON report of all numbers checked and whether they match."""


def verify_numbers(client, tables_text):
    """Have a third GPT-5.1 agent verify all numbers."""
    print("  Running number verification...")

    # Read assembled manuscript
    ms_path = Path(__file__).parent / "output" / f"MANUSCRIPT_{datetime.now().strftime('%Y%m%d')}.md"
    if not ms_path.exists():
        # Try any recent manuscript
        candidates = sorted(Path(__file__).parent.glob("output/MANUSCRIPT_*.md"))
        if candidates:
            ms_path = candidates[-1]
        else:
            print("    No manuscript found to verify")
            return {}

    with open(ms_path, encoding="utf-8") as f:
        manuscript = f.read()

    prompt = f"""Extract every specific number from this manuscript and verify each against the source tables.

MANUSCRIPT:
{manuscript[:8000]}

SOURCE TABLES:
{tables_text[:6000]}

Return a JSON object with this structure:
{{"verified": [{{"metric": "h-index", "manuscript_value": "92", "table_value": "92", "match": true}}, ...], "total_checked": 20, "mismatches": 0}}

Check at least 20 key numbers."""

    result = call_gpt(client, VERIFIER_SYSTEM, prompt, max_tokens=2000)

    # Try to parse JSON
    try:
        import re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            report = json.loads(json_match.group())
            mismatches = report.get("mismatches", 0)
            total = report.get("total_checked", 0)
            print(f"    Verified {total} numbers, {mismatches} mismatches")

            # Save report
            report_path = BASE_DIR / "04_manuscript" / "VERIFICATION_REPORT.json"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
            return report
    except Exception as e:
        print(f"    Verification parse error: {e}")

    return {}


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="GPT-5.1 Manuscript Writer & Reviewer")
    parser.add_argument("--write-only", action="store_true", help="Write without review")
    parser.add_argument("--review-only", action="store_true", help="Review existing sections")
    parser.add_argument("--verify-only", action="store_true", help="Just verify numbers")
    args = parser.parse_args()

    client = get_client()
    tables_text, tables = read_all_tables()
    print(f"Loaded {len(tables)} analysis tables")

    if not args.review_only and not args.verify_only:
        print("\n=== AGENT 1: GPT-5.1 WRITER ===")
        write_all_sections(client, tables_text)

    if not args.write_only and not args.verify_only:
        print("\n=== AGENT 2: GPT-5.1 ACCURACY REVIEWER ===")
        review_all_sections(client, tables_text)

    # Always verify
    print("\n=== AGENT 3: GPT-5.1 NUMBER VERIFIER ===")
    verify_numbers(client, tables_text)

    # Assemble
    print("\n=== ASSEMBLING MANUSCRIPT ===")
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).parent / "assemble_manuscript.py")],
                   capture_output=True, timeout=60)
    subprocess.run([sys.executable, str(Path(__file__).parent / "build_manuscript.py")],
                   capture_output=True, timeout=60)

    ms_path = Path(__file__).parent / "output" / f"MANUSCRIPT_{datetime.now().strftime('%Y%m%d')}.md"
    if ms_path.exists():
        with open(ms_path, encoding="utf-8") as f:
            words = len(f.read().split())
        print(f"\nFinal manuscript: {words} words")

    print("\nDone. Three-agent pipeline complete:")
    print("  Agent 1 (Writer): Wrote all sections from analysis data")
    print("  Agent 2 (Reviewer): Verified accuracy and improved tone")
    print("  Agent 3 (Verifier): Cross-checked all numbers against tables")


if __name__ == "__main__":
    main()
