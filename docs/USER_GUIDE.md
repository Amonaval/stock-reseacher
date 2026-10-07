# User Guide — Personal AI Stock Researcher

This guide is written for the end user, not for the developer.

## The simplest way to use the app

Use **Guided Research** for the normal workflow. Follow the six numbered research steps from top to bottom.

You do not need to understand internal version names, JSON objects, research engines or data-model details.

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
        ↓
Research Confidence
        ↓
Valuation Intelligence
        ↓
Conviction & Decision Synthesis
```

The home page always shows a **Next recommended action** through the six-step research flow. The specialist workspaces then take the strongest researched cases through quality control, valuation and synthesis.

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

Changing Streamlit pages does **not** cancel those jobs. Use **Background Jobs** to inspect status, progress and worker logs.

---

## What each research step does

### 1. Connect & prepare strategies

Define what kinds of companies you want the researcher to look for. The system can learn from historical Screener screens or use an imported fallback file.

Use **Operator Control** when you want to edit strategy philosophy, hard queries, enabled strategies or save/load a strategy profile.

### 2. Screen the market

Run the enabled strategies and create one deduplicated candidate list. The live Screener POC executes queries, crawls result pages, captures exact company links and preserves visible screen metrics.

### 3. Check financial quality

Collect multi-period financials and decide which companies deserve expensive company research.

Important rules:

- missing data is not treated as neutral;
- weak coverage becomes `DATA_RETRY`;
- internal scores are prioritization aids, not investment truth.

### 4. Research the business

Acquire source documents and build a source-linked research dossier covering business model, growth, cash conversion, management, governance, risks and catalysts.

Open **Research Evidence** to inspect exactly what was attempted, fetched, learned and left unresolved.

### 5. Deepen unresolved research

The depth plan diagnoses how much more research each company needs. Companies may be assigned `SOURCE_GAP`, `STRUCTURED`, `TARGETED`, `DEEP`, `ADVERSARIAL` or `RESEARCH_QUEUE`.

Use **Resolve evidence gaps in background** for companies that still need more work. The deeper pass preserves existing evidence, broadens source discovery, fills missing missions, looks for downside evidence and rebuilds the depth plan.

### 6. Challenge the thesis

For sufficiently researched companies:

1. a Bull researcher builds the strongest positive case;
2. a Bear / forensic researcher attacks it;
3. a neutral challenge identifies surviving arguments, contradictions, fragility and unresolved questions.

This is a confirmation-bias test, not a recommendation.

---

## After the six steps: Research Confidence

Open **Research Confidence** to judge the quality of the dossier itself.

It evaluates:

- source authority;
- source freshness;
- evidence traceability;
- fundamental mission coverage;
- cross-source triangulation;
- downside/governance evidence;
- contradiction handling;
- financial-data coverage;
- unresolved questions.

Important distinction:

> **Research confidence is not investment conviction.**

A bearish thesis may have high research confidence. A compelling growth story may still have low research confidence.

`READY_FOR_VALUATION_CONTEXT` means the evidence foundation is strong enough to support valuation analysis. It does **not** mean undervalued.

---

## Valuation Intelligence

Use **Valuation Intelligence** after Research Confidence.

Valuation Intelligence v1 supports:

- **General / quality businesses** — normalized EPS × contextual P/E scenarios;
- **Banks / NBFCs / lending businesses** — justified P/B using sustainable ROE, growth and cost of equity;
- **Cyclicals / commodities** — longer full-cycle EPS normalization, including weak/loss years, with more conservative multiples;
- **Utilities / regulated / asset-heavy businesses** — conservative normalized-earnings framework in v1;
- **Insurance** — deliberately blocked until embedded-value / VNB inputs exist.

The automatic valuation family is visible and can be overridden by the operator.

The output is Bear / Base / Bull **scenario valuation**, not a target price.

The app shows:

- captured market price from the financial-research run;
- Bear / Base / Bull fair-value scenarios;
- upside/downside vs the captured price;
- valuation family and method;
- normalized EPS or book-value basis;
- historical / industry multiple anchors;
- scenario assumptions;
- warnings and limitations;
- what factors would change the valuation.

The price used by v1 is **not live-refreshed** inside Valuation Intelligence.

---

## Conviction & Decision Synthesis

Use **Conviction & Decision Synthesis** after the upstream research, thesis challenge and valuation work are meaningful.

It combines four separate dimensions instead of hiding them inside one master score:

1. **Research quality** — how trustworthy is the evidence foundation?
2. **Financial quality** — what did the financial gate conclude, including any explicit user override?
3. **Thesis challenge** — did Bull survive, Bear dominate, or remain contested/fragile?
4. **Valuation posture** — where is the captured price relative to the Bear/Base/Bull scenarios?

Typical system states include:

- `HIGH_PRIORITY_RESEARCH_CANDIDATE`
- `POSITIVE_THESIS_NEAR_BASE_VALUE`
- `POSITIVE_THESIS_VALUATION_STRETCHED`
- `CONTESTED_RESEARCH_CASE`
- `FRAGILE_RESEARCH_CASE`
- `RISK_DOMINATED_RESEARCH_CASE`
- `FINANCIAL_QUALITY_CONFLICT`
- `MORE_RESEARCH_NEEDED`
- `THESIS_CHALLENGE_PENDING`
- `VALUATION_CONTEXT_INCOMPLETE`

These are research states, **not BUY/SELL/HOLD instructions**.

The workspace also exposes:

- why the state was produced;
- blockers;
- unresolved questions;
- what must be true for the Bull case;
- invalidation conditions;
- what could strengthen the case;
- what could weaken the case.

### Your Investor Review

Your own judgement stays separate from the system synthesis.

Optional stances include:

- `AGREE_WITH_SYSTEM`
- `NEED_MORE_RESEARCH`
- `WATCH_CLOSELY`
- `PASS_FOR_NOW`
- `HIGH_INTEREST`

You can also store your own current `LOW / MEDIUM / HIGH` conviction and notes.

That is **your judgement**, not a system-generated probability or recommendation.

---

## What the sidebar pages mean

### Guided Research
Normal end-to-end research workflow.

### User Guide
Plain-language explanation of the product.

### Background Jobs
Monitor crawling/research while navigating freely.

### Research Evidence
Detailed source/evidence inspection.

### Deep Research & Thesis Challenge
Research-depth allocation, gap resolution and Bull/Bear analysis.

### Research Confidence
Evidence-quality control before valuation.

### Valuation Intelligence
Business-model-aware Bear / Base / Bull valuation scenarios.

### Conviction & Decision Synthesis
Explainable synthesis of research quality, financial quality, thesis challenge and valuation context, plus a separate optional Investor Review.

### Operator Control
Optional strategy/candidate/override controls.

### Runtime Settings
Technical settings such as Screener request delay.

---

## Important status terms

- `ADVANCE` — financial evidence is sufficient for company research.
- `WATCHLIST` — retain, but the financial case is mixed.
- `DATA_RETRY` — financial coverage is too incomplete for a confident decision.
- `SOURCE_GAP` — insufficient usable source evidence.
- `RESEARCH_INCOMPLETE` — research exists but important gaps remain.
- `EVIDENCE_READY` — current company-research contract is satisfied; not a buy signal.
- `STRUCTURED / TARGETED / DEEP` — progressively deeper research work is required.
- `RESEARCH_QUEUE` — evidence gate passed but current research capacity is full.
- `ADVERSARIAL` — enough evidence exists for independent Bull/Bear challenge.
- `CONTESTED` — Bull and Bear evidence remain relatively balanced.
- `BULL_CASE_SURVIVES` — Bull evidence survives better; not a buy recommendation.
- `BEAR_CASE_DOMINATES` — Bear evidence dominates; not an automatic sell recommendation.
- `FRAGILE` — thesis depends heavily on unresolved assumptions/contradictions.
- `HIGH / MODERATE / LOW_RESEARCH_CONFIDENCE` — quality of the research process, not stock attractiveness.
- `READY_FOR_VALUATION_CONTEXT` — evidence foundation is strong enough for valuation analysis.
- `VALUED` — the selected valuation framework had enough inputs to produce scenarios.
- `BLOCKED` — valuation is intentionally withheld because the research gate, data or valuation family is insufficient.
- `HIGH_PRIORITY_RESEARCH_CANDIDATE` — the completed research case deserves attention under the current contract; not BUY.
- `READY_FOR_INVESTOR_REVIEW` — the implemented upstream stages are complete enough for your review; not an instruction to invest.

---

## What should the user pay attention to?

Prefer this chain:

```text
Decision state
→ Why
→ Evidence
→ Assumptions
→ Bull/Bear conflict
→ Valuation context
→ What must be true
→ Invalidation conditions
→ Missing information
→ Your review
```

Do not over-focus on numeric scores, a single fair-value number or a single synthesis label.

---

## Recommended first real acceptance test

1. tune strategies until the result set is manageable;
2. carry roughly 5–15 companies through financial analysis;
3. inspect 2–3 dossiers in Research Evidence;
4. resolve deep research gaps;
5. run Bull/Bear on evidence-ready names;
6. inspect Research Confidence;
7. run Valuation Intelligence for 2–3 research-ready companies;
8. challenge the selected valuation family, normalized earnings, benchmark anchors and Bear/Base/Bull assumptions;
9. run Conviction & Decision Synthesis;
10. verify that Bear-dominated, fragile and contested cases are not hidden by favorable valuation scenarios;
11. record your own Investor Review separately and compare it with the system synthesis.

Ranking, portfolio construction and monitoring should only be built after this full research-to-decision workflow proves useful on real companies.
