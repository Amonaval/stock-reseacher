from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from navigation import render_navigation
from company_research_engine import run_company_research_engine
from research_contracts import validate_company_research_contract, contract_status

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Research Evidence · Personal AI Stock Researcher", page_icon="🔎", layout="wide")
render_navigation()

st.title("🔎 Research Evidence")
st.caption("Use this page when you want to inspect what the researcher actually read, learned, could not verify, and still needs to investigate.")
st.info("Normal flow: run company research from **Guided Research**. Come here to inspect or retry specific companies in more detail.")

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from Guided Research first.")
    st.page_link("main.py", label="← Return to Guided Research")
    st.stop()

companies = list(run.companies.values())
research_candidates = [
    c for c in companies
    if (c.financial_assessment or {}).get(
        "effective_research_decision",
        (c.financial_assessment or {}).get("decision"),
    ) in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}
]

with st.expander("Retry / customize company research", expanded=False):
    if not research_candidates:
        st.info("No companies are currently approved for company research. Review financial-stage selections in Operator Control first.")
    else:
        names = [c.company for c in research_candidates]
        selected = st.multiselect(
            "Companies to research",
            names,
            default=names,
            help="Research all survivors or retry only selected companies.",
        )
        c1, c2, c3 = st.columns(3)
        per_type = c1.number_input(
            "Max sources per document type", min_value=1, max_value=5, value=2,
            help="Prevents over-fetching. The researcher ranks sources and fetches only the highest-value documents per type.",
        )
        min_score = c2.number_input(
            "Minimum source-quality score", min_value=0, max_value=100, value=45,
            help="Lower values broaden coverage; higher values prefer authoritative sources.",
        )
        use_llm = c3.checkbox(
            "Use configured LLM for semantic extraction", value=False,
            help="If disabled, deterministic source excerpts are still extracted.",
        )

        if st.button("Research selected companies", type="primary", disabled=not selected):
            bar = st.progress(0)
            message = st.empty()
            try:
                def progress(i, n, company, stage):
                    bar.progress(i / max(n, 1))
                    message.write(f"{i}/{n} · {company} · {stage.replace('_', ' ')}")

                memories = run_company_research_engine(
                    run,
                    st.session_state.get("cdp_url", "http://127.0.0.1:9222"),
                    company_names=selected,
                    use_llm=use_llm,
                    max_sources_per_type=int(per_type),
                    min_source_score=float(min_score),
                    progress=progress,
                )
                st.session_state.research_memories = memories
                run.save(RUNS)
                message.empty()
                states = run.stage_summary.get("research", {}).get("states", {})
                st.success(f"Company research completed. Research states: {states}")
            except Exception as exc:
                run.log("RESEARCH", "ENGINE_FAILED", str(exc), status="ERROR")
                run.save(RUNS)
                st.error(str(exc))

summary = run.stage_summary.get("research", {})
memories = st.session_state.get("research_memories") or []

st.markdown("## At a glance")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Companies targeted", summary.get("eligible_companies", len(research_candidates)))
c2.metric("Sources discovered", summary.get("discovered_sources", summary.get("source_links", 0)))
c3.metric("Documents fetched", summary.get("documents", 0))
c4.metric("Evidence items", summary.get("evidence_items", 0))
c5.metric("Fetch errors", summary.get("fetch_errors", 0))
source_gaps = sum(1 for c in research_candidates if getattr(c, "research_state", "") == "SOURCE_GAP" or len(c.documents) == 0 or len(c.evidence) == 0)
c6.metric("Source gaps", source_gaps)

expected = [c.company for c in research_candidates]
contract_issues = validate_company_research_contract(memories, expected)
status = contract_status(contract_issues)
if status == "COMPLETE":
    st.success("The current company-research completion contract is satisfied.")
else:
    st.warning(f"Research is still incomplete for {len(contract_issues)} contract checks. This is useful information—not a hidden failure.")
    with st.expander("Show research contract gaps"):
        for issue in contract_issues:
            st.write(f"- {issue}")

st.markdown("## Company research status")
rows = []
for c in research_candidates:
    assessment = c.financial_assessment or {}
    dossier = getattr(c, "research_dossier", {}) or {}
    state = getattr(c, "research_state", "NOT_RESEARCHED") or "NOT_RESEARCHED"
    if state == "NOT_RESEARCHED":
        if len(c.documents) == 0 or len(c.evidence) == 0:
            state = "SOURCE_GAP" if getattr(c, "source_attempts", []) else "NOT_RESEARCHED"
        elif c.research_questions:
            state = "RESEARCH_INCOMPLETE"
        else:
            state = "EVIDENCE_READY"
    rows.append({
        "Company": c.company,
        "Research state": state,
        "Mission coverage %": dossier.get("mission_coverage", 0),
        "Evidence quality": dossier.get("evidence_quality", 0),
        "Research readiness": dossier.get("research_readiness", 0),
        "Documents": len(c.documents),
        "Evidence items": len(c.evidence),
        "Open questions": len(c.research_questions),
        "Financial decision": assessment.get("effective_research_decision", assessment.get("decision")),
    })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No companies are currently marked for company research.")

