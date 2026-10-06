# Autonomy and Data Sources

## Product direction

The desired normal workflow is **zero manual per-company data collection**.

The user should not have to:

- upload 100 annual reports
- prepare financial-history spreadsheets company by company
- manually collect ratios for every finalist
- manually find concall transcripts or rating reports

When information is missing, the system should create a research/data-acquisition task.

## Current data paths

### Historical methodology

Screener screen exports/crawling teach the system the user's historical screening logic.

### Candidate result snapshots

Screener result XLSX/CSV can be imported and the app preserves available ratios instead of discarding them.

### Multi-period financial enrichment

`screener_auto_financials.py` can use a logged-in Chrome session to resolve company pages and retrieve historical financial tables for candidate companies.

### Research documents

V4/V4.5 supports direct uploads, direct URL manifests, autonomous web discovery and prioritized fetching.

### Search

Brave Search is currently the implemented discovery adapter when `BRAVE_SEARCH_API_KEY` is configured. The provider is replaceable.

## Source hierarchy

Preferred order:

1. Exchange / regulatory / company primary material
2. Credit-rating agencies and other authoritative sources
3. Company investor-relations pages
4. Reputable secondary financial/business sources
5. General web material when needed for context

Primary-source location does not mean every management claim is independently verified. The evidence model keeps **facts, management claims, risks and inferences distinct**.

## Optional local crawler

`ENABLE_LOCAL_CRAWLER=false` by default.

When enabled, the fallback is intentionally constrained and should be used only where permitted:

- local research
- robots-aware
- rate limited
- non-recursive / narrow document-link extraction

## Remaining autonomy gap

The biggest front-of-pipeline gap is a provider-independent **Market Data & Screening Gateway** that will:

- acquire the listed-stock universe
- resolve identifiers
- obtain canonical current and historical ratios
- execute V2 master strategies locally
- feed V3 without requiring a Screener result export

Screener should ultimately remain an optional adapter/fallback rather than the only way to execute filters.
