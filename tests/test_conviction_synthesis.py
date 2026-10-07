import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from conviction_synthesis import synthesize_company, synthesize_run
from research_models import CompanyResearch, ResearchRun


def _base_company(name="Example Ltd"):
    company = CompanyResearch(company=name)
    company.financial_assessment = {
        "decision": "ADVANCE",
        "effective_research_decision": "ADVANCE",
        "data_confidence": 90,
        "financial_score": 72,
        "labels": {"growth": "Healthy", "cash_generation": "Healthy"},
    }
    company.research_dossier = {
        "evidence_confidence": {
            "research_confidence_state": "HIGH_RESEARCH_CONFIDENCE",
            "research_confidence_score": 86,
            "valuation_context": "READY_FOR_VALUATION_CONTEXT",
            "critical_gaps": [],
        }
    }
    company.adversarial_result = {
        "classification": {
            "thesis_status": "BULL_CASE_SURVIVES",
            "thesis_balance": 68,
            "fragility_score": 30,
            "adversarial_readiness": 84,
            "bull_strength": 75,
            "bear_strength": 42,
            "unresolved_questions": [],
            "fragility_flags": [],
        },
        "challenge": {"contradictions": [], "unresolved_questions": [], "fragility_flags": []},
    }
    company.bull_case = {
        "what_must_be_true": ["Capacity utilization must improve"],
        "invalidation_conditions": ["Margins structurally fall below the normalized range"],
    }
    company.bear_case = {
        "points": [{"point": "Customer concentration remains material"}],
    }
    company.valuation = {
        "status": "VALUED",
        "price_context": "CAPTURED_DURING_FINANCIAL_RESEARCH_NOT_LIVE",
        "method": "NORMALIZED_EARNINGS_MULTIPLE",
        "valuation_family": {"label": "General / quality business"},
        "scenarios": {
            "bear": {"upside_downside_pct": -15},
            "base": {"upside_downside_pct": 25},
            "bull": {"upside_downside_pct": 55},
        },
        "warnings": [],
    }
    return company


def test_high_priority_requires_surviving_bull_and_favorable_base_context():
    result = synthesize_company(_base_company())
    assert result["decision_state"] == "HIGH_PRIORITY_RESEARCH_CANDIDATE"
    assert result["decision_readiness"] == "READY_FOR_INVESTOR_REVIEW"
    assert result["dimensions"]["valuation"]["base_vs_captured_pct"] == 25
    assert result["what_must_be_true"]
    assert result["invalidation_conditions"]


def test_wide_bear_downside_blocks_high_priority_state():
    company = _base_company()
    company.valuation["scenarios"]["bear"]["upside_downside_pct"] = -45
    result = synthesize_company(company)
    assert result["decision_state"] == "POSITIVE_THESIS_WIDE_DOWNSIDE"
    assert result["decision_readiness"] == "READY_FOR_INVESTOR_REVIEW"


def test_bear_dominated_overrides_attractive_valuation_context():
    company = _base_company()
    company.adversarial_result["classification"]["thesis_status"] = "BEAR_CASE_DOMINATES"
    company.adversarial_result["classification"]["thesis_balance"] = 32
    result = synthesize_company(company)
    assert result["decision_state"] == "RISK_DOMINATED_RESEARCH_CASE"
    assert result["dimensions"]["valuation"]["base_vs_captured_pct"] == 25


def test_bear_dominated_remains_visible_even_without_valuation():
    company = _base_company()
    company.adversarial_result["classification"]["thesis_status"] = "BEAR_CASE_DOMINATES"
    company.valuation = {}
    result = synthesize_company(company)
    assert result["decision_state"] == "RISK_DOMINATED_RESEARCH_CASE"


def test_fragility_overrides_large_valuation_upside():
    company = _base_company()
    company.adversarial_result["classification"]["thesis_status"] = "FRAGILE"
    company.adversarial_result["classification"]["fragility_score"] = 82
    result = synthesize_company(company)
    assert result["decision_state"] == "FRAGILE_RESEARCH_CASE"


def test_positive_thesis_can_be_valuation_stretched():
    company = _base_company()
    company.valuation["scenarios"]["base"]["upside_downside_pct"] = -18
    result = synthesize_company(company)
    assert result["decision_state"] == "POSITIVE_THESIS_VALUATION_STRETCHED"


def test_contested_thesis_stays_contested():
    company = _base_company()
    company.adversarial_result["classification"]["thesis_status"] = "CONTESTED"
    company.adversarial_result["classification"]["thesis_balance"] = 51
    result = synthesize_company(company)
    assert result["decision_state"] == "CONTESTED_RESEARCH_CASE"


def test_research_gate_blocks_decision_synthesis_even_with_valuation():
    company = _base_company()
    confidence = company.research_dossier["evidence_confidence"]
    confidence["research_confidence_state"] = "LOW_RESEARCH_CONFIDENCE"
    confidence["valuation_context"] = "MORE_RESEARCH_NEEDED"
    confidence["critical_gaps"] = ["No current operating source"]
    result = synthesize_company(company)
    assert result["decision_state"] == "MORE_RESEARCH_NEEDED"
    assert result["decision_readiness"] == "NOT_READY_FOR_INVESTOR_REVIEW"


def test_unoverridden_financial_hold_is_explicit_conflict():
    company = _base_company()
    company.financial_assessment["decision"] = "HOLD"
    company.financial_assessment["effective_research_decision"] = "HOLD"
    result = synthesize_company(company)
    assert result["decision_state"] == "FINANCIAL_QUALITY_CONFLICT"


def test_synthesis_refresh_preserves_separate_investor_review():
    run = ResearchRun.create()
    company = _base_company()
    company.decision_synthesis = {
        "investor_review": {
            "stance": "WATCH_CLOSELY",
            "conviction": "MEDIUM",
            "notes": "Track execution",
        }
    }
    run.companies["example ltd"] = company
    rows = synthesize_run(run)
    assert rows[0]["investor_review"]["stance"] == "WATCH_CLOSELY"
    assert run.companies["example ltd"].decision_synthesis["investor_review"]["notes"] == "Track execution"


def test_old_run_without_decision_synthesis_is_backward_compatible():
    old = {
        "run_id": "run-old",
        "created_at": "2026-01-01T00:00:00+00:00",
        "companies": {
            "example ltd": {
                "company": "Example Ltd",
                "financial_assessment": {"decision": "ADVANCE"},
                "valuation": {},
            }
        },
    }
    run = ResearchRun.from_dict(old)
    assert run.companies["example ltd"].decision_synthesis == {}
