# Personal AI Stock Researcher

An experimental, evidence-driven research system for Indian equities.

The goal is simple: **start with a broad stock universe, progressively narrow it using financial quality and research evidence, challenge the surviving ideas with independent bull/bear analysis, and eventually produce an explainable ranked portfolio proposal.**

This is not intended to be a black-box stock tip generator. Every stage is designed to show **what survived, what was rejected or held, and why**.

## What it does today

The current baseline contains the work developed through **V6.1**:

1. **Methodology Miner** — learns recurring patterns from historical Screener.in screens.
2. **Strategy Intelligence** — derives master screening strategies with provenance back to the original methodology.
3. **Candidate Universe** — combines results, deduplicates companies and keeps strategy-overlap context.
4. **Autonomous V3 Financial Intelligence** — keeps ratios already present in screen exports and can enrich candidates with multi-period financial history from a logged-in Screener session.
5. **Company Research Memory** — ingests/fetches annual reports, results, presentations, concalls, filings and rating reports into a source-linked evidence ledger.
6. **Autonomous Source Acquisition & Orchestrator** — discovers and prioritizes research sources and decides what a company needs next.
7. **Deep Research Funnel** — spends progressively more research effort on progressively fewer companies.
8. **Bull/Bear Adversarial Research** — independently builds bullish and bearish cases, then challenges contradictions and thesis fragility.

The final portfolio/valuation/conviction layers are still on the roadmap.

## The intended user experience

The long-term target is:

```text
Start Autonomous Research
        ↓
Acquire stock universe + ratios
        ↓
Run master strategies
        ↓
Candidate universe
        ↓
Financial intelligence
        ↓
Autonomous filings/reports research
        ↓
Progressive deep research
        ↓
Bull/Bear challenge
        ↓
Valuation + evidence confidence
        ↓
Conviction + ranking
        ↓
₹1,00,000 portfolio proposal
```

Manual Excel/CSV upload remains available as a fallback and debugging route, but **the product direction is autonomous end-to-end research**.

## Quick start

### Prerequisites

- Python 3.11+ recommended
- Chrome/Chromium if using logged-in Screener automation

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

To let the app use an existing logged-in Screener session, launch a separate Chrome profile with remote debugging enabled.

Windows example:

```bat
chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\screener-crawler-profile"
```

Then log in to Screener.in in that browser. The app defaults to:

```text
http://127.0.0.1:9222
```

Do not put Screener credentials in this project.

## Optional AI / web research configuration

Copy `.env.example` to your preferred environment-loading mechanism and configure only what you use:

```text
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=...
BRAVE_SEARCH_API_KEY=...
ENABLE_LOCAL_CRAWLER=false
```

The research pipeline has deterministic fallbacks where possible. Semantic evidence extraction and adversarial thesis construction are much stronger with an LLM configured.

## PDF / `fitz` issue

PDF extraction uses **PyMuPDF**. The code now imports the supported module name `pymupdf` first and falls back to legacy `fitz` for compatibility.

If PDF support is missing:

```bash
python -m pip install -r requirements.txt
```

or specifically:

```bash
python -m pip install "PyMuPDF>=1.24,<2"
```

See [docs/SETUP_AND_TROUBLESHOOTING.md](docs/SETUP_AND_TROUBLESHOOTING.md).

## Documentation

- [What this is — for stock investors](docs/OVERVIEW_FOR_INVESTORS.md)
- [How the research pipeline works](docs/HOW_IT_WORKS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Autonomy and data sources](docs/AUTONOMY_AND_DATA_SOURCES.md)
- [Setup and troubleshooting](docs/SETUP_AND_TROUBLESHOOTING.md)
- [Roadmap](ROADMAP.md)

## Important limitations

- This project is **research software**, not a SEBI-registered advisory service.
- A high research score or strategy overlap is not the same as expected return.
- Automated web/source access should respect site terms, robots policies, rate limits and applicable law.
- Screener automation is a convenience adapter, not intended to be the system's permanent single data dependency.
- The system is still under active development and has not yet implemented the final valuation/conviction/portfolio layers.

## Current milestone

**V6.1 baseline committed:** autonomous financial enrichment is connected to the accumulated V1→V6 research pipeline. The next major integration goal is to remove the remaining need for manually executing Screener master queries by adding an autonomous market-data/screening gateway.
