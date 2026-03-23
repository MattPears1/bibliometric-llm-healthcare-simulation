#!/usr/bin/env python3
"""
Enhanced Manuscript Builder
============================
Auto-populates a publication-ready manuscript from analysis results.
Reads all tables and results, generates formatted .docx with proper
academic structure, embedded tables, and figure references.

Can optionally use GPT-5.1 to write/refine the Discussion section
based on the actual results data.
"""

import json
import os
import sys
import glob
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.stdout.reconfigure(encoding="utf-8")

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "03_analysis"
TABLES_DIR = ANALYSIS_DIR / "tables"


def read_latest_table(prefix):
    """Read the latest version of a table file."""
    files = sorted(glob.glob(str(TABLES_DIR / f"{prefix}_*.md")))
    if not files:
        return ""
    with open(files[-1], encoding="utf-8") as f:
        return f.read()


def parse_md_table(md_text, table_name):
    """Extract rows from a markdown table."""
    rows = []
    for line in md_text.split("\n"):
        line = line.strip()
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if cells:
                rows.append(cells)
    return rows


def add_formatted_table(doc, rows, title=None):
    """Add a properly formatted table to the document."""
    if not rows or len(rows) < 2:
        return

    if title:
        p = doc.add_paragraph()
        run = p.add_run(title)
        run.bold = True
        run.font.size = Pt(10)

    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = "Light Shading Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    n_cols = len(rows[0])
    for i, row_data in enumerate(rows):
        for j in range(min(len(row_data), n_cols)):
            cell = table.rows[i].cells[j]
            cell.text = row_data[j].strip().replace("**", "")
            for paragraph in cell.paragraphs:
                paragraph.style.font.size = Pt(9)
                if i == 0:
                    for run in paragraph.runs:
                        run.bold = True

    doc.add_paragraph("")


def load_results():
    """Load all analysis results."""
    results = {}

    # Load core dataset
    core_path = ANALYSIS_DIR / "core_dataset.json"
    if core_path.exists():
        with open(core_path, encoding="utf-8") as f:
            results["papers"] = json.load(f)
    else:
        results["papers"] = []

    # Load monthly/final results if available
    for rfile in ["MONTHLY_RESULTS.json", "CORE_RESULTS.json", "FINAL_RESULTS.json"]:
        rpath = ANALYSIS_DIR / rfile
        if rpath.exists():
            with open(rpath, encoding="utf-8") as f:
                results.update(json.load(f))
            break

    # Parse key tables
    for prefix in ["publication_trends", "citation_summary", "citation_top20",
                    "author_summary", "journal_summary", "bradford_zones",
                    "geographic_analysis", "nts_domains", "llm_model_summary",
                    "simulation_type_summary", "research_methods", "urology_results",
                    "descriptive_stats"]:
        content = read_latest_table(prefix)
        if content:
            results[f"table_{prefix}"] = content

    return results


