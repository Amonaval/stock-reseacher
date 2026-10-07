from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from importer import read_uploaded_file
from universe import owners, filter_owners
from screener_adapter import ScreenerAdapter
from research_models import ResearchRun
from research_service import ResearchService
from company_research_engine import run_company_research_engine
from research_analysis_orchestrator import plan_research_for_run, run_thesis_analysis
from ux_guidance import workflow_steps, next_action, status_icon

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
    "adversarial_results": [],
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def active_run(depth="Deep", capital=100000) -> ResearchRun:
    if st.session_state.run is None:
        st.session_state.run = ResearchRun.create(depth, capital)
    return st.session_state.run


def reset_run(depth, capital):
    st.session_state.run = ResearchRun.create(depth, capital)
    for key in [
        "screen_candidates", "screen_queries", "strategies", "candidate_universe",
        "financial_assessments", "research_memories", "research_plan", "adversarial_results",
    ]:
        st.session_state[key] = [] if key not in {"research_plan"} else {}


with st.sidebar:
    st.header("Navigation & global settings")
    st.caption("Use this sidebar for app-wide settings and specialist workspaces. The main page below is the normal step-by-step workflow.")

    st.page_link("main.py", label="🏠 Guided Research", help="The normal end-to-end workflow")
    st.page_link("pages/5_User_Guide.py", label="📘 User Guide", help="Start here if this is your first run")
    st.page_link("pages/3_Research_Evidence.py", label="🔎 Research Evidence", help="Inspect sources, evidence, gaps and dossiers")
    st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="⚖️ Deep Research & Thesis Challenge", help="Research-depth plan and Bull/Bear analysis")
    st.page_link("pages/1_Operator_Control.py", label="🎛️ Operator Control", help="Tune strategies and override stage selections")
    st.page_link("pages/2_Runtime_Settings.py", label="⚙️ Runtime Settings", help="Screener request delay and runtime behavior")

    st.divider()
    st.subheader("Global settings")
    cdp = st.text_input("Logged-in Chrome CDP", "http://127.0.0.1:9222", help="Local Chrome debugging endpoint used by the Screener POC adapter.")
    st.session_state.cdp_url = cdp
    capital = st.number_input("Research capital (₹)", min_value=1000, value=100000, step=10000)
    depth = st.selectbox("Research depth", ["Standard", "Deep"], index=1)
    st.caption("These settings affect the whole research run. Screener is only the current POC data adapter.")

run = active_run(depth, capital)

st.title("📈 Personal AI Stock Researcher")
st.caption("One guided workflow: define what you seek → screen → verify financials → research evidence → challenge the thesis.")

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

with st.expander("What do the sidebar workspaces mean?", expanded=False):
    st.markdown(
        """
- **Guided Research** — the normal flow. Stay here for most runs.
- **User Guide** — plain-language explanation of the product and first-run walkthrough.
- **Research Evidence** — detailed source attempts, documents, evidence, open questions and company dossiers.
- **Deep Research & Thesis Challenge** — research budgets, depth allocation, Bull/Bear arguments, contradictions and fragility.
- **Operator Control** — optional advanced control over strategies, candidates and overrides.
- **Runtime Settings** — technical/runtime controls such as Screener request delay.

You do **not** need to visit every page. The guided workflow tells you when a specialist workspace is useful.
"""
    )

st.divider()

# STEP 0 / run controls
r1, r2 = st.columns([1, 4])
if r1.button("Start new research run"):
    reset_run(depth, capital)
    st.rerun()
r2.caption("Start a new run only when you want to clear the current workflow state. Strategy profiles can be exported/imported separately from Operator Control.")

