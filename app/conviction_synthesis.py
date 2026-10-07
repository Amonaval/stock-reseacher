from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any


DECISION_STATES = {
    "MORE_RESEARCH_NEEDED": "More research needed",
    "THESIS_CHALLENGE_PENDING": "Thesis challenge pending",
    "VALUATION_CONTEXT_INCOMPLETE": "Valuation context incomplete",
    "FINANCIAL_QUALITY_CONFLICT": "Financial quality conflicts with the thesis",
    "FRAGILE_RESEARCH_CASE": "Fragile research case",
    "RISK_DOMINATED_RESEARCH_CASE": "Risk-dominated research case",
    "CONTESTED_RESEARCH_CASE": "Contested research case",
    "HIGH_PRIORITY_RESEARCH_CANDIDATE": "High-priority research candidate",
    "POSITIVE_THESIS_NEAR_BASE_VALUE": "Positive thesis near base valuation",
    "POSITIVE_THESIS_VALUATION_STRETCHED": "Positive thesis but valuation stretched",
}


def _num(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _unique(items, limit=8):
    out = []
    seen = set()
    for item in items or []:
        if isinstance(item, dict):
            text = str(item.get("question") or item.get("point") or item.get("claim") or item.get("text") or item.get("reason") or "").strip()
        else:
            text = str(item or "").strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _research_confidence(company) -> dict:
    return dict((company.research_dossier or {}).get("evidence_confidence") or {})


def _classification(company) -> dict:
    adversarial = dict(company.adversarial_result or {})
    classification = dict(adversarial.get("classification") or {})
    if classification:
        return classification
    for decision in reversed(company.decisions or []):
        if decision.get("stage") == "ADVERSARIAL":
            return {"thesis_status": decision.get("decision")}
    return {}


def _challenge(company) -> dict:
    return dict((company.adversarial_result or {}).get("challenge") or company.contradiction_review or {})


def _valuation_posture(valuation: dict) -> dict:
    if not valuation:
        return {"state": "NOT_ASSESSED", "reason": "No valuation context has been produced yet."}
    if valuation.get("status") != "VALUED":
        return {
            "state": "BLOCKED_OR_INCOMPLETE",
            "reason": "; ".join(valuation.get("warnings") or []) or "The valuation model could not produce a supported scenario range.",
        }
    scenarios = valuation.get("scenarios") or {}
    bear = _num((scenarios.get("bear") or {}).get("upside_downside_pct"))
    base = _num((scenarios.get("base") or {}).get("upside_downside_pct"))
    bull = _num((scenarios.get("bull") or {}).get("upside_downside_pct"))
    if base is None:
        state = "SCENARIO_AVAILABLE_PRICE_COMPARISON_MISSING"
        reason = "Valuation scenarios exist, but price comparison is unavailable."
    elif base >= 20:
        state = "CAPTURED_PRICE_BELOW_BASE_SCENARIO"
        reason = f"Base fair-value scenario is {base:+.1f}% versus the price captured during financial research."
    elif base >= -10:
        state = "CAPTURED_PRICE_NEAR_BASE_SCENARIO"
        reason = f"Base fair-value scenario is {base:+.1f}% versus the captured price; price is broadly around the base scenario."
    else:
        state = "CAPTURED_PRICE_ABOVE_BASE_SCENARIO"
        reason = f"Base fair-value scenario is {base:+.1f}% versus the captured price; the current research assumptions do not support the captured valuation."
    return {
        "state": state,
        "reason": reason,
        "bear_vs_captured_pct": bear,
        "base_vs_captured_pct": base,
        "bull_vs_captured_pct": bull,
        "price_context": valuation.get("price_context"),
        "family": (valuation.get("valuation_family") or {}).get("label"),
        "method": valuation.get("method"),
    }


def _financial_posture(company) -> dict:
    assessment = dict(company.financial_assessment or {})
    system_decision = assessment.get("decision") or "NOT_ASSESSED"
    effective = assessment.get("effective_research_decision") or system_decision
    labels = dict(assessment.get("labels") or {})
    warnings = list(assessment.get("warnings") or [])
    return {
        "system_decision": system_decision,
        "effective_decision": effective,
        "data_confidence": _num(assessment.get("data_confidence"), 0.0),
        "financial_score": _num(assessment.get("financial_score")),
        "labels": labels,
        "warnings": warnings,
        "operator_override": effective != system_decision,
    }


def _thesis_posture(company) -> dict:
    classification = _classification(company)
    challenge = _challenge(company)
    return {
        "status": classification.get("thesis_status") or "NOT_CHALLENGED",
        "balance": _num(classification.get("thesis_balance")),
        "fragility": _num(classification.get("fragility_score")),
        "adversarial_readiness": _num(classification.get("adversarial_readiness")),
        "bull_strength": _num(classification.get("bull_strength")),
        "bear_strength": _num(classification.get("bear_strength")),
        "unresolved_questions": _unique(classification.get("unresolved_questions") or challenge.get("unresolved_questions"), 10),
        "fragility_flags": _unique(classification.get("fragility_flags") or challenge.get("fragility_flags"), 8),
        "contradictions": list(challenge.get("contradictions") or []),
    }


def _bull_conditions(company) -> tuple[list[str], list[str], list[str]]:
    bull = dict(company.bull_case or (company.adversarial_result or {}).get("bull_bear", {}).get("bull") or {})
    bear = dict(company.bear_case or (company.adversarial_result or {}).get("bull_bear", {}).get("bear") or {})
    must_hold = _unique((bull.get("what_must_be_true") or []) + (bull.get("key_assumptions") or []), 8)
    invalidation = _unique(bull.get("invalidation_conditions") or [], 8)
    bear_points = _unique(bear.get("points") or [], 6)
    return must_hold, invalidation, bear_points


def synthesize_company(company) -> dict[str, Any]:
    """Build an explainable research decision state, never a buy/sell instruction.

    No composite conviction score is produced. The state is derived from visible
    gates and orthogonal dimensions so the investor can disagree with any input.
    """
    confidence = _research_confidence(company)
    financial = _financial_posture(company)
    thesis = _thesis_posture(company)
    valuation = dict(company.valuation or {})
    valuation_posture = _valuation_posture(valuation)

    research_state = confidence.get("research_confidence_state") or "NOT_ASSESSED"
    valuation_gate = confidence.get("valuation_context") or "MORE_RESEARCH_NEEDED"
    critical_gaps = _unique(confidence.get("critical_gaps") or [], 8)
    research_questions = _unique(company.research_questions or (company.research_dossier or {}).get("open_questions") or [], 8)
    unresolved = _unique(research_questions + thesis.get("unresolved_questions", []), 10)

    must_hold, invalidation, bear_points = _bull_conditions(company)
    fragility = thesis.get("fragility")
    thesis_status = thesis.get("status")
    base_delta = valuation_posture.get("base_vs_captured_pct")

    reasons = []
    blockers = []

    if valuation_gate != "READY_FOR_VALUATION_CONTEXT":
        state = "MORE_RESEARCH_NEEDED"
        blockers.extend(critical_gaps or ["Research Confidence has not cleared the valuation-context gate."])
        reasons.append("The evidence foundation is not yet strong enough for a decision-quality synthesis.")
    elif thesis_status in {"NOT_CHALLENGED", "INSUFFICIENT_EVIDENCE"}:
        state = "THESIS_CHALLENGE_PENDING"
        blockers.append("Bull/Bear thesis challenge is missing or still reports insufficient evidence.")
        reasons.append("Research quality passed, but the thesis has not survived adversarial review yet.")
    elif not valuation or valuation.get("status") != "VALUED":
        state = "VALUATION_CONTEXT_INCOMPLETE"
        blockers.extend(valuation.get("warnings") or ["Supported valuation scenarios are not available."])
        reasons.append("The researched thesis exists, but price/value context is incomplete.")
    elif financial.get("system_decision") in {"ELIMINATE", "HOLD"} and not financial.get("operator_override"):
        state = "FINANCIAL_QUALITY_CONFLICT"
        blockers.append(f"Financial stage system decision is {financial.get('system_decision')} without an operator override.")
        reasons.append("Later narrative/valuation evidence conflicts with the earlier financial-quality gate.")
    elif thesis_status == "BEAR_CASE_DOMINATES":
        state = "RISK_DOMINATED_RESEARCH_CASE"
        reasons.append("The independent Bear case is better supported than the Bull case on the current evidence.")
    elif thesis_status == "FRAGILE" or (fragility is not None and fragility >= 70):
        state = "FRAGILE_RESEARCH_CASE"
        reasons.append("The thesis depends heavily on unresolved assumptions, contradictions or fragile evidence.")
    elif thesis_status == "CONTESTED":
        state = "CONTESTED_RESEARCH_CASE"
        reasons.append("Bull and Bear interpretations remain materially contested after adversarial review.")
    elif thesis_status == "BULL_CASE_SURVIVES":
        if base_delta is not None and base_delta >= 20 and (fragility is None or fragility < 55):
            state = "HIGH_PRIORITY_RESEARCH_CANDIDATE"
            reasons.append("The Bull case survives adversarial review and the base valuation scenario remains meaningfully above the captured price.")
        elif base_delta is not None and base_delta < -10:
            state = "POSITIVE_THESIS_VALUATION_STRETCHED"
            reasons.append("The Bull case survives, but the captured price is above the current base valuation scenario.")
        else:
            state = "POSITIVE_THESIS_NEAR_BASE_VALUE"
            reasons.append("The Bull case survives while the captured price is broadly near the current base valuation scenario.")
    else:
        state = "CONTESTED_RESEARCH_CASE"
        reasons.append(f"Thesis state {thesis_status} does not support a stronger synthesis state yet.")

    if financial.get("operator_override"):
        reasons.append(
            f"Operator override is active at the financial gate: system {financial.get('system_decision')} → effective {financial.get('effective_decision')}."
        )
    if valuation.get("warnings"):
        reasons.extend(_unique(valuation.get("warnings"), 3))

    what_raises = []
    what_lowers = []
    if critical_gaps:
        what_raises.extend([f"Resolve: {x}" for x in critical_gaps[:4]])
    if unresolved:
        what_raises.extend([f"Answer: {x}" for x in unresolved[:4]])
    if valuation_posture.get("state") == "CAPTURED_PRICE_ABOVE_BASE_SCENARIO":
        what_raises.append("A lower captured/live market valuation or stronger evidence-backed normalized earnings could improve valuation posture.")
    if thesis_status == "CONTESTED":
        what_raises.append("Resolve the highest-impact Bull/Bear contradictions with newer primary evidence.")
    if thesis_status == "BULL_CASE_SURVIVES":
        what_lowers.extend(invalidation[:4])
        what_lowers.extend(bear_points[:3])
    elif bear_points:
        what_lowers.extend(bear_points[:4])
    what_lowers.extend(thesis.get("fragility_flags", [])[:3])

    decision_readiness = (
        "READY_FOR_INVESTOR_REVIEW"
        if state not in {"MORE_RESEARCH_NEEDED", "THESIS_CHALLENGE_PENDING", "VALUATION_CONTEXT_INCOMPLETE"}
        else "NOT_READY_FOR_INVESTOR_REVIEW"
    )

    return {
        "company": company.company,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "decision_state": state,
        "decision_label": DECISION_STATES[state],
        "decision_readiness": decision_readiness,
        "dimensions": {
            "research_quality": {
                "state": research_state,
                "score": confidence.get("research_confidence_score"),
                "critical_gaps": critical_gaps,
            },
            "financial_quality": financial,
            "thesis": thesis,
            "valuation": valuation_posture,
        },
        "reasons": _unique(reasons, 8),
        "blockers": _unique(blockers, 8),
        "unresolved_questions": unresolved,
        "what_must_be_true": must_hold,
        "invalidation_conditions": invalidation,
        "what_could_raise_confidence": _unique(what_raises, 8),
        "what_could_lower_confidence": _unique(what_lowers, 8),
        "system_scope": (
            "Research decision synthesis only. This state is not a buy/sell recommendation, return forecast, portfolio weight, or personalized investment instruction."
        ),
    }


def synthesize_run(run) -> list[dict[str, Any]]:
    results = []
    counts = Counter()
    readiness = Counter()
    for company in run.companies.values():
        if not company.financial_assessment:
            continue
        result = synthesize_company(company)
        company.decision_synthesis = result
        results.append(result)
        counts[result["decision_state"]] += 1
        readiness[result["decision_readiness"]] += 1
    run.stage_summary["decision_synthesis"] = {
        "companies": len(results),
        "states": dict(counts),
        "readiness": dict(readiness),
    }
    run.log(
        "DECISION_SYNTHESIS",
        "SYNTHESIS_COMPLETE",
        f"Decision synthesis completed for {len(results)} companies: {dict(counts)}.",
        details=run.stage_summary["decision_synthesis"],
    )
    return sorted(
        results,
        key=lambda x: (
            0 if x.get("decision_state") == "HIGH_PRIORITY_RESEARCH_CANDIDATE" else 1,
            x.get("decision_label", ""),
            x.get("company", "").casefold(),
        ),
    )
