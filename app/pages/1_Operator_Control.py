from __future__ import annotations

import pandas as pd
import streamlit as st

from operator_controls import select_candidates, apply_financial_review, apply_adversarial_review
from strategy_profiles import (
    ensure_strategy_metadata,
    export_strategy_profile,
    import_strategy_profile,
    update_strategy_from_editor,
)

st.set_page_config(page_title="Operator Control · Personal AI Stock Researcher", layout="wide")
st.title("Operator Control")
st.caption("Autonomous by default. Review, refine or override any major stage when you want control.")

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run from the main Research page first. Strategy-profile import is still available below.")

st.markdown("## 1. Strategy philosophy & query control")
strategies = ensure_strategy_metadata(st.session_state.get("strategies") or (run.strategies if run else []))
profile_name = st.text_input("Strategy profile name", st.session_state.get("strategy_profile_name", "My Strategy Philosophy"))
st.session_state.strategy_profile_name = profile_name

profile_upload = st.file_uploader("Import saved strategy profile (.json)", type=["json"], key="strategy_profile_import")
if profile_upload and st.button("Import strategy profile"):
    try:
        name, imported = import_strategy_profile(profile_upload.getvalue())
        st.session_state.strategy_profile_name = name
        st.session_state.strategies = imported
        if run:
            run.strategies = imported
        strategies = imported
        st.success(f"Imported '{name}' with {len(imported)} strategies.")
    except Exception as exc:
        st.error(str(exc))

if strategies:
    st.info("Generated values are preserved inside each profile. Editing below changes only your working/tuned version.")
    rows = []
    for s in strategies:
        rows.append({
            "Enabled": bool(s.get("enabled", True)),
            "ID": s.get("id"),
            "Name": s.get("name", ""),
            "Philosophy / purpose": s.get("purpose", ""),
            "Hard query": s.get("hard_query", ""),
            "My notes": s.get("user_notes", ""),
            "Methodology support": s.get("evidence_confidence", 0),
            "Generated query": s.get("generated_hard_query", s.get("hard_query", "")),
        })
    edited = st.data_editor(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        disabled=["ID", "Methodology support", "Generated query"],
        column_config={
            "Enabled": st.column_config.CheckboxColumn("Enabled"),
            "Hard query": st.column_config.TextColumn("Hard query", width="large"),
            "Philosophy / purpose": st.column_config.TextColumn("Philosophy / purpose", width="large"),
            "Generated query": st.column_config.TextColumn("Generated query", width="large"),
        },
        key="strategy_editor",
    )
    c1, c2 = st.columns(2)
    if c1.button("Apply strategy edits", type="primary"):
        updated = []
        by_id = {s.get("id"): s for s in strategies}
        for _, row in edited.iterrows():
            original = by_id.get(row["ID"], {})
            updated.append(update_strategy_from_editor(
                original,
                enabled=bool(row["Enabled"]),
                name=row["Name"],
                purpose=row["Philosophy / purpose"],
                hard_query=row["Hard query"],
                notes=row["My notes"],
            ))
        st.session_state.strategies = updated
        if run:
            run.strategies = updated
            run.log("OPERATOR", "STRATEGY_PROFILE_APPLIED", f"Applied user-tuned strategy profile '{profile_name}' with {sum(bool(x.get('enabled')) for x in updated)} enabled strategies.")
        st.success("Strategy edits applied. The main Research page will run these tuned queries.")

    export_json = export_strategy_profile(st.session_state.get("strategies") or strategies, profile_name)
    c2.download_button(
        "Export strategy profile",
        data=export_json.encode("utf-8"),
        file_name="stock-research-strategy-profile.json",
        mime="application/json",
    )

    with st.expander("Compare tuned vs generated philosophy"):
        for s in st.session_state.get("strategies") or strategies:
            st.markdown(f"### {s.get('id')} · {s.get('name')}")
            st.write("**Generated philosophy:**", s.get("generated_purpose", s.get("purpose", "")))
            st.code(s.get("generated_hard_query", ""))
            st.write("**Your working philosophy:**", s.get("purpose", ""))
            st.code(s.get("hard_query", ""))
else:
    st.warning("No strategies are loaded yet. Analyze methodology on the main Research page or import a saved profile above.")

st.divider()
st.markdown("## 2. Candidate-universe review before financial analysis")
universe = st.session_state.get("candidate_universe") or []
if not universe:
    st.info("Run screening first. When results exist, you can prune the 200–1000 candidates here before financial collection.")
