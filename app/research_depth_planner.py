from __future__ import annotations


def _n(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def plan_research_depth(memories: list[dict], budgets: dict | None = None) -> dict:
    """Allocate progressively more expensive research effort.

    This planner is intentionally *not* an investment-conviction engine. It answers:
    "How much more research does this company deserve given what we currently know?"

    Inputs may include the newer investor dossier fields produced by
    ``company_research_engine``:
      - research_state
      - mission_coverage
      - open_questions
      - missing_document_types

    Older memories remain supported for backward compatibility.
    """
    budgets = budgets or {"STRUCTURED": 100, "TARGETED": 50, "DEEP": 25, "ADVERSARIAL": 15}
    rows = []

    for m in memories:
        f = m.get("financial_context", {}) or {}
        fin_decision = (
            f.get("effective_research_decision")
            or f.get("decision")
            or f.get("v3_funnel_decision")
            or ""
        )
        docs = int(m.get("documents") or 0)
        doc_cov = _n(m.get("document_coverage"))
        evq = _n(m.get("evidence_quality"))
        ready = _n(m.get("research_readiness"))
        risks = int(m.get("risk_items") or 0)
        unresolved_claims = int(m.get("management_claims") or 0)
        research_state = str(m.get("research_state") or "").strip().upper()
        mission_coverage = _n(m.get("mission_coverage"))
        open_questions = list(m.get("open_questions") or [])
        missing_doc_types = list(m.get("missing_document_types") or [])

        # New constitution-aware gates take precedence. Older runs without dossier
        # fields fall through to the legacy evidence thresholds below.
        if fin_decision and fin_decision not in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}:
            stage = "FINANCIAL_HOLD"
            reason = f"Financial stage is {fin_decision}; company is retained but not allocated expensive research."
        elif research_state == "SOURCE_GAP":
            stage = "SOURCE_GAP"
            reason = "Authoritative source/evidence acquisition is incomplete; resolve the source gap before deeper thesis work."
        elif docs < 1:
            stage = "SOURCE_GAP"
            reason = "No usable company research document has been collected yet."
        elif research_state == "RESEARCH_INCOMPLETE" and (mission_coverage < 45 or doc_cov < 35 or evq < 35):
            stage = "STRUCTURED"
            reason = "Research exists but core analyst missions/source coverage remain too incomplete for targeted thesis work."
        elif research_state == "RESEARCH_INCOMPLETE" and (mission_coverage < 70 or doc_cov < 55 or evq < 50):
            stage = "TARGETED"
            reason = "Resolve specific missing analyst missions and source classes before deep thesis work."
        elif doc_cov < 35 or evq < 35:
            stage = "STRUCTURED"
            reason = "Initial evidence exists, but source/evidence coverage is still incomplete."
        elif doc_cov < 55 or evq < 50:
            stage = "TARGETED"
            reason = "Enough evidence for targeted gap resolution, but not yet for deep thesis work."
        elif research_state and research_state != "EVIDENCE_READY":
            stage = "DEEP"
            reason = "Evidence is meaningful, but the company-research contract still has unresolved questions requiring deep work."
        elif risks == 0:
            stage = "DEEP"
            reason = "Evidence coverage supports deep research, but explicit downside/risk evidence is still missing."
        elif ready < 70:
            stage = "DEEP"
            reason = "Deep research is justified; evidence readiness is not yet strong enough for adversarial handoff."
        else:
            stage = "ADVERSARIAL"
            reason = "Source coverage, analyst-mission coverage, evidence quality and downside evidence support an independent Bull/Bear challenge."

        # Research priority ranks work allocation only. It is not expected return.
        priority = (
            ready * 0.35
            + evq * 0.25
            + doc_cov * 0.15
            + mission_coverage * 0.25
        )
        rows.append({
            "company": m.get("company"),
            "stage": stage,
            "system_stage": stage,
            "reason": reason,
            "system_reason": reason,
            "research_state": research_state or "LEGACY_MEMORY",
            "documents": docs,
            "document_coverage": doc_cov,
            "evidence_quality": evq,
            "research_readiness": ready,
            "mission_coverage": mission_coverage,
            "risk_items": risks,
            "open_questions": len(open_questions),
            "missing_document_types": len(missing_doc_types),
            "unresolved_management_claims": unresolved_claims,
            "research_priority": round(priority, 1),
        })

    # Capacity budgets are applied only after evidence gates. A company that passes
    # a gate but falls outside the current budget is queued, never silently dropped.
    for stage in ["STRUCTURED", "TARGETED", "DEEP", "ADVERSARIAL"]:
        candidates = sorted(
            [r for r in rows if r["stage"] == stage],
            key=lambda x: -x["research_priority"],
        )
        cap = int(budgets.get(stage, 999999))
        for idx, row in enumerate(candidates):
            if idx >= cap:
                row["original_stage"] = stage
                row["stage"] = "RESEARCH_QUEUE"
                row["reason"] = (
                    f"Evidence gate passed for {stage}, but the current research budget is {cap}; "
                    "retained for a later pass."
                )

    counts = {}
    for r in rows:
        counts[r["stage"]] = counts.get(r["stage"], 0) + 1

    utilization = {}
    for stage in ["STRUCTURED", "TARGETED", "DEEP", "ADVERSARIAL"]:
        admitted = sum(1 for r in rows if r["stage"] == stage)
        passed_gate = sum(
            1
            for r in rows
            if r.get("system_stage") == stage
        )
        utilization[stage] = {
            "budget": int(budgets.get(stage, 0)),
            "passed_gate": passed_gate,
            "admitted": admitted,
            "queued": max(0, passed_gate - admitted),
        }

    stage_order = {
        "ADVERSARIAL": 0,
        "DEEP": 1,
        "TARGETED": 2,
        "STRUCTURED": 3,
        "RESEARCH_QUEUE": 4,
        "SOURCE_GAP": 5,
        "FINANCIAL_HOLD": 6,
    }
    return {
        "rows": sorted(
            rows,
            key=lambda x: (stage_order.get(x["stage"], 99), -x["research_priority"]),
        ),
        "counts": counts,
        "budgets": budgets,
        "budget_utilization": utilization,
    }
