# Bibliometric Analysis: LLMs in Healthcare Simulation

A fully replicable bibliometric analysis pipeline examining the research landscape of Large Language Models (LLMs) in healthcare simulation and non-technical skills (NTS) training.

## Key Features

- **100,000+ records** from 7 free, open-access databases
- **No institutional access required** - uses only freely available APIs
- **Fully automated** - from data collection through manuscript generation
- **Replicable** - designed to be re-run every 6 months for landscape updates
- **Three-tier analysis** - progressively focuses from LLM+Medical to +Simulation to +NTS

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/[username]/bibliometric-llm-healthcare-simulation.git
cd bibliometric-llm-healthcare-simulation
pip install -r requirements.txt

# 2. Set up API keys (optional but recommended)
cp .env.example .env
# Edit .env with your CORE and Semantic Scholar API keys

# 3. Run the full pipeline
python run_pipeline.py --all

# Or run individual phases
python run_pipeline.py --collect    # Data collection only
python run_pipeline.py --process    # Normalize + dedup + screen
python run_pipeline.py --analyze    # Run all analyses

# Continuous mode (for autonomous operation)
python run_pipeline.py --loop --interval 24 --max-days 7
```

## Data Sources

| Source | Auth Required | Records | Coverage |
|--------|-------------|---------|----------|
| OpenAlex | No (email for polite pool) | ~49,000 | Broadest coverage |
| Europe PMC | No | ~19,000 | Biomedical focus |
| Crossref | No | ~19,000 | DOI authority |
| Semantic Scholar | Free API key | ~7,500 | AI-enriched metadata |
| CORE | Free API key | ~4,600 | Full-text OA papers |
| PubMed | No | ~1,100 | Gold-standard medical |
| DOAJ | No | ~40 | OA journals directory |

## Pipeline Architecture

```
01_collection/          Data collection (7 source-specific collectors)
  collector_base.py     Base class: checkpointing, retry, rate limiting
  *_collector.py        One per source
  raw/                  Raw JSONL output

02_processing/          Data processing
  normalizer.py         Standardize to common schema
  deduplicator.py       3-tier dedup (DOI, fuzzy title, author+year)
  screener.py           2-stage screening (keyword + AI-assisted)
  irr_sampler.py        Inter-rater reliability sample generator

03_analysis/            Bibliometric analyses
  publication_trends.py
  citation_analysis.py
  author_analysis.py    (Lotka's law)
  journal_analysis.py   (Bradford's law)
  geographic_analysis.py
  keyword_cooccurrence.py
  thematic_mapping.py   (Callon's strategic diagram)
  nts_analysis.py
  llm_model_analysis.py
  simulation_type_analysis.py
  urology_subanalysis.py
  prisma_diagram.py
  figures/              Publication-quality PNG (300 DPI)
  tables/               Summary tables (Markdown)

04_manuscript/          Manuscript generation
  template.md           IMRAD template with placeholders
  assemble_manuscript.py  Combines sections into .md + .docx
  sections/             Individual manuscript sections
  output/               Final manuscript, cover letter, checklist

config.yaml             All configuration in one place
run_pipeline.py         Master orchestrator
```

## Re-Running Every 6 Months

1. Update `config.yaml` date range (e.g., `to_year: 2027`)
2. Run `python run_pipeline.py --all`
3. Review outputs in `03_analysis/figures/` and `04_manuscript/output/`
4. The pipeline handles checkpointing, so interrupted runs resume automatically

## Key Findings (March 2026)

- **12,715 papers** included from 100,277 raw records
- **CAGR: 35.5%** - explosive growth post-ChatGPT
- **92.8%** of papers published after ChatGPT launch (Nov 2022)
- **h-index: 155** with 168,407 total citations
- **Lotka's law**: beta = 2.06 (R² = 0.908) - near-perfect fit
- **Bradford's law**: 75 core journals produce 1/3 of papers
- **ChatGPT dominates** LLM mentions (29.7%); open-source models only 1.7%
- **NTS gap**: CRM (7 papers) and situational awareness (52) critically under-researched
- **320 urology papers**, 0 combining LLMs with simulation boot camps

## Citation

If you use this pipeline or findings, please cite:

> Pears, M., et al. (2026). Large Language Models in Healthcare Simulation: A Bibliometric Analysis Mapping the Research Landscape. [Journal]. DOI: [pending]

## License

MIT License - free to use, modify, and distribute.

## Contributing

Contributions welcome. Please open an issue or pull request.
