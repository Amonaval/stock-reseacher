from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from importer import read_uploaded_file
from universe import owners, filter_owners
from screener_adapter import ScreenerAdapter
from research_models import ResearchRun
from research_service import ResearchService
from research_analysis_orchestrator import plan_research_for_run
from ux_guidance import workflow_steps, next_action, status_icon
from navigation import render_navigation
from background_jobs import start_job, sync_session_from_jobs, active_jobs, jobs_for_run

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Personal AI Stock Researcher", page_icon="📈", layout="wide")

DEFAULTS = {
    "run": None,
    "screen_candidates": [],
    "screen_queries": [],
    "strategies": [],
    "candidate_universe": [],
    "connection": None,
    "financial_assessments": [],
    "research_memories": [],
    "research_plan": {},
    "deep_gap_result": {},
    "adversarial_results": [],
    "applied_background_jobs": set(),
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def active_run(depth="Deep", capital=100000) -> ResearchRun:
    if st.session_state.run is None:
        st.session_state.run = ResearchRun.create(depth, capital)
        st.session_state.run.save(RUNS)
    return st.session_state.run


def reset_run(depth, capital):
    st.session_state.run = ResearchRun.create(depth, capital)
    st.session_state.run.save(RUNS)
    for key in [
        "screen_candidates", "screen_queries", "strategies", "candidate_universe",
        "financial_assessments", "research_memories", "adversarial_results",
    ]:
        st.session_state[key] = []
    st.session_state.research_plan = {}
    st.session_state.deep_gap_result = {}
    st.session_state.applied_background_jobs = set()


def launch_background(job_type: str, payload: dict, label: str):
    start_job(job_type, payload, label=label)
    st.rerun()


render_navigation()
with st.sidebar:
    st.divider()
    st.subheader("Global settings")
    cdp = st.text_input("Logged-in Chrome CDP", "http://127.0.0.1:9222", help="Local Chrome debugging endpoint used by the Screener POC adapter.")
    st.session_state.cdp_url = cdp
    capital = st.number_input("Research capital (₹)", min_value=1000, value=100000, step=10000)
    depth = st.selectbox("Research depth", ["Standard", "Deep"], index=1)
    st.caption("These settings affect the whole research run. Screener is only the current POC data adapter.")

run = active_run(depth, capital)
# Pull results from detached workers whenever any page reruns/returns here.
sync_session_from_jobs(st, run.run_id)
run = st.session_state.run
running_jobs = active_jobs(run.run_id)
busy = bool(running_jobs)

st.title("📈 Personal AI Stock Researcher")
st.caption("One guided workflow: define what you seek → screen → verify financials → research evidence → deepen gaps → challenge the thesis.")

if running_jobs:
    job = running_jobs[0]
    st.info(
        f"🧵 **Background work is running:** {job.get('label')} — {job.get('progress_message')} "
        f"({float(job.get('progress') or 0) * 100:.0f}%). You may navigate to any page; the worker will continue."
    )
    cjob1, cjob2 = st.columns([1, 4])
    if cjob1.button("Refresh background status"):
        st.rerun()
    cjob2.page_link("pages/6_Background_Jobs.py", label="Open Background Jobs monitor →")
else:
    latest_jobs = jobs_for_run(run.run_id)
    if latest_jobs and latest_jobs[0].get("status") == "FAILED":
        st.error(f"Latest background job failed: {latest_jobs[0].get('error')}")
        st.page_link("pages/6_Background_Jobs.py", label="Inspect background-job details →")

steps = workflow_steps(run, st.session_state)
next_step, next_text = next_action(steps)

c1, c2, c3 = st.columns([2, 2, 3])
with c1:
    st.metric("Run", run.run_id.split("-")[-1])
with c2:
    st.metric("Current status", run.status.replace("_", " ").title())
with c3:
    if next_step:
        st.info(f"**Next recommended action — Step {next_step.number}: {next_step.title}**\n\n{next_text}")
    else:
        st.success(next_text)

st.markdown("### Your research journey")
journey_cols = st.columns(6)
for col, step in zip(journey_cols, steps):
    col.markdown(f"**{status_icon(step.status)} {step.number}. {step.title}**")
    col.caption(step.detail)

with st.expander("How background work behaves", expanded=False):
    st.markdown(
        """
Long-running crawling and research now execute in a **separate local worker process**.

- You can change pages while it runs.
- Streamlit navigation/reruns no longer cancel the job.
- Progress is persisted under `jobs/`.
- Completed results are synchronized when a page reloads.
- To protect the research-run file, only one long-running job is started at a time for a run.

Use **Background Jobs** in the sidebar whenever you want to inspect progress or an error.
"""
    )

st.divider()
r1, r2 = st.columns([1, 4])
if r1.button("Start new research run", disabled=busy):
    reset_run(depth, capital)
    st.rerun()
r2.caption("Start a new run only when you want to clear the current workflow state. Strategy profiles can be exported/imported separately from Operator Control.")

# STEP 1
steps = workflow_steps(run, st.session_state)
step = steps[0]
with st.expander(f"{status_icon(step.status)} Step 1 — Connect & prepare strategies", expanded=step.status in {"NEXT", "IN_PROGRESS"}):
    st.write("**Goal:** teach the researcher what kinds of companies you are interested in. You can learn this from historical Screener screens or import your existing screen file.")
    a, b = st.columns([1, 2])
    if a.button("Check Screener connection", disabled=busy):
        try:
            with ScreenerAdapter(cdp) as adapter:
                st.session_state.connection = adapter.connection_status()
            run.log("SYSTEM", "SCREENER_CONNECTION", "Connected to the local Screener browser session.", details=st.session_state.connection)
            run.save(RUNS)
        except Exception as exc:
            st.session_state.connection = {"connected": False, "logged_in": False, "error": str(exc)}
            run.log("SYSTEM", "SCREENER_CONNECTION_FAILED", str(exc), status="ERROR")
            run.save(RUNS)
    conn = st.session_state.connection
    if conn:
        (b.success if conn.get("connected") else b.error)(
            f"Connected · login detection: {'yes' if conn.get('logged_in') else 'uncertain'}" if conn.get("connected") else conn.get("error", "Connection failed")
        )

    source_mode = st.radio("Methodology source", ["Logged-in Screener", "Import historical screens"], horizontal=True)
    screens_to_analyze = []
    if source_mode == "Logged-in Screener":
        explore = st.text_input("Screen discovery page", "https://www.screener.in/explore/")
        p1, p2 = st.columns(2)
        max_pages = p1.number_input("Discovery pages", 1, 100, 15)
        max_screens = p2.number_input("Max screens (0 = all)", 0, 10000, 0)
        if st.button("Discover screens/users", disabled=busy):
            launch_background(
                "discover_screens",
                {"run_id": run.run_id, "cdp_url": cdp, "explore_url": explore, "max_pages": int(max_pages), "max_screens": int(max_screens)},
                "Discover historical Screener screens",
            )
        candidates = st.session_state.screen_candidates
        if candidates:
            detected = owners(candidates)
            selected_owners = st.multiselect("Choose Screener user(s)", detected, default=detected[:1] if detected else [])
            matched = filter_owners(candidates, selected_owners) if selected_owners else []
            st.caption(f"{len(matched)} screens match the selected user(s).")
            if matched and st.button("Fetch selected screen queries", disabled=busy):
                launch_background(
                    "fetch_screen_queries",
                    {"run_id": run.run_id, "cdp_url": cdp, "urls": [x["url"] for x in matched], "source_items": matched},
                    "Fetch historical screen queries",
                )
            screens_to_analyze = st.session_state.screen_queries
    else:
        upload = st.file_uploader("Historical Screener screens CSV/XLSX", type=["csv", "xlsx", "xls"])
        if upload:
            try:
                screens_to_analyze = read_uploaded_file(upload)
                st.success(f"Loaded {len(screens_to_analyze)} historical screens.")
            except Exception as exc:
                st.error(str(exc))

    if screens_to_analyze and st.button("Analyze methodology & prepare strategies", type="primary", disabled=busy):
        try:
            st.session_state.strategies = ResearchService(run, RUNS).analyze_screens(screens_to_analyze)
            run.save(RUNS)
            st.success(f"Prepared {len(st.session_state.strategies)} master strategies.")
            st.page_link("pages/1_Operator_Control.py", label="Optional: review/tune strategy philosophy before screening →")
        except Exception as exc:
            st.error(str(exc))

# STEP 2
steps = workflow_steps(run, st.session_state)
step = steps[1]
with st.expander(f"{status_icon(step.status)} Step 2 — Screen the market", expanded=step.status == "NEXT"):
    strategies = st.session_state.strategies or run.strategies
    if not strategies:
        st.info("Complete Step 1 first.")
    else:
        st.write("**Goal:** execute your enabled strategies and combine all matches into one deduplicated candidate universe.")
        labels = {s["id"]: f"{s['id']} · {s['name']}" for s in strategies}
        enabled = st.multiselect("Strategies to run", list(labels), default=[s["id"] for s in strategies if s.get("enabled", True)], format_func=lambda x: labels[x])
        st.caption("Want fewer/more results? Tune the philosophy/query and preview it in Operator Control before running the full screen.")
        st.page_link("pages/1_Operator_Control.py", label="Tune or preview strategies →")
        if st.button("Run screening & build candidate universe", type="primary", disabled=busy or not enabled):
            launch_background(
                "screening",
                {"run_id": run.run_id, "cdp_url": cdp, "enabled_ids": enabled},
                "Run screening strategies",
            )
        if st.session_state.candidate_universe:
            st.success(f"Candidate universe ready: {len(st.session_state.candidate_universe)} unique companies.")
            st.page_link("pages/1_Operator_Control.py", label="Optional: review/prune candidates before financial analysis →")

# STEP 3
steps = workflow_steps(run, st.session_state)
step = steps[2]
with st.expander(f"{status_icon(step.status)} Step 3 — Check financial quality", expanded=step.status == "NEXT"):
    universe = st.session_state.candidate_universe
    if not universe:
        st.info("Complete Step 2 first.")
    else:
        st.write(f"**Goal:** collect multi-period financials for the {len(universe)} selected candidates and identify which names deserve expensive company research.")
        st.caption("The system uses exact company links where possible. Missing data becomes DATA_RETRY; it is not treated as neutral evidence.")
        if st.button("Analyze financials automatically", type="primary", disabled=busy):
            launch_background(
                "financials",
                {"run_id": run.run_id, "cdp_url": cdp, "candidate_universe": universe},
                "Collect and analyze financial histories",
            )
        if st.session_state.financial_assessments:
            counts = run.stage_summary.get("financial", {}).get("decisions", {})
            st.success(f"Financial analysis available: {counts}")
            st.page_link("pages/1_Operator_Control.py", label="Optional: review/override which companies continue to research →")

# STEP 4
steps = workflow_steps(run, st.session_state)
step = steps[3]
with st.expander(f"{status_icon(step.status)} Step 4 — Research the business", expanded=step.status == "NEXT"):
    eligible = [
        c for c in run.companies.values()
        if (c.financial_assessment or {}).get("effective_research_decision", (c.financial_assessment or {}).get("decision"))
        in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}
    ]
    if not eligible:
        st.info("Complete financial analysis and approve companies for research first.")
    else:
        st.write(f"**Goal:** research {len(eligible)} approved companies using source documents, then expose what is known and what remains unknown.")
        states = {}
        for company in eligible:
            states[company.research_state or "NOT_RESEARCHED"] = states.get(company.research_state or "NOT_RESEARCHED", 0) + 1
        st.write("Current research states:", states)
        if st.button("Research approved companies", type="primary", disabled=busy):
            launch_background(
                "company_research",
                {
                    "run_id": run.run_id, "cdp_url": cdp,
                    "company_names": [c.company for c in eligible],
                    "use_llm": False, "max_sources_per_type": 2, "min_source_score": 45,
                },
                "Research approved companies",
            )
        st.page_link("pages/3_Research_Evidence.py", label="Inspect sources, findings and open questions →")

