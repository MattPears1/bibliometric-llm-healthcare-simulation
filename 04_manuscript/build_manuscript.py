#!/usr/bin/env python3
"""
Publication-Quality Manuscript Builder
=======================================
Generates a properly formatted .docx from markdown sections with:
- Correct bold/italic rendering (no raw ** markers)
- Embedded tables from analysis results
- Three key figures embedded inline
- Professional academic formatting
"""

import glob
import json
import re
import sys
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
SECTIONS_DIR = Path(__file__).parent / "sections"
TABLES_DIR = BASE_DIR / "03_analysis" / "tables"
FIGS_DIR = BASE_DIR / "03_analysis" / "figures"


def add_rich_paragraph(doc, text, style=None, alignment=None, space_after=None):
    """Add a paragraph with proper bold/italic/reference handling."""
    p = doc.add_paragraph()
    if style:
        p.style = doc.styles[style]
    if alignment:
        p.alignment = alignment
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)

    # Parse markdown inline formatting: **bold**, *italic*, [num] refs
    # Split on ** for bold and * for italic
    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = p.add_run(part[2:-2])
            run.bold = True
        elif part.startswith('*') and part.endswith('*') and not part.startswith('**'):
            run = p.add_run(part[1:-1])
            run.italic = True
        elif part.startswith('---'):
            # Em dash
            run = p.add_run(part.replace('---', '\u2014'))
        else:
            # Handle em dashes within text
            cleaned = part.replace('---', '\u2014').replace('--', '\u2013')
            run = p.add_run(cleaned)
    return p


def add_md_section(doc, content):
    """Parse markdown content and add to document with proper formatting."""
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Headings
        if line.startswith('# '):
            h = doc.add_heading(line[2:], level=1)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0, 51, 102)
            i += 1
            continue
        if line.startswith('## '):
            h = doc.add_heading(line[3:], level=2)
            for run in h.runs:
                run.font.color.rgb = RGBColor(0, 71, 133)
            i += 1
            continue
        if line.startswith('### '):
            doc.add_heading(line[4:], level=3)
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\.\s', line):
            text = re.sub(r'^\d+\.\s', '', line)
            add_rich_paragraph(doc, text, style='List Number')
            i += 1
            continue

        # Bullet list with bold prefix
        if line.startswith('- '):
            text = line[2:]
            add_rich_paragraph(doc, text, style='List Bullet')
            i += 1
            continue

        # Table (collect all table lines)
        if line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            _add_table_from_md(doc, table_lines)
            continue

        # Regular paragraph
        # Collect continuation lines (non-empty, non-special)
        para_text = line
        i += 1
        while i < len(lines):
            next_line = lines[i].rstrip()
            if (not next_line or next_line.startswith('#') or
                next_line.startswith('- ') or next_line.startswith('|') or
                re.match(r'^\d+\.\s', next_line)):
                break
            para_text += ' ' + next_line
            i += 1

        add_rich_paragraph(doc, para_text, space_after=6)


def _add_table_from_md(doc, lines):
    """Parse markdown table lines into a formatted docx table."""
    rows = []
    for line in lines:
        if '---' in line and '|' in line:
            continue  # Skip separator line
        cells = [c.strip().replace('**', '') for c in line.split('|')[1:-1]]
        if cells:
            rows.append(cells)

    if len(rows) < 2:
        return

    n_cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=n_cols)
    table.style = 'Light Shading Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for i, row_data in enumerate(rows):
        for j in range(min(len(row_data), n_cols)):
            cell = table.rows[i].cells[j]
            cell.text = row_data[j]
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    if i == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0, 51, 102)

    doc.add_paragraph('')


def read_latest_table(prefix):
    """Read the latest version of a table file."""
    files = sorted(glob.glob(str(TABLES_DIR / f"{prefix}_*.md")))
    if not files:
        return ""
    with open(files[-1], encoding="utf-8") as f:
        return f.read()


