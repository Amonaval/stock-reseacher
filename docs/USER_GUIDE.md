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
5. Deepen unresolved research
        ↓
6. Challenge the thesis
```

The home page always shows a **Next recommended action** so you know what to do next.

---

## Long-running work continues in the background

The following stages run in a detached local worker process:

- historical screen discovery;
- historical query crawling;
- screening strategy execution;
- company financial collection;
- company research;
- deeper evidence-gap resolution;
- Bull/Bear thesis challenge.

This means changing Streamlit pages does **not** cancel the job.

Background progress and results are persisted under `jobs/`. The directory is ignored by Git.

Use **Background Jobs** in the sidebar to inspect:

- current job;
- progress;
- worker status;
- completion/failure;
- worker logs.

The app intentionally starts only one long-running background job at a time per research run so multiple workers do not overwrite the same research-run state.

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

### 5. Deepen unresolved research

Purpose: first decide how much additional research each company needs, then actually perform that research.

A depth plan is only a diagnosis. Companies can be assigned:

- `SOURCE_GAP`
- `STRUCTURED`
- `TARGETED`
- `DEEP`
- `ADVERSARIAL`
- `RESEARCH_QUEUE`

If a company is `SOURCE_GAP`, `STRUCTURED`, `TARGETED` or `DEEP`, use **Resolve evidence gaps in background**.

That deeper pass will:

- broaden source acquisition;
- preserve evidence already collected;
- acquire additional useful source classes;
- fill uncovered fundamental-research missions;
- seek explicit downside/risk evidence;
- rebuild each company dossier;
- automatically rebuild the research-depth plan afterward.

The app no longer requires every possible document class before a company can become evidence-ready. The minimum evidence contract is intentionally practical:

- an annual report or equivalent core longitudinal source;
- at least one fresh operating/disclosure source such as a result, filing, presentation or earnings call;
- sufficient fundamental analyst mission coverage.

Other missing source classes stay visible as research gaps rather than becoming absolute blockers.

### 6. Challenge the thesis

Purpose: reduce confirmation bias by deliberately arguing both sides of the same company.

The automatic gate opens only when the evidence base is strong enough.

For each evidence-ready company:

1. **Bull researcher** — builds the strongest positive thesis supported by current evidence.
2. **Bear / forensic researcher** — attacks the thesis using supported business, cash-flow, governance, concentration, competition, execution and capital-allocation risks.
3. **Neutral challenge** — compares both sides and identifies:
   - which Bull arguments survive;
   - which Bear arguments survive;
   - contradictions;
   - fragile assumptions;
   - unresolved questions;
   - evidence still needed.

If no company passes the Bull/Bear gate, that means the app is refusing to manufacture a confident thesis from weak evidence. Return to Step 5 and resolve the remaining evidence gaps.

This stage does **not** produce a buy/sell recommendation or expected-return probability.

---

## What the sidebar pages mean

### Guided Research
The normal end-to-end workflow. Use this page most of the time.

### User Guide
Plain-language explanation of the product, statuses and recommended workflow.

### Background Jobs
Monitor long-running crawling and research while moving freely around the app.

### Research Evidence
Detailed source/evidence inspection and company research retry controls.

### Deep Research & Thesis Challenge
Detailed research-depth allocation, deeper evidence-gap execution and Bull/Bear thesis analysis.

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
Some evidence exists, but critical source coverage or important analyst missions remain open.

### `EVIDENCE_READY`
A sufficient core/current evidence base and enough analyst-mission coverage exist. Optional research gaps may remain visible. This means ready for deeper challenge, not ready to buy.

### `STRUCTURED`
Core evidence exists but significant research structure/coverage still needs work.

### `TARGETED`
The remaining gaps are narrower and can be investigated specifically.

### `DEEP`
The company needs deeper thesis work, often around downside evidence, unresolved assumptions, management claims, competition or cash conversion.

### `RESEARCH_QUEUE`
The evidence gate passed, but the current research-depth budget is full. The company remains retained.

### `ADVERSARIAL`
Enough evidence, readiness and explicit downside evidence exist to justify independent Bull/Bear analysis.

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
6. run **Resolve evidence gaps** for names in `SOURCE_GAP`, `STRUCTURED`, `TARGETED` or `DEEP`;
7. review which names become `ADVERSARIAL`;
8. run Bull/Bear thesis challenge on those names;
9. compare the app's thesis challenge with your own judgement.

Only after this workflow proves useful should we invest heavily in valuation, conviction, ranking and portfolio-construction layers.