# STEP 5
steps = workflow_steps(run, st.session_state)
step = steps[4]
with st.expander(f"{status_icon(step.status)} Step 5 — Deepen unresolved research", expanded=step.status in {"NEXT", "IN_PROGRESS"}):
    researched = [c for c in run.companies.values() if c.research_state not in {"", "NOT_RESEARCHED"} or c.evidence]
    if not researched:
        st.info("Complete Step 4 first.")
    else:
        st.write("**Goal:** first decide *how much* more research each company needs, then actually resolve those evidence gaps before Bull/Bear analysis.")
        default_budgets = {"STRUCTURED": 100, "TARGETED": 50, "DEEP": 25, "ADVERSARIAL": 15} if depth == "Deep" else {"STRUCTURED": 60, "TARGETED": 30, "DEEP": 15, "ADVERSARIAL": 8}
        if st.button("Create / refresh deep-research plan", type="primary", disabled=busy):
            st.session_state.research_plan = plan_research_for_run(run, default_budgets)
            run.save(RUNS)
            st.rerun()

        plan = st.session_state.research_plan or {}
        if plan:
            counts = plan.get("counts", {})
            st.dataframe(
                pd.DataFrame([{"Stage": k.replace("_", " ").title(), "Companies": v} for k, v in counts.items()]),
                use_container_width=True, hide_index=True,
            )
            needs_work_rows = [
                r for r in plan.get("rows", [])
                if r.get("stage") in {"SOURCE_GAP", "STRUCTURED", "TARGETED", "DEEP"}
            ]
            ready_rows = [r for r in plan.get("rows", []) if r.get("stage") == "ADVERSARIAL"]
            if needs_work_rows:
                st.warning(
                    f"{len(needs_work_rows)} companies still need additional evidence work. "
                    "This is why they cannot yet enter Bull/Bear thesis challenge."
                )
                with st.expander("What does deeper research do?", expanded=True):
                    st.markdown(
                        """
The app will make a broader second research pass for these companies:

- retry source discovery with a wider source budget,
- fetch additional annual/quarterly/presentation/call/filing/rating material,
- preserve evidence already collected,
- fill missing fundamental-analysis missions,
- look specifically for downside/risk evidence,
- rebuild each company dossier,
- automatically re-run the depth plan afterward.

A company reaches **Bull/Bear-ready** only when the evidence set is strong enough to support both a positive and a negative case.
"""
                    )
                selected_deep = st.multiselect(
                    "Companies to deepen now",
                    [r.get("company") for r in needs_work_rows],
                    default=[r.get("company") for r in needs_work_rows],
                )
                if st.button("Resolve evidence gaps in background", type="primary", disabled=busy or not selected_deep):
                    launch_background(
                        "deep_gap_research",
                        {
                            "run_id": run.run_id, "cdp_url": cdp,
                            "company_names": selected_deep,
                            "use_llm": False,
                            "budgets": plan.get("budgets") or default_budgets,
                        },
                        "Resolve deep-research evidence gaps",
                    )
            if ready_rows:
                st.success(f"{len(ready_rows)} companies already pass the evidence gate for thesis challenge.")

        gap_result = st.session_state.deep_gap_result or {}
        if gap_result:
            st.markdown("#### Latest deeper-research result")
            st.write("Research states after the pass:", gap_result.get("states", {}))
            if gap_result.get("transitions"):
                st.dataframe(pd.DataFrame(gap_result["transitions"]), use_container_width=True, hide_index=True)
        st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="Review budgets and every company's depth decision →")

