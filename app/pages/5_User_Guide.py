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
    "collects source evidence, spends deeper research effort only where justified, and then challenges the thesis from both Bull and Bear perspectives."
)

st.markdown("## The normal six-step journey")
steps = [
    ("1", "Connect & prepare strategies", "Teach the system what kinds of companies you seek. Review/tune the generated philosophy if needed."),
    ("2", "Screen the market", "Run the enabled strategies and combine results into one deduplicated candidate universe."),
    ("3", "Check financial quality", "Collect multi-period financials and decide which candidates deserve expensive company research."),
    ("4", "Research the business", "Acquire source documents, extract evidence, expose risks, catalysts and unanswered questions."),
    ("5", "Allocate deeper research", "Spend progressively more analyst effort on fewer companies based on evidence quality and gaps."),
    ("6", "Challenge the thesis", "Run independent Bull/Bear analysis and surface contradictions, fragility and missing evidence."),
]
for n, title, text in steps:
    st.markdown(f"### {n}. {title}")
    st.write(text)

st.markdown("## What the sidebar pages are for")
st.markdown(
    """
- **Guided Research** — the normal workflow. Use this most of the time.
- **Research Evidence** — detailed company-level source attempts, documents, findings and open questions.
- **Deep Research & Thesis Challenge** — detailed research-budget decisions plus Bull/Bear outputs.
- **Operator Control** — optional advanced controls: strategy tuning, candidate pruning, user overrides and Bull/Bear inclusion.
- **Runtime Settings** — technical settings such as delay between Screener requests.

You are not expected to move page-by-page from top to bottom. The **Guided Research** page tells you when a specialist workspace is useful.
"""
)

st.markdown("## Important status terms")
terms = [
    ("ADVANCE", "Financial evidence is sufficient and no hard gate currently blocks company research."),
    ("WATCHLIST", "Interesting enough to retain, but not as clean/complete as a straightforward advance."),
    ("DATA_RETRY", "Financial data coverage is too incomplete for a confident decision. This is not a rejection."),
    ("SOURCE_GAP", "The research engine could not acquire enough usable source evidence. This is not proof that the company is weak."),
    ("RESEARCH_INCOMPLETE", "Some evidence exists, but important analyst missions or source classes remain open."),
    ("EVIDENCE_READY", "The current company-research contract is satisfied. It means ready to challenge, not ready to buy."),
    ("RESEARCH_QUEUE", "The evidence gate was passed, but the current research-depth budget is full. The company is retained."),
    ("ADVERSARIAL", "Enough evidence exists to justify independent Bull/Bear thesis challenge."),
    ("CONTESTED", "Bull and Bear evidence remain relatively balanced after challenge."),
    ("BULL_CASE_SURVIVES", "The Bull case is better supported by current evidence. This is not a buy recommendation."),
    ("BEAR_CASE_DOMINATES", "The Bear case is better supported by current evidence. This is not an automatic sell recommendation."),
    ("FRAGILE", "The thesis depends heavily on unresolved assumptions, contradictions or weak evidence."),
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
    "Treat all scores as prioritization aids, not truth. Prefer the visible chain: **decision → reason → evidence → missing information → next action**. "
    "A high score with poor evidence coverage should never be treated as a strong investment conclusion."
)

st.markdown("## Recommended first real test")
st.markdown(
    """
1. Use a small/tuned strategy set rather than hundreds of candidates.
2. Carry roughly **5–15 companies** through financial and company research.
3. Open **Research Evidence** for 2–3 names and verify whether the sources/findings make sense to you.
4. Create the deep-research plan.
5. Run Bull/Bear on the evidence-ready names.
6. Compare the app's thesis challenge with your own judgement.

This is the best way to evaluate whether the product is adding real research value before we build valuation, conviction and portfolio layers.
"""
)

st.page_link("main.py", label="← Return to Guided Research")
