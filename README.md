# Personal AI Stock Researcher

An experimental **Personal AI Equity Research Operating System** for Indian equities.

> **Autonomous by default. Evidence-driven. Investor-controlled. Self-challenging.**

The product is not intended to be a black-box stock-tip generator. Its job is to learn an investor's screening philosophy, discover candidates, collect financial and company evidence, expose uncertainty, progressively allocate research effort, challenge the thesis, judge research quality, build assumption-driven valuation context and synthesize the full research case without hiding it behind BUY/SELL output.

Every major stage should answer:

1. What did the system do?
2. What did it learn?
3. What evidence supports that?
4. What is still unknown?
5. What happens next?

A successful function call is not considered research completion.

## Start here

For first-time use, read [User Guide](docs/USER_GUIDE.md).

The application home page is **Guided Research**. It presents one six-step research journey and always shows a **Next recommended action**. Specialist workspaces then take completed research through quality control, valuation and decision synthesis.

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

## Current workflow

```text
Historical screens / saved strategy profile
        ↓
Methodology intelligence
        ↓
Editable + versioned master strategies
        ↓
Automated Screener POC execution
        ↓
Candidate universe + operator review
        ↓
Automatic multi-period financial collection
        ↓
Coverage-aware financial assessment
        ↓
Operator review
        ↓
Company Research Engine
        ↓
Source-attempt ledger + evidence dossier
        ↓
SOURCE_GAP / RESEARCH_INCOMPLETE / EVIDENCE_READY
        ↓
Depth planning
        ↓
Execute deeper evidence-gap research where needed
        ↓
Rebuild depth plan
        ↓
Bull/Bear adversarial challenge
        ↓
Research Confidence quality gate
        ↓
Sector/business-model-aware valuation scenarios
        ↓
Explainable decision synthesis + separate Investor Review
```

Conviction & Decision Synthesis v1 is implemented. Final ranking, portfolio construction and continuous monitoring remain deliberately pending until the full research-to-decision workflow is validated on real companies.

## Long-running work runs in the background

Crawling/research is no longer tied to the current Streamlit page.

Detached local worker jobs are used for:

- screen discovery;
- historical query fetch;
- strategy execution and result crawling;
- financial collection;
- company research;
- deeper evidence-gap resolution;
- Bull/Bear thesis challenge.

You may navigate anywhere in the app while these jobs run. Progress and errors are persisted under `jobs/` and can be inspected from **Background Jobs**.

The app currently allows one long-running background worker per research run at a time to avoid concurrent writes to the same run state.

## Main application areas

### Guided Research

The normal end-to-end research workflow. This is where most users should stay.

It provides:
- six numbered research stages;
- stage completion status;
- one highlighted next recommended action;
- direct links to specialist workspaces only when useful;
- compact results at each stage.

### User Guide

Plain-language explanation of the workflow, specialist pages and status terminology.

### Background Jobs

Monitor long-running work that continues independently of Streamlit page navigation:

- status and progress;
- current action;
- process ID;
- completion/failure;
- worker log.

### Research Evidence

Detailed company-research workspace for:
- source attempts;
- source quality;
- documents acquired;
- analyst-mission coverage;
- evidence findings;
- risks / catalysts / management claims;
- open questions;
- raw evidence ledger.

### Deep Research & Thesis Challenge

Detailed workspace for:
- research-depth budgets;
- budget utilization;
- company-by-company depth decisions;
- execution of deeper evidence-gap research;
- Bull and Bear arguments;
- contradictions;
- fragility;
- unresolved questions.

### Research Confidence

Quality-control layer that asks **how much the research dossier itself should be trusted**.

It evaluates:
- source authority;
- source freshness;
- evidence traceability;
- fundamental mission coverage;
- cross-source triangulation;
- downside/governance evidence;
- contradiction handling;
- financial-data coverage;
- unresolved research questions.

Research Confidence is intentionally separate from investment conviction.

### Valuation Intelligence

Assumption-driven valuation context for companies that pass the Research Confidence quality gate.

Valuation Intelligence v1 provides:
- visible and overridable valuation-family classification;
- normalized earnings for general/quality businesses;
- justified P/B for banks/NBFCs/lending businesses;
- longer-cycle earnings normalization for cyclicals/commodities including weak/loss years;
- conservative v1 treatment for utility/regulated/asset-heavy businesses;
- explicit blocking of insurer valuation until embedded-value/VNB data exists;
- Bear / Base / Bull scenario values;
- captured-price upside/downside context;
- visible assumptions, anchors, warnings and limitations.

Valuation scenarios are not target-price predictions or investment recommendations.

