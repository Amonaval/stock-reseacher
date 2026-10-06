from __future__ import annotations

from financial_scoring import financial_scorecard, elimination_reasons


def band(value):
    if value is None:
        return "Insufficient data"
    if value >= 75:
        return "Strong"
    if value >= 60:
        return "Healthy"
    if value >= 45:
        return "Mixed"
    if value >= 30:
        return "Weak"
    return "Poor"


def assess_company(row: dict) -> dict:
    score = financial_scorecard(row)
    hard, warnings = elimination_reasons(row, score)
    coverage = float(score.get("data_confidence") or 0)
    overall = float(score.get("financial_score") or 0)

    if hard:
        decision = "ELIMINATE"
        reason = "; ".join(hard)
    elif coverage < 60:
        decision = "DATA_RETRY"
        reason = f"Only {coverage:.0f}% of required financial dimensions are available; collect more evidence before narrowing."
    elif overall >= 60:
        decision = "ADVANCE"
        reason = "Adequate financial evidence with no distress gate and a healthy preliminary financial profile."
    elif overall >= 45:
        decision = "WATCHLIST"
        reason = "Financial profile is mixed; retain for contextual research rather than treating it as a clean pass."
    else:
        decision = "HOLD"
        reason = "Financial profile is weak on the currently available evidence."

    return {
        **score,
        "decision": decision,
        "funnel_decision": decision,
        "decision_reason": reason,
        "hard_exclusions": hard,
        "warnings": warnings,
        "labels": {
            "growth": band(score.get("growth_score")),
            "capital_efficiency": band(score.get("quality_score")),
            "balance_sheet": band(score.get("balance_sheet_score")),
            "cash_generation": band(score.get("cash_flow_score")),
            "ownership": band(score.get("ownership_score")),
            "valuation": band(score.get("valuation_score")),
        },
        "assessment_type": "PRELIMINARY_FINANCIAL_RESEARCH",
        "score_is_internal": True,
    }


def assess_universe(companies: list[dict]) -> list[dict]:
    out = [{**row, **assess_company(row)} for row in companies]
    order = {"ADVANCE": 0, "WATCHLIST": 1, "DATA_RETRY": 2, "HOLD": 3, "ELIMINATE": 4}
    return sorted(out, key=lambda x: (order.get(x.get("decision"), 9), -(x.get("financial_score") or 0), x.get("company", "").casefold()))
