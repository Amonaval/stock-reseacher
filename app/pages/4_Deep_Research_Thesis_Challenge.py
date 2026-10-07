from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from navigation import render_navigation
from research_analysis_orchestrator import plan_research_for_run
from background_jobs import start_job, sync_session_from_jobs, active_jobs

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Deep Research & Thesis Challenge · Personal AI Stock Researcher", page_icon="⚖️", layout="wide")
render_navigation()

st.title("⚖️ Deep Research & Thesis Challenge")
st.caption("First resolve unresolved evidence gaps. Only then challenge evidence-ready theses with independent Bull/Bear analysis.")
st.info("**Three jobs:** (1) decide where more research effort belongs, (2) execute the deeper evidence work, (3) stress-test the thesis. This page does not produce buy/sell recommendations.")

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from Guided Research first.")
    st.page_link("main.py", label="← Return to Guided Research")
    st.stop()

sync_session_from_jobs(st, run.run_id)
run = st.session_state.get("run") or run
busy_jobs = active_jobs(run.run_id)
busy = bool(busy_jobs)
if busy:
    job = busy_jobs[0]
    st.info(f"🧵 Background work continues: **{job.get('label')}** — {job.get('progress_message')} ({float(job.get('progress') or 0)*100:.0f}%). You may navigate away.")
    st.page_link("pages/6_Background_Jobs.py", label="Monitor background work →")

current_plan = st.session_state.get("research_plan") or {}
existing_budgets = current_plan.get("budgets") or (
    {"STRUCTURED": 100, "TARGETED": 50, "DEEP": 25, "ADVERSARIAL": 15}
    if str(run.research_depth).lower() == "deep"
    else {"STRUCTURED": 60, "TARGETED": 30, "DEEP": 15, "ADVERSARIAL": 8}
)

st.markdown("## A. Decide where deeper research belongs")
st.write("Budgets control analyst attention. A company that passes a gate but falls outside the current budget stays in **RESEARCH_QUEUE**—it is not discarded.")

with st.expander("Adjust research-depth budgets", expanded=not bool(current_plan)):
    b1, b2, b3, b4 = st.columns(4)
    structured_budget = b1.number_input("Structured", min_value=0, max_value=1000, value=int(existing_budgets.get("STRUCTURED", 100)))
    targeted_budget = b2.number_input("Targeted", min_value=0, max_value=1000, value=int(existing_budgets.get("TARGETED", 50)))
    deep_budget = b3.number_input("Deep", min_value=0, max_value=1000, value=int(existing_budgets.get("DEEP", 25)))
    adversarial_budget = b4.number_input("Bull/Bear", min_value=0, max_value=1000, value=int(existing_budgets.get("ADVERSARIAL", 15)))
    if st.button("Create / update research-depth plan", type="primary", disabled=busy):
        budgets = {
            "STRUCTURED": int(structured_budget),
            "TARGETED": int(targeted_budget),
            "DEEP": int(deep_budget),
            "ADVERSARIAL": int(adversarial_budget),
        }
        plan = plan_research_for_run(run, budgets)
        st.session_state.research_plan = plan
        run.save(RUNS)
        st.rerun()

plan = st.session_state.get("research_plan") or current_plan
if not plan:
    st.warning("No deep-research plan exists yet. Complete company research first, then create the plan here or from Guided Research.")
    st.page_link("main.py", label="← Return to Guided Research")
    st.stop()

counts = plan.get("counts", {})
metric_cols = st.columns(6)
for idx, stage in enumerate(["ADVERSARIAL", "DEEP", "TARGETED", "STRUCTURED", "RESEARCH_QUEUE", "SOURCE_GAP"]):
    metric_cols[idx].metric(stage.replace("_", " ").title(), counts.get(stage, 0))

with st.expander("What do these stages mean?"):
    st.markdown(
        """
- **SOURCE GAP** — not enough usable source evidence yet.
- **STRUCTURED** — organize core evidence and fill basic research missions.
- **TARGETED** — investigate specific unanswered questions or weak themes.
- **DEEP** — investigate thesis breakers, management claims, cash conversion, competition and missing downside evidence.
- **ADVERSARIAL / BULL-BEAR** — enough evidence exists to independently argue both sides.
- **RESEARCH QUEUE** — the evidence gate passed, but the current budget is full.
- **FINANCIAL HOLD** — the company was not approved for expensive company research.
"""
    )

utilization = plan.get("budget_utilization", {})
if utilization:
    st.markdown("### Budget use")
    st.dataframe(pd.DataFrame([{
        "Stage": stage.replace("_", " ").title(),
        "Budget": info.get("budget"),
        "Passed evidence gate": info.get("passed_gate"),
        "Admitted now": info.get("admitted"),
        "Queued": info.get("queued"),
    } for stage, info in utilization.items()]), use_container_width=True, hide_index=True)