# STEP 1
step = steps[0]
with st.expander(f"{status_icon(step.status)} Step 1 — Connect & prepare strategies", expanded=step.status in {"NEXT", "IN_PROGRESS"}):
    st.write("**Goal:** teach the researcher what kinds of companies you are interested in. You can learn this from historical Screener screens or import your existing screen file.")
    a, b = st.columns([1, 2])
    if a.button("Check Screener connection"):
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
        if st.button("Discover screens/users"):
            try:
                st.session_state.screen_candidates = ScreenerAdapter.discover_screens(cdp, explore, int(max_pages), int(max_screens), None)
                run.log("STRATEGY", "SCREEN_DISCOVERY", f"Discovered {len(st.session_state.screen_candidates)} historical screen candidates.")
            except Exception as exc:
                st.error(str(exc))
        candidates = st.session_state.screen_candidates
        if candidates:
            detected = owners(candidates)
            selected_owners = st.multiselect("Choose Screener user(s)", detected, default=detected[:1] if detected else [])
            matched = filter_owners(candidates, selected_owners) if selected_owners else []
            st.caption(f"{len(matched)} screens match the selected user(s).")
            if matched and st.button("Fetch selected screen queries"):
                try:
                    crawled = ScreenerAdapter.fetch_screen_queries(cdp, [x["url"] for x in matched], None)
                    original = {x["url"]: x for x in matched}
                    for item in crawled:
                        src = original.get(item.get("url"), {})
                        item["owner"] = item.get("owner") or src.get("owner", "")
                        item["title"] = item.get("title") or src.get("title", "")
                    st.session_state.screen_queries = crawled
                except Exception as exc:
                    st.error(str(exc))
            screens_to_analyze = st.session_state.screen_queries
    else:
        upload = st.file_uploader("Historical Screener screens CSV/XLSX", type=["csv", "xlsx", "xls"])
        if upload:
            try:
                screens_to_analyze = read_uploaded_file(upload)
                st.success(f"Loaded {len(screens_to_analyze)} historical screens.")
            except Exception as exc:
                st.error(str(exc))

    if screens_to_analyze and st.button("Analyze methodology & prepare strategies", type="primary"):
        try:
            st.session_state.strategies = ResearchService(run, RUNS).analyze_screens(screens_to_analyze)
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
        if st.button("Run screening & build candidate universe", type="primary"):
            bar, message = st.progress(0), st.empty()
            try:
                def progress(si, sn, sid, name, page_no, total_rows):
                    bar.progress((si - 1 + min(page_no, 5) / 5) / max(sn, 1))
                    message.write(f"{sid} · {name}: page {page_no}, {total_rows} rows captured")
                st.session_state.candidate_universe = ResearchService(run, RUNS).execute_strategies(cdp, set(enabled), progress)
                st.success(f"Candidate universe ready: {len(st.session_state.candidate_universe)} unique companies.")
                st.page_link("pages/1_Operator_Control.py", label="Optional: review/prune candidates before financial analysis →")
            except Exception as exc:
                st.error(str(exc))

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
        if st.button("Analyze financials automatically", type="primary"):
            bar, message = st.progress(0), st.empty()
            try:
                def fprogress(i, n, company, status):
                    bar.progress(i / max(n, 1)); message.write(f"{i}/{n} · {company} · {status}")
                st.session_state.financial_assessments = ResearchService(run, RUNS).collect_financials(cdp, universe, fprogress)
                counts = run.stage_summary.get("financial", {}).get("decisions", {})
                st.success(f"Financial analysis complete: {counts}")
                st.page_link("pages/1_Operator_Control.py", label="Optional: review/override which companies continue to research →")
            except Exception as exc:
                st.error(str(exc))

# STEP 4
steps = workflow_steps(run, st.session_state)
step = steps[3]
with st.expander(f"{status_icon(step.status)} Step 4 — Research the business", expanded=step.status == "NEXT"):
    eligible = [c for c in run.companies.values() if (c.financial_assessment or {}).get("effective_research_decision", (c.financial_assessment or {}).get("decision")) in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}]
    if not eligible:
        st.info("Complete financial analysis and approve companies for research first.")
    else:
        st.write(f"**Goal:** research {len(eligible)} approved companies using source documents, then expose what is known and what remains unknown.")
        states = {}
        for c in eligible:
            states[c.research_state or "NOT_RESEARCHED"] = states.get(c.research_state or "NOT_RESEARCHED", 0) + 1
        st.write("Current research states:", states)
        if st.button("Research approved companies", type="primary"):
            bar, message = st.progress(0), st.empty()
            try:
                def rprogress(i, n, company, stage):
                    bar.progress(i / max(n, 1)); message.write(f"{i}/{n} · {company} · {stage.replace('_', ' ')}")
                st.session_state.research_memories = run_company_research_engine(
                    run, cdp, company_names=[c.company for c in eligible], use_llm=False,
                    max_sources_per_type=2, min_source_score=45, progress=rprogress,
                )
                run.save(RUNS)
                st.success(f"Company research complete: {run.stage_summary.get('research', {}).get('states', {})}")
            except Exception as exc:
                st.error(str(exc))
        st.page_link("pages/3_Research_Evidence.py", label="Inspect sources, findings and open questions →")

