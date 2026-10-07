# Personal AI Stock Researcher

An experimental **Personal AI Equity Research Operating System** for Indian equities.

> **Autonomous by default. Evidence-driven. Investor-controlled. Self-challenging.**

The product is not intended to be a black-box stock-tip generator. Its job is to learn an investor's screening philosophy, discover candidates, collect financial and company evidence, expose uncertainty, progressively allocate research effort and eventually support explainable valuation, conviction and portfolio decisions.

Every major stage should answer:

1. What did the system do?
2. What did it learn?
3. What evidence supports that?
4. What is still unknown?
5. What happens next?

A successful function call is not considered research completion.

## Start here

For first-time use, read [User Guide](docs/USER_GUIDE.md).

The application home page is now **Guided Research**. It presents one six-step journey and always shows a **Next recommended action**. Specialist workspaces are optional and should normally be opened only when the guided flow points to them.

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
Progressive deep research
        ↓
Bull/Bear adversarial challenge
```

The valuation / conviction / final-ranking / portfolio layers remain deliberately paused until the current research foundation has been evaluated strategically.

## Main application areas

### Guided Research

The normal end-to-end workflow. This is where most users should stay.

It provides:
- six numbered stages;
- stage completion status;
- one highlighted next recommended action;
- direct links to specialist workspaces only when useful;
- compact results at each stage.

### User Guide

Plain-language explanation of the workflow, specialist pages and status terminology.

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
- Bull and Bear arguments;
- contradictions;
- fragility;
- unresolved questions.

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
- deep-research capacity.

System proposals remain preserved separately from user overrides.

### Financial research

- automatic company-page financial-history collection
- snapshot ratios + multi-period statements
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
- deterministic source-linked evidence extraction
- optional semantic LLM extraction
- evidence IDs and page references
- analyst-mission coverage
- risks / catalysts / management claims
- explicit open questions
- explicit next action

Research states are intentionally different from investment opinions:
- `SOURCE_GAP` — insufficient usable source/evidence base
- `RESEARCH_INCOMPLETE` — evidence exists, but important missions/source classes remain open
- `EVIDENCE_READY` — current company-research contract is satisfied; ready for deeper challenge

`EVIDENCE_READY` does **not** mean BUY.

### Deep research and thesis challenge

- dossier-aware research-depth planner
- transparent capacity budgets
- companies retained in `RESEARCH_QUEUE` rather than silently dropped
- independent Bull and Bear evidence cases
- neutral contradiction challenge
- fragility and unresolved-question output
- deterministic fallback when no compatible LLM is configured

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
- [Deep Research & Thesis Challenge](docs/DEEP_RESEARCH_AND_THESIS_CHALLENGE.md)
- [Strategic Review Checkpoint](docs/STRATEGIC_REVIEW_CHECKPOINT.md)

Other implementation docs:
- [What this is — for stock investors](docs/OVERVIEW_FOR_INVESTORS.md)
- [How the pipeline works](docs/HOW_IT_WORKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Autonomy and data sources](docs/AUTONOMY_AND_DATA_SOURCES.md)
- [Setup and troubleshooting](docs/SETUP_AND_TROUBLESHOOTING.md)
- [Roadmap](ROADMAP.md)

## Important limitations

- This is research software, not a SEBI-registered advisory service.
- Strategy overlap, financial score, research readiness and evidence readiness are not expected-return probabilities.
- Screener is a POC adapter, not intended to remain the permanent authoritative data layer.
- Source acquisition should be validated against real companies before downstream intelligence is trusted heavily.
- Deterministic evidence extraction is intentionally conservative and shallow compared with semantic research.
- Sector-specific financial models are not yet implemented.
- Final valuation, conviction, ranking and portfolio construction remain deliberately pending.

## Current checkpoint

The current milestone is **guided-workflow UX consolidation on top of the completed screening → financial → company research → deep research → thesis challenge chain**.

The next product step should be a strategic review and one real end-to-end experiment on a manageable company set before valuation/conviction work begins.
