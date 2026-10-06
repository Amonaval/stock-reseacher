# Personal AI Stock Researcher

A personal, evidence-driven equity research operating system for Indian stocks.

The goal is not to generate stock tips or another opaque score. The goal is to help an investor move from **screening ideas → understanding businesses → collecting evidence → challenging the thesis → valuation → conviction**, while preserving full control and a visible research trail.

## Product thesis

The system should:

1. learn the investor's historical screening philosophy
2. turn that philosophy into editable and reusable strategies
3. execute screening automatically
4. preserve exact company identity and strategy provenance
5. collect multi-period financial data automatically
6. explain financial decisions with evidence coverage and reasons
7. autonomously acquire company research sources
8. maintain a durable company research memory
9. spend progressively more research effort on fewer companies
10. build independent Bull and Bear cases
11. expose contradictions, missing evidence and thesis fragility
12. eventually add valuation, conviction, ranking and portfolio construction

The system is **autonomous by default, but user-controlled at every important gate**.

## Current investor workflow

```text
Learn / load investing philosophy
        ↓
Review / edit strategy profile
        ↓
Run screening automatically
        ↓
Review candidate universe
        ↓
Collect financial history
        ↓
Review financial decisions
        ↓
Research surviving companies
        ↓
Allocate deeper research
        ↓
Bull / Bear challenge
        ↓
[future] valuation
        ↓
[future] conviction + ranking
        ↓
[future] portfolio proposal
```

Manual CSV/XLSX imports remain available for recovery/debugging, but they are not the intended normal workflow.

## Design constitution

Every new feature should follow the product constitution:

- evidence before opinion
- autonomy without loss of user authority
- missing information becomes a research task
- no false precision
- no hidden eliminations
- distinguish methodology confidence, evidence quality, research readiness, valuation and conviction
- challenge the thesis rather than only supporting it
- keep provider-specific code behind adapters
- optimize for investor workflow, not engineering workflow

See [docs/PRODUCT_CONSTITUTION.md](docs/PRODUCT_CONSTITUTION.md).

## Current strengths

- historical screen/methodology mining
- methodology-derived master strategies
- editable/exportable/importable strategy profiles
- autonomous logged-in Screener query execution
- exact company-link capture
- candidate review and user pruning
- multi-period financial enrichment
- coverage-aware financial decisions
- operator overrides
- configurable Screener pacing/rate-limit delay
- company research/source infrastructure
- evidence ledger/research memory foundations
- progressive research-depth planning
- Bull/Bear adversarial research foundations

## Current incomplete area

The major remaining research milestone is **Company Research Engine + Evidence Acquisition Completion**.

The infrastructure exists, but the investor-facing contract is not yet complete until company research consistently shows:

- sources attempted and acquired
- documents reviewed
- business-model summary
- growth drivers
- management/capital-allocation observations
- risks/governance concerns
- catalysts
- source-linked evidence
- unresolved questions
- explicit `SOURCE_GAP` when evidence could not be acquired

Deep research and Bull/Bear become meaningful only after this layer is reliable.

## Quick start

### Prerequisites

- Python 3.11+ recommended
- Chrome/Chromium for logged-in Screener automation

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

Screener is the current POC provider adapter. The long-term architecture is designed to support NSE/BSE and other legitimate data providers.

Launch a separate Chrome profile with remote debugging:

```bat
chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\screener-crawler-profile"
```

Log in to Screener in that browser. The app defaults to:

```text
http://127.0.0.1:9222
```

The automation uses dedicated worker tabs rather than navigating your Streamlit tab.

The Screener request delay is configurable in **Runtime Settings**; the default is deliberately conservative.

## Optional AI / web research configuration

Configure only the providers you use:

```text
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=...
BRAVE_SEARCH_API_KEY=...
ENABLE_LOCAL_CRAWLER=false
```

LLM-assisted research must remain evidence-bound. Missing evidence should produce an explicit gap, not a fabricated answer.

## Documentation

### Product principles
- [Product Constitution](docs/PRODUCT_CONSTITUTION.md)
- [Investor Outlook](docs/INVESTOR_OUTLOOK.md)
- [Fundamental Research Analyst Playbook](docs/FUNDAMENTAL_RESEARCH_ANALYST_PLAYBOOK.md)
- [Differentiation and Competitive Map](docs/DIFFERENTIATION_AND_COMPETITIVE_MAP.md)
- [Research Stage Contracts](docs/RESEARCH_STAGE_CONTRACTS.md)
- [Operator Control](docs/OPERATOR_CONTROL.md)

### Product / engineering
- [What this is — for stock investors](docs/OVERVIEW_FOR_INVESTORS.md)
- [How the research pipeline works](docs/HOW_IT_WORKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Consolidated Workflow](docs/CONSOLIDATED_WORKFLOW.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Autonomy and data sources](docs/AUTONOMY_AND_DATA_SOURCES.md)
- [Setup and troubleshooting](docs/SETUP_AND_TROUBLESHOOTING.md)
- [Static validation](docs/STATIC_VALIDATION.md)
- [Roadmap](ROADMAP.md)

## Research-stage completion rule

A stage is not complete because code ran without throwing an exception.

Every major stage must answer:

1. What did the system do?
2. What did it learn?
3. What evidence supports that?
4. What is still unknown?
5. What happens next?

The app now includes `app/research_contracts.py` as the beginning of enforceable investor-facing completion contracts.

## Important limitations

- This is research software, not a SEBI-registered advisory service.
- Strategy overlap, financial scores, research readiness and Bull/Bear outputs are not expected-return probabilities.
- Web/source access must respect site terms, access controls, rate limits and applicable law.
- Screener is a POC adapter, not a permanent master-data dependency.
- Final valuation, conviction, ranking and portfolio-construction layers are still future work.
