from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from company_research_engine import run_company_research_engine
from research_contracts import validate_company_research_contract, contract_status

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

st.set_page_config(page_title="Research Evidence · Personal AI Stock Researcher", layout="wide")
st.title("Research Evidence")
st.caption("Run the company researcher, inspect every source attempt, understand what was learned, and keep unknowns visible.")

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from the main Research page first.")
    st.stop()

companies = list(run.companies.values())
research_candidates = [
    c for c in companies
    if (c.financial_assessment or {}).get(
        "effective_research_decision",
        (c.financial_assessment or {}).get("decision"),
    ) in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}
]

st.markdown("## Run / retry company research")
if not research_candidates:
    st.info("No companies are currently approved for company research. Review financial-stage selections in Operator Control first.")
else:
    names = [c.company for c in research_candidates]
    selected = st.multiselect(
        "Companies to research",
        names,
        default=names,
        help="You remain in control. Research all survivors or retry only selected companies.",
    )
    c1, c2, c3 = st.columns(3)
    per_type = c1.number_input(
        "Max sources per document type",
        min_value=1,
        max_value=5,
        value=2,
        help="Prevents over-fetching. The researcher ranks sources and fetches only the highest-value documents per type.",
    )
    min_score = c2.number_input(
        "Minimum source-quality score",
        min_value=0,
        max_value=100,
        value=45,
        help="Lower values broaden coverage; higher values prefer authoritative sources.",
    )
    use_llm = c3.checkbox(
        "Use configured LLM for semantic extraction",
        value=False,
        help="If disabled, deterministic source excerpts are still extracted. LLM mode produces stronger evidence classification when configured.",
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

st.markdown("## Research-stage overview")
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
    st.success("Company-research stage satisfies the current investor-facing completion contract.")
else:
    st.warning(
        f"Company research is still incomplete for {len(contract_issues)} contract checks. "
        "A crawler finishing successfully is not considered research completion."
    )
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
        "Source attempts": len(getattr(c, "source_attempts", [])),
        "Financial decision": assessment.get("effective_research_decision", assessment.get("decision")),
    })

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No companies are currently marked for company research.")

if research_candidates:
    st.markdown("## Investor research dossier")
    chosen = st.selectbox("Inspect company", [c.company for c in research_candidates])
    company = next(c for c in research_candidates if c.company == chosen)
    dossier = getattr(company, "research_dossier", {}) or {}
    state = getattr(company, "research_state", "NOT_RESEARCHED") or "NOT_RESEARCHED"

    st.markdown(f"### {company.company}")
    a, b, c, d = st.columns(4)
    a.metric("Research state", state)
    b.metric("Mission coverage", f"{dossier.get('mission_coverage', 0)}%")
    c.metric("Documents", len(company.documents))
    d.metric("Evidence items", len(company.evidence))
    st.write("**What happens next:**", dossier.get("what_happens_next", "Run company research or resolve remaining source gaps."))
    st.write("**Exact company URL:**", company.screener_url or "Missing")

    st.markdown("### 1. What the researcher attempted")
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
        st.info("No source-acquisition attempt has been recorded yet for this company.")

    st.markdown("### 2. Sources / documents acquired")
    if company.documents:
        drows = []
        for doc in company.documents:
            drows.append({
                "Type": doc.get("doc_type"),
                "Title": doc.get("title"),
                "Date": doc.get("document_date"),
                "Source class": doc.get("source_class"),
                "Source score": doc.get("source_score"),
                "Domain": doc.get("source_domain"),
                "URL": doc.get("url"),
                "Pages": doc.get("page_count"),
            })
        st.dataframe(pd.DataFrame(drows), use_container_width=True, hide_index=True)
    else:
        st.error("SOURCE_GAP: no usable research document was acquired for this company.")

    st.markdown("### 3. Fundamental analyst missions")
    missions = dossier.get("missions", [])
    if missions:
        mdf = pd.DataFrame([{
            "Mission": m.get("label"),
            "Status": m.get("status"),
            "Evidence": m.get("evidence_count"),
            "Why it matters": m.get("why"),
        } for m in missions])
        st.dataframe(mdf, use_container_width=True, hide_index=True)
        for mission in missions:
            if not mission.get("findings"):
                continue
            with st.expander(f"{mission.get('label')} · {mission.get('evidence_count')} evidence items"):
                for finding in mission.get("findings", []):
                    st.write(f"- {finding.get('finding')}")
                    st.caption(
                        f"{finding.get('document') or 'Source'} · page {finding.get('page') or 'NA'} · "
                        f"evidence {finding.get('evidence_id')} · confidence {finding.get('confidence')}"
                    )
    else:
        st.info("Run the new company research engine to build the analyst mission dossier.")

    st.markdown("### 4. Risks, catalysts and management claims")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("**Risks / governance**")
        risks = dossier.get("risk_findings", [])
        if risks:
            for item in risks:
                st.write(f"- {item.get('claim') or item.get('excerpt')}")
        else:
            st.caption("No source-linked risk finding extracted yet. This may be a coverage gap, not proof of low risk.")
    with r2:
        st.markdown("**Catalysts / milestones**")
        cats = dossier.get("catalyst_findings", [])
        if cats:
            for item in cats:
                st.write(f"- {item.get('claim') or item.get('excerpt')}")
        else:
            st.caption("No source-linked catalyst finding extracted yet.")
    with r3:
        st.markdown("**Management claims to verify**")
        claims = dossier.get("management_claims", [])
        if claims:
            for item in claims:
                st.write(f"- {item.get('claim') or item.get('excerpt')}")
        else:
            st.caption("No management claim has yet been classified for promise-vs-delivery tracking.")

    st.markdown("### 5. Open questions / missing evidence")
    if company.research_questions:
        for q in company.research_questions:
            st.write(f"- **{q.get('status', 'OPEN')}** — {q.get('question')}")
            if q.get("reason"):
                st.caption(q.get("reason"))
    elif state == "EVIDENCE_READY":
        st.success("Current company-research contract is satisfied. The next stage should challenge the thesis rather than assume it is correct.")
    else:
        st.write("- Run/retry research and acquire authoritative source evidence.")

    st.markdown("### 6. Raw evidence ledger")
    if company.evidence:
        erows = []
        for e in company.evidence:
            erows.append({
                "Theme": e.get("theme"),
                "Type": e.get("kind"),
                "Finding": e.get("claim") or e.get("excerpt"),
                "Document": e.get("document_title"),
                "Page": e.get("page"),
                "Evidence ID": e.get("evidence_id"),
                "Confidence": e.get("confidence"),
            })
        st.dataframe(pd.DataFrame(erows), use_container_width=True, hide_index=True)
    else:
        st.warning("No source-linked evidence has been extracted yet. Do not advance this company solely because financial screening looked attractive.")

st.divider()
st.caption(
    "Constitution rule: company research must show what was attempted, what was acquired, what was learned, "
    "what remains unknown, and what happens next. Unknowns are first-class outputs, not hidden failures."
)
