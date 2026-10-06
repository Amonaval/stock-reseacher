# Product Roadmap

## North star

Build an autonomous, explainable Indian-equity research system that can progress from a broad universe to a small ranked portfolio proposal without requiring the user to manually assemble per-company data.

## Completed foundation

### V1 — Methodology Miner ✅

Learn the user's historical screening language from saved Screener screens.

### V1.1 — Trusted Screen Universe ✅

Allow imported screens, selected Screener users, or combined datasets without contaminating the methodology with unrelated public screens.

### V1.2 — Methodology Intelligence ✅

Thresholds, relative rules, co-occurrence, archetypes, duplicates and Investment DNA.

### V2 — Strategy Intelligence ✅

Generate reusable master strategy families with provenance.

### V2.1 — Candidate Universe ✅

Combine strategy results, deduplicate stocks, retain overlap/provenance and source ratios.

### V3 — Financial Intelligence ✅

Normalize financials, calculate trends/CAGRs, score growth/quality/balance-sheet/cash-flow/ownership/valuation and penalize missing data.

### V4 — Company Research Agent ✅

Build source-linked evidence memory from reports, results, presentations, calls, filings and rating material.

### V4.5 — Autonomous Source Acquisition + Orchestrator ✅

Discover/fetch sources, identify research gaps and decide what each company needs next.

### V5 — Autonomous Deep Research Funnel ✅

Allocate increasing research depth to decreasing company counts with a full narrowing audit.

### V6 — Bull/Bear Adversarial Research ✅

Independent opposing theses, contradiction review, thesis fragility and unresolved questions.

### V6.1 — Autonomous V3 Enrichment ✅

Use strategy-result snapshot ratios immediately and automatically enrich candidate companies with multi-period Screener financial history instead of asking the user for per-company financial spreadsheets.

---

## Next autonomy milestone

### V6.2 — Autonomous Market Data & Screening Gateway ⏭️

Remove the remaining normal-flow requirement for the user to execute master queries in Screener and export results.

Build a provider-independent gateway that:

- acquires the Indian listed-equity universe
- resolves canonical identifiers (NSE/BSE/company)
- fetches current and historical financial metrics
- evaluates V2 strategy expressions locally
- builds the candidate universe automatically
- uses Screener as an optional adapter/fallback, not a hard dependency

Target user experience:

```text
[ Start Full Research ]
        ↓
Market-data gateway
        ↓
Run 5–7 strategies
        ↓
Candidate universe
        ↓
V3→V6 pipeline automatically
```

---

## Remaining intelligence layers

### V7 — Evidence & Confidence Engine

- source authority / recency
- cross-source corroboration
- fact vs management claim vs inference
- contradiction severity
- evidence coverage by thesis dimension
- confidence calibration

### V8 — Valuation Intelligence

- current vs historical valuation
- peer/industry valuation
- growth-adjusted valuation
- simple scenario/value ranges
- entry attractiveness separated from business quality

### V9 — Conviction Engine

Combine business, financial, management, risk, evidence and valuation dimensions into an explainable conviction model.

### V10 — Final Ranking

Rank finalists while preserving the underlying dimensional scorecard and uncertainty.

### V11 — ₹1 Lakh Portfolio Constructor

Position sizing should consider:

- conviction
- valuation attractiveness
- downside/fragility
- liquidity
- diversification / correlation

The highest-ranked business does not automatically receive the largest allocation.

### V12 — Continuous Monitoring

Watch new results, filings, management changes, credit events, thesis-invalidating metrics and material price/valuation changes.

### V13 — Outcome Learning

Compare historical theses with later reality:

- what was predicted?
- what actually happened?
- which signals were useful?
- which management claims were delivered?
- where did valuation assumptions fail?

Use this to improve research prioritization without blindly fitting to price performance.