### Conviction & Decision Synthesis

Explainable final research-case synthesis. It combines, without averaging them into one hidden score:

- Research Confidence;
- financial-stage conclusion and any user override;
- Bull/Bear thesis status and fragility;
- valuation posture;
- unresolved questions;
- Bull assumptions and invalidation conditions.

System states include high-priority research candidate, positive thesis near/stretched valuation, contested case, fragile case, risk-dominated case, financial-quality conflict and explicit incomplete states.

The workspace also stores an optional **Investor Review** separately from system synthesis. The user can record their own stance, conviction and notes without rewriting the system conclusion.

This layer does not produce BUY/SELL instructions, return probabilities or portfolio weights.

### Operator Control

Optional advanced cockpit for:
- strategy philosophy/query editing;
- strategy preview;
- strategy profile import/export;
- candidate pruning;
- financial-stage overrides;
- deep-research capacity tuning.

### Runtime Settings

Technical controls such as Screener request pacing. Default delay is approximately 1.5 seconds and can be adjusted by the operator.

## What is implemented

### Methodology and strategy

- historical-screen mining
- trusted screen-universe controls
- threshold and co-occurrence intelligence
- methodology-derived master strategies
- editable philosophy, thresholds/query and notes
- strategy enable/disable
- generated-vs-tuned comparison
- strategy profile import/export
- preview workflow before full screening

### Screening POC

Screener is the initial proof-of-concept adapter.

- logged-in local Chrome/CDP integration
- dedicated temporary worker tab
- automated strategy execution
- result-table extraction
- pagination
- exact company URL capture
- visible screen-result ratios retained
- configurable request delay / pacing

Long term, exchange/company/provider adapters should replace Screener as the master-data dependency.

### Investor control

Automation is not intended to remove authority from the user.

Optional control is available at important gates:
- strategy philosophy and query;
- enabled strategies;
- candidate-universe pruning;
- minimum strategy overlap;
- maximum companies sent to financial research;
- manual company include/exclude;
- financial-stage override;
- deep-research capacity;
- valuation-family and assumption overrides;
- separate Investor Review after synthesis.

System proposals remain preserved separately from user overrides/reviews.

### Financial research

- automatic company-page financial-history collection
- snapshot ratios + multi-period history
- growth/trend/CAGR support
- quality / balance-sheet / cash-flow / valuation dimensions
- explicit evidence coverage
- `DATA_RETRY` rather than false confidence when data is incomplete
- investor-readable decisions and reasons

### Company Research Engine

Fundamental-analyst missions include:
- business model & economics
- growth drivers & durability
- cash conversion / working capital
- management & capital allocation
- governance
- business / financial risks
- catalysts / milestones

The engine provides:
- bounded source discovery
- source authority scoring
- document-type prioritization
- per-company source acquisition attempts
- fetch success/failure visibility
- persistent source/evidence accumulation across retries
- deterministic source-linked evidence extraction
- optional semantic LLM extraction
- evidence IDs and page references
- analyst-mission coverage
- risks / catalysts / management claims
- explicit open questions
- explicit next action

Research states are intentionally different from investment opinions:
- `SOURCE_GAP` — insufficient usable source/evidence base
- `RESEARCH_INCOMPLETE` — evidence exists, but critical source coverage or important missions remain open
- `EVIDENCE_READY` — a sufficient core/current evidence base and analyst-mission coverage exist; ready for deeper challenge

`EVIDENCE_READY` does **not** mean BUY.

The evidence contract is sufficient rather than checkbox-complete: an annual report/core source, at least one fresh operating/disclosure source, and adequate mission coverage are required. Missing supplementary source classes remain visible instead of automatically blocking the company.

### Deep research and thesis challenge

- dossier-aware research-depth planner
- transparent capacity budgets
- companies retained in `RESEARCH_QUEUE` rather than silently dropped
- executable deeper evidence-gap pass for `SOURCE_GAP / STRUCTURED / TARGETED / DEEP`
- automatic dossier + depth-plan rebuild after deeper research
- explicit downside/risk evidence gate
- independent Bull and Bear evidence cases
- neutral contradiction challenge
- fragility and unresolved-question output
- deterministic fallback when no compatible LLM is configured

The Bull/Bear gate deliberately refuses to manufacture a thesis from weak evidence. `research_readiness` remains visible as a diagnostic but is not stacked as another opaque hard cutoff after explicit evidence gates have already passed.

### Research Confidence