if research_candidates:
    st.markdown("## Inspect one company")
    chosen = st.selectbox("Company", [c.company for c in research_candidates])
    company = next(c for c in research_candidates if c.company == chosen)
    dossier = getattr(company, "research_dossier", {}) or {}
    state = getattr(company, "research_state", "NOT_RESEARCHED") or "NOT_RESEARCHED"

    a, b, c, d = st.columns(4)
    a.metric("Research state", state)
    b.metric("Mission coverage", f"{dossier.get('mission_coverage', 0)}%")
    c.metric("Documents", len(company.documents))
    d.metric("Evidence items", len(company.evidence))

    st.info(f"**What happens next:** {dossier.get('what_happens_next', 'Run company research or resolve remaining source gaps.')} ")

    with st.expander("1. What the researcher attempted", expanded=False):
        attempts = getattr(company, "source_attempts", []) or []
        if attempts:
            adf = pd.DataFrame([{
                "Time": a.get("at", "")[11:19],
                "Stage": a.get("stage"),
                "Provider": a.get("provider"),
                "Status": a.get("status"),
                "Document type": a.get("doc_type"),
                "Source score": a.get("source_score"),
                "What happened": a.get("message"),
                "URL": a.get("url"),
            } for a in attempts])
            st.dataframe(adf, use_container_width=True, hide_index=True)
        else:
            st.info("No source-acquisition attempt has been recorded yet.")

    with st.expander("2. Sources / documents acquired", expanded=True):
        if company.documents:
            drows = []
            for doc in company.documents:
                drows.append({
                    "Type": doc.get("doc_type"), "Title": doc.get("title"), "Date": doc.get("document_date"),
                    "Source class": doc.get("source_class"), "Source score": doc.get("source_score"),
                    "Domain": doc.get("source_domain"), "URL": doc.get("url"), "Pages": doc.get("page_count"),
                })
            st.dataframe(pd.DataFrame(drows), use_container_width=True, hide_index=True)
        else:
            st.error("SOURCE_GAP: no usable research document was acquired for this company.")

    with st.expander("3. Fundamental analyst missions", expanded=True):
        missions = dossier.get("missions", [])
        if missions:
            mdf = pd.DataFrame([{
                "Mission": m.get("label"), "Status": m.get("status"), "Evidence": m.get("evidence_count"), "Why it matters": m.get("why"),
            } for m in missions])
            st.dataframe(mdf, use_container_width=True, hide_index=True)
            for mission in missions:
                if not mission.get("findings"):
                    continue
                st.markdown(f"**{mission.get('label')}**")
                for finding in mission.get("findings", []):
                    st.write(f"- {finding.get('finding')}")
                    st.caption(f"{finding.get('document') or 'Source'} · page {finding.get('page') or 'NA'} · evidence {finding.get('evidence_id')}")
        else:
            st.info("Run company research to build the analyst mission dossier.")

    with st.expander("4. Risks, catalysts & management claims", expanded=False):
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown("**Risks / governance**")
            for item in dossier.get("risk_findings", []): st.write(f"- {item.get('claim') or item.get('excerpt')}")
            if not dossier.get("risk_findings"): st.caption("No source-linked risk finding extracted yet. This may be a coverage gap.")
        with r2:
            st.markdown("**Catalysts / milestones**")
            for item in dossier.get("catalyst_findings", []): st.write(f"- {item.get('claim') or item.get('excerpt')}")
            if not dossier.get("catalyst_findings"): st.caption("No source-linked catalyst finding extracted yet.")
        with r3:
            st.markdown("**Management claims to verify**")
            for item in dossier.get("management_claims", []): st.write(f"- {item.get('claim') or item.get('excerpt')}")
            if not dossier.get("management_claims"): st.caption("No management claim has yet been classified.")

    with st.expander("5. Open questions / missing evidence", expanded=True):
        if company.research_questions:
            for q in company.research_questions:
                st.write(f"- **{q.get('status', 'OPEN')}** — {q.get('question')}")
                if q.get("reason"): st.caption(q.get("reason"))
        elif state == "EVIDENCE_READY":
            st.success("Current research contract is satisfied. The next stage should challenge the thesis rather than assume it is correct.")
        else:
            st.write("- Run/retry research and acquire authoritative source evidence.")

    with st.expander("6. Raw evidence ledger", expanded=False):
        if company.evidence:
            erows = [{
                "Theme": e.get("theme"), "Type": e.get("kind"), "Finding": e.get("claim") or e.get("excerpt"),
                "Document": e.get("document_title"), "Page": e.get("page"), "Evidence ID": e.get("evidence_id"), "Confidence": e.get("confidence"),
            } for e in company.evidence]
            st.dataframe(pd.DataFrame(erows), use_container_width=True, hide_index=True)
        else:
            st.warning("No source-linked evidence has been extracted yet.")

st.divider()
st.page_link("main.py", label="← Return to Guided Research")
st.caption("Constitution rule: unknowns are first-class outputs. A crawler finishing successfully is not the same as research completion.")
