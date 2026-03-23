#!/usr/bin/env python3
"""Build a .docx with all 32 figures and descriptions."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
title = doc.add_heading('Bibliometric Analysis: LLMs in Healthcare Simulation', level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('Complete Figure Compendium - Core Dataset (3,000 papers)')
doc.add_paragraph('Generated: March 2026')
doc.add_paragraph('')

figures = [
    ('graphical_abstract.png', 'Graphical Abstract',
     'Summary infographic highlighting four key findings: 38.0% CAGR growth, the NTS gap (Decision-making 889 vs CRM 4), proprietary LLM dominance (42.7% vs 2.8% open-source), and the urology boot camp gap (0 papers).'),
    ('prisma_flow.png', 'Figure 1: PRISMA 2020 Flow Diagram',
     'Three-level corpus selection: 100,277 raw records from 7 databases, deduplication to 86,635 unique, screening to extended (7,893), primary (3,587), and core (3,000) corpus.'),
    ('publication_trends.png', 'Figure 2: Publication Trends by Year',
     'Annual counts showing ChatGPT inflection point. Pre-ChatGPT: 186 papers (6.2%), post-ChatGPT: 2,814 (93.8%), peak 2025 with 1,366 papers.'),
    ('cumulative_growth.png', 'Figure 3: Cumulative Growth',
     'Cumulative growth curve with CAGR of 38.0%, showing exponential acceleration from 2023.'),
    ('citation_distribution.png', 'Figure 4: Citation Distribution',
     'Log-scaled histogram. h-index 91, g-index 165, mean 15.30 citations, ~35% uncited due to publication recency.'),
    ('citations_by_year.png', 'Figure 5: Citations by Year',
     'Mean and total citations by year showing citation maturation: earlier papers have higher means, 2025-2026 papers have insufficient citation windows.'),
    ('strategic_diagram.png', 'Figure 6: Callon Strategic Diagram',
     'Five thematic clusters plotted by centrality and density. Three motor themes (upper-right) and two emerging themes (lower-left).'),
    ('nts_domain_frequencies.png', 'Figure 7: NTS Domain Frequencies',
     'Nine NTS domains: Decision-making (889, 29.6%) and Communication (612, 20.4%) dominate. CRM (4, 0.1%) is critically under-researched.'),
    ('nts_domain_year_heatmap.png', 'Figure 8: NTS Temporal Heatmap',
     'Year-by-domain heatmap showing Decision-making and Communication growth across all years, while CRM remains sparse throughout.'),
    ('simulation_nts_crosstab.png', 'Figure 9: Simulation x NTS Cross-Tabulation',
     'Heatmap of simulation modalities vs NTS domains. VR/MR/XR has broadest NTS coverage. Mannequin-based simulation has minimal CRM engagement.'),
    ('simulation_type_frequencies.png', 'Figure 10: Simulation Type Frequencies',
     'VR/MR/XR leads (687, 22.9%), Scenario-based (406, 13.5%), Virtual Patient/Chatbot (299, 10.0%). Mannequin (80, 2.7%) is underrepresented.'),
    ('llm_model_frequencies.png', 'Figure 11: LLM Model Frequencies',
     'ChatGPT dominates (778, 25.9%), GPT-4 (217, 7.2%), Gemini (145, 4.8%). Open-source: Llama (48), Mistral (7).'),
    ('llm_proprietary_vs_opensource.png', 'Figure 12: Proprietary vs Open-Source',
     'Proprietary models in 32.0% of papers vs 0.5% open-source. Raises reproducibility and institutional dependency concerns.'),
    ('llm_model_trends.png', 'Figure 13: LLM Model Trends',
     'Temporal trends: ChatGPT sustained dominance, Gemini steepest growth, GPT-3.5 declining as newer models supersede it.'),
    ('top_countries.png', 'Figure 14: Top 20 Countries',
     '84 countries. USA (239), China (168), UK (74), India (63), Canada (59). High-income countries dominate.'),
    ('continent_distribution.png', 'Figure 15: Continental Distribution',
     'Concentration in Asia and North America/Europe. Limited Africa and South America representation raises equity concerns.'),
    ('top_authors.png', 'Figure 16: Top 20 Authors',
     'Most prolific authors. Chinese-affiliated name predominance may partly reflect disambiguation challenges.'),
    ('author_productivity.png', 'Figure 17: Author Productivity',
     '86.4% of 12,488 authors contributed one paper. Characteristic of a young field attracting diverse first-time contributors.'),
    ('lotkas_law.png', 'Figure 18: Lotka Law Test',
     'Log-log regression: beta=2.602, R-squared=0.955. Excellent fit confirming classical inverse-square author productivity.'),
    ('collaboration_index.png', 'Figure 19: Collaboration Index',
     'Mean 5.51 authors per paper, consistent with multidisciplinary biomedical research norms.'),
    ('top_journals.png', 'Figure 20: Top 20 Journals',
     'arXiv (85) and Cureus (83) lead, reflecting preprint and open-access culture in AI research.'),
    ('bradford_law.png', 'Figure 21: Bradford Law Zones',
     '1,299 journals in three zones. Zone 1 (core): 63 journals. Multiplier 7.25 confirms expected scatter.'),
    ('publication_types.png', 'Figure 22: Publication Types',
     'Articles (38.4%), reviews (8.6%), preprints (8.0%). Document type heterogeneity affects evidence quality.'),
    ('research_methods.png', 'Figure 23: Research Methods',
     'Development studies (630) and comparative studies (595) dominate. Only 36 RCTs (1.2%) identified.'),
    ('top_keywords.png', 'Figure 24: Top 30 Keywords',
     'AI, computer science, medicine, medical education as dominant terms reflecting interdisciplinary nature.'),
    ('keyword_cooccurrence_network.png', 'Figure 25: Keyword Co-occurrence Network',
     'Network showing intellectual structure with clusters around AI methodology, clinical applications, and education.'),
    ('keyword_wordcloud.png', 'Figure 26: Keyword Word Cloud',
     'Visual keyword frequency representation confirming interdisciplinary character of the field.'),
    ('urology_trends.png', 'Figure 27: Urology Sub-Analysis',
     '102 urology papers, growth from 2 (2020) to 40 (2025). Zero combine LLMs with simulation boot camps.'),
    ('source_database_distribution.png', 'Figure 28: Source Database Distribution',
     'OpenAlex largest contributor, followed by Europe PMC and Crossref. Validates multi-source approach.'),
    ('tier_distribution.png', 'Figure 29: Tier Distribution',
     'Tier 2 (LLM+healthcare simulation): 57.5%, Tier 3 (+NTS): 42.5% of core corpus.'),
    ('document_type_distribution.png', 'Figure 30: Document Types',
     'Peer-reviewed articles vs preprints, book chapters, and conference proceedings breakdown.'),
    ('data_completeness.png', 'Figure 31: Metadata Completeness',
     'Citation (100%), year (100%), authors (99.6%) high completeness. Journal info (77.9%) is the main gap.'),
]

fig_dir = Path('03_analysis/figures')
count = 0
for filename, title_text, description in figures:
    filepath = fig_dir / filename
    if not filepath.exists():
        continue
    doc.add_heading(title_text, level=2)
    doc.add_picture(str(filepath), width=Inches(6.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(description)
    p.style.font.size = Pt(10)
    doc.add_paragraph('')
    count += 1

doc.save('04_manuscript/output/FIGURE_COMPENDIUM.docx')
print(f'Saved FIGURE_COMPENDIUM.docx with {count} figures')
