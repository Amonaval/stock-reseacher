from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from research_analysis_orchestrator import plan_research_for_run, run_thesis_analysis

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Deep Research & Thesis Challenge · Personal AI Stock Researcher", layout="wide")
st.title("Deep Research & Thesis Challenge")
st.caption(
    "Allocate research effort transparently, inspect why each company is at its current depth, "
    "and independently challenge evidence-ready theses. No buy/sell recommendation is produced here."
)

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from the main Research page first.")
    st.stop()

st.markdown("## 1. Deep-research budget")
st.write(
    "Budgets control how many companies receive increasingly expensive analysis. "
    "They do not represent conviction or expected return. Companies outside a budget remain queued rather than disappearing."
)

current_plan = st.session_state.get("research_plan") or {}
existing_budgets = current_plan.get("budgets") or (
    {"STRUCTURED": 100, "TARGETED": 50, "DEEP": 25, "ADVERSARIAL": 15}
    if str(run.research_depth).lower() == "deep"
    else {"STRUCTURED": 60, "TARGETED": 30, "DEEP": 15, "ADVERSARIAL": 8}
)

b1, b2, b3, b4 = st.columns(4)
structured_budget = b1.number_input("Structured", min_value=0, max_value=1000, value=int(existing_budgets.get("STRUCTURED", 100)))
targeted_budget = b2.number_input("Targeted", min_value=0, max_value=1000, value=int(existing_budgets.get("TARGETED", 50)))
deep_budget = b3.number_input("Deep", min_value=0, max_value=1000, value=int(existing_budgets.get("DEEP", 25)))
adversarial_budget = b4.number_input("Bull/Bear", min_value=0, max_value=1000, value=int(existing_budgets.get("ADVERSARIAL", 15)))

if st.button("Allocate research depth", type="primary"):
    budgets = {
        "STRUCTURED": int(structured_budget),
        "TARGETED": int(targeted_budget),
        "DEEP": int(deep_budget),
        "ADVERSARIAL": int(adversarial_budget),
    }
    plan = plan_research_for_run(run, budgets)
    st.session_state.research_plan = plan
    run.save(RUNS)
    st.success(f"Research-depth plan created: {plan.get('counts', {})}")
    current_plan = plan

plan = st.session_state.get("research_plan") or current_plan

if not plan:
    st.info(
        "No deep-research plan exists yet. Run company research first, then allocate research depth here. "
        "The planner uses persistent company dossiers, so it does not depend on a hidden CSV handoff."
    )
    st.stop()

st.markdown("## 2. What the planner decided")
counts = plan.get("counts", {})
metric_cols = st.columns(7)
for idx, stage in enumerate(["ADVERSARIAL", "DEEP", "TARGETED", "STRUCTURED", "RESEARCH_QUEUE", "SOURCE_GAP", "FINANCIAL_HOLD"]):
    metric_cols[idx].metric(stage.replace("_", " ").title(), counts.get(stage, 0))

with st.expander("What each research depth means", expanded=False):
    st.markdown(
        """
- **SOURCE GAP** — we do not yet have enough authoritative material to justify deeper work.
- **STRUCTURED** — gather/organize core company evidence and fill basic analyst missions.
- **TARGETED** — resolve specific missing questions, source classes or weak themes.
- **DEEP** — investigate thesis breakers, management claims, cash conversion, competition and unresolved contradictions.
- **BULL/BEAR (ADVERSARIAL)** — enough evidence exists to independently build and challenge the strongest positive and negative interpretations.
- **RESEARCH QUEUE** — the evidence gate passed, but the current research budget is already full.
- **FINANCIAL HOLD** — the financial stage has not approved expensive company research.
        """
    )

utilization = plan.get("budget_utilization", {})
if utilization:
    st.markdown("### Budget utilization")
    udf = pd.DataFrame([
        {
            "Stage": stage,
            "Budget": info.get("budget"),
            "Passed evidence gate": info.get("passed_gate"),
            "Admitted now": info.get("admitted"),
            "Queued": info.get("queued"),
        }
        for stage, info in utilization.items()
    ])
    st.dataframe(udf, use_container_width=True, hide_index=True)

