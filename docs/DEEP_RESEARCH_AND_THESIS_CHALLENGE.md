# Deep Research & Thesis Challenge

This stage turns company evidence into a transparent research-allocation decision and, for sufficiently researched companies, an independent Bull/Bear thesis challenge.

It does **not** produce a buy/sell recommendation, target price, expected return or portfolio allocation.

## Why this stage exists

Company research is expensive. Once dozens or hundreds of screened companies have financial and source-linked evidence, the system must answer two different questions:

1. **Where should additional analyst effort be spent?**
2. **For sufficiently researched companies, which parts of the thesis survive an independent challenge?**

Those questions are deliberately separated from investment conviction.

## Research-depth stages

### SOURCE_GAP

There is not enough authoritative material to justify deeper thesis work.

Typical next action:
- acquire missing annual reports, filings, results, transcripts or rating material;
- retry failed source acquisition;
- resolve company identity/source problems.

### STRUCTURED

Some evidence exists, but core fundamental-analyst missions or source classes remain incomplete.

Typical next action:
- organize business-model evidence;
- fill major document gaps;
- cover missing analyst missions.

### TARGETED

Enough evidence exists to ask specific research questions, but not enough for full thesis challenge.

Typical next action:
- investigate working capital;
- verify management guidance;
- resolve customer/concentration questions;
- find industry/competition evidence;
- obtain missing downside evidence.

### DEEP

The company is sufficiently researched for deeper thesis work, but material gaps remain before independent adversarial analysis.

Typical next action:
- look for thesis breakers;
- validate management promises vs delivery;
- investigate capital allocation and governance;
- examine cash conversion and competitive durability;
- ensure downside/risk evidence is not missing.

### ADVERSARIAL / Bull-Bear

The source set, analyst-mission coverage and downside evidence are strong enough to build two independent interpretations of the same evidence.

This is a research gate, not a statement that the company is investable.

### RESEARCH_QUEUE

The company passed an evidence gate but the current research-capacity budget is full. It is retained for a later pass rather than discarded.

### FINANCIAL_HOLD

The earlier financial stage has not approved expensive company research.

## Research budgets

The operator controls four budgets:

- Structured
- Targeted
- Deep
- Bull/Bear

Budgets represent **research capacity**. They must never be described as conviction thresholds.

For each stage the UI shows:

- configured budget;
- number of companies that passed the evidence gate;
- number admitted now;
- number queued.

## Inputs from the Company Research Engine

The depth planner consumes the persistent company dossier rather than depending on a transient CSV/session object.

Important inputs include:

- research state;
- financial-stage decision / operator override;
- document coverage;
- evidence quality;
- research readiness;
- fundamental mission coverage;
- explicit risk/governance evidence;
- open research questions;
- missing source classes.

## Bull/Bear thesis challenge

The adversarial stage has three roles.

### Bull researcher

Construct the strongest evidence-supported positive interpretation.

It should expose:
- thesis points;
- evidence IDs;
- assumptions;
- what must be true;
- invalidation conditions;
- missing evidence.

### Bear / forensic researcher

Attack the thesis using supported evidence around:
- business-model fragility;
- cash conversion / working capital;
- governance;
- customer concentration;
- competition;
- execution;
- leverage;
- capital allocation;
- other source-supported risks.

It must not invent a problem merely to make the Bear case stronger.

### Neutral challenge

Compare the two cases and identify:
- surviving Bull points;
- surviving Bear points;
- contradictions;
- fragile assumptions;
- unresolved questions;
- evidence still needed.

## Research-state outputs

Possible thesis-analysis states include:

- `INSUFFICIENT_EVIDENCE`
- `FRAGILE`
- `CONTESTED`
- `BULL_CASE_SURVIVES`
- `BEAR_CASE_DOMINATES`

These labels describe the **current evidence set**, not future stock returns.

`BULL_CASE_SURVIVES`, for example, means the positive thesis is better supported after the current evidence challenge. It does not mean "buy".

## Thesis balance and fragility

### Thesis balance

A value above 50 means the positive case has greater support in the current evidence comparison. A value below 50 means the negative case has greater support.

It is not:
- probability of a positive return;
- expected return;
- confidence in a target price.

### Fragility

Fragility measures dependence on weak assumptions, unresolved questions and incomplete evidence.

It is not a forecast of price downside.

## Deterministic vs LLM mode

Without a configured compatible LLM, the system performs deterministic source-backed comparison. This can still surface positive and negative evidence but cannot reliably perform semantic contradiction resolution.

The UI must make this limitation visible.

With an LLM configured, the analysis remains evidence-bound: arguments must use the supplied source-linked evidence and should cite evidence IDs.

## Investor-facing completion contract

This stage is useful only if the investor can answer:

1. Why was this company allocated this research depth?
2. Which evidence gates were passed or failed?
3. Which questions remain open?
4. What does the Bull case actually rely on?
5. What does the Bear case actually rely on?
6. Which points survived neutral challenge?
7. What would invalidate either interpretation?
8. Is the output deterministic or semantic/LLM-assisted?
9. What evidence is still missing?

If these are not visible, the stage is not complete even if the backend analysis executed successfully.