- source authority and freshness
- source/page traceability
- analyst-mission coverage
- theme-level cross-document triangulation
- downside/governance source diversity
- contradiction/unresolved-question handling
- financial-data coverage
- explicit critical gaps
- `HIGH / MODERATE / LOW_RESEARCH_CONFIDENCE`
- `READY_FOR_VALUATION_CONTEXT` quality gate

Research Confidence measures the research process, not stock attractiveness.

### Valuation Intelligence v1

- persistent per-company valuation result
- research-confidence gate
- business-model-aware valuation-family classification
- operator override of valuation family and assumptions
- normalized-EPS earnings-multiple scenarios
- justified P/B bank/NBFC scenarios
- longer normalized earnings for cyclicals including weak/loss years
- explicit unsupported-insurer state instead of generic substitution
- Bear / Base / Bull fair-value scenarios
- upside/downside vs captured run price
- historical / industry P/E anchor visibility
- explicit warnings when current P/E is the only fallback anchor
- visible sensitivity drivers

Important v1 limitations include no full DCF, SOTP, EV/EBITDA, insurer embedded-value acquisition, forward consensus estimates or scenario probabilities.

### Conviction & Decision Synthesis v1

- persistent per-company decision synthesis
- no master system conviction score
- separate research-quality, financial-quality, thesis and valuation dimensions
- explicit decision readiness
- state precedence that prevents favorable valuation from hiding Bear/fragility/research gaps
- visible rationale and blockers
- unresolved questions
- Bull assumptions / what must be true
- thesis invalidation conditions where available
- what could strengthen/weaken the case
- separate optional Investor Review with stance, user conviction and notes
- no BUY/SELL, expected-return probability or portfolio-weight output

## Quick start

### Prerequisites

- Python 3.11+ recommended
- Chrome/Chromium for logged-in Screener POC automation

### Windows

```bat
run.bat
```

Or manually:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m playwright install chromium
streamlit run app/main.py
```

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
streamlit run app/main.py
```

## Screener browser connection

Launch a separate Chrome profile with remote debugging enabled.

Windows example:

```bat
chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\screener-crawler-profile"
```

Log in to Screener in that browser. The app defaults to:

```text
http://127.0.0.1:9222
```

The automation uses a dedicated temporary worker tab and should not navigate the Streamlit application tab.

Do not place Screener credentials in the repository.

## Optional AI / web research configuration

Configure only what you use:

```text
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=...
BRAVE_SEARCH_API_KEY=...
ENABLE_LOCAL_CRAWLER=false
```

The Company Research Engine has deterministic evidence extraction when an LLM is unavailable. Semantic classification is stronger when an LLM is configured.

## PDF support

PDF extraction uses **PyMuPDF** and imports `pymupdf` first, with legacy `fitz` as a compatibility fallback.

Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Product constitution and research doctrine

- [User Guide](docs/USER_GUIDE.md)
- [Product Constitution](docs/PRODUCT_CONSTITUTION.md)
- [Investor Outlook](docs/INVESTOR_OUTLOOK.md)
- [Fundamental Research Analyst Playbook](docs/FUNDAMENTAL_RESEARCH_ANALYST_PLAYBOOK.md)
- [Differentiation & Competitive Map](docs/DIFFERENTIATION_AND_COMPETITIVE_MAP.md)
- [Research Stage Contracts](docs/RESEARCH_STAGE_CONTRACTS.md)
- [Operator Control](docs/OPERATOR_CONTROL.md)
- [Company Research Engine](docs/COMPANY_RESEARCH_ENGINE.md)
- [Background Jobs & Deep Research](docs/BACKGROUND_JOBS_AND_DEEP_RESEARCH.md)
- [Deep Research & Thesis Challenge](docs/DEEP_RESEARCH_AND_THESIS_CHALLENGE.md)
- [Research Confidence](docs/RESEARCH_CONFIDENCE.md)
- [Strategic Review Outcome](docs/STRATEGIC_REVIEW_OUTCOME.md)
- [Valuation Intelligence v1](docs/VALUATION_INTELLIGENCE_V1.md)
- [Conviction & Decision Synthesis v1](docs/CONVICTION_DECISION_SYNTHESIS_V1.md)
- [Strategic Review Checkpoint](docs/STRATEGIC_REVIEW_CHECKPOINT.md)

Other implementation docs:
- [What this is — for stock investors](docs/OVERVIEW_FOR_INVESTORS.md)
- [How the pipeline works](docs/HOW_IT_WORKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Autonomy and data sources](docs/AUTONOMY_AND_DATA_SOURCES.md)
- [Setup and troubleshooting](docs/SETUP_AND_TROUBLESHOOTING.md)
- [Roadmap](ROADMAP.md)
