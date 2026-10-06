# Strategic Review Checkpoint

This document intentionally freezes the product state after the Company Research Engine milestone.

The next development session should begin with a strategic review before adding new roadmap layers.

---

## Product thesis at this checkpoint

**Personal AI Equity Research Operating System**

Autonomous by default. Evidence-driven. Investor-controlled. Self-challenging.

The product is not intended to compete by merely displaying more ratios or adding generic AI chat over filings.

Its intended differentiation is the full loop:

1. learn the investor's historical screening philosophy;
2. generate editable/versioned strategies;
3. execute screening autonomously;
4. preserve exact company identity and source provenance;
5. allow operator review before every expensive stage;
6. collect financial history automatically;
7. conduct evidence-backed company research;
8. expose source gaps and unknowns;
9. progressively allocate deeper research effort;
10. independently challenge bullish ideas with a Bear researcher;
11. later connect evidence, valuation, conviction, ranking and portfolio construction;
12. keep a living research memory over time.

---

## What is solid enough to retain

### Methodology intelligence

- historical-screen import/crawling path
- parameter normalization
- threshold analysis
- co-occurrence intelligence
- strategy provenance
- seven master strategy philosophies

### Investor strategy control

- generated philosophy preserved separately from user edits
- strategy enable/disable
- query editing
- philosophy/purpose editing
- notes
- profile import/export
- preview workflow

### Screening POC

- logged-in local Screener adapter
- dedicated worker browser tab
- result-table parsing
- pagination
- exact company href capture
- visible ratios retained
- configurable Screener pacing delay

### Candidate control

- deduplication
- strategy overlap
- manual include/exclude
- minimum strategy overlap
- cap on next-stage company count

### Financial research

- automatic company-page financial collection
- current ratios + multi-period history
- growth/trend/CAGR support
- evidence-coverage guardrail
- explicit DATA_RETRY for insufficient data
- investor-readable financial decision view
- operator override before expensive research

### Research-run architecture

- persistent ResearchRun
- persistent CompanyResearch
- research log/events
- stage summaries
- decision history
- backward-compatible persisted runs

### Product constitution

- PRODUCT_CONSTITUTION.md
- INVESTOR_OUTLOOK.md
- FUNDAMENTAL_RESEARCH_ANALYST_PLAYBOOK.md
- DIFFERENTIATION_AND_COMPETITIVE_MAP.md
- RESEARCH_STAGE_CONTRACTS.md
- OPERATOR_CONTROL.md

### Company Research Engine

- explicit analyst missions
- source discovery from exact company page
- optional broader source discovery
- source authority scoring
- source queue limits
- source-attempt ledger
- fetch success/failure visibility
- deterministic evidence extraction
- optional semantic LLM extraction
- investor dossier
- SOURCE_GAP / RESEARCH_INCOMPLETE / EVIDENCE_READY states
- explicit open questions and next action
- configurable company retry / source breadth / quality threshold

---

## What is partial and must be challenged

### Screener as a data source

Screener is only the POC adapter.

Questions:

- Is the workflow useful enough to justify first-class NSE/BSE adapters?
- Which data should be sourced directly from exchanges vs company IR vs commercial providers?
- What identifiers become the permanent master identity: NSE symbol, ISIN, BSE code?

### Financial analysis model

Current financial scoring is useful for prioritization but is still generic.

Questions:

- Should banks/NBFCs/insurance/utilities/commodities use separate financial models?
- Which dimensions should be hard gates vs context-dependent?
- Should ranking use absolute thresholds, sector-relative percentiles or historical self-comparison?

### Company research source coverage

The engine now makes source gaps visible, but source acquisition is still POC-level.

Questions:

- Can we reliably acquire annual reports, results, presentations, transcripts, ratings and filings for most Indian listed companies?
- Should source freshness matter more than raw document count?
- How should company-IR and exchange documents outrank third-party mirrors?

### Evidence quality

Deterministic keyword extraction is deliberately conservative but shallow.

Questions:

- Where does semantic extraction materially improve decisions?
- How do we distinguish facts, accounting disclosures, management claims and analyst inference?
- How do we detect contradictions across periods/documents?

### Research depth

The progressive research funnel exists conceptually and in code, but should not be trusted blindly until the Company Research Engine produces reliable evidence coverage.

Questions:

- What is the correct transition criterion from broad research to deep research?
- Should a strong company with missing evidence be held back or actively retried?
- How much research budget should depend on financial attractiveness vs uncertainty?

### Bull/Bear research

The adversarial architecture exists, but it should only operate after evidence quality is high enough.

Questions:

- Are the Bull and Bear researchers genuinely independent?
- Does the neutral challenge layer punish unsupported narrative?
- How should unresolved contradictions influence later conviction?

---

## What is deliberately not built yet

Do not continue automatically into these items before the strategic review:

- final evidence-confidence engine
- valuation intelligence
- conviction engine
- final ranking
- ₹1L portfolio construction
- continuous monitoring
- learning engine
- autonomous trading

These are downstream consequences of research quality. Building them before validating the research foundation would create false precision.

---

## Strategic review questions

The next session should challenge the following in order.

### 1. Is the user journey genuinely high value?

Can a serious investor go from philosophy → candidates → financial review → company dossier with substantially less manual effort while retaining control?

### 2. Where is the unique value?

Which portions are commodity features already available in Screener, Trendlyne, TIKR, AlphaSense or similar tools?

Which 2–3 workflows are genuinely differentiated enough to become the product's core?

### 3. What should the product refuse to do?

Examples:

- hide uncertainty behind scores;
- advance companies with weak evidence merely to fill a funnel quota;
- hallucinate missing research;
- infer a moat directly from a high ROCE;
- treat management guidance as fact;
- optimize for feature count over research usefulness.

### 4. What is the correct source architecture?

Define a durable provider interface for:

- identity/master data;
- financial statements;
- prices/market data;
- exchange filings;
- company IR;
- transcripts;
- ratings;
- news / industry context.

### 5. What does a truly excellent company dossier look like?

Before implementing valuation, define the research artifact an experienced fundamental analyst would trust.

### 6. What should be measured?

Possible product-quality measures:

- percentage of candidates with exact identity;
- financial evidence coverage;
- authoritative-source coverage;
- research mission coverage;
- unresolved critical questions;
- source freshness;
- management promise/delivery accuracy;
- time saved vs manual research;
- investor override frequency;
- thesis changes after Bear review.

### 7. Is the research funnel correctly shaped?

Validate actual run sizes rather than assuming 100 → 50 → 25 → 15.

Research depth should follow evidence and opportunity, not arbitrary fixed quotas.

---

## Acceptance test before moving beyond strategic review

Run one real end-to-end research experiment on a manageable company set.

Recommended:

1. 1–2 tuned strategies;
2. 20–40 resulting companies;
3. operator review → 10–20 financial analyses;
4. operator review → 5–10 company research dossiers;
5. inspect source-attempt ledger and evidence manually;
6. compare at least 2–3 dossiers with a human fundamental-research review;
7. record what the system missed, misunderstood or made easier.

Only then decide what deserves the next major engineering investment.

---

## Current development rule

**No new intelligence layer should be considered complete unless it improves an investor-visible research artifact and satisfies the product constitution.**
