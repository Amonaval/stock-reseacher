import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from research_models import CompanyResearch, ResearchRun
from valuation_intelligence import classify_valuation_family, value_company


def _ready(company):
    company.research_dossier = {
        "evidence_confidence": {
            "research_confidence_state": "HIGH_RESEARCH_CONFIDENCE",
            "research_confidence_score": 86,
            "valuation_context": "READY_FOR_VALUATION_CONTEXT",
            "critical_gaps": [],
        }
    }
    return company


def test_valuation_is_blocked_without_research_confidence_gate():
    company = CompanyResearch(company="Example Ltd")
    company.financial_assessment = {"price": 100, "pe": 20, "eps_latest": 5}
    result = value_company(company)
    assert result["status"] == "BLOCKED"
    assert "Research Confidence" in result["warnings"][0]


def test_general_earnings_uses_normalized_eps_and_benchmark_anchor():
    company = _ready(CompanyResearch(company="Quality Manufacturing Ltd"))
    company.financial_history = [
        {"year": "Mar 2024", "eps": 4},
        {"year": "Mar 2025", "eps": 5},
        {"year": "Mar 2026", "eps": 6},
    ]
    company.financial_assessment = {
        "price": 100,
        "pe": 20,
        "five_year_pe": 20,
        "industry_pe": 16,
        "eps_latest": 6,
    }
    result = value_company(company)
    assert result["status"] == "VALUED"
    assert result["method"] == "NORMALIZED_EARNINGS_MULTIPLE"
    assert result["valuation_inputs"]["eps_basis"]["normalized_eps"] == 5
    assert result["valuation_inputs"]["multiple_anchor"]["base_multiple"] == 18
    assert result["scenarios"]["base"]["fair_value"] == 90
    assert result["scenarios"]["base"]["upside_downside_pct"] == -10.0


def test_cyclical_uses_longer_normalized_earnings_history():
    company = _ready(CompanyResearch(company="Example Steel Ltd"))
    company.evidence = [{"claim": "Steel commodity cycle remains volatile", "theme": "risk"}]
    company.financial_history = [
        {"year": "Mar 2022", "eps": 2},
        {"year": "Mar 2023", "eps": 9},
        {"year": "Mar 2024", "eps": 3},
        {"year": "Mar 2025", "eps": 11},
        {"year": "Mar 2026", "eps": 5},
    ]
    company.financial_assessment = {"price": 70, "industry_pe": 10, "pe": 14, "eps_latest": 5}
    family = classify_valuation_family(company)
    result = value_company(company)
    assert family["family"] == "CYCLICAL_NORMALIZED"
    assert result["status"] == "VALUED"
    assert result["valuation_inputs"]["eps_basis"]["periods_used"] == 5
    assert result["valuation_inputs"]["eps_basis"]["normalized_eps"] == 5
    assert result["scenarios"]["bear"]["multiple"] == 6.5


def test_bank_family_uses_justified_price_to_book():
    company = _ready(CompanyResearch(company="Example Bank"))
    company.financial_assessment = {
        "price": 180,
        "book_value": 100,
        "roe_latest": 15,
        "data_confidence": 90,
    }
    family = classify_valuation_family(company)
    result = value_company(company)
    assert family["family"] == "FINANCIAL_PB"
    assert result["status"] == "VALUED"
    assert result["method"] == "JUSTIFIED_PRICE_TO_BOOK"
    assert result["scenarios"]["base"]["fair_pb"] > 1
    assert result["scenarios"]["base"]["fair_value"] > 100


def test_insurer_is_not_forced_into_generic_bank_or_pe_model():
    company = _ready(CompanyResearch(company="Example Life Insurance"))
    company.financial_assessment = {"price": 500, "pe": 45, "book_value": 90, "roe_latest": 14}
    company.evidence = [{"claim": "Value of new business grew", "theme": "growth"}]
    family = classify_valuation_family(company)
    result = value_company(company)
    assert family["family"] == "INSURANCE_EMBEDDED_VALUE"
    assert result["status"] == "BLOCKED"
    assert any("embedded value" in x.lower() for x in result["warnings"])


def test_operator_can_explore_with_gate_override_but_warning_remains():
    company = CompanyResearch(company="Exploratory Ltd")
    company.financial_history = [
        {"year": "Mar 2024", "eps": 4},
        {"year": "Mar 2025", "eps": 5},
        {"year": "Mar 2026", "eps": 6},
    ]
    company.financial_assessment = {"price": 100, "industry_pe": 18, "eps_latest": 6}
    result = value_company(company, allow_gate_override=True)
    assert result["status"] == "VALUED"
    assert any("Operator override" in x for x in result["warnings"])


def test_old_run_without_valuation_field_remains_backward_compatible():
    old = {
        "run_id": "run-old",
        "created_at": "2026-01-01T00:00:00+00:00",
        "companies": {
            "example ltd": {
                "company": "Example Ltd",
                "financial_assessment": {"decision": "ADVANCE"},
            }
        },
    }
    run = ResearchRun.from_dict(old)
    assert run.companies["example ltd"].valuation == {}
