#!/usr/bin/env python3
"""
AI-Powered Figure Compendium Generator
=======================================
Reads each figure image with GPT-5.1 vision to generate contextual
descriptions, then assembles into a .docx with all figures annotated.
Falls back to pre-written descriptions if API is unavailable.
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE_DIR = Path(__file__).parent
FIG_DIR = BASE_DIR / "03_analysis" / "figures"
OUT_DIR = BASE_DIR / "04_manuscript" / "output"

# Figure metadata: (filename, title, fallback_description)
FIGURES = [
    ("graphical_abstract.png", "Graphical Abstract"),
    ("prisma_flow.png", "Figure 1: PRISMA 2020 Flow Diagram"),
    ("publication_trends.png", "Figure 2: Publication Trends by Year"),
    ("cumulative_growth.png", "Figure 3: Cumulative Publication Growth"),
    ("citation_distribution.png", "Figure 4: Citation Distribution"),
    ("citations_by_year.png", "Figure 5: Citations Stratified by Year"),
    ("strategic_diagram.png", "Figure 6: Callon Strategic Thematic Diagram"),
    ("nts_domain_frequencies.png", "Figure 7: NTS Domain Frequencies"),
    ("nts_domain_year_heatmap.png", "Figure 8: NTS Domain Temporal Heatmap"),
    ("simulation_nts_crosstab.png", "Figure 9: Simulation x NTS Cross-Tabulation"),
    ("simulation_type_frequencies.png", "Figure 10: Simulation Type Frequencies"),
    ("llm_model_frequencies.png", "Figure 11: LLM Model Mention Frequencies"),
    ("llm_proprietary_vs_opensource.png", "Figure 12: Proprietary vs Open-Source LLM Split"),
    ("llm_model_trends.png", "Figure 13: LLM Model Temporal Trends"),
    ("top_countries.png", "Figure 14: Top 20 Countries"),
    ("continent_distribution.png", "Figure 15: Continental Distribution"),
    ("top_authors.png", "Figure 16: Top 20 Most Prolific Authors"),
    ("author_productivity.png", "Figure 17: Author Productivity Distribution"),
    ("lotkas_law.png", "Figure 18: Lotka's Law Test"),
    ("collaboration_index.png", "Figure 19: Collaboration Index"),
    ("top_journals.png", "Figure 20: Top 20 Journals/Sources"),
    ("bradford_law.png", "Figure 21: Bradford's Law Zones"),
    ("publication_types.png", "Figure 22: Publication Type Distribution"),
    ("research_methods.png", "Figure 23: Research Methods Distribution"),
    ("top_keywords.png", "Figure 24: Top 30 Keywords"),
    ("keyword_cooccurrence_network.png", "Figure 25: Keyword Co-occurrence Network"),
    ("keyword_wordcloud.png", "Figure 26: Keyword Word Cloud"),
    ("urology_trends.png", "Figure 27: Urology Sub-Analysis Trends"),
    ("source_database_distribution.png", "Figure 28: Source Database Distribution"),
    ("tier_distribution.png", "Figure 29: Screening Tier Distribution"),
    ("document_type_distribution.png", "Figure 30: Document Type Distribution"),
    ("data_completeness.png", "Figure 31: Metadata Completeness"),
]


def describe_figure_with_gpt(image_path: Path, title: str) -> str:
    """Use GPT-5.1 vision to describe a figure."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-5.1",
            max_completion_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant writing figure descriptions for an academic "
                        "bibliometric analysis paper about Large Language Models in Healthcare Simulation. "
                        "Write one concise paragraph (2-3 sentences) describing what this figure shows "
                        "and its key finding. Use formal academic language. Include specific numbers "
                        "visible in the figure. Do not start with 'This figure shows' - start with "
                        "the finding itself."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Describe this figure titled '{title}' for a bibliometric analysis paper:"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}},
                    ],
                },
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  GPT vision error for {image_path.name}: {e}")
        return ""


def build_compendium(use_ai: bool = True):
    """Build the figure compendium document."""
    doc = Document()

    # Style the document
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Title page
    title = doc.add_heading("Bibliometric Analysis of LLMs in Healthcare Simulation", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = RGBColor(21, 101, 192)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Complete Figure Compendium")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(66, 66, 66)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    from datetime import datetime
    run = meta.add_run(f"Core Dataset: 3,000 papers | Generated: {datetime.now().strftime('%B %Y')}")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(117, 117, 117)

    doc.add_paragraph("")

    # Summary table
    doc.add_heading("Dataset Summary", level=1)
    try:
        with open(BASE_DIR / "03_analysis" / "core_dataset.json", encoding="utf-8") as f:
            papers = json.load(f)

        summary_data = [
            ("Total papers (core corpus)", f"{len(papers):,}"),
            ("Raw records collected", "100,277"),
            ("Databases searched", "7"),
            ("Query strategies", "35"),
            ("Date range", "January 2020 - March 2026"),
        ]

        table = doc.add_table(rows=len(summary_data) + 1, cols=2)
        table.style = "Light Shading Accent 1"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.rows[0].cells[0].text = "Metric"
        table.rows[0].cells[1].text = "Value"
        for i, (metric, value) in enumerate(summary_data):
            table.rows[i + 1].cells[0].text = metric
            table.rows[i + 1].cells[1].text = value
    except Exception:
        pass

    doc.add_page_break()

    # Figures
    descriptions_cache = {}
    cache_path = BASE_DIR / "03_analysis" / "figure_descriptions.json"
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            descriptions_cache = json.load(f)

    count = 0
    for filename, title_text in FIGURES:
        filepath = FIG_DIR / filename
        if not filepath.exists():
            continue

        doc.add_heading(title_text, level=2)

        # Add figure
        doc.add_picture(str(filepath), width=Inches(6.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Get description
        desc = descriptions_cache.get(filename, "")
        if not desc and use_ai:
            print(f"  Generating AI description for {filename}...")
            desc = describe_figure_with_gpt(filepath, title_text)
            if desc:
                descriptions_cache[filename] = desc
            time.sleep(1)  # Rate limit

        if desc:
            p = doc.add_paragraph()
            run = p.add_run(f"{title_text}: ")
            run.bold = True
            run.font.size = Pt(10)
            run = p.add_run(desc)
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(66, 66, 66)
        else:
            p = doc.add_paragraph(f"[Description pending - run with --ai flag to generate]")
            p.runs[0].font.size = Pt(9)
            p.runs[0].font.color.rgb = RGBColor(150, 150, 150)

        doc.add_paragraph("")  # spacer
        count += 1

    # Save description cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(descriptions_cache, f, indent=2, ensure_ascii=False)

    # Save document
    out_path = OUT_DIR / "FIGURE_COMPENDIUM.docx"
    doc.save(str(out_path))
    print(f"Saved FIGURE_COMPENDIUM.docx with {count} figures ({len(descriptions_cache)} AI descriptions cached)")
    return out_path


if __name__ == "__main__":
    use_ai = "--no-ai" not in sys.argv
    build_compendium(use_ai=use_ai)
