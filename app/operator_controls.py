from __future__ import annotations


def select_candidates(universe: list[dict], included_names: set[str]) -> list[dict]:
    keys = {str(x).strip().casefold() for x in included_names}
    return [x for x in universe if str(x.get("company", "")).strip().casefold() in keys]


def apply_financial_review(run, selected_for_research: set[str]) -> None:
    """Preserve the system proposal while allowing explicit user override.

    Existing downstream code reads financial_assessment['decision']; therefore the
    effective decision is changed, while system_decision/system_reason retain the
    original assessment for transparency and reset/debug.
    """
    keys = {str(x).strip().casefold() for x in selected_for_research}
    for key, company in run.companies.items():
        fa = company.financial_assessment
        if not fa:
            continue
        fa.setdefault("system_decision", fa.get("decision"))
        fa.setdefault("system_reason", fa.get("decision_reason"))
        selected = key in keys
        fa["user_selected_for_research"] = selected
        if selected:
            if fa.get("system_decision") in {"ADVANCE", "WATCHLIST"}:
                fa["decision"] = fa.get("system_decision")
                fa["decision_reason"] = fa.get("system_reason")
            else:
                fa["decision"] = "ADVANCE"
                fa["decision_reason"] = (
                    f"User override: continue research despite system proposal "
                    f"{fa.get('system_decision')}. Original reason: {fa.get('system_reason')}"
                )
        else:
            fa["decision"] = "USER_HOLD"
            fa["decision_reason"] = (
                f"Held by user review. System proposal was {fa.get('system_decision')}: "
                f"{fa.get('system_reason')}"
            )


def apply_adversarial_review(plan: dict, selected_names: set[str]) -> dict:
    keys = {str(x).strip().casefold() for x in selected_names}
    for row in plan.get("rows", []):
        key = str(row.get("company", "")).strip().casefold()
        row.setdefault("system_stage", row.get("stage"))
        row.setdefault("system_reason", row.get("reason"))
        if key in keys:
            row["stage"] = "ADVERSARIAL"
            if row.get("system_stage") != "ADVERSARIAL":
                row["reason"] = (
                    f"User override: include in adversarial review. System stage was "
                    f"{row.get('system_stage')}: {row.get('system_reason')}"
                )
        elif row.get("system_stage") == "ADVERSARIAL":
            row["stage"] = "DEEP"
            row["reason"] = (
                f"Held from adversarial review by user. System proposal: "
                f"{row.get('system_reason')}"
            )
    counts = {}
    for row in plan.get("rows", []):
        counts[row.get("stage", "UNKNOWN")] = counts.get(row.get("stage", "UNKNOWN"), 0) + 1
    plan["counts"] = counts
    return plan
