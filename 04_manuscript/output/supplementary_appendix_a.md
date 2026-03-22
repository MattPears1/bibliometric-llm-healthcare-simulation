# Supplementary Appendix A: Complete Search Strategies by Database

## A.1 OpenAlex (7 query strategies)

**API:** https://api.openalex.org/works
**Filter:** `publication_year:2020-2026`
**Field:** `search` (full-text title and abstract search)

| Strategy | Query String |
|----------|-------------|
| broad_llm_sim | `large language model simulation healthcare` |
| chatgpt_training | `ChatGPT simulation training medical education` |
| genai_nts | `generative AI non-technical skills healthcare simulation` |
| llm_virtual_patient | `LLM virtual patient communication` |
| ai_sim_education | `artificial intelligence simulation education clinical` |
| chatgpt_medical_education | `ChatGPT medical education` |
| llm_healthcare_training | `large language model healthcare training` |

**Records retrieved:** 49,068

---

## A.2 PubMed via E-utilities (6 query strategies)

**API:** https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
**Date filter:** `mindate=2020/01/01, maxdate=2026/12/31`

| Strategy | Query String |
|----------|-------------|
| llm_sim_nts | `("large language model"[TIAB] OR ChatGPT[TIAB] OR "generative AI"[TIAB] OR GPT[TIAB]) AND (simulation[TIAB] OR "simulated patient"[TIAB] OR "virtual patient"[TIAB]) AND (communication[TIAB] OR teamwork[TIAB] OR "non-technical skills"[TIAB])` |
| llm_sim_medical | `("large language model"[TIAB] OR ChatGPT[TIAB] OR "generative AI"[TIAB] OR LLM[TIAB]) AND (simulation[TIAB] OR simulator[TIAB] OR debriefing[TIAB]) AND (medical[TIAB] OR healthcare[TIAB] OR clinical[TIAB])` |
| chatgpt_virtual_patient | `(ChatGPT[TIAB] OR "GPT-4"[TIAB]) AND ("virtual patient"[TIAB] OR "simulated patient"[TIAB] OR "standardized patient"[TIAB])` |
| genai_med_ed | `("generative AI"[TIAB] OR "generative artificial intelligence"[TIAB] OR "large language model"[TIAB]) AND ("medical education"[TIAB] OR "simulation training"[TIAB])` |
| mesh_sim_ai | `"Simulation Training"[MeSH] AND "Artificial Intelligence"[MeSH]` |
| broad_ai_sim | `("artificial intelligence"[TIAB] OR "AI"[TIAB]) AND ("simulation"[TIAB]) AND ("medical education"[TIAB] OR "healthcare education"[TIAB] OR "clinical education"[TIAB])` |

**Records retrieved:** 1,066

---

## A.3 Europe PMC (3 query strategies)

**API:** https://www.ebi.ac.uk/europepmc/webservices/rest/search
**Date filter:** `PUB_YEAR:[2020 TO 2026]`

| Strategy | Query String |
|----------|-------------|
| llm_sim_nts_med | `(ChatGPT OR "large language model" OR LLM OR GPT) AND (simulation OR simulator OR "virtual patient") AND (teamwork OR communication OR "non-technical skills") AND (healthcare OR medical)` |
| llm_sim_broad | `(ChatGPT OR "large language model" OR "generative AI") AND (simulation OR "simulated patient") AND (medical OR healthcare OR clinical)` |
| ai_med_education | `("artificial intelligence" OR ChatGPT OR LLM) AND ("medical education" OR "simulation training" OR "clinical training")` |

**Records retrieved:** 18,721

---

## A.4 Crossref (4 query strategies)

**API:** https://api.crossref.org/works
**Filter:** `from-pub-date:2020-01-01,until-pub-date:2026-12-31`

| Strategy | Query String |
|----------|-------------|
| llm_sim_nts | `large language model simulation healthcare non-technical skills` |
| chatgpt_sim_med | `ChatGPT simulation medical education training` |
| genai_healthcare_sim | `generative AI healthcare simulation communication teamwork` |
| ai_virtual_patient | `artificial intelligence virtual patient medical training` |

**Records retrieved:** 19,219

---

## A.5 Semantic Scholar (10 query strategies)

**API:** https://api.semanticscholar.org/graph/v1/paper/search
**Filter:** `year:2020-2026`

| Strategy | Query String |
|----------|-------------|
| llm_sim_healthcare | `large language model simulation healthcare` |
| chatgpt_medical_training | `ChatGPT medical education simulation training` |
| genai_nts_healthcare | `generative AI non-technical skills healthcare simulation` |
| llm_virtual_patient | `LLM virtual patient communication medical` |
| ai_sim_teamwork | `artificial intelligence simulation teamwork clinical education` |
| chatgpt_clinical_communication | `ChatGPT clinical communication skills training` |
| gpt4_medical_simulation | `GPT-4 medical simulation education` |
| llm_debriefing | `large language model debriefing simulation healthcare` |
| ai_standardized_patient | `AI standardized patient medical education` |
| chatgpt_osce | `ChatGPT OSCE clinical examination` |

**Records retrieved:** 7,536

---

## A.6 CORE (3 query strategies)

**API:** https://api.core.ac.uk/v3/search/works
**Authentication:** API key required (free registration)

| Strategy | Query String |
|----------|-------------|
| llm_sim_healthcare | `large language model simulation healthcare` |
| chatgpt_med_training | `ChatGPT medical education simulation` |
| genai_clinical_sim | `generative AI clinical simulation training` |

**Records retrieved:** 4,626

---

## A.7 DOAJ (2 query strategies)

**API:** https://doaj.org/api/search/articles/
**No authentication required**

| Strategy | Query String |
|----------|-------------|
| llm_sim_healthcare | `large language model simulation healthcare` |
| chatgpt_medical_education | `ChatGPT medical education simulation` |

**Records retrieved:** 41

---

## Summary

| Database | Strategies | Records | Auth Required |
|----------|-----------|---------|---------------|
| OpenAlex | 7 | 49,068 | No |
| Crossref | 4 | 19,219 | No |
| Europe PMC | 3 | 18,721 | No |
| Semantic Scholar | 10 | 7,536 | Free API key |
| CORE | 3 | 4,626 | Free API key |
| PubMed | 6 | 1,066 | No |
| DOAJ | 2 | 41 | No |
| **Total** | **35** | **100,277** | |