else:
    all_universe = st.session_state.get("candidate_universe_all") or universe
    if "candidate_universe_all" not in st.session_state:
        st.session_state.candidate_universe_all = list(universe)
    all_universe = st.session_state.candidate_universe_all

    max_overlap = max([int(x.get("strategy_count") or 0) for x in all_universe] + [1])
    c1, c2 = st.columns(2)
    min_overlap = c1.number_input("Minimum strategies matched", min_value=1, max_value=max_overlap, value=1)
    max_next = c2.number_input("Maximum companies sent to financial analysis (0 = no cap)", min_value=0, max_value=max(1, len(all_universe)), value=0)

    filtered = [x for x in all_universe if int(x.get("strategy_count") or 0) >= int(min_overlap)]
    filtered = sorted(filtered, key=lambda x: (-int(x.get("strategy_count") or 0), -float(x.get("research_priority_score") or 0), str(x.get("company"))))
    if max_next:
        filtered = filtered[:int(max_next)]

    default_selected = {x.get("company") for x in st.session_state.get("candidate_universe", filtered)}
    review_rows = []
    for x in filtered:
        review_rows.append({
            "Include": x.get("company") in default_selected,
            "Company": x.get("company"),
            "Strategies matched": x.get("strategy_count"),
            "Strategy IDs": x.get("strategies"),
            "Exact URL": x.get("url"),
            "Internal priority": x.get("research_priority_score"),
        })
    candidate_edit = st.data_editor(
        pd.DataFrame(review_rows),
        use_container_width=True,
        hide_index=True,
        disabled=["Company", "Strategies matched", "Strategy IDs", "Exact URL", "Internal priority"],
        key="candidate_review_editor",
    )
    if st.button("Apply candidate review"):
        selected = set(candidate_edit.loc[candidate_edit["Include"] == True, "Company"].tolist())
        st.session_state.candidate_universe = select_candidates(all_universe, selected)
        if run:
            run.log("OPERATOR", "CANDIDATE_REVIEW_APPLIED", f"User selected {len(selected)} of {len(all_universe)} candidates for financial analysis.")
        st.success(f"Financial analysis will use {len(selected)} companies.")

st.divider()
st.markdown("## 3. Financial-stage review before company research")
assessments = st.session_state.get("financial_assessments") or []
if not assessments or run is None:
    st.info("Run financial analysis first. Then you can accept or override which companies receive expensive company research.")
else:
    rows = []
    system_default = set()
    for x in assessments:
        proposed = x.get("system_decision", x.get("decision"))
        if proposed in {"ADVANCE", "WATCHLIST"}:
            system_default.add(x.get("company"))
        rows.append({
            "Research?": x.get("company") in system_default,
            "Company": x.get("company"),
            "System proposal": proposed,
            "Evidence coverage %": x.get("data_confidence"),
            "Why": x.get("system_reason", x.get("decision_reason")),
        })
    fin_edit = st.data_editor(
        pd.DataFrame(rows), use_container_width=True, hide_index=True,
        disabled=["Company", "System proposal", "Evidence coverage %", "Why"],
        key="financial_review_editor",
    )
    if st.button("Apply financial review"):
        selected = set(fin_edit.loc[fin_edit["Research?"] == True, "Company"].tolist())
        apply_financial_review(run, selected)
        run.log("OPERATOR", "FINANCIAL_REVIEW_APPLIED", f"User selected {len(selected)} companies for company research after reviewing system proposals.")
        st.success(f"Company research will use {len(selected)} companies. Original system proposals remain preserved.")

st.divider()
st.markdown("## 4. Deep-research & Bull/Bear control")
plan = st.session_state.get("research_plan") or {}
if not plan:
    st.info("Create the progressive research plan first. Its budgets should be treated as defaults, not immutable decisions.")
else:
    rows = plan.get("rows", [])
    plan_df = pd.DataFrame([{
        "Bull/Bear?": r.get("stage") == "ADVERSARIAL",
        "Company": r.get("company"),
        "System stage": r.get("system_stage", r.get("stage")),
        "Current stage": r.get("stage"),
        "Reason": r.get("system_reason", r.get("reason")),
        "Evidence quality": r.get("evidence_quality"),
        "Research readiness": r.get("research_readiness"),
    } for r in rows])
    plan_edit = st.data_editor(
        plan_df, use_container_width=True, hide_index=True,
        disabled=["Company", "System stage", "Current stage", "Reason", "Evidence quality", "Research readiness"],
        key="adversarial_review_editor",
    )
    if st.button("Apply Bull/Bear review"):
        selected = set(plan_edit.loc[plan_edit["Bull/Bear?"] == True, "Company"].tolist())
        st.session_state.research_plan = apply_adversarial_review(plan, selected)
        if run:
            run.log("OPERATOR", "ADVERSARIAL_REVIEW_APPLIED", f"User selected {len(selected)} companies for Bull/Bear challenge.")
        st.success(f"Bull/Bear stage will use {len(selected)} companies.")

st.divider()
st.caption("Operator overrides are explicit and logged. They do not erase the system's generated proposal, evidence coverage, or original reasoning.")
