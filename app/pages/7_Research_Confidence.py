from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from navigation import render_navigation
from evidence_confidence import assess_run_evidence_confidence

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Research Confidence · Personal AI Stock Researcher", page_icon="🧭", layout="wide")
render_navigation()

st.title("🧭 Research Confidence")
st.caption("Judge the quality of the research before trusting any future valuation or conviction layer.")
st.info(
    "This page measures **confidence in the evidence and research process** — not whether the stock is attractive. "
    "A company can have high research confidence and still have a weak or bearish investment thesis."
)

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from Guided Research first.")
    st.page_link("main.py", label="← Return to Guided Research")
    st.stop()

existing = []
for company in run.companies.values():
    result = (company.research_dossier or {}).get("evidence_confidence")
    if result:
        existing.append(result)

c1, c2 = st.columns([1, 4])
if c1.button("Assess / refresh confidence", type="primary"):
    existing = assess_run_evidence_confidence(run)
    run.save(RUNS)
    st.success(f"Assessed research confidence for {len(existing)} companies.")
else:
    existing = sorted(existing, key=lambda x: -float(x.get("research_confidence_score") or 0))

c2.write(
    "Use this after company research and ideally after Bull/Bear challenge. "
    "It is the quality gate we will use before adding valuation intelligence."
)

if not existing:
    st.warning("No research-confidence assessment exists yet. Research at least one company, then click **Assess / refresh confidence**.")
    st.page_link("pages/3_Research_Evidence.py", label="Open Research Evidence →")
    st.stop()

summary = run.stage_summary.get("evidence_confidence", {})
st.markdown("## At a glance")
state_counts = summary.get("states", {})
a, b, c, d = st.columns(4)
a.metric("Companies assessed", summary.get("companies", len(existing)))
b.metric("High confidence", state_counts.get("HIGH_RESEARCH_CONFIDENCE", 0))
c.metric("Moderate confidence", state_counts.get("MODERATE_RESEARCH_CONFIDENCE", 0))
d.metric("Valuation context ready", summary.get("valuation_context_ready", sum(1 for x in existing if x.get("valuation_context") == "READY_FOR_VALUATION_CONTEXT")))

st.caption(
    "Valuation context ready means the current dossier is sufficiently grounded to support valuation work. "
    "It does not mean the company is undervalued or investable."
)

st.markdown("## Company confidence overview")
rows = []
for result in existing:
    dims = result.get("dimensions") or {}
    rows.append({
        "Company": result.get("company"),
        "Research confidence": result.get("research_confidence_state"),
        "Score": result.get("research_confidence_score"),
        "Source authority": dims.get("source_authority"),
        "Freshness": dims.get("source_freshness"),
        "Traceability": dims.get("evidence_traceability"),
        "Mission coverage": dims.get("fundamental_mission_coverage"),
        "Triangulation": dims.get("cross_source_triangulation"),
        "Downside coverage": dims.get("downside_evidence_coverage"),
        "Open questions": result.get("open_questions"),
        "Critical gaps": len(result.get("critical_gaps") or []),
        "Next quality gate": result.get("valuation_context"),
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("## Inspect one company")
company_names = [r.get("company") for r in existing if r.get("company")]
chosen = st.selectbox("Company", company_names)
result = next(r for r in existing if r.get("company") == chosen)
dims = result.get("dimensions") or {}

m1, m2, m3, m4 = st.columns(4)
m1.metric("Research confidence", result.get("research_confidence_state"))
m2.metric("Confidence score", result.get("research_confidence_score"))
m3.metric("Documents", result.get("documents"))
m4.metric("Evidence items", result.get("evidence_items"))

if result.get("valuation_context") == "READY_FOR_VALUATION_CONTEXT":
    st.success("Current evidence is strong enough to support a future valuation-context analysis.")
else:
    st.warning("More research is recommended before relying on a future valuation/conviction layer.")

st.markdown("### Why the research has this confidence")
labels = {
    "source_authority": "Source authority",
    "source_freshness": "Source freshness",
    "evidence_traceability": "Evidence traceability",
    "fundamental_mission_coverage": "Fundamental mission coverage",
    "cross_source_triangulation": "Cross-source triangulation",
    "downside_evidence_coverage": "Downside / governance evidence",
    "contradiction_handling": "Contradiction handling",
    "financial_data_coverage": "Financial-data coverage",
}
df = pd.DataFrame([
    {"Dimension": labels.get(key, key), "Score / 100": value}
    for key, value in dims.items()
])
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("### Critical research gaps")
gaps = result.get("critical_gaps") or []
if gaps:
    for gap in gaps:
        st.write(f"- {gap}")
else:
    st.success("No current critical evidence-quality gap was detected by this contract.")

c1, c2 = st.columns(2)
with c1:
    st.markdown("### Themes covered")
    themes = result.get("covered_themes") or []
    if themes:
        for theme in themes:
            st.write(f"- {theme.replace('_', ' ').title()}")
    else:
        st.caption("No research themes covered yet.")
with c2:
    st.markdown("### Themes supported by multiple documents")
    themes = result.get("triangulated_themes") or []
    if themes:
        for theme in themes:
            st.write(f"- {theme.replace('_', ' ').title()}")
    else:
        st.caption("No theme is currently supported by evidence from multiple documents.")

st.markdown("## How to read this")
st.markdown(
    """
- **High research confidence** — strong source/evidence foundation with no current critical gap.
- **Moderate research confidence** — useful research exists, but one or two important quality gaps remain.
- **Low research confidence** — do not let later valuation or conviction outputs create false precision; strengthen the dossier first.

The overall score is a **quality-control aid**, not an investment score. The dimensions and gaps matter more than the number itself.
"""
)

st.page_link("pages/3_Research_Evidence.py", label="Inspect underlying evidence →")
st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="Inspect Bull/Bear challenge →")
st.page_link("main.py", label="← Return to Guided Research")
