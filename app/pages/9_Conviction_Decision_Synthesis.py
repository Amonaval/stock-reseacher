from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from navigation import render_navigation
from conviction_synthesis import DECISION_STATES, synthesize_run

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Conviction & Decision Synthesis · Personal AI Stock Researcher", page_icon="🧠", layout="wide")
render_navigation()

st.title("🧠 Conviction & Decision Synthesis")
st.caption("Bring financial quality, evidence quality, Bull/Bear challenge and valuation together without collapsing them into a black-box BUY/SELL score.")
st.info(
    "This workspace produces a **research decision state**, not an investment recommendation. "
    "System synthesis and your own Investor Review remain separate."
)

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from Guided Research first.")
    st.page_link("main.py", label="← Return to Guided Research")
    st.stop()

# Preserve investor reviews even when the system synthesis is refreshed.
existing_reviews = {
    c.company: dict((c.decision_synthesis or {}).get("investor_review") or {})
    for c in run.companies.values()
}

c1, c2 = st.columns([1, 4])
if c1.button("Refresh decision synthesis", type="primary"):
    rows = synthesize_run(run)
    for company in run.companies.values():
        review = existing_reviews.get(company.company) or {}
        if review:
            company.decision_synthesis["investor_review"] = review
    run.save(RUNS)
    st.success(f"Synthesized {len(rows)} companies.")
else:
    rows = [c.decision_synthesis for c in run.companies.values() if c.decision_synthesis]

c2.write(
    "Use this after Research Confidence, thesis challenge and Valuation Intelligence. "
    "Missing upstream work remains visible instead of being converted into false conviction."
)

if not rows:
    st.warning("No decision synthesis exists yet. Refresh the synthesis after the upstream research/valuation stages have meaningful results.")
    st.page_link("pages/8_Valuation_Intelligence.py", label="Open Valuation Intelligence →")
    st.stop()

summary = run.stage_summary.get("decision_synthesis", {})
ready_count = (summary.get("readiness") or {}).get("READY_FOR_INVESTOR_REVIEW", sum(1 for r in rows if r.get("decision_readiness") == "READY_FOR_INVESTOR_REVIEW"))
high_priority = sum(1 for r in rows if r.get("decision_state") == "HIGH_PRIORITY_RESEARCH_CANDIDATE")
needs_more = sum(1 for r in rows if r.get("decision_readiness") != "READY_FOR_INVESTOR_REVIEW")

st.markdown("## At a glance")
a, b, c, d = st.columns(4)
a.metric("Companies synthesized", len(rows))
b.metric("Ready for investor review", ready_count)
c.metric("High-priority research candidates", high_priority)
d.metric("Need upstream work", needs_more)

st.caption(
    "High-priority research candidate means the current evidence/thesis/valuation combination deserves attention. "
    "It does not mean BUY, does not predict returns and does not prescribe a portfolio weight."
)

st.markdown("## Research decision overview")
overview = []
for r in rows:
    dims = r.get("dimensions") or {}
    rq = dims.get("research_quality") or {}
    fin = dims.get("financial_quality") or {}
    thesis = dims.get("thesis") or {}
    val = dims.get("valuation") or {}
    investor = r.get("investor_review") or {}
    overview.append({
        "Company": r.get("company"),
        "System state": r.get("decision_label") or DECISION_STATES.get(r.get("decision_state"), r.get("decision_state")),
        "Readiness": r.get("decision_readiness"),
        "Research quality": rq.get("state"),
        "Financial": fin.get("effective_decision"),
        "Thesis": thesis.get("status"),
        "Fragility": thesis.get("fragility"),
        "Valuation posture": val.get("state"),
        "Base vs captured %": val.get("base_vs_captured_pct"),
        "Investor review": investor.get("stance", "UNREVIEWED"),
    })
st.dataframe(pd.DataFrame(overview), use_container_width=True, hide_index=True)

st.markdown("## Inspect one company")
company_names = [r.get("company") for r in rows if r.get("company")]
chosen = st.selectbox("Company", company_names)
company = next(c for c in run.companies.values() if c.company == chosen)
result = company.decision_synthesis or next(r for r in rows if r.get("company") == chosen)
dims = result.get("dimensions") or {}
rq = dims.get("research_quality") or {}
fin = dims.get("financial_quality") or {}
thesis = dims.get("thesis") or {}
val = dims.get("valuation") or {}

m1, m2, m3, m4 = st.columns(4)
m1.metric("System synthesis", result.get("decision_label") or result.get("decision_state"))
m2.metric("Research quality", rq.get("state", "—"))
m3.metric("Thesis", thesis.get("status", "—"))
base_delta = val.get("base_vs_captured_pct")
m4.metric("Base vs captured price", f"{base_delta:+.1f}%" if base_delta is not None else "—")

