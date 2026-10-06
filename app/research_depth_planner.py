from __future__ import annotations


def _n(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def plan_research_depth(memories: list[dict], budgets: dict | None = None) -> dict:
    """Allocate research effort without pretending the ordering is investment conviction.

    Gates are evidence-oriented. Budgets control how many companies receive increasingly
    expensive analysis; held companies remain in the run with a reason.
    """
    budgets = budgets or {"STRUCTURED": 100, "TARGETED": 50, "DEEP": 25, "ADVERSARIAL": 15}
    rows = []
    for m in memories:
        f = m.get("financial_context", {})
        fin_decision = f.get("decision") or f.get("v3_funnel_decision") or ""
        docs = int(m.get("documents") or 0)
        doc_cov = _n(m.get("document_coverage"))
        evq = _n(m.get("evidence_quality"))
        ready = _n(m.get("research_readiness"))
        risks = int(m.get("risk_items") or 0)
        unresolved = int(m.get("management_claims") or 0)
        if fin_decision not in {"ADVANCE", "WATCHLIST"}:
            stage = "FINANCIAL_HOLD"
            reason = f"Financial stage is {fin_decision or 'not ready'}."
        elif docs < 1:
            stage = "SOURCE_GAP"
            reason = "No usable company research document has been collected yet."
        elif doc_cov < 35 or evq < 35:
            stage = "STRUCTURED"
            reason = "Initial evidence exists, but source/evidence coverage is still incomplete."
        elif doc_cov < 55 or evq < 50:
            stage = "TARGETED"
            reason = "Enough evidence for targeted gap resolution, but not yet for deep thesis work."
        elif risks == 0:
            stage = "DEEP"
            reason = "Evidence coverage supports deep research, but explicit downside/risk evidence is still missing."
        elif ready < 70:
            stage = "DEEP"
            reason = "Deep research is justified; remaining gaps prevent adversarial handoff."
        else:
            stage = "ADVERSARIAL"
            reason = "Source coverage, evidence quality, and downside evidence are sufficient for Bull/Bear challenge."
        priority = ready * 0.5 + evq * 0.3 + doc_cov * 0.2
        rows.append({
            "company": m.get("company"), "stage": stage, "reason": reason, "documents": docs,
            "document_coverage": doc_cov, "evidence_quality": evq, "research_readiness": ready,
            "risk_items": risks, "unresolved_management_claims": unresolved,
            "research_priority": round(priority, 1),
        })

    for stage in ["STRUCTURED", "TARGETED", "DEEP", "ADVERSARIAL"]:
        candidates = sorted([r for r in rows if r["stage"] == stage], key=lambda x: -x["research_priority"])
        cap = int(budgets.get(stage, 999999))
        for idx, row in enumerate(candidates):
            if idx >= cap:
                row["original_stage"] = stage
                row["stage"] = "RESEARCH_QUEUE"
                row["reason"] = f"Evidence gate passed for {stage}, but current research budget is {cap}; retained for a later pass."

    counts = {}
    for r in rows:
        counts[r["stage"]] = counts.get(r["stage"], 0) + 1
    return {"rows": sorted(rows, key=lambda x: (x["stage"], -x["research_priority"])), "counts": counts, "budgets": budgets}
