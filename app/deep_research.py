from __future__ import annotations

"""V5 research-depth funnel.

This module decides how much *research effort* to spend on each company based on
source/evidence completeness. It does not make an investment recommendation.
"""

STAGES = [
    ("L1_STRUCTURED", 30, 25, 100),
    ("L2_TARGETED", 45, 40, 50),
    ("L3_DEEP", 60, 52, 25),
    ("L4_MAXIMUM", 72, 62, 15),
]


def _num(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def run_progressive_funnel(memories, tasks=None, budgets=None):
    """Allocate progressively deeper research to better-documented companies.

    Companies outside a stage budget remain available for future research runs.
    """
    budgets = budgets or {}
    current = list(memories)
    stages = {}
    audit = []

    for stage, min_readiness, min_quality, default_budget in STAGES:
        budget = int(budgets.get(stage, default_budget))
        eligible = []
        deferred = []
        for memory in current:
            readiness = _num(memory.get("research_readiness"))
            quality = _num(memory.get("evidence_quality"))
            row = {
                "company": memory.get("company"),
                "stage": stage,
                "research_readiness": readiness,
                "evidence_quality": quality,
                "research_priority": round(readiness * 0.55 + quality * 0.45, 2),
            }
            if readiness < min_readiness or quality < min_quality:
                row.update(status="NEEDS_MORE_EVIDENCE", reason="Evidence/readiness gate not met.")
                deferred.append(row)
            else:
                eligible.append(row)

        eligible.sort(key=lambda x: -x["research_priority"])
        selected = eligible[:budget]
        overflow = eligible[budget:]
        for row in selected:
            row.update(status="DEEPER_RESEARCH", reason="Inside current research-depth budget.")
        for row in overflow:
            row.update(status="DEFERRED", reason="Outside current research-depth budget; retained for later.")
        deferred.extend(overflow)

        selected_names = {row["company"] for row in selected}
        current = [m for m in current if m.get("company") in selected_names]
        stages[stage] = {
            "budget": budget,
            "selected": selected,
            "deferred": deferred,
            "selected_count": len(selected),
            "deferred_count": len(deferred),
        }
        audit.extend(selected + deferred)
        if not current:
            break

    return {
        "stages": stages,
        "audit": audit,
        "finalists": stages.get("L4_MAXIMUM", {}).get("selected", []),
    }


def funnel_summary(funnel):
    lines = ["# V5 Autonomous Deep Research Funnel", ""]
    for stage, payload in funnel.get("stages", {}).items():
        lines.extend([
            f"## {stage}",
            f"Selected for deeper research: {payload.get('selected_count', 0)}",
            f"Deferred / needs evidence: {payload.get('deferred_count', 0)}",
            "",
        ])
    return "\n".join(lines)