if result.get("decision_readiness") == "READY_FOR_INVESTOR_REVIEW":
    st.success("The implemented upstream gates are complete enough for an investor review of this research case.")
else:
    st.warning("This case is not ready for a decision-quality investor review yet. Complete the blockers below first.")

st.markdown("### Why the system reached this state")
for item in result.get("reasons") or []:
    st.write(f"- {item}")

if result.get("blockers"):
    st.markdown("### Current blockers")
    for item in result.get("blockers") or []:
        st.write(f"- {item}")

st.markdown("### Decision dimensions")
dimension_rows = [
    {"Dimension": "Research quality", "State": rq.get("state"), "Context": f"Confidence score {rq.get('score')}" if rq.get("score") is not None else "Not assessed"},
    {"Dimension": "Financial quality", "State": fin.get("effective_decision"), "Context": f"System: {fin.get('system_decision')} · data coverage {fin.get('data_confidence')}%"},
    {"Dimension": "Thesis challenge", "State": thesis.get("status"), "Context": f"Balance {thesis.get('balance')} · fragility {thesis.get('fragility')}"},
    {"Dimension": "Valuation posture", "State": val.get("state"), "Context": val.get("reason")},
]
st.dataframe(pd.DataFrame(dimension_rows), use_container_width=True, hide_index=True)

left, right = st.columns(2)
with left:
    st.markdown("### What must be true")
    items = result.get("what_must_be_true") or []
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.caption("No explicit Bull assumptions were extracted. Inspect Bull/Bear evidence directly before treating this as complete.")

    st.markdown("### Unresolved questions")
    items = result.get("unresolved_questions") or []
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.caption("No unresolved question is currently recorded by this synthesis contract.")

with right:
    st.markdown("### What would invalidate / weaken the case")
    items = result.get("invalidation_conditions") or result.get("what_could_lower_confidence") or []
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.caption("No explicit invalidation condition was extracted. Treat that as a research gap rather than as safety.")

    st.markdown("### What could strengthen the case")
    items = result.get("what_could_raise_confidence") or []
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.caption("No additional strengthening action is currently recorded.")

st.markdown("## Your Investor Review (optional)")
st.caption("Your judgement is stored separately from the system synthesis. Refreshing the system should not silently rewrite your view.")
existing_review = dict(result.get("investor_review") or {})
stance_options = ["UNREVIEWED", "AGREE_WITH_SYSTEM", "NEED_MORE_RESEARCH", "WATCH_CLOSELY", "PASS_FOR_NOW", "HIGH_INTEREST"]
default_stance = existing_review.get("stance", "UNREVIEWED")
stance = st.selectbox("Your stance", stance_options, index=stance_options.index(default_stance) if default_stance in stance_options else 0)
conviction = st.selectbox(
    "Your conviction in your own current view",
    ["UNSET", "LOW", "MEDIUM", "HIGH"],
    index=["UNSET", "LOW", "MEDIUM", "HIGH"].index(existing_review.get("conviction", "UNSET")) if existing_review.get("conviction", "UNSET") in {"UNSET", "LOW", "MEDIUM", "HIGH"} else 0,
    help="This is your self-recorded judgement, not a system-generated probability or recommendation.",
)
notes = st.text_area("Your notes", value=existing_review.get("notes", ""), height=110)
if st.button("Save Investor Review"):
    result["investor_review"] = {
        "stance": stance,
        "conviction": conviction,
        "notes": notes.strip(),
    }
    company.decision_synthesis = result
    run.save(RUNS)
    st.success("Investor Review saved separately from the system synthesis.")

st.markdown("## How to interpret the system states")
st.markdown(
    """
- **High-priority research candidate** — research quality passed, Bull thesis survived, valuation context is favorable enough to deserve attention, and fragility is not extreme.
- **Positive thesis near base valuation** — thesis survived, but price/value context is not offering a large base-scenario discount.
- **Positive thesis but valuation stretched** — thesis survived, but current assumptions do not support the captured price.
- **Contested research case** — both Bull and Bear interpretations remain material.
- **Fragile research case** — too much depends on unresolved assumptions/contradictions.
- **Risk-dominated research case** — Bear evidence currently dominates.
- **Financial quality conflict** — later research conflicts with an earlier unoverridden financial-quality gate.
- **More research / thesis challenge / valuation incomplete** — upstream work is not complete enough for decision synthesis.
"""
)

st.warning(result.get("system_scope"))

st.divider()
st.page_link("pages/8_Valuation_Intelligence.py", label="← Review Valuation Intelligence")
st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="← Review Bull/Bear evidence")
st.page_link("main.py", label="← Guided Research")
