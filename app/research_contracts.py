from __future__ import annotations

"""Investor-facing completion contracts for research stages.

These checks intentionally validate usefulness rather than model quality. A stage can
execute successfully and still be incomplete if it fails to produce the information
an investor needs to understand what happened.
"""


CONTRACTS = {
    "FINANCIAL": {
        "required_per_company": [
            "company",
            "decision",
            "decision_reason",
            "data_confidence",
            "labels",
        ],
    },
    "COMPANY_RESEARCH": {
        "required_memory": [
            "company",
            "documents",
            "evidence_items",
            "research_readiness",
            "evidence_quality",
        ],
    },
    "ADVERSARIAL": {
        "required_result": [
            "company",
            "bull_bear",
            "challenge",
            "classification",
        ],
    },
}


def _missing_keys(item: dict, required: list[str]) -> list[str]:
    return [key for key in required if key not in item or item.get(key) is None]


def validate_financial_contract(assessments: list[dict]) -> list[str]:
    issues = []
    required = CONTRACTS["FINANCIAL"]["required_per_company"]
    for item in assessments:
        missing = _missing_keys(item, required)
        if missing:
            issues.append(f"{item.get('company', '<unknown>')}: missing {', '.join(missing)}")
    return issues


def validate_company_research_contract(memories: list[dict], expected_companies: list[str]) -> list[str]:
    """Return investor-facing completion gaps.

    A company with no research memory is explicitly a SOURCE_GAP, not a successful
    research completion.
    """
    issues = []
    required = CONTRACTS["COMPANY_RESEARCH"]["required_memory"]
    by_company = {str(x.get("company", "")).strip().casefold(): x for x in memories}
    for company in expected_companies:
        item = by_company.get(str(company).strip().casefold())
        if not item:
            issues.append(f"{company}: SOURCE_GAP — no usable company research memory was produced")
            continue
        missing = _missing_keys(item, required)
        if missing:
            issues.append(f"{company}: incomplete research memory; missing {', '.join(missing)}")
        if int(item.get("documents") or 0) == 0 or int(item.get("evidence_items") or 0) == 0:
            issues.append(f"{company}: SOURCE_GAP — research has no usable documents/evidence")
    return issues


def validate_adversarial_contract(results: list[dict]) -> list[str]:
    issues = []
    required = CONTRACTS["ADVERSARIAL"]["required_result"]
    for item in results:
        missing = _missing_keys(item, required)
        if missing:
            issues.append(f"{item.get('company', '<unknown>')}: missing {', '.join(missing)}")
    return issues


def contract_status(issues: list[str]) -> str:
    return "COMPLETE" if not issues else "INCOMPLETE"
