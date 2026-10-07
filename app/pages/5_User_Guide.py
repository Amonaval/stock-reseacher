from __future__ import annotations

import streamlit as st

from navigation import render_navigation

st.set_page_config(page_title="User Guide · Personal AI Stock Researcher", page_icon="📘", layout="wide")
render_navigation(show_settings_hint=False)

st.title("📘 User Guide")
st.caption("How to use the researcher without needing to understand its internal versions or engines.")

st.info("**If this is your first run:** stay on **Guided Research** and follow the six numbered steps. Open specialist pages only when the guided flow links you there.")

st.markdown("## The product in one sentence")
st.write(
    "The app learns or uses your stock-screening philosophy, finds candidates, verifies their financials, "
    "collects source evidence, resolves important evidence gaps, deliberately argues both sides of the strongest researched theses, "
    "and then checks whether the research itself is strong enough to support later valuation work."
)

st.markdown("## The normal six-step journey")
steps = [
    ("1", "Connect & prepare strategies", "Teach the system what kinds of companies you seek. Review/tune the generated philosophy if needed."),
    ("2", "Screen the market", "Run the enabled strategies and combine results into one deduplicated candidate universe."),
    ("3", "Check financial quality", "Collect multi-period financials and decide which candidates deserve expensive company research."),
    ("4", "Research the business", "Acquire source documents, extract evidence, expose risks, catalysts and unanswered questions."),
    ("5", "Deepen unresolved research", "Plan the research depth, then actually resolve source/mission/risk-evidence gaps for the companies that need more work."),
    ("6", "Challenge the thesis", "For evidence-ready companies, build the strongest Bull case and strongest Bear case, then compare what survives."),
]
for n, title, text in steps:
    st.markdown(f"### {n}. {title}")
    st.write(text)

st.markdown("## After the six steps: Research Confidence")
st.write(
    "Open **Research Confidence** when you want to judge whether the dossier itself is trustworthy enough to support the next analytical layer. "
    "It checks source authority, source freshness, traceability, analyst-mission coverage, cross-source triangulation, downside evidence, contradiction handling and financial-data coverage."
)
st.warning(
    "Research confidence is **not investment conviction**. A bearish thesis can have high research confidence, while a very bullish-looking story can still have low research confidence."
)

st.markdown("## Long-running work continues in the background")
st.success(
    "Screen discovery, query crawling, screening, financial collection, company research, deep evidence-gap research and Bull/Bear challenge now run in a separate local worker process."
)
st.markdown(
    """
You can safely open another page while those jobs run.

- Streamlit navigation does **not** cancel the worker.
- Progress/results are written to disk.
- Return to Guided Research or open **Background Jobs** to refresh/inspect progress.
- The app intentionally allows one long-running worker per research run at a time to avoid conflicting writes.
"""
)

st.markdown("## What the sidebar pages are for")
st.markdown(
    """
- **Guided Research** — the normal workflow. Use this most of the time.
- **User Guide** — plain-language explanation of the product and first-run walkthrough.
- **Background Jobs** — monitor crawling/research that continues while you move around the app.
- **Research Evidence** — detailed company-level source attempts, documents, findings and open questions.
- **Deep Research & Thesis Challenge** — detailed research-depth decisions, deeper evidence-gap work, and Bull/Bear outputs.
- **Research Confidence** — quality-control view that asks whether the research foundation is strong enough for future valuation work.
- **Operator Control** — optional advanced controls: strategy tuning, candidate pruning and user overrides.
- **Runtime Settings** — technical settings such as delay between Screener requests.

You are not expected to move page-by-page from top to bottom. **Guided Research** tells you when a specialist workspace is useful.
"""
)

st.markdown("## What Step 5 really means")
st.write(
    "A research-depth plan is only a diagnosis. If a company is marked SOURCE_GAP, STRUCTURED, TARGETED or DEEP, the app still needs to perform additional research before Bull/Bear analysis becomes meaningful."
)
st.markdown(
    """
Use **Resolve evidence gaps in background**. The deeper pass will:

- broaden source acquisition;
- keep evidence already collected rather than replacing it;
- fetch additional useful source classes;
- fill uncovered fundamental-analysis missions;
- seek explicit downside/risk evidence;
- rebuild the company dossier;
- automatically rebuild the research-depth plan.
"""
)