rows = plan.get("rows", [])
if rows:
    st.markdown("### Company-by-company allocation")
    pdf = pd.DataFrame(rows)
    show = [c for c in [
        "company", "stage", "system_stage", "research_state", "reason",
        "mission_coverage", "document_coverage", "evidence_quality",
        "research_readiness", "risk_items", "open_questions",
        "missing_document_types", "research_priority",
    ] if c in pdf.columns]
    st.dataframe(pdf[show], use_container_width=True, hide_index=True)

st.markdown("## 3. Inspect why a company is at this depth")
company_names = [r.get("company") for r in rows if r.get("company")]
if company_names:
    chosen = st.selectbox("Company", company_names, key="depth_inspect_company")
    row = next(r for r in rows if r.get("company") == chosen)
    company = run.ensure_company(chosen)
    dossier = company.research_dossier or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Allocated stage", row.get("stage"))
    c2.metric("Mission coverage", f"{row.get('mission_coverage', 0)}%")
    c3.metric("Evidence quality", row.get("evidence_quality", 0))
    c4.metric("Research readiness", row.get("research_readiness", 0))
    st.write("**Why:**", row.get("reason"))

    if row.get("stage") == "RESEARCH_QUEUE":
        st.info(f"This company passed the {row.get('original_stage')} evidence gate but is waiting because of the current research budget.")
    if row.get("stage") == "SOURCE_GAP":
        st.warning("Deeper analysis is intentionally blocked until source/evidence gaps are resolved or you explicitly override the next stage.")

    missions = dossier.get("missions", [])
    if missions:
        st.markdown("### Analyst mission coverage")
        st.dataframe(
            pd.DataFrame([
                {
                    "Mission": m.get("label"),
                    "Status": m.get("status"),
                    "Evidence items": m.get("evidence_count"),
                    "Why it matters": m.get("why"),
                }
                for m in missions
            ]),
            use_container_width=True,
            hide_index=True,
        )

    if company.research_questions:
        st.markdown("### Questions still open")
        for q in company.research_questions:
            st.write(f"- {q.get('question')}")
            if q.get("reason"):
                st.caption(q.get("reason"))

st.divider()
st.markdown("## 4. Bull/Bear thesis challenge")
st.write(
    "The system builds the strongest evidence-supported positive case and the strongest evidence-supported negative case, "
    "then a neutral challenge compares them. Thesis balance is evidence support—not a probability of return."
)

system_ready = [r.get("company") for r in rows if r.get("stage") == "ADVERSARIAL" and r.get("company")]
evidence_candidates = [
    c.company for c in run.companies.values()
    if c.evidence and (c.research_state in {"EVIDENCE_READY", "RESEARCH_INCOMPLETE"})
]
selectable = list(dict.fromkeys(system_ready + evidence_candidates))
selected_for_challenge = st.multiselect(
    "Companies to challenge",
    selectable,
    default=system_ready,
    help=(
        "System-ready companies are selected by default. You may explicitly add another evidence-bearing company; "
        "its weaker readiness remains visible in the result."
    ),
)

if not system_ready:
    st.info(
        "No company currently passes the automatic adversarial evidence gate. You can improve company research first, "
        "adjust research budgets, or explicitly select an evidence-bearing company for analysis."
    )

if st.button("Run Bull/Bear thesis challenge", disabled=not selected_for_challenge):
    bar = st.progress(0)
    status = st.empty()
    try:
        def challenge_progress(i, n, company):
            bar.progress(i / max(n, 1))
            status.write(f"{i}/{n} · challenging {company}")

        results = run_thesis_analysis(
            run,
            plan,
            company_names=selected_for_challenge,
            progress=challenge_progress,
        )
        st.session_state.adversarial_results = results
        run.save(RUNS)
        status.empty()
        st.success(f"Thesis challenge completed for {len(results)} companies.")
    except Exception as exc:
        run.log("ADVERSARIAL", "ANALYSIS_FAILED", str(exc), status="ERROR")
        run.save(RUNS)
        st.error(str(exc))

results = st.session_state.get("adversarial_results") or [
    c.adversarial_result for c in run.companies.values() if getattr(c, "adversarial_result", None)
]