# STEP 6
steps = workflow_steps(run, st.session_state)
step = steps[5]
with st.expander(f"{status_icon(step.status)} Step 6 — Challenge the thesis", expanded=step.status == "NEXT"):
    plan = st.session_state.research_plan or {}
    ready = [r.get("company") for r in plan.get("rows", []) if r.get("stage") == "ADVERSARIAL"]
    if not ready:
        counts = plan.get("counts", {}) if plan else {}
        st.info(
            "**Why no company is ready yet:** Bull/Bear is deliberately blocked until a company has enough source coverage, "
            "fundamental-mission coverage, evidence quality, research readiness, and explicit downside/risk evidence."
        )
        if plan:
            st.write("Current deep-research states:", counts)
            blocked = [r for r in plan.get("rows", []) if r.get("stage") in {"SOURCE_GAP", "STRUCTURED", "TARGETED", "DEEP"}]
            if blocked:
                st.warning(
                    f"{len(blocked)} companies are still in evidence-building stages. Go back to Step 5 and run **Resolve evidence gaps in background**. "
                    "After it finishes, the research plan is rebuilt automatically."
                )
                st.dataframe(
                    pd.DataFrame([{
                        "Company": r.get("company"), "Current stage": r.get("stage"), "Why blocked": r.get("reason"),
                        "Mission coverage": r.get("mission_coverage"), "Evidence quality": r.get("evidence_quality"),
                        "Research readiness": r.get("research_readiness"), "Risk evidence": r.get("risk_items"),
                    } for r in blocked]),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.caption("Create the deep-research plan in Step 5 first.")
    else:
        st.write(
            f"**Goal:** independently challenge {len(ready)} evidence-ready companies. "
            "A Bull researcher builds the strongest positive case, a Bear researcher attacks it using supported risks, and a neutral challenge identifies what survives."
        )
        st.caption("This does not predict returns or issue a buy/sell recommendation. It tests whether the current investment thesis survives serious opposition.")
        if st.button("Run Bull/Bear thesis challenge", type="primary", disabled=busy):
            launch_background(
                "thesis_challenge",
                {"run_id": run.run_id, "plan": plan, "company_names": ready},
                "Run Bull/Bear thesis challenge",
            )
        if st.session_state.adversarial_results:
            rows = []
            for result in st.session_state.adversarial_results:
                classification = result.get("classification") or {}
                rows.append({
                    "Company": result.get("company"),
                    "Research state": classification.get("thesis_status"),
                    "Thesis balance": classification.get("thesis_balance"),
                    "Fragility": classification.get("fragility_score"),
                    "Adversarial readiness": classification.get("adversarial_readiness"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="Inspect Bull/Bear evidence, contradictions and unresolved questions →")

st.divider()
st.markdown("### Need more detail?")
q1, q2, q3, q4 = st.columns(4)
with q1:
    st.page_link("pages/5_User_Guide.py", label="📘 First-time user guide")
with q2:
    st.page_link("pages/6_Background_Jobs.py", label="🧵 Background jobs")
with q3:
    st.page_link("pages/3_Research_Evidence.py", label="🔎 Company research dossiers")
with q4:
    st.page_link("pages/1_Operator_Control.py", label="🎛️ Advanced controls")

with st.expander("Research activity log", expanded=False):
    if run.events:
        st.dataframe(pd.DataFrame([{
            "Time": e.at[11:19] if len(e.at) >= 19 else e.at,
            "Stage": e.stage,
            "Status": e.status,
            "Company": e.company,
            "What happened": e.message,
        } for e in run.events]), use_container_width=True, hide_index=True)
    else:
        st.info("Research actions will appear here as the run progresses.")