# STEP 5
steps = workflow_steps(run, st.session_state)
step = steps[4]
with st.expander(f"{status_icon(step.status)} Step 5 — Allocate deeper research", expanded=step.status == "NEXT"):
    researched = [c for c in run.companies.values() if c.research_state not in {"", "NOT_RESEARCHED"} or c.evidence]
    if not researched:
        st.info("Complete Step 4 first.")
    else:
        st.write("**Goal:** spend progressively more analyst effort on fewer companies. This is a research-attention budget, not an investment ranking.")
        default_budgets = {"STRUCTURED": 100, "TARGETED": 50, "DEEP": 25, "ADVERSARIAL": 15} if depth == "Deep" else {"STRUCTURED": 60, "TARGETED": 30, "DEEP": 15, "ADVERSARIAL": 8}
        if st.button("Create deep-research plan", type="primary"):
            try:
                st.session_state.research_plan = plan_research_for_run(run, default_budgets)
                run.save(RUNS)
                st.success(f"Plan ready: {st.session_state.research_plan.get('counts', {})}")
            except Exception as exc:
                st.error(str(exc))
        if st.session_state.research_plan:
            counts = st.session_state.research_plan.get("counts", {})
            st.dataframe(pd.DataFrame([{"Stage": k.replace("_", " ").title(), "Companies": v} for k, v in counts.items()]), use_container_width=True, hide_index=True)
        st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="Review budgets and every company's depth decision →")

# STEP 6
steps = workflow_steps(run, st.session_state)
step = steps[5]
with st.expander(f"{status_icon(step.status)} Step 6 — Challenge the thesis", expanded=step.status == "NEXT"):
    plan = st.session_state.research_plan or {}
    ready = [r.get("company") for r in plan.get("rows", []) if r.get("stage") == "ADVERSARIAL"]
    if not ready:
        st.info("No company currently passes the evidence gate for Bull/Bear analysis. Review the deep-research plan and unresolved evidence gaps.")
    else:
        st.write(f"**Goal:** independently challenge {len(ready)} evidence-ready companies. This is a thesis stress test, not a buy/sell recommendation.")
        if st.button("Run Bull/Bear thesis challenge", type="primary"):
            bar, message = st.progress(0), st.empty()
            try:
                def aprogress(i, n, company):
                    bar.progress(i / max(n, 1)); message.write(f"{i}/{n} · challenging {company}")
                st.session_state.adversarial_results = run_thesis_analysis(run, plan, company_names=ready, progress=aprogress)
                run.save(RUNS)
                st.success(f"Thesis challenge complete for {len(st.session_state.adversarial_results)} companies.")
            except Exception as exc:
                st.error(str(exc))
        if st.session_state.adversarial_results:
            rows = []
            for result in st.session_state.adversarial_results:
                c = result.get("classification") or {}
                rows.append({
                    "Company": result.get("company"),
                    "Research state": c.get("thesis_status"),
                    "Thesis balance": c.get("thesis_balance"),
                    "Fragility": c.get("fragility_score"),
                    "Adversarial readiness": c.get("adversarial_readiness"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="Inspect Bull/Bear evidence, contradictions and unresolved questions →")

st.divider()
st.markdown("### Need more detail?")
q1, q2, q3 = st.columns(3)
with q1:
    st.page_link("pages/5_User_Guide.py", label="📘 First-time user guide")
with q2:
    st.page_link("pages/3_Research_Evidence.py", label="🔎 Company research dossiers")
with q3:
    st.page_link("pages/1_Operator_Control.py", label="🎛️ Advanced operator controls")

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
