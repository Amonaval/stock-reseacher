# Architecture

## Design principles

1. **Progressive cost** — expensive research only on smaller candidate sets.
2. **Evidence before narrative** — claims should trace back to source documents.
3. **Provider independence** — screen/data/search providers are adapters, not the core intelligence.
4. **Graceful missing data** — missing information lowers confidence and creates research tasks; it should not silently become a neutral score.
5. **Auditability** — every stage should preserve why a company advanced or was held.
6. **Adversarial reasoning** — Bull and Bear research are independent before neutral synthesis.

## Logical architecture

```text
Screen Methodology / Market Universe
               ↓
        Strategy Engine
               ↓
       Candidate Universe
               ↓
      Financial Intelligence
               ↓
       Research Orchestrator
        ↙              ↘
Source Discovery     Research Gaps
        ↓              ↓
   Document Fetch / Ingestion
               ↓
         Evidence Ledger
               ↓
       Company Research Memory
               ↓
       Deep Research Funnel
               ↓
     Bull / Bear Adversarial
               ↓
     [planned downstream layers]
 Evidence → Valuation → Conviction
               ↓
        Ranking / Portfolio
```

## Main modules

| Module | Responsibility |
|---|---|
| `analyzer.py`, `intelligence.py` | Historical-screen methodology analysis |
| `strategy.py` | Master strategy generation |
| `candidates.py`, `universe.py` | Candidate/result normalization and overlap |
| `financials.py`, `financial_scoring.py` | V3 financial normalization/scoring |
| `screener_auto_financials.py` | Autonomous multi-period Screener enrichment |
| `research_documents.py` | PDF/text/HTML extraction and chunking |
| `research_agent.py` | Evidence extraction and company research memory |
| `source_discovery.py`, `source_policy.py` | Web-source discovery, scoring and policy |
| `autonomous_fetch.py`, `autonomous_pipeline.py` | Source fetching and automated ingestion |
| `orchestrator.py` | Research gaps, states and next actions |
| `deep_research.py` | Progressive V5 research budgets and narrowing |
| `adversarial_research.py` | Independent Bull/Bear cases |
| `contradiction_engine.py`, `thesis_fragility.py` | Neutral challenge and fragility assessment |
| `v6_pipeline.py` | V6 orchestration |
| `main.py` | Streamlit UI / stage integration |

## Runtime outputs

Generated run outputs are written under `data/` and `reports/`. `.gitignore` excludes user-generated outputs while keeping committed SAMPLE fixtures.

## LLM abstraction

LLM-enabled modules use an OpenAI-compatible `chat/completions` style endpoint configured through:

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

LLM usage is deliberately separated from deterministic parsing/scoring where possible.
