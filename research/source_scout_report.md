# Source Scout Report: Academic APIs and Data Sources for Bibliometric Analysis

**Topic:** Large Language Models in Healthcare Simulation
**Date:** 2026-03-22
**Purpose:** Comprehensive inventory of every free/accessible academic API and data source for paper collection

---

## Table of Contents

1. [Tier 1: Primary Sources (Must-Use)](#tier-1-primary-sources-must-use)
2. [Tier 2: Strong Supplementary Sources](#tier-2-strong-supplementary-sources)
3. [Tier 3: Niche / Conditional Sources](#tier-3-niche--conditional-sources)
4. [Tier 4: Not Recommended / Unavailable](#tier-4-not-recommended--unavailable)
5. [Summary Decision Matrix](#summary-decision-matrix)
6. [Recommended Collection Pipeline Order](#recommended-collection-pipeline-order)

---

## Tier 1: Primary Sources (Must-Use)

These sources should form the backbone of our data collection pipeline.

---

### 1. OpenAlex

| Attribute | Details |
|-----------|---------|
| **URL** | https://openalex.org/ |
| **API Docs** | https://docs.openalex.org/ |
| **Authentication** | Free API key required (as of Feb 2025). Without key: 100 credits/day (testing only). With free key: 100,000 credits/day |
| **Rate Limits** | 100,000 credits/day with free API key. Credits vary by endpoint complexity |
| **Query Syntax** | REST API with filters, search, sort, pagination. Supports `?search=`, `?filter=publication_year:2024,is_oa:true`, Boolean via pipes for OR. Filter on `title_and_abstract.search:`, `fulltext.search:`, concepts, keywords, topics |
| **Data Fields** | title, DOI, abstract (inverted index), authors + affiliations + ORCID, publication_year, source/journal, type, cited_by_count, FWCI, cited_by_percentile_year, referenced_works, related_works, open_access status, concepts/topics/keywords, grants/funding |
| **Coverage** | ~271 million works (Nov 2025, Walden rebuild). All disciplines. Successor to Microsoft Academic Graph |
| **Special Features** | Concepts/topics taxonomy, citation network, author/institution entities, group_by analytics, full data snapshots available |
| **Recommendation** | **YES -- PRIMARY SOURCE.** Best single free API for bibliometric analysis. Broadest coverage, richest metadata, no paywall. Start here. |

---

### 2. PubMed E-utilities (NCBI)

| Attribute | Details |
|-----------|---------|
| **URL** | https://pubmed.ncbi.nlm.nih.gov/ |
| **API Docs** | https://www.ncbi.nlm.nih.gov/books/NBK25497/ |
| **Authentication** | Free API key via NCBI account (recommended). Works without key at lower rate |
| **Rate Limits** | Without API key: 3 requests/second. With API key: 10 requests/second. Higher rates available by request |
| **Query Syntax** | ESearch (search + get PMIDs), EFetch (get full records), ESummary (get summaries). Supports MeSH terms, Boolean operators, field tags [ti], [ab], [tw], date ranges |
| **Data Fields** | PMID, title, abstract, authors, MeSH terms, keywords, journal, publication date, DOI, grants, conflict of interest statements, chemicals, all cited references, publication types |
| **Coverage** | 40+ million citations and abstracts. Primarily biomedical/life sciences. 30,000+ journals indexed. Dating back to 1966 (selectively to 1809) |
| **Special Features** | MeSH controlled vocabulary (critical for healthcare topics), PubMed Central full-text subset, citation linking, related articles algorithm |
| **Recommendation** | **YES -- PRIMARY SOURCE.** Essential for healthcare/biomedical focus. MeSH terms are invaluable for precision. Best coverage of medical simulation literature specifically. |

---

### 3. Semantic Scholar (Allen AI)

| Attribute | Details |
|-----------|---------|
| **URL** | https://www.semanticscholar.org/ |
| **API Docs** | https://api.semanticscholar.org/api-docs/ |
| **Authentication** | No API key required for basic access. Free API key available for higher limits |
| **Rate Limits** | Unauthenticated: 5,000 requests per 5 minutes (shared pool). Authenticated: 1 RPS default (can request higher). Exponential backoff required |
| **Query Syntax** | REST API. Keyword search against title and abstract. Paper lookup by S2 ID, DOI, arXiv ID, PMID, etc. Batch endpoints available. `fields` parameter to select return data |
| **Data Fields** | paperId, title, abstract, authors (with affiliations, h-index), year, venue/journal, citationCount, influentialCitationCount, references, citations, SPECTER2 embeddings, TLDR (AI summary), isOpenAccess, fieldsOfStudy |
| **Coverage** | 225+ million papers, 100+ million authors, 2.8+ billion citation edges. All disciplines |
| **Special Features** | AI-powered TLDR summaries, influential citation tracking, SPECTER2 paper embeddings (for similarity), citation intent classification, recommendation engine |
| **Recommendation** | **YES -- PRIMARY SOURCE.** Excellent for citation network analysis and AI-enriched metadata. TLDR and influential citation features are unique. Good coverage of CS/AI papers. |

---

### 4. Europe PMC

| Attribute | Details |
|-----------|---------|
| **URL** | https://europepmc.org/ |
| **API Docs** | https://europepmc.org/RestfulWebService |
| **Authentication** | None required |
| **Rate Limits** | ~10 requests/second (based on forum discussions; not strictly documented). Generous for typical research use |
| **Query Syntax** | REST API returning JSON or XML. Supports Boolean operators, field-specific search (TITLE:, ABSTRACT:, AUTH:), date ranges, source filters (e.g., SRC:MED for PubMed). Pagination via cursorMark |
| **Data Fields** | PMID, PMCID, DOI, title, abstract, authors, journal, publication date, citation count, reference list, MeSH terms, full text (OA subset), text-mined entities (genes, diseases, chemicals, organisms, GO terms) |
| **Coverage** | 43+ million publications. Sources include PubMed, Agricola, European Patents Office, NICE, preprints. 10.2M full text, 6.5M open access. 19.4M publication reference lists |
| **Special Features** | Text-mined annotations (diseases, genes, chemicals), preprint integration, Europe-focused grant linkage, Annotations API |
| **Recommendation** | **YES -- PRIMARY SOURCE.** Superset of PubMed with European sources added. Text-mined annotations valuable for healthcare topic extraction. Preprint coverage adds breadth. |

---

### 5. Crossref

| Attribute | Details |
|-----------|---------|
| **URL** | https://api.crossref.org/ |
| **API Docs** | https://www.crossref.org/documentation/retrieve-metadata/rest-api/ |
| **Authentication** | None required. "Polite" pool: include `mailto:` parameter (recommended). "Plus" pool: paid |
| **Rate Limits** | Public/Polite pools: ~50 req/sec (revised Dec 2025; check response headers `x-rate-limit-limit` and `x-rate-limit-interval` for current values). Generous for typical use |
| **Query Syntax** | REST API. `/works` endpoint with `query=`, `filter=`, `select=`, `sort=`, `rows=`, `offset=`. Filters: `from-pub-date`, `has-abstract`, `type`, `ISSN`, `DOI`, etc. |
| **Data Fields** | DOI, title, abstract (when deposited), authors + ORCID + affiliations, journal/source, publication date, type, ISSN/ISBN, funder info, license, reference list, citation count (via "is-referenced-by-count") |
| **Coverage** | ~180 million metadata records. All disciplines. Covers virtually all DOI-registered scholarly content |
| **Special Features** | DOI resolution authority, funder metadata, license/OA info, reference linking, public data file for bulk download |
| **Recommendation** | **YES -- PRIMARY SOURCE.** Authoritative DOI metadata. Use for deduplication (DOI matching), enriching records from other sources, and getting standardized metadata. Abstract coverage is incomplete (depends on publisher deposit). |

---

## Tier 2: Strong Supplementary Sources

These sources provide significant added value and should be included unless effort/complexity is prohibitive.

---

### 6. CORE (core.ac.uk)

| Attribute | Details |
|-----------|---------|
| **URL** | https://core.ac.uk/ |
| **API Docs** | https://api.core.ac.uk/docs/v3 |
| **Authentication** | Free registration recommended (faster rates). **We have an API key** |
| **Rate Limits** | Unregistered: 1 batch or 5 single requests per 10 seconds. Registered: faster (exact rate unlisted; contact for high-volume) |
| **Query Syntax** | REST API v3. Search by keyword, DOI, CORE ID. Boolean queries supported. Pagination via scrollId |
| **Data Fields** | title, authors, abstract, DOI, publication date, journal, full text (when available), download URL, repository source, language, topics, data providers |
| **Coverage** | 431 million metadata records, 323M free-to-read full text links, 46M full texts hosted. Open access focus. Thousands of repositories and journals worldwide |
| **Special Features** | Full text access (largest OA full-text collection), repository aggregation, CORE Discovery/Recommender, data provider metadata |
| **Recommendation** | **YES.** We already have an API key. Largest OA full-text collection. Useful for retrieving full text PDFs for content analysis. May find grey literature and repository-only papers not in other databases. |

---

### 7. Unpaywall

| Attribute | Details |
|-----------|---------|
| **URL** | https://unpaywall.org/products/api |
| **API Docs** | https://unpaywall.org/products/api |
| **Authentication** | Email address required as URL parameter |
| **Rate Limits** | 100,000 calls/day. Bulk data snapshot available for larger needs |
| **Query Syntax** | Simple DOI lookup: `api.unpaywall.org/v2/{DOI}?email=you@example.com`. No search endpoint -- DOI-based only |
| **Data Fields** | DOI, is_oa, oa_status (gold/green/hybrid/bronze), best_oa_location (URL, version, license), all oa_locations, journal_is_oa, journal_is_in_doaj, journal_issns, genre, authors |
| **Coverage** | All Crossref-DOI articles (~180M DOIs). 27+ million OA articles identified. 50,000+ OA content sources checked |
| **Special Features** | OA status classification, links to free full-text versions, embargo detection, version tracking (published/accepted/submitted) |
| **Recommendation** | **YES.** Not a discovery source (no search), but essential enrichment. Use DOIs collected from other sources to find OA full-text URLs. Critical for assessing open access landscape of our corpus. |

---

### 8. OpenCitations (COCI)

| Attribute | Details |
|-----------|---------|
| **URL** | https://opencitations.net/ |
| **API Docs** | https://api.opencitations.net/index/v2 |
| **Authentication** | None required |
| **Rate Limits** | 180 requests/minute per IP |
| **Query Syntax** | REST API. Query by DOI, PMID, ORCID, OMID, ISBN, ISSN. Endpoints for citations-to, references-from, citation metadata |
| **Data Fields** | OCI (Open Citation Identifier), citing/cited DOIs, creation date, timespan between citing and cited, journal_sc (self-citation flag), author_sc (self-citation flag) |
| **Coverage** | 624+ million citation links from Crossref reference data (open + limited sets) + DataCite |
| **Special Features** | Fully open citation data (CC0), SPARQL endpoint, self-citation detection, bulk downloads, citation timespan analysis |
| **Recommendation** | **YES.** Use for citation network enrichment. Complements Semantic Scholar and OpenAlex citation data with fully open, granular citation records. Self-citation detection is unique. |

---

### 9. arXiv

| Attribute | Details |
|-----------|---------|
| **URL** | https://arxiv.org/ |
| **API Docs** | https://info.arxiv.org/help/api/user-manual.html |
| **Authentication** | None required |
| **Rate Limits** | 1 request every 3 seconds. Single connection at a time. Max 30,000 results per query (2,000 per page) |
| **Query Syntax** | Atom-based API. Search fields: ti (title), au (author), abs (abstract), cat (category), all. Boolean: AND, OR, ANDNOT. Date range via submittedDate |
| **Data Fields** | arXiv ID, title, abstract, authors, categories, comment, journal_ref, DOI (if published), submission date, update date, PDF/HTML links |
| **Coverage** | ~2.4+ million preprints. Physics, math, CS, quantitative biology, statistics, economics, EE. Strong in cs.AI, cs.CL (LLM papers), cs.LG |
| **Special Features** | Preprint access before publication, full PDF access, category-based browsing, LaTeX source available |
| **Recommendation** | **YES.** Critical for capturing LLM preprints that may not yet be published. Many AI/healthcare simulation papers appear here first. Categories cs.AI, cs.CL, cs.HC are directly relevant. |

---

### 10. DOAJ (Directory of Open Access Journals)

| Attribute | Details |
|-----------|---------|
| **URL** | https://doaj.org/ |
| **API Docs** | https://doaj.org/api/v4/docs |
| **Authentication** | None for search/read. API key only for CRUD operations (journal/article management) |
| **Rate Limits** | 2 requests/second (bursts of 5 allowed). Search results capped at 1,000 records per query |
| **Query Syntax** | Elasticsearch-based. AND/OR/AND NOT (case sensitive). Field-specific: `bibjson.title:`, `bibjson.abstract:`, `bibjson.author.name:`, date ranges. JSON response |
| **Data Fields** | title, abstract, authors, DOI, journal title, ISSN, publisher, publication date, keywords, subject terms, license, language, full-text URL |
| **Coverage** | 21,480+ OA journals, 11+ million articles. All disciplines. Quality-vetted (peer-reviewed OA only) |
| **Special Features** | Quality assurance (vetted journals), journal-level metadata, license/OA policy info, subject classification |
| **Recommendation** | **YES.** Good for discovering OA articles and validating journal quality. The 1,000-record search cap requires careful query splitting. Useful as a supplementary source, not primary. |

---

### 11. Springer Nature API

| Attribute | Details |
|-----------|---------|
| **URL** | https://dev.springernature.com/ |
| **API Docs** | https://dev.springernature.com/docs/api-endpoints/metadata-api/ |
| **Authentication** | Free API key required (register at developer portal) |
| **Rate Limits** | Free tier: 100 requests/minute. Single API key per account |
| **Query Syntax** | REST API. Metadata API and Open Access API. Query by keyword, DOI, subject, date. Supports Boolean operators |
| **Data Fields** | title, abstract, authors, DOI, journal, publication date, publisher, ISSN/ISBN, subject, keywords, volume/issue/pages, URL, full text (OA subset) |
| **Coverage** | Metadata API: ~12 million documents (articles, book chapters, protocols). Open Access API: 460,000+ OA documents (BioMed Central, SpringerOpen) |
| **Special Features** | Full text for OA articles, publisher-authoritative metadata, Python wrapper (`sprynger`) |
| **Recommendation** | **YES.** Springer/Nature/BMC are major publishers in healthcare and simulation. Direct publisher metadata is high quality. OA full text access is a bonus. |

---

### 12. Lens.org

| Attribute | Details |
|-----------|---------|
| **URL** | https://www.lens.org/ |
| **API Docs** | https://docs.api.lens.org/ |
| **Authentication** | API token required. Free 14-day trial available. Academic users get fee-waived accounts (starting 2025) |
| **Rate Limits** | Trial: 5,000 API requests/month, 10 requests/minute, up to 1,000 records/request, up to 5M records/month |
| **Query Syntax** | REST API with JSON POST requests. Elasticsearch-based queries. Supports Boolean, field-level filters, date ranges, aggregations |
| **Data Fields** | title, abstract, authors + affiliations, DOI, PMID, date, source, fields of study, citations, references, patent citations, OA status, funding, MeSH terms |
| **Coverage** | 272+ million scholarly works. Sources: Crossref, PubMed, OpenAlex, Unpaywall, CORE. 155M+ patents |
| **Special Features** | Patent-to-literature linking, scholarly-patent citation analysis, aggregated from multiple sources, bulk export |
| **Recommendation** | **MAYBE.** Powerful but API access is more restricted (trial/academic application). Web search is freely available without login. If we can get academic access, useful for cross-validation and patent-to-literature analysis. Lower priority than OpenAlex which covers similar ground freely. |

---

### 13. DBLP

| Attribute | Details |
|-----------|---------|
| **URL** | https://dblp.org/ |
| **API Docs** | https://dblp.org/faq/How+to+use+the+dblp+search+API.html |
| **Authentication** | None required |
| **Rate Limits** | Not explicitly documented. Excessive requests return HTTP 429 with `Retry-After` header. Keep to "reasonable" rate |
| **Query Syntax** | REST API. Publication search: `https://dblp.org/search/publ/api?q=QUERY&format=json`. Author search, venue search also available. Simple keyword queries |
| **Data Fields** | title, authors, year, venue (journal/conference), pages, DOI, URL, type, key (DBLP identifier) |
| **Coverage** | 6.5+ million publications, 3+ million authors. Computer science focused. 50,000+ journal volumes, 50,000+ proceedings volumes |
| **Special Features** | CC0 open data, comprehensive CS conference coverage, author disambiguation, venue normalization |
| **Recommendation** | **YES.** Essential for CS conference papers on LLMs/AI that may not appear in PubMed or medical databases. Covers NeurIPS, ACL, AAAI, CHI, AMIA, etc. Computer science simulation papers will be here. |

---

## Tier 3: Niche / Conditional Sources

Include these if time/resources allow, or if initial collection reveals gaps.

---

### 14. medRxiv / bioRxiv

| Attribute | Details |
|-----------|---------|
| **URL** | https://api.biorxiv.org/ / https://api.medrxiv.org/ |
| **API Docs** | https://api.biorxiv.org/pubs/help |
| **Authentication** | None required |
| **Rate Limits** | Not explicitly documented. Results paginated at 100 per call |
| **Query Syntax** | REST API. Endpoints for: content by date range, detail by DOI, published linkage. Date range: `/details/[server]/[start]/[end]/[cursor]`. DOI lookup: `/pubs/[server]/[DOI]/na/[format]` |
| **Data Fields** | biorxiv_doi, published_doi, published_journal, title, authors, corresponding author, category, preprint_date, published_date, abstract |
| **Coverage** | 180,000+ preprints combined (as of late 2022; growing). medRxiv: health/clinical science. bioRxiv: biology/life sciences |
| **Special Features** | Preprint-to-publication linkage, health sciences preprints (medRxiv), no peer-review delay |
| **Recommendation** | **YES.** medRxiv specifically covers health sciences preprints. Healthcare simulation papers may appear here before journal publication. Already partly covered via Europe PMC, but direct API gives complete preprint metadata. |

---

### 15. Dimensions

| Attribute | Details |
|-----------|---------|
| **URL** | https://www.dimensions.ai/ |
| **API Docs** | https://docs.dimensions.ai/dsl/ |
| **Authentication** | Free access requires application + approval for non-commercial scientometric research. Must describe project, intend to publish, non-commercial use |
| **Rate Limits** | Determined upon approval. DSL (Dimensions Search Language) queries |
| **Query Syntax** | Proprietary DSL. `search publications where ... return publications`. Supports Boolean, field filters, facets, aggregations |
| **Data Fields** | title, abstract, authors + affiliations + ORCID, DOI, journal, date, type, citations, references, grants/funding, clinical trials, patents, policy documents, altmetrics, field of research codes, open access status |
| **Coverage** | 140+ million publications, plus grants, patents, clinical trials, policy documents, datasets |
| **Special Features** | Cross-entity linking (papers-grants-patents-trials-policy), Altmetric integration, clinical trial linkage, Google BigQuery access, comprehensive funding data |
| **Recommendation** | **MAYBE.** Excellent for bibliometric analysis but requires application (up to 1 month). If we apply now and get approved, the grant/clinical trial linkage is uniquely valuable for healthcare simulation. Worth applying but do not depend on it for timeline. |

---

### 16. Elsevier/Scopus API

| Attribute | Details |
|-----------|---------|
| **URL** | https://dev.elsevier.com/ |
| **API Docs** | https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl |
| **Authentication** | Free API key required. Full access requires institutional Scopus subscription. Limited "BASIC" view for non-subscribers |
| **Rate Limits** | 20,000 requests per 7 days (default). Throttling varies by endpoint |
| **Query Syntax** | REST API. Scopus Search API, Abstract Retrieval API. Supports Boolean, field codes (TITLE, ABS, KEY, AUTH, AFFIL), date ranges, subject areas |
| **Data Fields** | Non-subscribers (BASIC view): title, authors, DOI, source, date, document type. Subscribers: + abstract, keywords, affiliations, citation count, references, subject areas, ASJC codes, funding |
| **Coverage** | 90+ million records. 27,000+ journals. Strong multidisciplinary coverage, especially strong in health sciences and engineering |
| **Special Features** | ASJC subject classification, Scopus Source List (journal quality), Author/Affiliation profiles, citation metrics |
| **Recommendation** | **MAYBE.** If we have institutional access, Scopus is a gold standard for bibliometric analysis. Without it, the BASIC view returns limited metadata (no abstracts). Check if we have institutional access. If yes, promote to Tier 1. |

---

### 17. IEEE Xplore API

| Attribute | Details |
|-----------|---------|
| **URL** | https://developer.ieee.org/ |
| **API Docs** | https://developer.ieee.org/docs |
| **Authentication** | Free API key required (registration + application description + organization URL). Keys issued during business hours |
| **Rate Limits** | Not publicly documented. Max 200 results per query. Max 10 words per query term |
| **Query Syntax** | REST API returning XML. Simple and Boolean search. Field-specific queries supported |
| **Data Fields** | title, abstract, authors, DOI, publication title, date, document type (journal/conference/book), keywords, INSPEC controlled terms |
| **Coverage** | 6+ million documents. Journals, conference proceedings, books, standards. IEEE and IET publications. Strong in engineering, CS, technology |
| **Special Features** | IEEE/IET conference proceedings (many simulation papers), standards documents, INSPEC indexing |
| **Recommendation** | **MAYBE.** IEEE publishes key simulation and CS/engineering journals. However, many IEEE papers are already indexed by OpenAlex, Semantic Scholar, and Crossref. Use if initial collection shows gaps in IEEE conference proceedings specifically. |

---

### 18. Web of Science Starter API (Clarivate)

| Attribute | Details |
|-----------|---------|
| **URL** | https://developer.clarivate.com/apis/wos-starter |
| **API Docs** | https://developer.clarivate.com/apis/wos-starter |
| **Authentication** | Free API key via Clarivate Developer Portal |
| **Rate Limits** | Free plan: 50 requests/day. Subscriber plan: 5,000/day. Institutional: 20,000/day |
| **Query Syntax** | REST API. Query by DOI, author, source title, publication year, etc. |
| **Data Fields** | Free plan: bibliographic metadata (DOI, authors, source title, year). Does NOT return times-cited on free plan. Subscriber plan adds citation counts |
| **Coverage** | Web of Science Core Collection (~90M records across SCIE, SSCI, A&HCI, ESCI, CPCI) |
| **Special Features** | Journal Impact Factor linkage (subscriber), WoS categories/subject areas, conference proceedings indexing |
| **Recommendation** | **MAYBE.** 50 requests/day is very restrictive for collection. Useful for validation/enrichment rather than discovery. If we have WoS institutional access, much more valuable. Without it, low priority. |

---

### 19. BASE (Bielefeld Academic Search Engine)

| Attribute | Details |
|-----------|---------|
| **URL** | https://www.base-search.net/ |
| **API Docs** | https://api.base-search.net/ |
| **Authentication** | IP address whitelisting required. Must contact BASE and describe use case |
| **Rate Limits** | Not publicly documented. Access-controlled |
| **Query Syntax** | HTTP-based search interface. Structured queries supported |
| **Data Fields** | title, authors, abstract, DOI, URL, document type, subject, language, data provider, OA status |
| **Coverage** | 400+ million documents from 12,000+ content providers. Strong in institutional repository content |
| **Special Features** | Institutional repository aggregation, OA content focus, multilingual content |
| **Recommendation** | **NO.** IP whitelisting requirement adds friction. Coverage largely overlaps with CORE and OpenAlex. Not worth the setup effort for marginal gain. |

---

### 20. OpenAIRE

| Attribute | Details |
|-----------|---------|
| **URL** | https://explore.openaire.eu/ |
| **API Docs** | https://graph.openaire.eu/docs/apis/home/ |
| **Authentication** | None for basic access (60 req/hour). Free registration for higher limits (7,200 req/hour) |
| **Rate Limits** | Unauthenticated: 60 requests/hour. Authenticated: 7,200 requests/hour. Max 15 req/sec. Max 37 concurrent requests. Query results limited to ~10,000 paged |
| **Query Syntax** | REST API. Search by keyword, DOI, project. Pagination via resumption token. OAI-PMH also available |
| **Data Fields** | title, authors, abstract, DOI, date, source, type, project/funding info, access rights, OA status, data provider |
| **Coverage** | Hundreds of millions of records. EU research focus. Aggregates from institutional repositories, journals, data repositories. Links to EU-funded project data |
| **Special Features** | EU funding/project linkage (Framework Programmes, Horizon), pan-European repository aggregation, research data linking |
| **Recommendation** | **MAYBE.** Useful if we want EU funding analysis or European repository-specific content. Coverage overlaps significantly with OpenAlex and CORE. Only include if EU-specific analysis is desired. |

---

### 21. Wiley TDM API

| Attribute | Details |
|-----------|---------|
| **URL** | https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining |
| **API Docs** | Documentation available via Wiley developer resources |
| **Authentication** | API token required. Academic subscribers: free TDM license for subscribed content. Also: Federated Search API (SRU, free) |
| **Rate Limits** | Not publicly documented |
| **Query Syntax** | TDM API for full-text PDF download. Federated Search API uses SRU (Search/Retrieval via URL) protocol |
| **Data Fields** | Via Crossref: full bibliographic metadata. Via TDM: full text PDFs for subscribed content |
| **Coverage** | Wiley journal content (~1,700 journals) |
| **Special Features** | Full-text PDF download for TDM, Python client package (pip installable) |
| **Recommendation** | **NO for discovery.** Wiley papers are already discoverable via Crossref, OpenAlex, Scopus. Only relevant if we need full-text PDFs of Wiley articles specifically, and have institutional subscription. |

---

### 22. ACM Digital Library

| Attribute | Details |
|-----------|---------|
| **URL** | https://dl.acm.org/ |
| **API Docs** | No documented public API for metadata search |
| **Authentication** | N/A (no public API) |
| **Rate Limits** | N/A |
| **Query Syntax** | Web search only. No programmatic API documented |
| **Data Fields** | N/A |
| **Coverage** | ACM publications (CS/IT focused journals and proceedings) |
| **Special Features** | ACM Computing Classification System |
| **Recommendation** | **NO.** No public API available. ACM papers are already indexed by DBLP, OpenAlex, Semantic Scholar, and Crossref. Manual web search not needed. |

---

### 23. SSRN

| Attribute | Details |
|-----------|---------|
| **URL** | https://www.ssrn.com/ |
| **API Docs** | No documented public API |
| **Authentication** | N/A |
| **Rate Limits** | N/A |
| **Query Syntax** | Web search only. SSRN preprint DOIs are in Crossref |
| **Data Fields** | Via Crossref: basic metadata. Web: title, abstract, authors, download counts, keywords |
| **Coverage** | Preprints in social sciences, law, economics, some health/management |
| **Special Features** | Preprint repository for social sciences |
| **Recommendation** | **NO.** No API. Limited relevance to LLM/healthcare simulation (more social science focused). Any relevant SSRN papers with DOIs will appear in Crossref/OpenAlex. |

---

### 24. ClinicalTrials.gov

| Attribute | Details |
|-----------|---------|
| **URL** | https://clinicaltrials.gov/ |
| **API Docs** | https://clinicaltrials.gov/data-api/api |
| **Authentication** | None required |
| **Rate Limits** | Not documented (generous for typical research use) |
| **Query Syntax** | REST API v2.0 (OpenAPI 3.0). Search by condition, intervention, keyword, status, date, etc. |
| **Data Fields** | Study title, description, conditions, interventions, outcomes, sponsors, study design, enrollment, dates, status, publications linked |
| **Coverage** | 400,000+ registered clinical studies worldwide |
| **Special Features** | Clinical trial metadata, intervention descriptions, study design details |
| **Recommendation** | **NO for bibliometric analysis.** This is a clinical trials registry, not a publication database. Not directly relevant to our paper-focused bibliometric analysis. Could be tangentially useful if analyzing whether LLM simulation research has led to clinical trials, but out of scope. |

---

## Tier 4: Not Recommended / Unavailable

---

### 25. Microsoft Academic (Graph)

| Attribute | Details |
|-----------|---------|
| **Status** | **DISCONTINUED.** Retired December 31, 2021 |
| **Successor** | OpenAlex (built on MAG data) |
| **Recommendation** | **NO.** Dead service. Use OpenAlex instead, which was built as its replacement and has expanded far beyond MAG's original coverage. |

---

### 26. Google Scholar

| Attribute | Details |
|-----------|---------|
| **Status** | **NO official API.** Google Scholar provides no programmatic API |
| **Workarounds** | Third-party scraping services exist (SerpAPI $75+/mo, Scrapingdog, ScrapingBee) but all are paid and violate Google TOS |
| **Recommendation** | **NO.** No free API. Scraping violates TOS and is unreliable. Google Scholar content is almost entirely covered by OpenAlex, Semantic Scholar, and Crossref combined. Not worth the cost or legal risk. |

---

## Summary Decision Matrix

| # | Source | Free? | Auth Needed? | Coverage (M) | Healthcare? | LLM/AI? | Rate Limit | Recommendation |
|---|--------|-------|-------------|--------------|-------------|---------|------------|----------------|
| 1 | **OpenAlex** | Yes | Free API key | 271M | Good | Excellent | 100K/day | **YES** |
| 2 | **PubMed** | Yes | Free API key | 40M | Excellent | Limited | 10/sec | **YES** |
| 3 | **Semantic Scholar** | Yes | Optional | 225M | Good | Excellent | 5K/5min | **YES** |
| 4 | **Europe PMC** | Yes | None | 43M | Excellent | Limited | ~10/sec | **YES** |
| 5 | **Crossref** | Yes | None (mailto) | 180M | Good | Good | ~50/sec | **YES** |
| 6 | **CORE** | Yes | We have key | 431M | Fair | Fair | 5/10sec | **YES** |
| 7 | **Unpaywall** | Yes | Email param | 180M (DOIs) | N/A (OA lookup) | N/A | 100K/day | **YES** (enrichment) |
| 8 | **OpenCitations** | Yes | None | 624M citations | N/A (citations) | N/A | 180/min | **YES** (enrichment) |
| 9 | **arXiv** | Yes | None | 2.4M | Limited | Excellent | 1/3sec | **YES** |
| 10 | **DOAJ** | Yes | None | 11M | Fair | Limited | 2/sec | **YES** |
| 11 | **Springer Nature** | Yes | Free API key | 12M | Good | Fair | 100/min | **YES** |
| 12 | **Lens.org** | Trial/Academic | Token | 272M | Good | Good | 10/min (trial) | **MAYBE** |
| 13 | **DBLP** | Yes | None | 6.5M | None | Excellent | Reasonable | **YES** |
| 14 | **medRxiv/bioRxiv** | Yes | None | 180K+ | Excellent | Growing | Not documented | **YES** |
| 15 | **Dimensions** | Application | Approved key | 140M | Excellent | Good | TBD | **MAYBE** |
| 16 | **Scopus/Elsevier** | Partial | API key | 90M | Excellent | Good | 20K/7 days | **MAYBE** |
| 17 | **IEEE Xplore** | Yes | API key | 6M | Limited | Good | Not documented | **MAYBE** |
| 18 | **WoS Starter** | Yes | API key | 90M | Good | Good | 50/day (free) | **MAYBE** |
| 19 | **BASE** | IP whitelist | Contact required | 400M | Fair | Fair | Not documented | **NO** |
| 20 | **OpenAIRE** | Yes | Optional | 100M+ | Fair | Fair | 60/hour (unauth) | **MAYBE** |
| 21 | **Wiley TDM** | Subscription | Token | N/A | Fair | Limited | Not documented | **NO** |
| 22 | **ACM DL** | N/A | N/A | N/A | None | Good | N/A | **NO** |
| 23 | **SSRN** | N/A | N/A | N/A | Limited | Limited | N/A | **NO** |
| 24 | **ClinicalTrials.gov** | Yes | None | 400K trials | Excellent | None | Generous | **NO** (not papers) |
| 25 | **Microsoft Academic** | Discontinued | N/A | N/A | N/A | N/A | N/A | **NO** |
| 26 | **Google Scholar** | No API | N/A | N/A | N/A | N/A | N/A | **NO** |

---

## Recommended Collection Pipeline Order

Based on coverage, data quality, rate limits, and relevance to "Large Language Models in Healthcare Simulation":

### Phase 1: Primary Discovery (Run in parallel where possible)

1. **OpenAlex** -- Broadest single sweep. Search `title_and_abstract.search:"large language model" AND title_and_abstract.search:"healthcare simulation"` plus variant queries. Collect all candidate papers with full metadata.

2. **PubMed** -- Healthcare-specific sweep. Use MeSH terms for controlled vocabulary searching. Captures medical/nursing/simulation papers that may use different terminology.

3. **Semantic Scholar** -- AI/CS-weighted sweep. Good for catching CS-venue papers. Collect citation data and TLDR summaries.

4. **Europe PMC** -- Superset of PubMed with preprints and European content. Capture text-mined annotations.

### Phase 2: Targeted Discovery (Fill gaps)

5. **arXiv** -- Preprint sweep for cs.AI, cs.CL, cs.HC categories. Catches unpublished LLM papers.

6. **DBLP** -- CS conference proceedings sweep. Catches NeurIPS, ACL, AAAI, CHI workshop papers.

7. **medRxiv/bioRxiv** -- Health preprint sweep. Catches in-progress healthcare simulation research.

8. **DOAJ** -- OA journal sweep. May find OA-only journals not fully indexed elsewhere.

9. **Springer Nature** -- Publisher-specific sweep for BMC, Nature-affiliated journals.

### Phase 3: Enrichment (DOI-based lookups on collected corpus)

10. **Crossref** -- Standardize metadata, get reference lists, verify DOIs.

11. **Unpaywall** -- Get OA status and full-text links for every DOI in corpus.

12. **OpenCitations** -- Build citation network from DOIs in corpus.

13. **CORE** -- Attempt full-text retrieval for papers in corpus.

### Phase 4: Conditional (If approved/accessible)

14. **Dimensions** -- Apply for free scientometric access. If approved, use for grant/funding analysis and cross-validation.

15. **Scopus** -- If institutional access available, use for validation and ASJC subject codes.

16. **Lens.org** -- If academic access granted, use for cross-validation.

---

## Key Observations

1. **No single API is sufficient.** The comparative literature confirms that combining 2+ APIs is necessary for comprehensive bibliometric analysis. Our topic spans healthcare (PubMed-indexed) and AI/CS (arXiv/DBLP-indexed), making multi-source collection essential.

2. **OpenAlex is the best starting point.** 271M works, free, excellent API, and successor to Microsoft Academic. But it may miss very recent preprints and some niche repository content.

3. **Deduplication is critical.** Most sources will return overlapping papers. DOI-based deduplication should be the primary strategy, supplemented by title/author fuzzy matching for DOI-less records.

4. **Our topic is inherently cross-disciplinary.** "LLMs in healthcare simulation" spans:
   - Medical education (PubMed, Europe PMC)
   - Computer science / AI (Semantic Scholar, arXiv, DBLP)
   - Nursing / allied health (PubMed, DOAJ)
   - Engineering / simulation (IEEE, Springer)
   - General multidisciplinary (OpenAlex, Crossref)

5. **Rate limits are manageable.** For a focused bibliometric analysis (likely <10,000 relevant papers), even the strictest rate limits (arXiv: 1/3sec, DOAJ: 2/sec) are workable with simple throttling.

6. **Abstract availability varies.** OpenAlex stores abstracts as inverted indexes (reconstructible). Crossref abstract coverage depends on publisher deposits (~50-60%). PubMed has abstracts for most indexed articles. Plan for some records having no abstract.

---

*Report compiled 2026-03-22. API documentation and rate limits should be verified at time of implementation as they may change.*
