from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone


def _num(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %Y", "%B %Y", "%Y"):
        try:
            dt = datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _authority(document: dict) -> float:
    if document.get("source_score") is not None:
        return max(0.0, min(100.0, _num(document.get("source_score"))))
    source_class = str(document.get("source_class") or document.get("source_kind") or "").lower()
    if any(x in source_class for x in ("exchange", "regulator", "company", "primary")):
        return 95.0
    if any(x in source_class for x in ("rating", "credit")):
        return 90.0
    if any(x in source_class for x in ("secondary", "media", "news")):
        return 60.0
    return 45.0


def _freshness(document: dict, now: datetime) -> float | None:
    dt = _parse_date(document.get("document_date") or document.get("date"))
    if not dt:
        return None
    age_days = max(0, (now - dt).days)
    doc_type = str(document.get("doc_type") or "")
    # Annual reports remain structurally useful for longer; operating/disclosure
    # sources should be more recent.
    if doc_type == "annual_report":
        if age_days <= 550:
            return 100.0
        if age_days <= 900:
            return 75.0
        return 45.0
    if age_days <= 180:
        return 100.0
    if age_days <= 365:
        return 85.0
    if age_days <= 730:
        return 60.0
    return 35.0


def _evidence_doc_id(item: dict) -> str:
    return str(item.get("document_id") or item.get("document_title") or "")


def assess_evidence_confidence(company, *, now: datetime | None = None) -> dict:
    """Assess research quality, never stock attractiveness.

    The score answers: "How trustworthy and decision-useful is the current
    research dossier?" It is intentionally separate from valuation, conviction,
    expected return and buy/sell decisions.
    """
    now = now or datetime.now(timezone.utc)
    documents = list(company.documents or [])
    evidence = list(company.evidence or [])
    dossier = dict(company.research_dossier or {})
    assessment = dict(company.financial_assessment or {})

    authority_values = [_authority(d) for d in documents]
    authority = round(sum(authority_values) / len(authority_values), 1) if authority_values else 0.0

    freshness_values = [x for x in (_freshness(d, now) for d in documents) if x is not None]
    freshness = round(sum(freshness_values) / len(freshness_values), 1) if freshness_values else 0.0

    traceable = [e for e in evidence if _evidence_doc_id(e) and (e.get("page") is not None or e.get("excerpt") or e.get("claim"))]
    traceability = round(100 * len(traceable) / max(1, len(evidence)), 1) if evidence else 0.0

    mission_coverage = _num(dossier.get("mission_coverage"), 0.0)

    # Theme-level triangulation: do multiple independent documents support each
    # covered research theme? This is intentionally not claimed as semantic
    # claim-level corroboration.
    docs_by_theme = defaultdict(set)
    for item in evidence:
        theme = str(item.get("theme") or "other")
        doc_id = _evidence_doc_id(item)
        if doc_id:
            docs_by_theme[theme].add(doc_id)
    covered_themes = [t for t, ds in docs_by_theme.items() if ds]
    triangulated = [t for t, ds in docs_by_theme.items() if len(ds) >= 2]
    triangulation = round(100 * len(triangulated) / max(1, len(covered_themes)), 1) if covered_themes else 0.0

    risk_items = [
        e for e in evidence
        if str(e.get("theme") or "").lower() in {"risk", "governance"}
        or str(e.get("kind") or "").upper() in {"RISK", "GOVERNANCE"}
    ]
    risk_docs = {_evidence_doc_id(e) for e in risk_items if _evidence_doc_id(e)}
    downside_coverage = 0.0
    if risk_items:
        downside_coverage = 55.0
        if len(risk_docs) >= 2:
            downside_coverage = 80.0
        if len(risk_docs) >= 3:
            downside_coverage = 100.0

    contradiction_review = dict(company.contradiction_review or {})
    adversarial = dict(getattr(company, "adversarial_result", {}) or {})
    challenge = dict((adversarial.get("challenge") or contradiction_review) or {})
    contradictions = list(challenge.get("contradictions") or [])
    unresolved = list(challenge.get("unresolved_questions") or [])
    if challenge:
        contradiction_handling = max(20.0, 100.0 - min(60.0, len(unresolved) * 12.0) - min(20.0, len(contradictions) * 3.0))
    else:
        contradiction_handling = 45.0  # not yet challenged; unknown, not failed

    financial_coverage = _num(assessment.get("data_confidence"), 0.0)
    open_questions = list(company.research_questions or dossier.get("open_questions") or [])

    dimensions = {
        "source_authority": round(authority, 1),
        "source_freshness": round(freshness, 1),
        "evidence_traceability": round(traceability, 1),
        "fundamental_mission_coverage": round(mission_coverage, 1),
        "cross_source_triangulation": round(triangulation, 1),
        "downside_evidence_coverage": round(downside_coverage, 1),
        "contradiction_handling": round(contradiction_handling, 1),
        "financial_data_coverage": round(financial_coverage, 1),
    }

    score = (
        authority * 0.15
        + freshness * 0.10
        + traceability * 0.15
        + mission_coverage * 0.20
        + triangulation * 0.15
        + downside_coverage * 0.10
        + contradiction_handling * 0.10
        + financial_coverage * 0.05
    )
    # Open questions reduce confidence, but never erase otherwise strong evidence.
    score -= min(18.0, len(open_questions) * 2.5)
    score = round(max(0.0, min(100.0, score)), 1)

    critical_gaps = []
    doc_types = {str(d.get("doc_type") or "") for d in documents}
    if "annual_report" not in doc_types:
        critical_gaps.append("No annual report / equivalent longitudinal primary source in the dossier.")
    fresh_types = {"quarterly_result", "exchange_filing", "investor_presentation", "earnings_call"}
    if not (doc_types & fresh_types):
        critical_gaps.append("No recent operating/disclosure source is present.")
    if mission_coverage < 70:
        critical_gaps.append("Fundamental analyst mission coverage is below 70%.")
    if traceability < 70:
        critical_gaps.append("Too much evidence lacks strong source/page traceability.")
    if downside_coverage == 0:
        critical_gaps.append("No explicit downside/governance evidence has been captured.")
    if financial_coverage and financial_coverage < 60:
        critical_gaps.append("Financial data coverage remains weak.")

    if score >= 75 and not critical_gaps:
        state = "HIGH_RESEARCH_CONFIDENCE"
    elif score >= 55 and len(critical_gaps) <= 2:
        state = "MODERATE_RESEARCH_CONFIDENCE"
    else:
        state = "LOW_RESEARCH_CONFIDENCE"

    valuation_context = (
        "READY_FOR_VALUATION_CONTEXT"
        if state in {"HIGH_RESEARCH_CONFIDENCE", "MODERATE_RESEARCH_CONFIDENCE"}
        and not critical_gaps
        and mission_coverage >= 70
        and financial_coverage >= 60
        and downside_coverage > 0
        else "MORE_RESEARCH_NEEDED"
    )

    return {
        "company": company.company,
        "research_confidence_state": state,
        "research_confidence_score": score,
        "dimensions": dimensions,
        "critical_gaps": critical_gaps,
        "open_questions": len(open_questions),
        "covered_themes": sorted(covered_themes),
        "triangulated_themes": sorted(triangulated),
        "documents": len(documents),
        "evidence_items": len(evidence),
        "valuation_context": valuation_context,
        "explanation": (
            "This measures confidence in the research evidence and process. It does not measure investment attractiveness, conviction or expected return."
        ),
    }


def assess_run_evidence_confidence(run) -> list[dict]:
    results = []
    counts = defaultdict(int)
    for company in run.companies.values():
        if not company.documents and not company.evidence:
            continue
        result = assess_evidence_confidence(company)
        company.research_dossier = dict(company.research_dossier or {})
        company.research_dossier["evidence_confidence"] = result
        results.append(result)
        counts[result["research_confidence_state"]] += 1
    run.stage_summary["evidence_confidence"] = {
        "companies": len(results),
        "states": dict(counts),
        "valuation_context_ready": sum(1 for r in results if r["valuation_context"] == "READY_FOR_VALUATION_CONTEXT"),
    }
    run.log(
        "EVIDENCE_CONFIDENCE",
        "ASSESSMENT_COMPLETE",
        f"Assessed research confidence for {len(results)} companies: {dict(counts)}.",
        details=run.stage_summary["evidence_confidence"],
    )
    return sorted(results, key=lambda x: -x["research_confidence_score"])
