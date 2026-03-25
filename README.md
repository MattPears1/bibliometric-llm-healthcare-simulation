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
git clone https://github.com/MattPears1/bibliometric-llm-healthcare-simulation.git
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
  screener.py           2-stage screening (keyword pre-filter + heuristic)
  irr_sampler.py        Inter-rater reliability sample generator
  ai_screening_log_171_papers.csv   AI screening validation (171 papers)
  irr_answer_key.csv    Human-AI IRR answer key (30-paper sample)
  low_confidence_review.csv  Low-confidence papers for review

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
  research_methods_analysis.py
  urology_subanalysis.py
  prisma_diagram.py
  run_replication.py    Replication master script
  core_corpus_dataset.json  3,107-paper analysis dataset
  figures/              Publication-quality PNG (300 DPI)
  tables/               Summary tables (Markdown)
  replication_20260325/ Full replication output (26 figs, 17 tables, report)

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

- **3,112 core corpus** (Tier 2+3, high/medium confidence) from 100,277 raw records across 7 databases
- **CAGR: 37.5%** — explosive growth post-ChatGPT (93.6% of papers published 2023–2026)
- **h-index: 92** with 46,823 total citations (mean 15.05, median 1)
- **12,937 unique authors** — 86.3% are single-paper contributors (Lotka's law: beta = 2.559, R² = 0.941)
- **Bradford's law**: 63 core journals produce 33% of papers; 1,343 total journals
- **ChatGPT dominates** LLM mentions (25.3%); open-source models only 1.7% (52 papers)
- **NTS gap**: CRM (4 papers, 0.1%) and situational awareness (54, 1.7%) critically under-researched
- **117 urology papers** (3.8%), 0 combining LLMs with simulation boot camps
- **AI-validated screening**: 171 borderline papers reviewed by individual AI agents (kappa = 0.93 with human reviewer); 200-paper pipeline validation confirmed 100% specificity on exclusions

## Screening Validation

The screening pipeline was validated at three levels:

1. **171 low-confidence Tier 2/3 papers** independently screened by 171 individual Claude Sonnet 4.6 agents (1 agent per paper), each providing a written rationale. 22 included, 149 excluded.
2. **30-paper IRR sample** — lead researcher independently screened a stratified sample blinded to AI decisions. Cohen's kappa = 0.93 (almost perfect agreement).
3. **200-paper pipeline validation** — stratified sample of 100 algorithmic includes + 100 algorithmic excludes reviewed by AI agents. Exclusion agreement: 100%. Inclusion agreement: 19% (by design — Stage 1 is deliberately liberal; subsequent tiering and confidence filtering refines the corpus).

All screening logs with individual decisions and rationales are provided in `02_processing/`.

## Citation

If you use this pipeline or findings, please cite:

> Pears, M., et al. (2026). Large Language Models in Healthcare Simulation: A Bibliometric Analysis Mapping the Research Landscape. [Journal]. DOI: [pending]

## License

MIT License - free to use, modify, and distribute.

## Contributing

Contributions welcome. Please open an issue or pull request.
