from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from navigation import render_navigation
from evidence_confidence import assess_run_evidence_confidence
from valuation_intelligence import (
    VALUATION_FAMILIES,
    classify_valuation_family,
    value_company,
    value_run,
)

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Valuation Intelligence · Personal AI Stock Researcher", page_icon="🧮", layout="wide")
render_navigation()

st.title("🧮 Valuation Intelligence")
st.caption("Translate evidence-backed research into explicit Bear / Base / Bull valuation scenarios without pretending fair value is a precise prediction.")
st.info(
    "Research confidence and investment attractiveness are separate. A company can have HIGH research confidence and still look expensive, fragile or unattractive."
)
st.caption("Price comparisons use the market price captured during the run's financial-research stage. Valuation Intelligence v1 does not live-refresh quotes.")

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from Guided Research first.")
    st.page_link("main.py", label="← Return to Guided Research")
    st.stop()

# Ensure the quality gate reflects the latest dossier before valuation.
confidence_rows = assess_run_evidence_confidence(run)
run.save(RUNS)

st.markdown("## 1. Research-quality gate")
ready = [r for r in confidence_rows if r.get("valuation_context") == "READY_FOR_VALUATION_CONTEXT"]
blocked = [r for r in confidence_rows if r.get("valuation_context") != "READY_FOR_VALUATION_CONTEXT"]
c1, c2, c3 = st.columns(3)
c1.metric("Research dossiers assessed", len(confidence_rows))
c2.metric("Ready for valuation context", len(ready))
c3.metric("Need more research", len(blocked))

st.caption(
    "Automatic valuation is allowed only when the research-quality gate has no critical evidence gap. "
    "You may explicitly override this for exploration, but the result remains visibly marked as lower-confidence."
)

if st.button("Run valuation for all research-ready companies", type="primary"):
    rows = value_run(run)
    run.save(RUNS)
    st.session_state.valuation_results = rows
    st.success(f"Valuation context assessed for {len(rows)} companies.")

results = st.session_state.get("valuation_results") or [
    c.valuation for c in run.companies.values() if getattr(c, "valuation", None)
]

if results:
    st.markdown("## 2. Valuation overview")
    overview = []
    for r in results:
        scenarios = r.get("scenarios") or {}
        overview.append({
            "Company": r.get("company"),
            "Status": r.get("status"),
            "Research confidence": (r.get("research_gate") or {}).get("state"),
            "Family": (r.get("valuation_family") or {}).get("label"),
            "Method": r.get("method") or "—",
            "Captured price": r.get("current_price"),
            "Bear value": (scenarios.get("bear") or {}).get("fair_value"),
            "Base value": (scenarios.get("base") or {}).get("fair_value"),
            "Bull value": (scenarios.get("bull") or {}).get("fair_value"),
            "Base vs captured price %": (scenarios.get("base") or {}).get("upside_downside_pct"),
        })
    st.dataframe(pd.DataFrame(overview), use_container_width=True, hide_index=True)
else:
    st.info("No valuation result exists yet. Run valuation above or inspect/tune one company below.")

companies = [c for c in run.companies.values() if c.financial_assessment]
if not companies:
    st.warning("No company has financial context yet.")
    st.stop()

st.markdown("## 3. Inspect / tune one company")
chosen_name = st.selectbox("Company", [c.company for c in companies])
company = next(c for c in companies if c.company == chosen_name)
auto_family = classify_valuation_family(company)
confidence = (company.research_dossier or {}).get("evidence_confidence") or {}
existing = company.valuation or {}

x1, x2, x3, x4 = st.columns(4)
x1.metric("Research confidence", confidence.get("research_confidence_state", "NOT ASSESSED"))
x2.metric("Confidence score", confidence.get("research_confidence_score", "—"))
x3.metric("Captured price", (company.financial_assessment or {}).get("price") or "—")
x4.metric("Auto family", auto_family.get("label"))

st.write("**Why this valuation family:**", auto_family.get("reason"))
st.caption(
    "Automatic family classification is heuristic. It uses the research evidence, not a hidden sector database. "
    "Override it whenever the business model is misclassified."
)