def build_manuscript():
    """Build the complete publication-quality manuscript."""
    doc = Document()
    date_str = datetime.now().strftime("%B %Y")

    # ── Global styles ──
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(4)

    for level in range(1, 4):
        hs = doc.styles[f'Heading {level}']
        hs.font.name = 'Calibri'

    # ══════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ══════════════════════════════════════════════════════════════
    for _ in range(5):
        doc.add_paragraph('')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Large Language Models in Healthcare Simulation:\nA Bibliometric Analysis Mapping the Research Landscape')
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0, 51, 102)

    doc.add_paragraph('')
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Matt Pears¹, [Colleague 1]², [Colleague 2]³, Shekhar [Surname]⁴*')
    run.font.size = Pt(12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('*Corresponding author')
    run.font.size = Pt(10)
    run.italic = True

    doc.add_paragraph('')
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f'Manuscript generated: {date_str}')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(140, 140, 140)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # SECTIONS FROM MARKDOWN FILES
    # ══════════════════════════════════════════════════════════════
    section_files = [
        'abstract.md', 'introduction.md', 'methods.md',
        'results.md', 'discussion.md', 'conclusions.md'
    ]

    for sf in section_files:
        path = SECTIONS_DIR / sf
        if not path.exists():
            continue
        with open(path, encoding='utf-8') as f:
            content = f.read()

        # Skip the Keywords line in abstract (we'll add it manually)
        if sf == 'abstract.md':
            content = re.sub(r'\*\*Keywords[:\*].*', '', content)

        add_md_section(doc, content)

        # After abstract, add keywords
        if sf == 'abstract.md':
            p = doc.add_paragraph()
            run = p.add_run('Keywords: ')
            run.bold = True
            run.font.size = Pt(10)
            run = p.add_run('bibliometric analysis; large language models; healthcare simulation; non-technical skills; medical education; open access')
            run.italic = True
            run.font.size = Pt(10)
            doc.add_page_break()

        # After results, insert key figures
        if sf == 'results.md':
            doc.add_page_break()
            _add_key_figures(doc)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # KEY RESULTS TABLES
    # ══════════════════════════════════════════════════════════════
    doc.add_heading('Appendix: Key Results Tables', level=1)

    table_configs = [
        ('publication_trends', 'Table 1: Publication Trends by Year'),
        ('citation_summary', 'Table 2: Citation Summary Statistics'),
        ('author_summary', 'Table 3: Author Analysis Summary'),
        ('nts_domains', 'Table 4: NTS Domain Classification'),
        ('llm_model_summary', 'Table 5: LLM Model Distribution'),
        ('simulation_type_summary', 'Table 6: Simulation Type Classification'),
        ('geographic_analysis', 'Table 7: Geographic Distribution'),
        ('research_methods', 'Table 8: Research Methods Distribution'),
        ('urology_results', 'Table 9: Urology Sub-Analysis'),
    ]

    for prefix, title in table_configs:
        content = read_latest_table(prefix)
        if content:
            h = doc.add_heading(title, level=3)
            for run in h.runs:
                run.font.size = Pt(11)
            # Extract and render the table
            table_lines = [l for l in content.split('\n') if l.strip().startswith('|')]
            if table_lines:
                _add_table_from_md(doc, table_lines)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════
    # REFERENCES
    # ══════════════════════════════════════════════════════════════
    ref_path = SECTIONS_DIR / 'references.md'
    if ref_path.exists():
        doc.add_heading('References', level=1)
        with open(ref_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    p = doc.add_paragraph()
                    # Handle italic journal names
                    parts = re.split(r'(\*[^*]+\*)', line)
                    for part in parts:
                        if part.startswith('*') and part.endswith('*'):
                            run = p.add_run(part[1:-1])
                            run.italic = True
                            run.font.size = Pt(9)
                        else:
                            run = p.add_run(part)
                            run.font.size = Pt(9)

    # ══════════════════════════════════════════════════════════════
    # DATA AVAILABILITY + DECLARATIONS
    # ══════════════════════════════════════════════════════════════
    doc.add_heading('Data Availability Statement', level=1)
    doc.add_paragraph(
        'The complete data collection pipeline, processing scripts, and analysis code are available at '
        'https://github.com/MattPears1/bibliometric-llm-healthcare-simulation. '
        'Raw bibliometric data and analysis outputs are available upon reasonable request.'
    )

    doc.add_heading('Declarations', level=1)
    p = doc.add_paragraph()
    run = p.add_run('Funding: ')
    run.bold = True
    p.add_run('[To be completed]')

    p = doc.add_paragraph()
    run = p.add_run('Competing Interests: ')
    run.bold = True
    p.add_run('The authors declare no competing interests.')

    # ── Save ──
    out_path = Path(__file__).parent / 'output' / f'MANUSCRIPT_{datetime.now().strftime("%Y%m%d")}.docx'
    doc.save(str(out_path))

    # Count words
    word_count = 0
    for para in doc.paragraphs:
        word_count += len(para.text.split())
    print(f'Manuscript saved: {out_path} ({word_count} words)')

    # Also build .md version
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).parent / 'assemble_manuscript.py')],
                   capture_output=True, timeout=60)

    return out_path


def _add_key_figures(doc):
    """Embed the three most important figures inline."""
    doc.add_heading('Key Figures', level=1)

    figures = [
        ('publication_trends.png',
         'Figure 1: Publication Trends (2020\u20132026)',
         'Annual publication counts showing the ChatGPT inflection point. '
         'Pre-ChatGPT output totalled 198 papers (6.4%), while post-ChatGPT '
         'output reached 2,914 (93.6%), peaking at 1,415 papers in 2025.'),
        ('nts_domain_frequencies.png',
         'Figure 2: Non-Technical Skills Domain Frequencies',
         'Distribution across nine NTS domains. Decision-making (889, 29.6%) '
         'and Communication (612, 20.4%) dominate, while Crisis Resource '
         'Management (4, 0.1%) is critically under-researched.'),
        ('strategic_diagram.png',
         'Figure 3: Callon Strategic Thematic Diagram',
         'Five thematic clusters plotted by centrality (external cohesion) '
         'and density (internal development). Three motor themes occupy the '
         'upper-right quadrant, indicating mature, driving research programmes.'),
    ]

    for filename, title, caption in figures:
        filepath = FIGS_DIR / filename
        if not filepath.exists():
            continue

        # Title
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 51, 102)

        # Image
        doc.add_picture(str(filepath), width=Inches(5.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Caption
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(caption)
        run.font.size = Pt(9)
        run.italic = True
        run.font.color.rgb = RGBColor(80, 80, 80)

        doc.add_paragraph('')


if __name__ == '__main__':
    build_manuscript()
