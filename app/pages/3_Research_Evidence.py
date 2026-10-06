from __future__ import annotations

import pandas as pd
import streamlit as st

from research_contracts import validate_company_research_contract, contract_status

st.set_page_config(page_title="Research Evidence · Personal AI Stock Researcher", layout="wide")
st.title("Research Evidence")
st.caption("What was researched, what evidence was found, what is missing, and what happens next.")

run = st.session_state.get("run")
memories = st.session_state.get("research_memories") or []

if run is None:
    st.info("Start a research run from the main Research page first.")
    st.stop()

companies = list(run.companies.values())
research_candidates = [
    c for c in companies
    if (c.financial_assessment or {}).get("effective_research_decision", (c.financial_assessment or {}).get("decision"))
    in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}
]

summary = run.stage_summary.get("research", {})

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Companies targeted", summary.get("eligible_companies", len(research_candidates)))
c2.metric("Source links found", summary.get("source_links", 0))
c3.metric("Documents fetched", summary.get("documents", 0))
c4.metric("Evidence items", summary.get("evidence_items", 0))
source_gaps = sum(1 for c in research_candidates if len(c.documents) == 0 or len(c.evidence) == 0)
c5.metric("Source gaps", source_gaps)

expected = [c.company for c in research_candidates]
contract_issues = validate_company_research_contract(memories, expected)
status = contract_status(contract_issues)
if status == "COMPLETE":
    st.success("Company-research stage satisfies the current investor-facing completion contract.")
else:
    st.warning(
        f"Company-research stage is incomplete for {len(contract_issues)} contract checks. "
        "A stage is not considered complete just because the crawler finished."
    )
    with st.expander("Show research contract gaps"):
        for issue in contract_issues:
            st.write(f"- {issue}")

st.markdown("## Company research status")
rows = []
for c in research_candidates:
    assessment = c.financial_assessment or {}
    docs = len(c.documents)
    evidence = len(c.evidence)
    questions = len(c.research_questions)
    if docs == 0 or evidence == 0:
        research_status = "SOURCE_GAP"
    elif questions:
        research_status = "RESEARCH_INCOMPLETE"
    else:
        research_status = "EVIDENCE_READY"
    rows.append({
        "Company": c.company,
        "Research status": research_status,
        "Financial decision": assessment.get("decision"),
        "Evidence coverage %": assessment.get("data_confidence"),
        "Documents": docs,
        "Evidence items": evidence,
        "Open questions": questions,
        "Exact company URL": c.screener_url,
    })

if rows:
    rdf = pd.DataFrame(rows)
    st.dataframe(rdf, use_container_width=True, hide_index=True)
else:
    st.info("No companies are currently marked for company research.")

if research_candidates:
    st.markdown("## Inspect a company")
    chosen = st.selectbox("Company", [c.company for c in research_candidates])
    company = next(c for c in research_candidates if c.company == chosen)

    docs = len(company.documents)
    evidence = len(company.evidence)
    status = "SOURCE_GAP" if docs == 0 or evidence == 0 else ("RESEARCH_INCOMPLETE" if company.research_questions else "EVIDENCE_READY")

    st.markdown(f"### {company.company}")
    st.write(f"**Research state:** {status}")
    st.write(f"**Exact company URL:** {company.screener_url or 'Missing'}")

    relevant_events = [e for e in run.events if e.company == company.company and e.stage == "RESEARCH"]
    if relevant_events:
        st.markdown("### What the researcher did")
        event_rows = []
        for e in relevant_events:
            event_rows.append({
                "Time": e.at[11:19] if len(e.at) >= 19 else e.at,
                "Status": e.status,
                "Action": e.action,
                "What happened": e.message,
            })
        st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)

    st.markdown("### Sources / documents acquired")
    if company.documents:
        drows = []
        for d in company.documents:
            drows.append({
                "Type": d.get("doc_type"),
                "Title": d.get("title"),
                "Date": d.get("document_date"),
                "Source": d.get("source_kind") or d.get("source"),
                "URL": d.get("source_url") or d.get("url"),
                "Pages": d.get("page_count"),
            })
        st.dataframe(pd.DataFrame(drows), use_container_width=True, hide_index=True)
    else:
        st.error("SOURCE_GAP: no usable research document was acquired for this company.")

    st.markdown("### What the evidence says")
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
        st.warning("No source-linked evidence has been extracted yet. Deep research should not advance on this company until this gap is resolved or explicitly overridden.")

    st.markdown("### Open research questions / missing evidence")
    if company.research_questions:
        for q in company.research_questions:
            st.write(f"- **{q.get('status', 'OPEN')}** — {q.get('question')}  ")
            if q.get("reason"):
                st.caption(q.get("reason"))
    elif docs and evidence:
        st.success("No explicit research questions are currently open. This does not guarantee the thesis is complete; the next-stage analyst should still challenge it.")
    else:
        st.write("- Acquire at least one authoritative company document and build source-linked evidence.")

st.divider()
st.caption(
    "Constitution rule: company research must show what was attempted, what was acquired, what was learned, "
    "what is still unknown, and what happens next. A successful crawler run alone is not research completion."
)
