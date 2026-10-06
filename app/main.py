from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from importer import read_uploaded_file
from universe import owners, filter_owners
from screener_adapter import ScreenerAdapter
from research_models import ResearchRun
from research_service import ResearchService
from candidates import read_result_file, build_candidate_universe

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Personal AI Stock Researcher", layout="wide")
st.title("Personal AI Stock Researcher")
st.caption("Screen → understand → research → challenge → narrow. Every action and decision remains visible.")

DEFAULTS = {
    "run": None,
    "screen_candidates": [],
    "screen_queries": [],
    "strategies": [],
    "candidate_universe": [],
    "manual_candidate_rows": [],
    "connection": None,
    "financial_assessments": [],
    "research_memories": [],
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

with st.sidebar:
    st.header("Research settings")
    cdp = st.text_input("Logged-in Chrome CDP", "http://127.0.0.1:9222")
    capital = st.number_input("Research capital (₹)", min_value=1000, value=100000, step=10000)
    depth = st.selectbox("Research depth", ["Standard", "Deep"], index=1)
    st.caption("Screener is the initial POC adapter. The research engines are designed so NSE/BSE/provider adapters can replace it later.")

T_RESEARCH, T_STRATEGIES, T_COMPANIES, T_SETTINGS = st.tabs([
    "Research", "Strategies", "Companies", "Settings / Debug"
])


def active_run() -> ResearchRun:
    if st.session_state.run is None:
        st.session_state.run = ResearchRun.create(depth, capital)
    return st.session_state.run


def event_df(run: ResearchRun):
    return pd.DataFrame([{
        "Time": e.at[11:19] if len(e.at) >= 19 else e.at,
        "Stage": e.stage,
        "Status": e.status,
        "Action": e.action,
        "Company": e.company,
        "What happened": e.message,
    } for e in run.events])


with T_RESEARCH:
    st.subheader("Start / continue a research run")
    a, b, c = st.columns([1, 1, 2])
    if a.button("New research run", type="primary"):
        st.session_state.run = ResearchRun.create(depth, capital)
        st.session_state.strategies = []
        st.session_state.candidate_universe = []
        st.session_state.manual_candidate_rows = []
        st.session_state.financial_assessments = []
        st.session_state.research_memories = []
        st.success(f"Created {st.session_state.run.run_id}")
    if b.button("Check Screener connection"):
        try:
            with ScreenerAdapter(cdp) as adapter:
                st.session_state.connection = adapter.connection_status()
            active_run().log("SYSTEM", "SCREENER_CONNECTION", "Connected to the local Screener browser session.", details=st.session_state.connection)
        except Exception as exc:
            st.session_state.connection = {"connected": False, "logged_in": False, "error": str(exc)}
            active_run().log("SYSTEM", "SCREENER_CONNECTION_FAILED", str(exc), status="ERROR")
    conn = st.session_state.connection
    if conn:
        if conn.get("connected"):
            c.success(f"Screener browser connected · logged-in detection: {'yes' if conn.get('logged_in') else 'uncertain'}")
        else:
            c.error(conn.get("error", "Connection failed"))

    run = active_run()
    st.markdown("### 1. Learn/select the screening methodology")
    source_mode = st.radio(
        "Historical screen source",
        ["Logged-in Screener", "Import historical screens (fallback/debug)"],
        horizontal=True,
    )

    screens_to_analyze = []
    if source_mode == "Logged-in Screener":
        explore = st.text_input("Screen discovery page", "https://www.screener.in/explore/")
        d1, d2 = st.columns(2)
        max_pages = d1.number_input("Discovery pages", 1, 100, 15)
        max_screens = d2.number_input("Max screens (0 = all)", 0, 10000, 0)
        if st.button("Discover screens/users"):
            bar = st.progress(0); message = st.empty()
            try:
                def discover_progress(i, n, item):
                    bar.progress(i/max(n,1)); message.write(f"Discovering {i}/{n}: {item.get('title') or item.get('url')}")
                st.session_state.screen_candidates = ScreenerAdapter.discover_screens(
                    cdp, explore, int(max_pages), int(max_screens), discover_progress
                )
                run.log("STRATEGY", "SCREEN_DISCOVERY", f"Discovered {len(st.session_state.screen_candidates)} historical screen candidates.")
            except Exception as exc:
                st.error(str(exc)); run.log("STRATEGY", "SCREEN_DISCOVERY_FAILED", str(exc), status="ERROR")

        candidates = st.session_state.screen_candidates
        detected = owners(candidates)
        if candidates:
            selected_owners = st.multiselect("Choose Screener user(s)", detected, default=detected[:1] if detected else [])
            matched = filter_owners(candidates, selected_owners) if selected_owners else []
            st.caption(f"{len(matched)} screens match the selected user(s).")
            if matched and st.button("Fetch selected screen queries"):
                bar = st.progress(0); message = st.empty()
                try:
                    def qprogress(i,n,item):
                        bar.progress(i/max(n,1)); message.write(f"Fetching query {i}/{n}: {item.get('title') or item.get('url')}")
                    crawled = ScreenerAdapter.fetch_screen_queries(cdp, [x["url"] for x in matched], qprogress)
                    original = {x["url"]: x for x in matched}
                    for item in crawled:
                        src = original.get(item.get("url"), {})
                        item["owner"] = item.get("owner") or src.get("owner", "")
                        item["title"] = item.get("title") or src.get("title", "")
                    st.session_state.screen_queries = crawled
                    run.log("STRATEGY", "SCREEN_QUERY_FETCH", f"Fetched {sum(bool(x.get('query')) for x in crawled)} usable queries from {len(crawled)} screens.")
                except Exception as exc:
                    st.error(str(exc)); run.log("STRATEGY", "SCREEN_QUERY_FETCH_FAILED", str(exc), status="ERROR")
            screens_to_analyze = st.session_state.screen_queries
    else:
        upload = st.file_uploader("Historical Screener screens CSV/XLSX", type=["csv","xlsx","xls"], key="historical_screens")
        if upload:
            try:
                screens_to_analyze = read_uploaded_file(upload)
                st.info(f"Loaded {len(screens_to_analyze)} historical screens. This is a fallback/debug path.")
            except Exception as exc:
                st.error(str(exc))

    if screens_to_analyze and st.button("Analyze methodology & prepare strategies", type="primary"):
        try:
            st.session_state.strategies = ResearchService(run, RUNS).analyze_screens(screens_to_analyze)
            st.success(f"Prepared {len(st.session_state.strategies)} master strategies.")
        except Exception as exc:
            st.error(str(exc)); run.log("STRATEGY", "METHODOLOGY_FAILED", str(exc), status="ERROR")

    st.markdown("### 2. Run enabled strategies")
    strategies = st.session_state.strategies or run.strategies
    if strategies:
        labels = {s["id"]: f"{s['id']} · {s['name']}" for s in strategies}
        enabled = st.multiselect("Enabled strategies", list(labels), default=list(labels), format_func=lambda x: labels[x])
        st.caption("The app runs each query in your logged-in browser, crawls result pages, and captures exact company links plus every visible result-table metric. No Screener Pro Excel export is required for this path.")
        if st.button("Run screening & build candidate universe", type="primary"):
            bar = st.progress(0); message = st.empty()
            try:
                def screen_progress(si, sn, sid, name, page_no, total_rows):
                    bar.progress((si-1 + min(page_no,5)/5)/max(sn,1)); message.write(f"{sid} · {name}: page {page_no}, {total_rows} rows captured")
                universe = ResearchService(run, RUNS).execute_strategies(cdp, set(enabled), screen_progress)
                st.session_state.candidate_universe = universe
                st.success(f"Candidate universe ready: {len(universe)} unique companies.")
            except Exception as exc:
                st.error(str(exc)); run.log("SCREENING", "SCREENING_FAILED", str(exc), status="ERROR")

    st.markdown("### 3. Analyze candidate financials")
    universe = st.session_state.candidate_universe
    if universe:
        st.caption("No additional financial spreadsheet is required. Exact company links from screening are used first; missing data is logged as a retry rather than silently treated as neutral.")
        if st.button("Analyze financials automatically", type="primary"):
            bar=st.progress(0); message=st.empty()
            try:
                def fprogress(i,n,company,status):
                    bar.progress(i/max(n,1)); message.write(f"{i}/{n} {company} — {status}")
                st.session_state.financial_assessments = ResearchService(run, RUNS).collect_financials(cdp, universe, fprogress)
                st.success("Financial assessment complete. Decisions are coverage-aware; low-data companies are routed to DATA_RETRY instead of receiving a confident pass.")
            except Exception as exc:
                st.error(str(exc)); run.log("FINANCIAL","FINANCIAL_STAGE_FAILED",str(exc),status="ERROR")

    st.markdown("### 4. Research surviving companies")
    if st.session_state.financial_assessments:
        eligible=sum(1 for x in st.session_state.financial_assessments if x.get("decision") in {"ADVANCE","WATCHLIST"})
        st.caption(f"{eligible} companies currently qualify for company/source research. The app discovers documents itself; uploads are debug overrides only.")
        if st.button("Research companies automatically"):
            bar=st.progress(0); message=st.empty()
            try:
                def rprogress(i,n,company,status):
                    bar.progress(i/max(n,1)); message.write(f"{i}/{n} {company} — {status}")
                st.session_state.research_memories = ResearchService(run,RUNS).collect_company_research(cdp,use_llm=False,progress=rprogress)
                st.success("Company research memory built from automatically discovered/fetched sources where available.")
            except Exception as exc:
                st.error(str(exc)); run.log("RESEARCH","RESEARCH_STAGE_FAILED",str(exc),status="ERROR")

    st.markdown("### Research log")
    if run.events:
        st.dataframe(event_df(run), use_container_width=True, hide_index=True)
    else:
        st.info("Actions performed by the researcher will appear here with their purpose and outcome.")

with T_STRATEGIES:
    st.subheader("Your methodology and master strategies")
    strategies = st.session_state.strategies or active_run().strategies
    if not strategies:
        st.info("Analyze historical screens first.")
    for s in strategies:
        with st.expander(f"{s.get('id')} · {s.get('name')}"):
            st.write(s.get("purpose", ""))
            st.code(s.get("hard_query", ""))
            st.caption(f"Methodology support: {s.get('evidence_confidence', 0)}/100. This is methodology support, not expected return.")

with T_COMPANIES:
    st.subheader("Candidate companies")
    universe = st.session_state.candidate_universe
    if not universe:
        st.info("Run screening first. Candidate Universe = all unique companies that passed at least one enabled strategy.")
    else:
        st.metric("Unique candidates", len(universe))
        if st.session_state.financial_assessments:
            fdf=pd.DataFrame([{
                "Company":x.get("company"),"Decision":x.get("decision"),"Evidence coverage %":x.get("data_confidence"),
                "Growth":(x.get("labels") or {}).get("growth"),"Capital efficiency":(x.get("labels") or {}).get("capital_efficiency"),
                "Balance sheet":(x.get("labels") or {}).get("balance_sheet"),"Cash generation":(x.get("labels") or {}).get("cash_generation"),
                "Valuation":(x.get("labels") or {}).get("valuation"),"Why":x.get("decision_reason")
            } for x in st.session_state.financial_assessments])
            st.markdown("### Financial research decisions")
            st.dataframe(fdf,use_container_width=True,hide_index=True)
            st.caption("Numeric scores are internal ordering aids. The user-facing decision is driven by evidence coverage, hard risk gates, qualitative dimensions and an explicit reason.")
        rows = []
        for x in universe:
            rows.append({
                "Company": x.get("company"), "Exact Screener URL": x.get("url"),
                "Strategies matched": x.get("strategy_count"), "Strategy IDs": x.get("strategies"),
                "Research priority (internal)": x.get("research_priority_score"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        chosen = st.selectbox("Inspect company", [x.get("company") for x in universe])
        item = next(x for x in universe if x.get("company") == chosen)
        st.write("**Why it is here:**", item.get("strategy_names") or item.get("strategies"))
        st.write("**Exact Screener company URL:**", item.get("url") or "Not captured — resolver fallback would be required")
        if item.get("snapshot"):
            st.markdown("**Metrics captured directly from the screen result**")
            st.dataframe(pd.DataFrame([item["snapshot"]]), use_container_width=True, hide_index=True)

with T_SETTINGS:
    st.subheader("Settings / Debug")
    st.write("Normal operation should not require files. These controls exist for recovery/testing.")
    manual = st.file_uploader("Import strategy result CSV/XLSX", type=["csv","xlsx","xls"], key="debug_result")
    sid = st.text_input("Strategy ID", "S1")
    if manual and st.button("Debug: import result file"):
        rows = read_result_file(manual, sid)
        st.session_state.manual_candidate_rows.extend(rows)
        st.success(f"Imported {len(rows)} rows.")
    if st.session_state.manual_candidate_rows and st.button("Debug: build universe from imports"):
        strategies = st.session_state.strategies or [{"id": sid, "name": "Imported", "evidence_confidence": 50}]
        st.session_state.candidate_universe = build_candidate_universe(st.session_state.manual_candidate_rows, strategies)
        st.success(f"Built {len(st.session_state.candidate_universe)} unique candidates.")
    st.caption("Debug imports preserve Excel cell hyperlinks when present; normal live-Screener runs capture exact hrefs directly from the result table.")
