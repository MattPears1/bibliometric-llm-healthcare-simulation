#!/usr/bin/env python3
"""Build a CLEAN .docx: no raw **, justified text, inline tables+figures."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

SECTIONS_DIR = Path(__file__).parent / 'sections'
FIGS = Path(__file__).parent.parent / '03_analysis' / 'figures'
OUT = Path(__file__).parent / 'output' / 'MANUSCRIPT_20260323.docx'

# Read + strip ALL ** from every section
def load(name):
    p = SECTIONS_DIR / name
    if not p.exists(): return ''
    text = p.read_text(encoding='utf-8')
    text = text.replace('**', '')  # Nuclear: remove all bold markers
    return text

def add_table(doc, rows):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = 'Light Shading Accent 1'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            t.rows[ri].cells[ci].text = val
            for run in t.rows[ri].cells[ci].paragraphs[0].runs:
                run.font.size = Pt(10)
                if ri == 0: run.bold = True
    doc.add_paragraph('')

def add_fig(doc, filename, title, caption):
    fp = FIGS / filename
    if not fp.exists(): return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title)
    run.bold = True; run.font.size = Pt(11); run.font.color.rgb = RGBColor(0,51,102)
    doc.add_picture(str(fp), width=Inches(5.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(caption)
    run.font.size = Pt(9); run.italic = True; run.font.color.rgb = RGBColor(80,80,80)
    doc.add_paragraph('')

def add_section(doc, text):
    for line in text.split('\n'):
        line = line.rstrip()
        if not line: continue
        if line.startswith('# '):
            h = doc.add_heading(line[2:], level=1)
            for r in h.runs: r.font.color.rgb = RGBColor(0,51,102)
        elif line.startswith('## '):
            h = doc.add_heading(line[3:], level=2)
            for r in h.runs: r.font.color.rgb = RGBColor(0,71,133)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('\u2022 '):
            p = doc.add_paragraph(line[2:], style='List Bullet')
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif re.match(r'^\d+\.\s', line):
            p = doc.add_paragraph(re.sub(r'^\d+\.\s','',line), style='List Number')
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif line.startswith('|'):
            pass  # skip md tables
        else:
            clean = line.replace('---','\u2014').replace('--','\u2013')
            p = doc.add_paragraph(clean)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# BUILD
doc = Document()
style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

# Title
for _ in range(5): doc.add_paragraph('')
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Large Language Models in Healthcare Simulation:\nA Bibliometric Analysis Mapping the Research Landscape')
run.bold = True; run.font.size = Pt(20); run.font.color.rgb = RGBColor(0,51,102)
doc.add_paragraph('')
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('Matt Pears, [Colleague 1], [Colleague 2], Shekhar [Surname]*').font.size = Pt(12)
doc.add_page_break()

# Abstract
abstract = load('abstract.md')
abstract = '\n'.join(l for l in abstract.split('\n') if 'keywords' not in l.lower() or l.strip().startswith('#'))
add_section(doc, abstract)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
run = p.add_run('Keywords: '); run.bold = True; run.font.size = Pt(10)
run = p.add_run('bibliometric analysis; large language models; healthcare simulation; non-technical skills; medical education; open access')
run.italic = True; run.font.size = Pt(10)
doc.add_page_break()

# Intro + Methods
add_section(doc, load('introduction.md'))
add_section(doc, load('methods.md'))

# Results
add_section(doc, load('results.md'))

# INLINE: Table 1 + Figure 1 + Table 2 + Figure 2
doc.add_paragraph('')
doc.add_heading('Table 1: Key Metrics Summary', level=3)
add_table(doc, [
    ['Metric','Value'],['Core corpus','3,112'],['CAGR','37.5%'],
    ['Post-ChatGPT','93.6%'],['Peak year','2025 (1,415)'],
    ['h-index / g-index','92 / 166'],['Total citations','46,823'],
    ['Mean citations','15.05'],['Authors','12,937'],['Journals','1,343'],
    ['Countries','86'],['Lotka \u03b2','2.559 (R\u00b2=0.941)'],
    ['RCTs','35 (1.1%)'],['Urology','117 (3.8%)'],
])
add_fig(doc, 'publication_trends.png',
    'Figure 1: Publication Trends (2020\u20132026)',
    'Annual counts showing ChatGPT inflection point. Peak: 1,415 in 2025. CAGR: 37.5%.')

doc.add_heading('Table 2: NTS Domain Distribution', level=3)
add_table(doc, [
    ['Domain','Papers','%'],['Decision-making','889','29.6%'],
    ['Communication','612','20.4%'],['Teamwork','374','12.5%'],
    ['Leadership','234','7.8%'],['Stress management','147','4.9%'],
    ['Professionalism','93','3.1%'],['Situational awareness','53','1.8%'],
    ['Task management','38','1.3%'],['CRM','4','0.1%'],
])
add_fig(doc, 'nts_domain_frequencies.png',
    'Figure 2: Non-Technical Skills Domain Frequencies',
    'Decision-making (889) and Communication (612) dominate. CRM: only 4 papers (222:1 disparity).')

# Discussion + Conclusions
add_section(doc, load('discussion.md'))
add_section(doc, load('conclusions.md'))
doc.add_page_break()

# References
doc.add_heading('References', level=1)
for line in load('references.md').split('\n'):
    line = line.strip()
    if line and not line.startswith('#'):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        parts = re.split(r'(\*[^*]+\*)', line)
        for part in parts:
            if part.startswith('*') and part.endswith('*'):
                run = p.add_run(part[1:-1]); run.italic = True; run.font.size = Pt(9)
            else:
                run = p.add_run(part); run.font.size = Pt(9)

# Data availability
doc.add_heading('Data Availability', level=1)
p = doc.add_paragraph('The complete pipeline is available at https://github.com/MattPears1/bibliometric-llm-healthcare-simulation.')
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# FORCE justify on every paragraph that isn't a heading or centered
for para in doc.paragraphs:
    if para.alignment not in (WD_ALIGN_PARAGRAPH.CENTER, None):
        continue
    if para.style.name.startswith('Heading'):
        continue
    # Check if it's a figure caption or title (centered)
    if para.alignment == WD_ALIGN_PARAGRAPH.CENTER:
        continue
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Actually force ALL non-heading, non-centered paragraphs
for para in doc.paragraphs:
    if para.style.name.startswith('Heading'):
        continue
    if any(r.text and r.font.color.rgb == RGBColor(0,51,102) for r in para.runs if r.font.color and r.font.color.rgb):
        continue  # Figure titles stay centered
    if para.alignment != WD_ALIGN_PARAGRAPH.CENTER:
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

doc.save(str(OUT))

# Verify
doc2 = Document(str(OUT))
stars = sum(1 for p in doc2.paragraphs if '**' in p.text)
tables = len(doc2.tables)
images = len(doc2.inline_shapes)
justified = sum(1 for p in doc2.paragraphs if p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY)
total = len(doc2.paragraphs)
words = sum(len(p.text.split()) for p in doc2.paragraphs)
print(f'Tables: {tables}, Images: {images}, Raw **: {stars}')
print(f'Justified: {justified}/{total} paragraphs')
print(f'Words: {words}')