if results:
    st.markdown("## 5. Thesis challenge results")
    summary_rows = []
    for result in results:
        classification = result.get("classification", {}) or {}
        challenge = result.get("challenge", {}) or {}
        summary_rows.append({
            "Company": result.get("company"),
            "Research state": classification.get("thesis_status"),
            "Thesis balance": classification.get("thesis_balance"),
            "Fragility": classification.get("fragility_score"),
            "Adversarial readiness": classification.get("adversarial_readiness"),
            "Bull strength": classification.get("bull_strength"),
            "Bear strength": classification.get("bear_strength"),
            "Mode": challenge.get("mode"),
            "Unresolved questions": len(classification.get("unresolved_questions") or []),
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    inspect = st.selectbox("Inspect thesis challenge", [r.get("company") for r in results], key="challenge_inspect_company")
    result = next(r for r in results if r.get("company") == inspect)
    bull = (result.get("bull_bear") or {}).get("bull", {}) or {}
    bear = (result.get("bull_bear") or {}).get("bear", {}) or {}
    challenge = result.get("challenge", {}) or {}
    classification = result.get("classification", {}) or {}

    st.markdown(f"### {inspect}")
    a, b, c, d = st.columns(4)
    a.metric("Research state", classification.get("thesis_status"))
    b.metric("Thesis balance", classification.get("thesis_balance"))
    c.metric("Fragility", classification.get("fragility_score"))
    d.metric("Adversarial readiness", classification.get("adversarial_readiness"))
    st.caption("Thesis balance >50 means the bull case is better supported by the current evidence set; it is not a return forecast.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Bull researcher")
        st.write(bull.get("summary", ""))
        for p in bull.get("points", []) or []:
            st.write(f"- {p.get('point')}")
            if p.get("evidence_ids"):
                st.caption("Evidence: " + ", ".join(str(x) for x in p.get("evidence_ids") or []))
        if bull.get("key_assumptions"):
            st.markdown("**Key assumptions**")
            for x in bull.get("key_assumptions") or []:
                st.write(f"- {x}")
        if bull.get("invalidation_conditions"):
            st.markdown("**What would invalidate the bull case**")
            for x in bull.get("invalidation_conditions") or []:
                st.write(f"- {x}")

    with right:
        st.markdown("#### Bear / forensic researcher")
        st.write(bear.get("summary", ""))
        for p in bear.get("points", []) or []:
            st.write(f"- {p.get('point')}")
            if p.get("evidence_ids"):
                st.caption("Evidence: " + ", ".join(str(x) for x in p.get("evidence_ids") or []))
        if bear.get("key_assumptions"):
            st.markdown("**Key assumptions**")
            for x in bear.get("key_assumptions") or []:
                st.write(f"- {x}")
        if bear.get("invalidation_conditions"):
            st.markdown("**What would invalidate the bear case**")
            for x in bear.get("invalidation_conditions") or []:
                st.write(f"- {x}")

    st.markdown("#### Neutral challenge")
    st.write(challenge.get("challenge_summary", ""))
    if challenge.get("contradictions"):
        st.markdown("**Contradictions / disputed points**")
        cdf = pd.DataFrame(challenge.get("contradictions") or [])
        st.dataframe(cdf, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Bull points that survived challenge**")
        for p in challenge.get("surviving_bull_points") or []:
            st.write(f"- {p.get('point') or p.get('claim') or p}")
        st.markdown("**Fragility flags**")
        for x in challenge.get("fragility_flags") or []:
            st.write(f"- {x}")
    with c2:
        st.markdown("**Bear points that survived challenge**")
        for p in challenge.get("surviving_bear_points") or []:
            st.write(f"- {p.get('point') or p.get('claim') or p}")
        st.markdown("**Unresolved questions**")
        for x in challenge.get("unresolved_questions") or []:
            st.write(f"- {x}")

    missing = list(dict.fromkeys((bull.get("missing_evidence") or []) + (bear.get("missing_evidence") or [])))
    if missing:
        st.markdown("#### Evidence still needed")
        for x in missing:
            st.write(f"- {x}")

    if challenge.get("mode") == "deterministic":
        st.warning(
            "This challenge used deterministic evidence comparison because no compatible LLM was configured. "
            "It can surface source-backed positive/negative evidence, but semantic contradiction resolution is intentionally limited."
        )
else:
    st.info("No Bull/Bear thesis analysis has been run yet.")

st.divider()
st.caption(
    "Constitution rule: deep research allocates attention; Bull/Bear challenges a thesis. Neither stage produces an investment recommendation or expected-return probability."
)
