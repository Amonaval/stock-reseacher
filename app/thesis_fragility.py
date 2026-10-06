from __future__ import annotations


def _num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def score_fragility(memory, challenge):
    """
    Measures how dependent the thesis is on unresolved assumptions / weak evidence.
    0 = robustly evidenced, 100 = highly fragile. This is NOT downside probability.
    """
    unresolved = len(challenge.get("unresolved_questions") or [])
    flags = len(challenge.get("fragility_flags") or [])
    contradictions = challenge.get("contradictions") or []
    unresolved_contradictions = sum(
        1 for c in contradictions if c.get("resolution") in {"unresolved", "mixed", None, ""}
    )
    mgmt_claims = int(memory.get("management_claims") or 0)
    evidence_quality = _num(memory.get("evidence_quality"), 0)
    doc_coverage = _num(memory.get("document_coverage"), 0)

    raw = (
        min(28, unresolved * 4)
        + min(22, flags * 3.5)
        + min(20, unresolved_contradictions * 5)
        + min(15, mgmt_claims * 2.5)
        + max(0, 70 - evidence_quality) * 0.22
        + max(0, 70 - doc_coverage) * 0.18
    )
    return round(max(0, min(100, raw)), 1)


def adversarial_readiness(memory, challenge):
    quality = _num(memory.get("evidence_quality"), 0)
    readiness = _num(memory.get("research_readiness"), 0)
    confidence = {
        "high": 100,
        "medium": 68,
        "low": 35,
    }.get(str(challenge.get("challenge_confidence", "")).lower(), 35)
    fragility = score_fragility(memory, challenge)

    score = (
        quality * 0.35
        + readiness * 0.30
        + confidence * 0.20
        + (100 - fragility) * 0.15
    )
    return round(max(0, min(100, score)), 1)


def classify_thesis(memory, challenge):
    fragility = score_fragility(memory, challenge)
    readiness = adversarial_readiness(memory, challenge)
    balance = _num(challenge.get("thesis_balance"), 50)

    if readiness < 50:
        status = "INSUFFICIENT_EVIDENCE"
    elif fragility >= 70:
        status = "FRAGILE"
    elif 42 <= balance <= 58:
        status = "CONTESTED"
    elif balance > 58:
        status = "BULL_CASE_SURVIVES"
    else:
        status = "BEAR_CASE_DOMINATES"

    return {
        "company": memory.get("company"),
        "thesis_status": status,
        "thesis_balance": balance,
        "fragility_score": fragility,
        "adversarial_readiness": readiness,
        "bull_strength": _num(challenge.get("bull_strength"), 0),
        "bear_strength": _num(challenge.get("bear_strength"), 0),
        "unresolved_questions": challenge.get("unresolved_questions") or [],
        "fragility_flags": challenge.get("fragility_flags") or [],
    }