def build_manuscript(results, use_ai=False):
    """Build the complete formatted manuscript."""
    doc = Document()
    n_papers = len(results.get("papers", []))
    date_str = datetime.now().strftime("%B %Y")

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.paragraph_format.line_spacing = 2.0

    # ============================================================
    # TITLE PAGE
    # ============================================================
    for _ in range(6):
        doc.add_paragraph("")

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Large Language Models in Healthcare Simulation:\nA Bibliometric Analysis Mapping the Research Landscape")
    run.bold = True
    run.font.size = Pt(16)

    doc.add_paragraph("")
    authors = doc.add_paragraph()
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = authors.add_run("Matt Pears, [Colleague 1], [Colleague 2], Shekhar [Surname]*")
    run.font.size = Pt(12)

    doc.add_paragraph("")
    corr = doc.add_paragraph()
    corr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = corr.add_run("*Corresponding author")
    run.font.size = Pt(10)
    run.italic = True

    doc.add_paragraph("")
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = date_p.add_run(f"Manuscript generated: {date_str}")
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(128, 128, 128)

    doc.add_page_break()

    # ============================================================
    # ABSTRACT
    # ============================================================
    doc.add_heading("Abstract", level=1)

    # Read the section file
    abstract_path = Path(__file__).parent / "sections" / "abstract.md"
    if abstract_path.exists():
        with open(abstract_path, encoding="utf-8") as f:
            abstract_text = f.read()
        # Parse structured abstract
        for line in abstract_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("**Keywords"):
                continue
            if line.startswith("**"):
                # Section header like **Background:**
                parts = line.split("**")
                if len(parts) >= 3:
                    p = doc.add_paragraph()
                    run = p.add_run(parts[1])
                    run.bold = True
                    run.font.size = Pt(11)
                    run = p.add_run(" " + parts[2].strip())
                    run.font.size = Pt(11)
            else:
                doc.add_paragraph(line)

    # Keywords
    p = doc.add_paragraph()
    run = p.add_run("Keywords: ")
    run.bold = True
    run = p.add_run("bibliometric analysis; large language models; healthcare simulation; non-technical skills; medical education; open access")
    run.italic = True

    doc.add_page_break()

    # ============================================================
    # MAIN SECTIONS - read from section files
    # ============================================================
    sections = ["introduction.md", "methods.md", "results.md", "discussion.md", "conclusions.md"]

    for section_file in sections:
        section_path = Path(__file__).parent / "sections" / section_file
        if not section_path.exists():
            continue

        with open(section_path, encoding="utf-8") as f:
            content = f.read()

        for line in content.split("\n"):
            line = line.rstrip()
            if not line:
                continue
            if line.startswith("# "):
                doc.add_heading(line[2:], level=1)
            elif line.startswith("## "):
                doc.add_heading(line[3:], level=2)
            elif line.startswith("### "):
                doc.add_heading(line[4:], level=3)
            elif line.startswith("- **"):
                # Bold list item
                p = doc.add_paragraph(style="List Bullet")
                parts = line[2:].split("**")
                if len(parts) >= 3:
                    run = p.add_run(parts[1])
                    run.bold = True
                    run = p.add_run(parts[2])
                else:
                    p.add_run(line[2:])
            elif line.startswith("- "):
                doc.add_paragraph(line[2:], style="List Bullet")
            elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. ") or line.startswith("4. "):
                doc.add_paragraph(line[3:], style="List Number")
            else:
                # Regular paragraph - handle markdown bold/italic
                p = doc.add_paragraph()
                text = line
                # Simple bold handling
                while "**" in text:
                    pre, rest = text.split("**", 1)
                    if "**" in rest:
                        bold_text, text = rest.split("**", 1)
                        if pre:
                            p.add_run(pre)
                        run = p.add_run(bold_text)
                        run.bold = True
                    else:
                        p.add_run(pre + "**" + rest)
                        text = ""
                        break
                if text:
                    p.add_run(text)

    doc.add_page_break()

    # ============================================================
    # KEY RESULTS TABLES (embedded)
    # ============================================================
    doc.add_heading("Appendix: Key Results Tables", level=1)

    # Publication trends table
    pub_table = results.get("table_publication_trends", "")
    if pub_table:
        rows = parse_md_table(pub_table, "publication_trends")
        add_formatted_table(doc, rows, "Table 1: Publication Trends by Year")

    # Citation summary
    cit_table = results.get("table_citation_summary", "")
    if cit_table:
        rows = parse_md_table(cit_table, "citation_summary")
        add_formatted_table(doc, rows, "Table 2: Citation Summary Statistics")

    # NTS domains
    nts_table = results.get("table_nts_domains", "")
    if nts_table:
        rows = parse_md_table(nts_table, "nts_domains")
        add_formatted_table(doc, rows, "Table 3: NTS Domain Classification")

    # LLM models
    llm_table = results.get("table_llm_model_summary", "")
    if llm_table:
        rows = parse_md_table(llm_table, "llm_models")
        add_formatted_table(doc, rows, "Table 4: LLM Model Distribution")

    # Urology
    uro_table = results.get("table_urology_results", "")
    if uro_table:
        rows = parse_md_table(uro_table, "urology")
        add_formatted_table(doc, rows, "Table 5: Urology Sub-Analysis")

    doc.add_page_break()

    # ============================================================
    # REFERENCES
    # ============================================================
    ref_path = Path(__file__).parent / "sections" / "references.md"
    if ref_path.exists():
        doc.add_heading("References", level=1)
        with open(ref_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    p = doc.add_paragraph(line)
                    p.style.font.size = Pt(10)

    # ============================================================
    # DATA AVAILABILITY
    # ============================================================
    doc.add_heading("Data Availability Statement", level=1)
    doc.add_paragraph(
        "The complete data collection pipeline, processing scripts, and analysis code are available at "
        "https://github.com/MattPears1/bibliometric-llm-healthcare-simulation. "
        "Raw bibliometric data and analysis outputs are available upon reasonable request from the corresponding author."
    )

    # Save
    out_path = Path(__file__).parent / "output" / f"MANUSCRIPT_{datetime.now().strftime('%Y%m%d')}.docx"
    doc.save(str(out_path))
    print(f"Manuscript saved: {out_path}")

    # Also save .md version via the assembler
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).parent / "assemble_manuscript.py")],
                   capture_output=True, timeout=60)

    return out_path


if __name__ == "__main__":
    results = load_results()
    use_ai = "--ai" in sys.argv
    build_manuscript(results, use_ai=use_ai)