st.markdown("## What 'Challenge the thesis' means")
st.write(
    "This is a confirmation-bias test, not a stock recommendation. The app refuses to run the automatic challenge until the evidence base is strong enough."
)
st.markdown(
    """
For each ready company:

1. **Bull researcher** — constructs the strongest positive thesis supported by the evidence.
2. **Bear / forensic researcher** — attacks that thesis using supported business, cash-flow, governance, competition, execution and capital-allocation risks.
3. **Neutral challenge** — compares both sides, identifies contradictions, fragile assumptions and unresolved questions.

A company being blocked from this step means **research is incomplete**, not that the company is bad.
"""
)

st.markdown("## Important status terms")
terms = [
    ("ADVANCE", "Financial evidence is sufficient and no hard gate currently blocks company research."),
    ("WATCHLIST", "Interesting enough to retain, but not as clean/complete as a straightforward advance."),
    ("DATA_RETRY", "Financial data coverage is too incomplete for a confident decision. This is not a rejection."),
    ("SOURCE_GAP", "The research engine could not acquire enough usable source evidence. This is not proof that the company is weak."),
    ("RESEARCH_INCOMPLETE", "Some evidence exists, but critical source coverage or fundamental analyst missions remain open."),
    ("EVIDENCE_READY", "A sufficient core/current evidence base and enough analyst-mission coverage exist. Optional gaps may remain visible. This is not a buy signal."),
    ("STRUCTURED / TARGETED / DEEP", "The company needs progressively more research work before thesis challenge."),
    ("RESEARCH_QUEUE", "The evidence gate was passed, but the current research-depth budget is full. The company is retained."),
    ("ADVERSARIAL", "Enough evidence, readiness and downside evidence exist to justify independent Bull/Bear thesis challenge."),
    ("CONTESTED", "Bull and Bear evidence remain relatively balanced after challenge."),
    ("BULL_CASE_SURVIVES", "The Bull case is better supported by current evidence. This is not a buy recommendation."),
    ("BEAR_CASE_DOMINATES", "The Bear case is better supported by current evidence. This is not an automatic sell recommendation."),
    ("FRAGILE", "The thesis depends heavily on unresolved assumptions, contradictions or weak evidence."),
    ("HIGH_RESEARCH_CONFIDENCE", "The research/evidence foundation is strong. This says nothing about whether the stock is attractive."),
    ("MODERATE_RESEARCH_CONFIDENCE", "Useful research exists, but important quality gaps remain visible."),
    ("LOW_RESEARCH_CONFIDENCE", "Do not let later valuation/conviction outputs create false precision; strengthen the dossier first."),
    ("READY_FOR_VALUATION_CONTEXT", "The research foundation is strong enough to support valuation analysis. It does not mean undervalued."),
]
for term, meaning in terms:
    st.write(f"**{term}** — {meaning}")

st.markdown("## When should I use Operator Control?")
st.write("Use it only when you want more control than the default autonomous path. Typical cases:")
st.markdown(
    """
- a generated strategy returns hundreds/thousands of stocks and you want to tighten it;
- you want to save/export your tuned investment philosophy;
- you want to cap the number of candidates entering financial analysis;
- you disagree with a system proposal and want to explicitly include/exclude a company;
- you want to change deep-research capacity budgets.
"""
)

st.markdown("## What should I trust?")
st.warning(
    "Treat all scores as prioritization or quality-control aids, not truth. Prefer the visible chain: **decision → reason → evidence → missing information → next action**. "
    "A high score with poor evidence coverage should never be treated as a strong investment conclusion."
)

st.markdown("## Recommended first real test")
st.markdown(
    """
1. Use a small/tuned strategy set rather than hundreds of candidates.
2. Carry roughly **5–15 companies** through financial and company research.
3. Open **Research Evidence** for 2–3 names and verify whether the sources/findings make sense to you.
4. Create the deep-research plan.
5. Run **Resolve evidence gaps** for companies still in SOURCE_GAP / STRUCTURED / TARGETED / DEEP.
6. Recheck which names become Bull/Bear-ready and run the thesis challenge.
7. Open **Research Confidence** and inspect why the strongest/weakest dossiers received their quality state.
8. Compare the app's conclusions with your own judgement.

This is the best way to evaluate whether the product is adding real research value before we build valuation, conviction and portfolio layers.
"""
)

st.page_link("main.py", label="← Return to Guided Research")
