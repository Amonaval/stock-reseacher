from __future__ import annotations

from collections import Counter

from research_depth_planner import plan_research_depth
from v6_pipeline import run_v6


def _key(name):
    return " ".join(str(name or "").split()).casefold()


def _document_coverage(company):
    required = {
        "annual_report",
        "quarterly_result",
        "investor_presentation",
        "earnings_call",
        "exchange_filing",
        "credit_rating",
    }
    present = {d.get("doc_type") for d in (company.documents or []) if d.get("doc_type")}
    return round(100 * len(required & present) / max(1, len(required)), 1)


def build_research_memories(run):
    """Rebuild analysis inputs from persistent company dossiers and evidence."""
    rows = []
    for company in run.companies.values():
        dossier = company.research_dossier or {}
        evidence = list(company.evidence or [])
        themes = Counter(str(e.get("theme") or "other") for e in evidence)
        risk_items = sum(
            1 for e in evidence
            if e.get("theme") in {"risk", "governance"}
            or str(e.get("kind", "")).upper() in {"RISK", "GOVERNANCE"}
        )
        rows.append({
            "company": company.company,
            "documents": len(company.documents or []),
            "document_types": sorted({d.get("doc_type") for d in (company.documents or []) if d.get("doc_type")}),
            "document_coverage": _document_coverage(company),
            "evidence_items": len(evidence),
            "evidence_quality": float(dossier.get("evidence_quality") or 0),
            "research_readiness": float(dossier.get("research_readiness") or 0),
            "research_state": company.research_state or dossier.get("research_state") or "NOT_RESEARCHED",
            "mission_coverage": float(dossier.get("mission_coverage") or 0),
            "open_questions": list(company.research_questions or dossier.get("open_questions") or []),
            "missing_document_types": list(dossier.get("missing_document_types") or []),
            "risk_items": risk_items,
            "catalyst_items": int(themes.get("catalyst", 0)),
            "management_claims": sum(
                1 for e in evidence
                if str(e.get("kind", "")).upper() in {"MANAGEMENT_CLAIM", "OUTLOOK"}
            ),
            "themes": dict(themes),
            "evidence": evidence,
            "financial_context": dict(company.financial_assessment or {}),
        })
    return rows


def plan_research_for_run(run, budgets=None):
    """Allocate research depth only. This is not an investment recommendation."""
    plan = plan_research_depth(build_research_memories(run), budgets)
    run.stage_summary["research_depth"] = {
        "counts": plan.get("counts", {}),
        "budgets": plan.get("budgets", {}),
        "budget_utilization": plan.get("budget_utilization", {}),
    }
    for row in plan.get("rows", []):
        company = run.ensure_company(row.get("company", ""))
        company.decisions.append({
            "stage": "RESEARCH_DEPTH",
            "decision": row.get("stage"),
            "system_decision": row.get("system_stage"),
            "reason": row.get("reason"),
            "system_reason": row.get("system_reason"),
        })
        run.log(
            "RESEARCH_DEPTH",
            "DEPTH_DECISION",
            f"{row.get('stage')}: {row.get('reason')}",
            company=row.get("company", ""),
            details={
                "research_state": row.get("research_state"),
                "mission_coverage": row.get("mission_coverage"),
                "document_coverage": row.get("document_coverage"),
                "evidence_quality": row.get("evidence_quality"),
                "research_readiness": row.get("research_readiness"),
                "risk_items": row.get("risk_items"),
                "open_questions": row.get("open_questions"),
            },
        )
    run.status = "RESEARCH_DEPTH_PLANNED"
    run.log(
        "RESEARCH_DEPTH",
        "PLANNING_COMPLETE",
        f"Research-depth allocation complete: {plan.get('counts', {})}.",
        details={"budget_utilization": plan.get("budget_utilization", {})},
    )
    return plan


def run_thesis_analysis(run, plan, company_names=None, progress=None):
    """Run evidence-bound bull/bear thesis analysis. No buy/sell recommendation is produced."""
    memories = build_research_memories(run)
    by_name = {_key(m.get("company")): m for m in memories}
    if company_names is None:
        names = [r.get("company") for r in plan.get("rows", []) if r.get("stage") == "ADVERSARIAL"]
    else:
        names = [x for x in company_names if x]
    selected = [by_name[_key(name)] for name in names if _key(name) in by_name]
    if not selected:
        run.log("ADVERSARIAL", "NO_READY_COMPANIES", "No company was selected for thesis analysis.", status="WARN")
        return []

    run.status = "ADVERSARIAL_RUNNING"
    run.log("ADVERSARIAL", "START", f"Running evidence-bound Bull/Bear thesis analysis for {len(selected)} companies.")
    results = run_v6(selected, finalist_names=[m.get("company") for m in selected], progress=progress)

    for result in results:
        company = run.ensure_company(result.get("company", ""))
        bundle = result.get("bull_bear", {}) or {}
        challenge = result.get("challenge", {}) or {}
        classification = result.get("classification", {}) or {}
        company.bull_case = bundle.get("bull", {}) or {}
        company.bear_case = bundle.get("bear", {}) or {}
        company.contradiction_review = challenge
        company.adversarial_result = result
        company.decisions.append({
            "stage": "ADVERSARIAL",
            "decision": classification.get("thesis_status"),
            "reason": challenge.get("challenge_summary", ""),
        })
        run.log(
            "ADVERSARIAL",
            "COMPANY_CHALLENGED",
            f"{classification.get('thesis_status')} · thesis balance {classification.get('thesis_balance')} · fragility {classification.get('fragility_score')}",
            company=company.company,
            details={
                "bull_strength": classification.get("bull_strength"),
                "bear_strength": classification.get("bear_strength"),
                "adversarial_readiness": classification.get("adversarial_readiness"),
                "unresolved_questions": classification.get("unresolved_questions", []),
                "fragility_flags": classification.get("fragility_flags", []),
                "mode": challenge.get("mode"),
            },
        )

    run.stage_summary["adversarial"] = {
        "companies": len(results),
        "states": dict(Counter((r.get("classification") or {}).get("thesis_status", "UNKNOWN") for r in results)),
    }
    run.status = "ADVERSARIAL_COMPLETE"
    run.log(
        "ADVERSARIAL",
        "COMPLETE",
        f"Bull/Bear thesis analysis completed for {len(results)} companies. These are research states, not recommendations.",
    )
    return results