rows = plan.get("rows", [])
if rows:
    st.markdown("### Why each company is at its current depth")
    pdf = pd.DataFrame(rows)
    show = [c for c in [
        "company", "stage", "research_state", "reason", "mission_coverage",
        "document_coverage", "evidence_quality", "research_readiness", "risk_items", "open_questions",
    ] if c in pdf.columns]
    st.dataframe(pdf[show], use_container_width=True, hide_index=True)

    chosen = st.selectbox("Inspect allocation for a company", [r.get("company") for r in rows if r.get("company")])
    row = next(r for r in rows if r.get("company") == chosen)
    company = run.ensure_company(chosen)
    dossier = company.research_dossier or {}
    a, b, c, d = st.columns(4)
    a.metric("Allocated stage", row.get("stage"))
    b.metric("Mission coverage", f"{row.get('mission_coverage', 0)}%")
    c.metric("Evidence quality", row.get("evidence_quality", 0))
    d.metric("Research readiness", row.get("research_readiness", 0))
    st.info(f"**Why:** {row.get('reason')}")

    if dossier.get("missions"):
        with st.expander("Analyst mission coverage"):
            st.dataframe(pd.DataFrame([{
                "Mission": m.get("label"), "Status": m.get("status"), "Evidence items": m.get("evidence_count"), "Why it matters": m.get("why"),
            } for m in dossier.get("missions", [])]), use_container_width=True, hide_index=True)
    if company.research_questions:
        with st.expander("Open research questions", expanded=row.get("stage") in {"SOURCE_GAP", "STRUCTURED", "TARGETED", "DEEP"}):
            for q in company.research_questions:
                st.write(f"- {q.get('question')}")
                if q.get("reason"): st.caption(q.get("reason"))

st.markdown("## B. Execute the deeper evidence work")
needs_work = [r for r in rows if r.get("stage") in {"SOURCE_GAP", "STRUCTURED", "TARGETED", "DEEP"}]
if needs_work:
    st.warning(f"{len(needs_work)} companies still need more evidence before the automatic Bull/Bear gate can open.")
    st.markdown(
        """
This pass is not another score. It actually performs more research: broader source acquisition, additional source classes, preservation of existing evidence, targeted filling of analyst missions, and explicit search for downside/risk evidence. The depth plan is rebuilt automatically afterward.
"""
    )
    selected_deep = st.multiselect(
        "Companies to deepen",
        [r.get("company") for r in needs_work],
        default=[r.get("company") for r in needs_work],
        key="deep_gap_selection",
    )
    use_llm_deep = st.checkbox("Use configured LLM for deeper semantic evidence extraction", value=False)
    if st.button("Resolve evidence gaps in background", type="primary", disabled=busy or not selected_deep):
        start_job(
            "deep_gap_research",
            {
                "run_id": run.run_id,
                "cdp_url": st.session_state.get("cdp_url", "http://127.0.0.1:9222"),
                "company_names": selected_deep,
                "use_llm": bool(use_llm_deep),
                "budgets": plan.get("budgets") or existing_budgets,
            },
            label="Resolve deep-research evidence gaps",
        )
        st.rerun()
else:
    st.success("No company currently needs an evidence-building pass within the active research budget.")

latest_gap = st.session_state.get("deep_gap_result") or {}
if latest_gap:
    with st.expander("Latest deeper-research transitions", expanded=True):
        st.write("States after deeper research:", latest_gap.get("states", {}))
        if latest_gap.get("transitions"):
            st.dataframe(pd.DataFrame(latest_gap.get("transitions")), use_container_width=True, hide_index=True)

st.divider()
st.markdown("## C. Challenge evidence-ready theses")
st.write(
    "**What this means:** the system deliberately argues both sides of the same company. The Bull researcher builds the strongest supported positive thesis; the Bear researcher attacks it using supported business, cash-flow, governance, competition and execution risks; then a neutral reviewer identifies which arguments survive and what remains unresolved."
)
st.caption("The purpose is to reduce confirmation bias. It is not a return forecast or buy/sell recommendation.")

# Re-read the plan from session because a completed deep-gap background job may have rebuilt it.
plan = st.session_state.get("research_plan") or plan
rows = plan.get("rows", [])
system_ready = [r.get("company") for r in rows if r.get("stage") == "ADVERSARIAL" and r.get("company")]
evidence_candidates = [c.company for c in run.companies.values() if c.evidence and c.research_state in {"EVIDENCE_READY", "RESEARCH_INCOMPLETE"}]
selectable = list(dict.fromkeys(system_ready + evidence_candidates))