with st.expander("Valuation controls & assumptions", expanded=not bool(existing)):
    family_options = ["AUTO"] + list(VALUATION_FAMILIES)
    family_override = st.selectbox(
        "Valuation family",
        family_options,
        format_func=lambda x: "Auto — infer from research evidence" if x == "AUTO" else VALUATION_FAMILIES.get(x, x),
    )
    selected_family = auto_family.get("family") if family_override == "AUTO" else family_override
    allow_override = st.checkbox(
        "Explore valuation even if Research Confidence gate is blocked",
        value=False,
        help="The output will retain an explicit warning. This does not change the underlying research-confidence state.",
    )

    assumptions = {}
    if selected_family == "FINANCIAL_PB":
        st.markdown("**Bank / NBFC assumptions**")
        a1, a2, a3 = st.columns(3)
        assumptions["bear_growth"] = a1.number_input("Bear long-term growth", 0.0, 10.0, 3.0, 0.5) / 100
        assumptions["base_growth"] = a2.number_input("Base long-term growth", 0.0, 10.0, 5.0, 0.5) / 100
        assumptions["bull_growth"] = a3.number_input("Bull long-term growth", 0.0, 10.0, 7.0, 0.5) / 100
        b1, b2, b3 = st.columns(3)
        assumptions["bear_cost_of_equity"] = b1.number_input("Bear cost of equity", 8.0, 25.0, 14.0, 0.5) / 100
        assumptions["base_cost_of_equity"] = b2.number_input("Base cost of equity", 8.0, 25.0, 12.0, 0.5) / 100
        assumptions["bull_cost_of_equity"] = b3.number_input("Bull cost of equity", 8.0, 25.0, 11.0, 0.5) / 100
        st.caption("The v1 bank/NBFC method uses justified P/B = (sustainable ROE − growth) / (cost of equity − growth).")
    elif selected_family == "INSURANCE_EMBEDDED_VALUE":
        st.warning(
            "Valuation Intelligence v1 deliberately does not substitute generic P/E or P/B for insurers. "
            "A proper insurer model needs embedded value, value of new business and related insurance-specific inputs."
        )
        st.caption("You can still change the family manually if the automatic classification is wrong, but forcing a generic framework should be treated as an operator override rather than the system default.")
    elif selected_family == "INSUFFICIENT":
        st.info("No valuation method is selected. Choose another family only if you can justify it from the business model and available data.")
    else:
        st.markdown("**Earnings-multiple assumptions**")
        fa = company.financial_assessment or {}
        suggested = fa.get("five_year_pe") or fa.get("industry_pe") or fa.get("pe") or 15.0
        base_multiple = st.number_input("Base P/E multiple", min_value=1.0, max_value=100.0, value=float(suggested), step=0.5)
        c1, c2 = st.columns(2)
        bear_multiple = c1.number_input("Bear P/E multiple (0 = system default)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        bull_multiple = c2.number_input("Bull P/E multiple (0 = system default)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
        assumptions["base_multiple"] = base_multiple
        if bear_multiple > 0:
            assumptions["bear_multiple"] = bear_multiple
        if bull_multiple > 0:
            assumptions["bull_multiple"] = bull_multiple
        st.caption("Prefer the 5-year or industry multiple as context. If neither exists, current P/E is only a labeled fallback—not an intrinsic-value anchor.")

    if st.button("Recalculate this company", type="primary"):
        result = value_company(
            company,
            family_override=None if family_override == "AUTO" else family_override,
            assumptions=assumptions,
            allow_gate_override=allow_override,
        )
        company.valuation = result
        run.log(
            "VALUATION",
            "COMPANY_VALUED" if result.get("status") == "VALUED" else "COMPANY_VALUATION_BLOCKED",
            f"{result.get('status')} using {(result.get('valuation_family') or {}).get('label')}: {result.get('method') or '; '.join(result.get('warnings') or [])}",
            company=company.company,
            status="INFO" if result.get("status") == "VALUED" else "WARN",
        )
        run.save(RUNS)
        st.session_state.valuation_results = [c.valuation for c in run.companies.values() if c.valuation]
        st.rerun()

result = company.valuation or {}
if result:
    st.markdown("## 4. Scenario valuation")
    if result.get("status") != "VALUED":
        st.warning("Valuation is currently blocked or lacks required inputs.")
        for warning in result.get("warnings") or []:
            st.write(f"- {warning}")
        gaps = (result.get("research_gate") or {}).get("critical_gaps") or []
        if gaps:
            st.markdown("**Research gaps blocking reliable valuation**")
            for gap in gaps:
                st.write(f"- {gap}")
    else:
        scenarios = result.get("scenarios") or {}
        cols = st.columns(3)
        for col, name in zip(cols, ["bear", "base", "bull"]):
            scenario = scenarios.get(name) or {}
            col.markdown(f"### {name.title()}")
            col.metric("Fair-value scenario", f"₹{scenario.get('fair_value', 0):,.2f}")
            delta = scenario.get("upside_downside_pct")
            if delta is not None:
                col.metric("Vs captured price", f"{delta:+.1f}%")
            if scenario.get("multiple") is not None:
                col.caption(f"P/E assumption: {scenario.get('multiple')}×")
            if scenario.get("fair_pb") is not None:
                col.caption(f"P/B assumption: {scenario.get('fair_pb')}× · ROE {scenario.get('sustainable_roe')}% · g {scenario.get('growth')}%")

        family = result.get("valuation_family") or {}
        inputs = result.get("valuation_inputs") or {}
        st.write("**Method:**", result.get("method"))
        st.write("**Family:**", family.get("label"))
        st.write("**Classification basis:**", family.get("basis"))
        if inputs.get("eps_basis"):
            eps = inputs.get("eps_basis") or {}
            st.write("**Normalized EPS:**", eps.get("normalized_eps"), f"({eps.get('method')})")
        if inputs.get("multiple_anchor"):
            anchor = inputs.get("multiple_anchor") or {}
            st.write("**Multiple anchors:**", anchor.get("anchors"))
            st.write("**Anchor quality:**", anchor.get("quality"))
        if inputs.get("book_value") is not None:
            st.write("**Book value:**", inputs.get("book_value"), "· **Observed ROE:**", inputs.get("observed_roe"))
        if inputs.get("assumption_note"):
            st.info(inputs.get("assumption_note"))

        if result.get("warnings"):
            st.warning("\n".join(f"• {x}" for x in result.get("warnings") or []))

        st.markdown("### What would change this valuation?")
        if (result.get("valuation_family") or {}).get("family") == "FINANCIAL_PB":
            st.markdown("- sustainable ROE\n- long-term growth\n- cost of equity / risk perception\n- book-value quality and credit losses")
        else:
            st.markdown("- normalized EPS / earnings durability\n- the justified market multiple\n- growth and margin normalization\n- cyclicality / capital intensity\n- new evidence that changes the Bull/Bear thesis")

        st.caption(result.get("disclaimer", "Valuation is assumption-driven research context, not a target-price prediction."))

st.divider()
st.page_link("pages/7_Research_Confidence.py", label="← Review Research Confidence")
st.page_link("main.py", label="← Guided Research")
