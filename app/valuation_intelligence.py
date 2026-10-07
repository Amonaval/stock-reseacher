from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Any


VALUATION_FAMILIES = {
    "GENERAL_EARNINGS": "General / quality business",
    "FINANCIAL_PB": "Bank / NBFC / financial business",
    "CYCLICAL_NORMALIZED": "Cyclical / commodity business",
    "UTILITY_ASSET_HEAVY": "Utility / regulated / asset-heavy business",
    "INSUFFICIENT": "Insufficient valuation inputs",
}


def _num(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _positive(values):
    return [float(x) for x in values if _num(x) is not None and float(x) > 0]


def _text_blob(company) -> str:
    parts: list[str] = [company.company]
    for item in list(company.evidence or [])[:250]:
        parts.extend([
            str(item.get("claim") or ""),
            str(item.get("excerpt") or ""),
            str(item.get("theme") or ""),
        ])
    return " ".join(parts).lower()


def classify_valuation_family(company, override: str | None = None) -> dict[str, Any]:
    if override and override != "AUTO":
        return {
            "family": override,
            "label": VALUATION_FAMILIES.get(override, override),
            "basis": "USER_OVERRIDE",
            "reason": "Valuation family explicitly selected by the operator.",
        }

    text = _text_blob(company)
    financial_terms = [
        "net interest margin", "npa", "gross npa", "net npa", "deposits", "advances",
        "credit cost", "capital adequacy", "loan book", "banking", "bank ", "nbfc",
        "insurance premium", "solvency ratio",
    ]
    cyclical_terms = [
        "commodity", "steel", "aluminium", "aluminum", "copper", "zinc", "mining",
        "iron ore", "crude oil", "refinery", "sugar cycle", "shipping rates", "freight cycle",
    ]
    utility_terms = [
        "regulated tariff", "power transmission", "electricity distribution", "utility",
        "generation capacity", "power generation", "toll road", "regulated return",
    ]

    if any(term in text for term in financial_terms):
        family = "FINANCIAL_PB"
        reason = "Research evidence contains banking/financial-business terminology; P/B with sustainable ROE is more appropriate than a generic industrial multiple."
    elif any(term in text for term in cyclical_terms):
        family = "CYCLICAL_NORMALIZED"
        reason = "Research evidence indicates a cyclical/commodity earnings profile; normalized earnings are preferred over latest-period earnings."
    elif any(term in text for term in utility_terms):
        family = "UTILITY_ASSET_HEAVY"
        reason = "Research evidence indicates a regulated/utility/asset-heavy profile; a conservative normalized earnings multiple is used in v1."
    else:
        family = "GENERAL_EARNINGS"
        reason = "No strong financial/cyclical/regulated-business signal was found; use the general normalized-earnings framework."

    return {
        "family": family,
        "label": VALUATION_FAMILIES[family],
        "basis": "HEURISTIC_FROM_RESEARCH_EVIDENCE",
        "reason": reason,
    }


def _latest(company, key: str):
    assessment = company.financial_assessment or {}
    if _num(assessment.get(key)) is not None:
        return _num(assessment.get(key))
    history = company.financial_history or []
    for row in reversed(history):
        if _num(row.get(key)) is not None:
            return _num(row.get(key))
    return None


def _series(company, key: str) -> list[float]:
    values = []
    for row in company.financial_history or []:
        value = _num(row.get(key))
        if value is not None:
            values.append(value)
    return values


def _research_confidence(company) -> dict:
    return dict((company.research_dossier or {}).get("evidence_confidence") or {})


def _gate(company) -> dict:
    confidence = _research_confidence(company)
    if not confidence:
        return {
            "allowed": False,
            "reason": "Research Confidence has not been assessed for this company yet.",
            "state": "NOT_ASSESSED",
        }
    allowed = confidence.get("valuation_context") == "READY_FOR_VALUATION_CONTEXT"
    return {
        "allowed": bool(allowed),
        "reason": (
            "Research-quality gate passed."
            if allowed
            else "Research-quality gate has not passed; resolve critical evidence gaps before relying on valuation."
        ),
        "state": confidence.get("research_confidence_state"),
        "score": confidence.get("research_confidence_score"),
        "critical_gaps": confidence.get("critical_gaps") or [],
    }


def _normalized_eps(company, periods: int = 3) -> dict:
    eps = _positive(_series(company, "eps"))
    latest = _num((company.financial_assessment or {}).get("eps_latest")) or (eps[-1] if eps else None)
    trailing = eps[-periods:] if eps else []
    normalized = median(trailing) if trailing else latest
    return {
        "latest_eps": round(latest, 2) if latest is not None else None,
        "normalized_eps": round(normalized, 2) if normalized is not None else None,
        "periods_used": len(trailing),
        "method": f"median of last {len(trailing)} positive annual EPS observations" if trailing else "latest available EPS",
    }


def _multiple_anchor(company, *, allow_current_fallback: bool = True) -> dict:
    a = company.financial_assessment or {}
    historical = _num(a.get("five_year_pe"))
    industry = _num(a.get("industry_pe"))
    current = _num(a.get("pe"))
    anchors = []
    if historical and 0 < historical < 100:
        anchors.append(("5-year P/E", historical))
    if industry and 0 < industry < 100:
        anchors.append(("industry P/E", industry))

    if anchors:
        base = median([x[1] for x in anchors])
        quality = "EVIDENCE_ANCHORED"
    elif allow_current_fallback and current and 0 < current < 100:
        base = current
        anchors.append(("current P/E fallback", current))
        quality = "CURRENT_MARKET_FALLBACK"
    else:
        return {"base_multiple": None, "anchors": [], "quality": "INSUFFICIENT"}

    return {
        "base_multiple": round(base, 2),
        "anchors": [{"name": n, "value": round(v, 2)} for n, v in anchors],
        "quality": quality,
    }


def _scenario_multiple(base: float, *, bear_factor=0.75, bull_factor=1.25):
    return {
        "bear": round(max(3.0, base * bear_factor), 2),
        "base": round(base, 2),
        "bull": round(min(80.0, base * bull_factor), 2),
    }


def _price_scenarios_from_eps(eps: float, multiples: dict[str, float]):
    return {name: round(max(0.0, eps * multiple), 2) for name, multiple in multiples.items()}


def _financial_pb_valuation(company, assumptions: dict | None = None) -> dict:
    assumptions = assumptions or {}
    a = company.financial_assessment or {}
    book = _num(a.get("book_value")) or _latest(company, "book_value")
    roe = _num(a.get("roe_latest")) or _num(a.get("roe")) or _latest(company, "roe")
    if book is None or book <= 0 or roe is None:
        return {"ok": False, "reason": "Book value and sustainable ROE are required for the financial-business P/B framework."}

    # Justified P/B = (ROE - g) / (cost of equity - g). Inputs are explicit and editable.
    roe_dec = roe / 100.0 if roe > 1 else roe
    scenarios = {
        "bear": {
            "growth": _num(assumptions.get("bear_growth"), 0.03),
            "cost_of_equity": _num(assumptions.get("bear_cost_of_equity"), 0.14),
            "roe": max(0.01, roe_dec * _num(assumptions.get("bear_roe_factor"), 0.85)),
        },
        "base": {
            "growth": _num(assumptions.get("base_growth"), 0.05),
            "cost_of_equity": _num(assumptions.get("base_cost_of_equity"), 0.12),
            "roe": roe_dec,
        },
        "bull": {
            "growth": _num(assumptions.get("bull_growth"), 0.07),
            "cost_of_equity": _num(assumptions.get("bull_cost_of_equity"), 0.11),
            "roe": roe_dec * _num(assumptions.get("bull_roe_factor"), 1.08),
        },
    }
    values = {}
    for name, s in scenarios.items():
        if s["cost_of_equity"] <= s["growth"] or s["roe"] <= s["growth"]:
            return {"ok": False, "reason": f"Invalid {name} P/B assumptions: cost of equity and ROE must exceed long-term growth."}
        justified_pb = (s["roe"] - s["growth"]) / (s["cost_of_equity"] - s["growth"])
        justified_pb = max(0.3, min(8.0, justified_pb))
        values[name] = {
            "fair_pb": round(justified_pb, 2),
            "fair_value": round(book * justified_pb, 2),
            "growth": round(s["growth"] * 100, 1),
            "cost_of_equity": round(s["cost_of_equity"] * 100, 1),
            "sustainable_roe": round(s["roe"] * 100, 1),
        }
    return {
        "ok": True,
        "method": "JUSTIFIED_PRICE_TO_BOOK",
        "book_value": round(book, 2),
        "observed_roe": round(roe_dec * 100, 1),
        "scenarios": values,
        "assumption_note": "P/B scenarios use an explicit Gordon-style justified P/B relationship. They are scenario assumptions, not forecasts.",
    }


def _earnings_valuation(company, family: str, assumptions: dict | None = None) -> dict:
    assumptions = assumptions or {}
    eps_info = _normalized_eps(company, periods=5 if family == "CYCLICAL_NORMALIZED" else 3)
    eps = eps_info.get("normalized_eps")
    if eps is None or eps <= 0:
        return {"ok": False, "reason": "Positive normalized EPS is required for this earnings-multiple framework."}

    anchor = _multiple_anchor(company, allow_current_fallback=True)
    base = _num(assumptions.get("base_multiple")) or anchor.get("base_multiple")
    if base is None:
        return {"ok": False, "reason": "No defensible historical/industry/current P/E anchor is available. Enter an explicit scenario multiple to continue."}

    if family == "CYCLICAL_NORMALIZED":
        default_bear, default_bull = 0.65, 1.15
    elif family == "UTILITY_ASSET_HEAVY":
        default_bear, default_bull = 0.80, 1.15
    else:
        default_bear, default_bull = 0.75, 1.25

    multiples = {
        "bear": _num(assumptions.get("bear_multiple")) or max(3.0, base * default_bear),
        "base": base,
        "bull": _num(assumptions.get("bull_multiple")) or min(80.0, base * default_bull),
    }
    multiples = {k: round(v, 2) for k, v in multiples.items()}
    fair_values = _price_scenarios_from_eps(eps, multiples)
    return {
        "ok": True,
        "method": "NORMALIZED_EARNINGS_MULTIPLE",
        "normalized_eps": eps,
        "eps_basis": eps_info,
        "multiple_anchor": anchor,
        "scenario_multiples": multiples,
        "fair_values": fair_values,
        "assumption_note": (
            "Cyclical earnings use a longer normalized EPS history and a wider downside haircut."
            if family == "CYCLICAL_NORMALIZED"
            else "Scenario multiples are anchored to available historical/industry context; current P/E is used only as a labeled fallback when stronger anchors are absent."
        ),
    }


def _upside(current_price: float | None, fair_value: float | None):
    if current_price is None or current_price <= 0 or fair_value is None:
        return None
    return round((fair_value / current_price - 1.0) * 100.0, 1)


def value_company(company, *, family_override: str | None = None, assumptions: dict | None = None, allow_gate_override: bool = False) -> dict:
    gate = _gate(company)
    current_price = _num((company.financial_assessment or {}).get("price")) or _latest(company, "price")
    family_info = classify_valuation_family(company, family_override)

    result = {
        "company": company.company,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "current_price": round(current_price, 2) if current_price is not None else None,
        "research_gate": gate,
        "valuation_family": family_info,
        "status": "BLOCKED",
        "method": None,
        "scenarios": {},
        "warnings": [],
        "assumptions": assumptions or {},
    }

    if not gate.get("allowed") and not allow_gate_override:
        result["warnings"].append("Valuation blocked because the Research Confidence gate has not passed.")
        return result
    if not gate.get("allowed") and allow_gate_override:
        result["warnings"].append("Operator override: valuation is being shown despite an incomplete Research Confidence gate.")
    if current_price is None or current_price <= 0:
        result["warnings"].append("Current market price is missing; upside/downside cannot be calculated.")

    family = family_info["family"]
    if family == "FINANCIAL_PB":
        core = _financial_pb_valuation(company, assumptions)
        if core.get("ok"):
            scenarios = {
                name: {
                    **payload,
                    "upside_downside_pct": _upside(current_price, payload.get("fair_value")),
                }
                for name, payload in core["scenarios"].items()
            }
        else:
            scenarios = {}
    elif family in {"GENERAL_EARNINGS", "CYCLICAL_NORMALIZED", "UTILITY_ASSET_HEAVY"}:
        core = _earnings_valuation(company, family, assumptions)
        if core.get("ok"):
            scenarios = {
                name: {
                    "multiple": core["scenario_multiples"][name],
                    "fair_value": fair,
                    "upside_downside_pct": _upside(current_price, fair),
                }
                for name, fair in core["fair_values"].items()
            }
        else:
            scenarios = {}
    else:
        core = {"ok": False, "reason": "No supported valuation family was selected."}
        scenarios = {}

    if not core.get("ok"):
        result["warnings"].append(core.get("reason", "Insufficient valuation inputs."))
        return result

    result.update({
        "status": "VALUED",
        "method": core.get("method"),
        "scenarios": scenarios,
        "valuation_inputs": {k: v for k, v in core.items() if k not in {"ok", "scenarios", "fair_values"}},
    })

    fair_values = [s.get("fair_value") for s in scenarios.values() if _num(s.get("fair_value")) is not None]
    if fair_values:
        result["valuation_range"] = {"low": round(min(fair_values), 2), "high": round(max(fair_values), 2)}
    if (core.get("multiple_anchor") or {}).get("quality") == "CURRENT_MARKET_FALLBACK":
        result["warnings"].append("No historical/industry multiple was available; current P/E is being used as a labeled relative-value fallback, so the output is weaker than a benchmark-anchored valuation.")
    result["disclaimer"] = "Valuation scenarios are assumption-driven research outputs, not target-price predictions or investment recommendations."
    return result


def value_run(run, *, overrides: dict[str, dict] | None = None) -> list[dict]:
    overrides = overrides or {}
    out = []
    states = {"VALUED": 0, "BLOCKED": 0}
    for company in run.companies.values():
        if not company.financial_assessment:
            continue
        config = overrides.get(company.company, {}) or {}
        result = value_company(
            company,
            family_override=config.get("family_override"),
            assumptions=config.get("assumptions"),
            allow_gate_override=bool(config.get("allow_gate_override", False)),
        )
        company.valuation = result
        out.append(result)
        states[result["status"]] = states.get(result["status"], 0) + 1
    run.stage_summary["valuation"] = {"companies": len(out), "states": states}
    run.log(
        "VALUATION",
        "VALUATION_COMPLETE",
        f"Valuation context assessed for {len(out)} companies: {states}.",
        details=run.stage_summary["valuation"],
    )
    return sorted(out, key=lambda x: (x.get("status") != "VALUED", x.get("company", "").casefold()))