if not system_ready:
    st.info(
        "No company passes the automatic Bull/Bear evidence gate yet. This is not an error: the system is refusing to manufacture a confident thesis from incomplete evidence. Run the deeper evidence work above, then refresh this page."
    )
    blocked = [r for r in rows if r.get("stage") in {"SOURCE_GAP", "STRUCTURED", "TARGETED", "DEEP"}]
    if blocked:
        st.dataframe(pd.DataFrame([{
            "Company": r.get("company"), "Stage": r.get("stage"), "Why not ready": r.get("reason"),
            "Mission coverage": r.get("mission_coverage"), "Evidence quality": r.get("evidence_quality"),
            "Research readiness": r.get("research_readiness"), "Risk evidence items": r.get("risk_items"),
        } for r in blocked]), use_container_width=True, hide_index=True)

selected_for_challenge = st.multiselect(
    "Companies to challenge",
    selectable,
    default=system_ready,
    help="System-ready companies are selected by default. You may explicitly include another evidence-bearing company; its weaker readiness remains visible.",
)

if st.button("Run Bull/Bear thesis challenge in background", type="primary", disabled=busy or not selected_for_challenge):
    start_job(
        "thesis_challenge",
        {"run_id": run.run_id, "plan": plan, "company_names": selected_for_challenge},
        label="Run Bull/Bear thesis challenge",
    )
    st.rerun()

results = st.session_state.get("adversarial_results") or [
    c.adversarial_result for c in run.companies.values() if getattr(c, "adversarial_result", None)
]

if results:
    st.markdown("### Thesis challenge summary")
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
            "Mode": challenge.get("mode"),
            "Unresolved questions": len(classification.get("unresolved_questions") or []),
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    inspect = st.selectbox("Inspect thesis challenge", [r.get("company") for r in results])
    result = next(r for r in results if r.get("company") == inspect)
    bull = (result.get("bull_bear") or {}).get("bull", {}) or {}
    bear = (result.get("bull_bear") or {}).get("bear", {}) or {}
    challenge = result.get("challenge", {}) or {}
    classification = result.get("classification", {}) or {}

    a, b, c, d = st.columns(4)
    a.metric("Research state", classification.get("thesis_status"))
    b.metric("Thesis balance", classification.get("thesis_balance"))
    c.metric("Fragility", classification.get("fragility_score"))
    d.metric("Adversarial readiness", classification.get("adversarial_readiness"))
    st.caption("Thesis balance is relative evidence support, not a forecast of returns.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### 🟢 Bull researcher")
        st.write(bull.get("summary", ""))
        for point in bull.get("points", []) or []:
            st.write(f"- {point.get('point')}")
            if point.get("evidence_ids"): st.caption("Evidence: " + ", ".join(str(x) for x in point.get("evidence_ids") or []))
        with st.expander("Bull assumptions / invalidation"):
            for x in bull.get("key_assumptions") or []: st.write(f"- Assumption: {x}")
            for x in bull.get("invalidation_conditions") or []: st.write(f"- Invalidation: {x}")

    with right:
        st.markdown("#### 🔴 Bear / forensic researcher")
        st.write(bear.get("summary", ""))
        for point in bear.get("points", []) or []:
            st.write(f"- {point.get('point')}")
            if point.get("evidence_ids"): st.caption("Evidence: " + ", ".join(str(x) for x in point.get("evidence_ids") or []))
        with st.expander("Bear assumptions / invalidation"):
            for x in bear.get("key_assumptions") or []: st.write(f"- Assumption: {x}")
            for x in bear.get("invalidation_conditions") or []: st.write(f"- Invalidation: {x}")

    st.markdown("#### Neutral challenge")
    st.info(challenge.get("challenge_summary", ""))
    if challenge.get("contradictions"):
        with st.expander("Contradictions / disputed points", expanded=True):
            st.dataframe(pd.DataFrame(challenge.get("contradictions") or []), use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Bull points that survived**")
        for p in challenge.get("surviving_bull_points") or []: st.write(f"- {p.get('point') or p.get('claim') or p}")
        st.markdown("**Fragility flags**")
        for x in challenge.get("fragility_flags") or []: st.write(f"- {x}")
    with c2:
        st.markdown("**Bear points that survived**")
        for p in challenge.get("surviving_bear_points") or []: st.write(f"- {p.get('point') or p.get('claim') or p}")
        st.markdown("**Unresolved questions**")
        for x in challenge.get("unresolved_questions") or []: st.write(f"- {x}")

    if challenge.get("mode") == "deterministic":
        st.warning("No compatible LLM was configured, so this used deterministic evidence comparison. Semantic contradiction resolution is intentionally limited.")
else:
    st.info("No Bull/Bear thesis challenge has been run yet.")

st.divider()
st.page_link("main.py", label="← Return to Guided Research")
st.caption("Research depth allocates attention; deeper research resolves evidence gaps; Bull/Bear challenges a thesis. None of these stages is an investment recommendation.")
