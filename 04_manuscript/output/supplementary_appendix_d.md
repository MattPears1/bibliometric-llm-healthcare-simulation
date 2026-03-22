# Supplementary Appendix D: Code Availability and Reproduction Guide

## Repository

The complete bibliometric analysis pipeline is available at:
**[GitHub URL to be added upon publication]**

## System Requirements

- Python 3.8 or higher
- 8 GB RAM minimum (tested on 8 GB laptop)
- Internet connection for API access
- Approximately 2 GB disk space for raw data

## Quick Reproduction

```bash
# Clone the repository
git clone https://github.com/MattPears1/bibliometric-llm-healthcare-simulation.git
cd bibliometric-llm-healthcare-simulation

# Install dependencies
pip install -r requirements.txt

# Optional: Set up API keys for better rate limits
cp .env.example .env
# Edit .env with your CORE and Semantic Scholar API keys

# Run the full pipeline
python run_pipeline.py --all
```

## Expected Duration

| Phase | Duration | Notes |
|-------|----------|-------|
| Data collection | 30-60 minutes | Rate-limited by APIs |
| Normalisation | 1-2 minutes | CPU-bound |
| Deduplication | 1-2 minutes | Includes fuzzy matching |
| Screening | 2-5 minutes | Keyword-based |
| All analyses | 5-10 minutes | Including figure generation |
| **Total** | **~45-80 minutes** | |

## Pipeline Components

### Data Collection (01_collection/)
- 7 source-specific collectors inheriting from `collector_base.py`
- Checkpointing: automatically resumes from last position if interrupted
- Retry with exponential backoff on API errors
- Rate limiting: configurable per source

### Data Processing (02_processing/)
- `normalizer.py`: Standardises records to common schema
- `deduplicator.py`: Three-tier deduplication (DOI, fuzzy title, author+year)
- `screener.py`: Two-stage screening (keyword + AI-assisted)
- `irr_sampler.py`: Generates inter-rater reliability samples

### Analysis (03_analysis/)
- 14 analysis scripts covering all major bibliometric dimensions
- Callon's strategic diagram, Lotka's law, Bradford's law
- All figures saved at 300 DPI for publication

### Manuscript (04_manuscript/)
- Template-based manuscript generation
- Automatic assembly into .md and .docx formats

## Updating Every Six Months

1. Update `config.yaml`: change `to_year` to current year
2. Run `python run_pipeline.py --all`
3. Review updated figures in `03_analysis/figures/`
4. Review updated manuscript in `04_manuscript/output/`

## Configuration

All parameters are centralised in `config.yaml`:
- Search terms and query strategies per database
- Rate limits and batch sizes
- Screening thresholds
- Analysis parameters (clustering resolution, minimum keyword frequency)

## API Keys

Two optional free API keys improve data coverage:
- **CORE** (core.ac.uk): Free registration, 30-day trial
- **Semantic Scholar** (semanticscholar.org): Free registration, 1 req/sec

Without API keys, the pipeline still works using the 5 unauthenticated sources.

## Licence

MIT Licence. Free to use, modify, and distribute with attribution.
