# Consolidated End-User Workflow

This document describes the post-consolidation product flow. The application is no longer intended to expose V1/V2/V3/V4/V5/V6 as separate user-operated products. Those are internal research capabilities.

## Normal user journey

```text
Connect logged-in Screener browser
        ↓
Discover/select historical screens/users
        ↓
Analyze methodology
        ↓
Prepare master strategies
        ↓
Run enabled strategies automatically
        ↓
Crawl result pagination
        ↓
Capture exact company href + visible ratios
        ↓
Build unique candidate universe
        ↓
Collect multi-period company financials automatically
        ↓
Coverage-aware preliminary financial assessment
        ↓
Discover/fetch company research sources automatically
        ↓
Build source-linked evidence memory
        ↓
Allocate progressively deeper research
        ↓
Independent Bull/Bear challenge for evidence-ready companies
```

Manual CSV/XLSX/document upload remains available only as a debug/recovery path.

## Why exact company URLs matter

The normal screening path captures the company link directly from the Screener result table. That URL is stored in `CompanyResearch.screener_url` and reused by financial and research stages.

This prevents a common failure mode where a company such as `Travel Food` is unnecessarily resolved through:

```text
/company/search/?q=Travel%20Food
```

Search is only a fallback when identity data is genuinely absent.

The debug XLSX importer also preserves a hyperlink attached to the company-name cell using `openpyxl`; pandas alone does not preserve those hyperlink targets.

## Candidate Universe

Candidate Universe means:

> all unique companies that matched at least one enabled master strategy.

The stage deduplicates overlapping strategy results while retaining:

- exact company URL
- matched strategy IDs/names
- visible result-table ratios
- source/provenance
- internal research-priority metadata

Strategy overlap is a research-order signal, not investment conviction.

## Financial stage

The user should not prepare a second financial-history spreadsheet.

The system:

1. starts with the ratios already captured by screening,
2. reuses the exact company URL,
3. retrieves multi-period P&L / balance sheet / cash-flow / ratio history from the logged-in Screener POC adapter,
4. normalizes the history,
5. calculates trends/CAGRs where supported,
6. produces an evidence-coverage-aware decision.

User-facing decisions are:

- `ADVANCE`
- `WATCHLIST`
- `DATA_RETRY`
- `HOLD`
- `ELIMINATE`

A numerical score is only an internal ordering aid. Missing dimensions lower coverage and cannot silently become a confident pass.

## Research stage

For financial survivors, the system looks for research documents without asking the user to upload them.

Initial POC discovery sources:

- links exposed on the exact Screener company page
- optional configured web-search provider

Research material can include annual reports, results, investor presentations, earnings-call transcripts, exchange filings, and credit-rating material.

Every extracted evidence item retains source/document/page metadata when available.

## Research log

Every `ResearchRun` stores events such as:

- strategy started/completed
- result counts
- exact URL capture counts
- financial collection status
- financial decision and reason
- source discovery status
- documents/evidence collected
- research-depth decision
- Bull/Bear challenge outcome

The product should answer not only **what survived**, but **what work was performed and why the list narrowed**.

## Research-depth planning

Research-depth stages are evidence gates, not stock ratings:

- `SOURCE_GAP`
- `STRUCTURED`
- `TARGETED`
- `DEEP`
- `ADVERSARIAL`
- `RESEARCH_QUEUE`

Research budgets limit how many companies receive expensive work. A queued/held company remains in the research run and can be revisited.

## Bull/Bear challenge

Only companies with enough source/evidence coverage are sent to independent Bull and Bear research.

The output is a research state such as contested/fragile/bull-case-survives/bear-case-dominates. It is not a buy/sell recommendation and not expected-return probability.

## Provider architecture

Screener is an initial POC adapter, not the permanent data architecture.

The intended future design is provider-independent:

```text
ScreeningProvider
MarketDataProvider
ResearchSourceProvider
```

Screener can then be supplemented or replaced by NSE/BSE and other data systems without rewriting the research intelligence layer.
