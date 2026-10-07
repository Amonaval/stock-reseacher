# User Guide — Personal AI Stock Researcher

This guide is written for the end user, not for the developer.

## The simplest way to use the app

Use **Guided Research** for the normal workflow. Follow the six numbered steps from top to bottom.

You do not need to understand internal version names, JSON objects, research engines or data-model details.

The normal flow is:

```text
1. Connect & prepare strategies
        ↓
2. Screen the market
        ↓
3. Check financial quality
        ↓
4. Research the business
        ↓
5. Allocate deeper research
        ↓
6. Challenge the thesis
```

The home page always shows a **Next recommended action** so you know what to do next.

---

## What each step does

### 1. Connect & prepare strategies

Purpose: define what kinds of companies you want the researcher to look for.

You can either:
- connect to your logged-in Screener session and analyze historical screens; or
- import your historical screen file as a fallback.

The system proposes master strategies from your historical methodology.

If you want control, open **Operator Control** to:
- change strategy philosophy;
- edit hard queries;
- enable/disable strategies;
- preview result size;
- export/import your tuned strategy profile.

### 2. Screen the market

Purpose: run the enabled strategies and create one deduplicated candidate list.

The live Screener POC path:
- executes each query;
- crawls result pages;
- captures exact company links;
- keeps visible ratios;
- combines overlaps across strategies.

If the result set is too broad, return to **Operator Control** and tighten the strategy before continuing.

### 3. Check financial quality

Purpose: automatically collect multi-period company financials and decide which candidates deserve expensive research.

Important rules:
- missing data is not treated as neutral;
- low coverage becomes `DATA_RETRY` rather than a confident pass;
- scores are internal prioritization aids, not investment truth.

After this step you may open **Operator Control** to explicitly include/exclude companies from company research.

### 4. Research the business

Purpose: acquire source documents and build a source-linked research dossier.

The researcher looks for evidence about:
- business model and economics;
- growth drivers;
- cash conversion and working capital;
- management and capital allocation;
- governance;
- business/financial risks;
- catalysts and milestones.

Open **Research Evidence** when you want to inspect:
- what sources were attempted;
- what documents were fetched;
- what evidence was extracted;
- what questions remain open;
- why the company is `SOURCE_GAP`, `RESEARCH_INCOMPLETE` or `EVIDENCE_READY`.

### 5. Allocate deeper research

Purpose: spend more analyst effort on fewer companies.

This is a research-attention decision, not investment conviction.

Typical stages:
- `SOURCE_GAP`
- `STRUCTURED`
- `TARGETED`
- `DEEP`
- `ADVERSARIAL`
- `RESEARCH_QUEUE`

Open **Deep Research & Thesis Challenge** to see:
- research budgets;
- who passed each evidence gate;
- who was admitted now;
- who is queued;
- why each company is at its current depth.

### 6. Challenge the thesis

Purpose: independently build and challenge the strongest positive and negative interpretations of the evidence.

The system produces:
- Bull case;
- Bear / forensic case;
- surviving Bull arguments;
- surviving Bear arguments;
- contradictions;
- fragility flags;
- unresolved questions;
- evidence still needed.

This stage does not produce a buy/sell recommendation.

---

## What the sidebar pages mean

### Guided Research
The normal end-to-end workflow. Use this page most of the time.

### User Guide
Plain-language explanation of the product, statuses and recommended workflow.

### Research Evidence
Detailed source/evidence inspection and company research retry controls.

### Deep Research & Thesis Challenge
Detailed research-depth allocation and Bull/Bear thesis analysis.

### Operator Control
Optional advanced control over:
- strategy philosophy;
- strategy queries;
- candidate pruning;
- financial-stage overrides;
- deep-research capacity.

### Runtime Settings
Technical settings such as delay between Screener requests.

---

## Important status terms

### `ADVANCE`
Financial evidence is sufficient and no hard gate currently blocks company research.

### `WATCHLIST`
Retain the company, but it is less clean/complete than a straightforward advance.

### `DATA_RETRY`
Financial data is too incomplete for a confident decision. This is not a rejection.

### `SOURCE_GAP`
The research engine could not acquire enough usable source evidence. This is not proof that the company is weak.

### `RESEARCH_INCOMPLETE`
Some evidence exists, but important analyst missions or source classes remain open.

### `EVIDENCE_READY`
The current company-research contract is satisfied. This means ready to challenge, not ready to buy.

### `RESEARCH_QUEUE`
The evidence gate passed, but the current research-depth budget is full. The company remains retained.

### `ADVERSARIAL`
Enough evidence exists to justify independent Bull/Bear analysis.

### `CONTESTED`
Bull and Bear evidence remain relatively balanced after challenge.

### `BULL_CASE_SURVIVES`
The Bull case is better supported by the current evidence set. This is not a buy recommendation.

### `BEAR_CASE_DOMINATES`
The Bear case is better supported by the current evidence set. This is not an automatic sell recommendation.

### `FRAGILE`
The thesis depends heavily on unresolved assumptions, contradictions or weak evidence.

---

## What should the user pay attention to?

Prefer this chain:

```text
Decision
→ Why
→ Evidence
→ Missing information
→ Next action
```

Do not over-focus on numeric scores.

A high score with weak evidence coverage is not a strong research conclusion.

---

## Recommended first real acceptance test

Do not start with hundreds of stocks.

A useful first validation run is:
1. tune strategies until the result set is manageable;
2. carry roughly 5–15 companies through financial analysis;
3. inspect 2–3 company dossiers manually in Research Evidence;
4. verify that the sources/findings are sensible;
5. create the deep-research plan;
6. run Bull/Bear on evidence-ready names;
7. compare the app's thesis challenge with your own judgement.

Only after this workflow proves useful should we invest heavily in valuation, conviction, ranking and portfolio-construction layers.
