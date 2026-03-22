# Dataset Options for Analysis

The pipeline produces multiple dataset levels. Choose which to use for the main analysis:

## Option 1: Refined Dataset (RECOMMENDED)
**File:** `03_analysis/refined_dataset.json`
**Papers:** 2,781
**Description:** LLM + (simulation OR education) + medical terms. Highest precision.
**Metrics:** h-index 88, CAGR 38.6%, 42,010 citations

## Option 2: Core Dataset
**File:** `03_analysis/core_dataset.json`
**Papers:** 3,000
**Description:** High/medium confidence with simulation terms, Tier 2/3 only.
**Metrics:** h-index 91, CAGR 38.0%, 45,900 citations

## Option 3: Primary Dataset
**File:** `03_analysis/primary_dataset.json`
**Papers:** 3,587
**Description:** All confidence levels with simulation terms.
**Metrics:** h-index 100, CAGR 37.6%, 56,306 citations

## Option 4: Extended Dataset
**File:** `03_analysis/analysis_dataset.json`
**Papers:** 7,893
**Description:** Full LLM + healthcare landscape (broadest, most noise).
**Metrics:** h-index 154, CAGR 42.1%, 149,461 citations

## Current Manuscript
The manuscript currently uses **Option 2 (Core, 3,000 papers)**.
All figures are generated from this dataset.

## Recommendation
Use **Option 2 (Core)** or **Option 1 (Refined)** for the main analysis.
Present Option 4 (Extended) as contextual landscape data.
The difference between Options 1 and 2 is small (~200 papers, similar metrics).
