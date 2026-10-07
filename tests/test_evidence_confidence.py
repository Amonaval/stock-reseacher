import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from evidence_confidence import assess_evidence_confidence
from research_models import CompanyResearch


def test_empty_research_is_low_confidence():
    company = CompanyResearch(company="Empty Ltd")
    result = assess_evidence_confidence(company, now=datetime(2026, 10, 7, tzinfo=timezone.utc))
    assert result["research_confidence_state"] == "LOW_RESEARCH_CONFIDENCE"
    assert result["valuation_context"] == "MORE_RESEARCH_NEEDED"
    assert result["critical_gaps"]


def test_good_primary_and_recent_evidence_can_be_high_confidence():
    company = CompanyResearch(company="Well Researched Ltd")
    company.financial_assessment = {"data_confidence": 90}
    company.documents = [
        {"document_id": "D1", "doc_type": "annual_report", "document_date": "2026-03-31", "source_score": 98},
        {"document_id": "D2", "doc_type": "quarterly_result", "document_date": "2026-09-30", "source_score": 98},
        {"document_id": "D3", "doc_type": "exchange_filing", "document_date": "2026-09-15", "source_score": 100},
    ]
    themes = ["business_model", "growth", "cash_flow", "management", "governance", "risk", "catalyst"]
    evidence = []
    i = 0
    # Two independent documents per theme creates explicit theme-level triangulation.
    for theme in themes:
        for doc_id in ("D1", "D2"):
            i += 1
            evidence.append({
                "evidence_id": f"E{i}",
                "document_id": doc_id,
                "document_title": doc_id,
                "page": i,
                "theme": theme,
                "kind": "RISK" if theme in {"risk", "governance"} else "FACT",
                "claim": f"Supported {theme} finding",
                "excerpt": f"Source-backed {theme} evidence",
            })
    # Add risk from a third document to strengthen downside-source diversity.
    evidence.append({
        "evidence_id": "E-risk-3", "document_id": "D3", "document_title": "D3", "page": 1,
        "theme": "risk", "kind": "RISK", "claim": "Additional downside evidence", "excerpt": "Risk disclosure",
    })
    company.evidence = evidence
    company.research_dossier = {"mission_coverage": 100, "open_questions": []}
    company.research_questions = []
    company.contradiction_review = {"contradictions": [], "unresolved_questions": []}

    result = assess_evidence_confidence(company, now=datetime(2026, 10, 7, tzinfo=timezone.utc))
    assert result["research_confidence_state"] == "HIGH_RESEARCH_CONFIDENCE"
    assert result["valuation_context"] == "READY_FOR_VALUATION_CONTEXT"
    assert result["dimensions"]["cross_source_triangulation"] == 100
    assert result["dimensions"]["downside_evidence_coverage"] == 100
    assert result["critical_gaps"] == []


def test_bullish_sounding_but_one_sided_research_stays_low():
    company = CompanyResearch(company="Narrative Ltd")
    company.financial_assessment = {"data_confidence": 85}
    company.documents = [
        {"document_id": "D1", "doc_type": "annual_report", "document_date": "2026-03-31", "source_score": 95},
        {"document_id": "D2", "doc_type": "investor_presentation", "document_date": "2026-08-01", "source_score": 85},
    ]
    company.evidence = [
        {"evidence_id": "E1", "document_id": "D1", "page": 10, "theme": "growth", "kind": "FACT", "claim": "Revenue grew", "excerpt": "Growth evidence"},
        {"evidence_id": "E2", "document_id": "D2", "page": 5, "theme": "catalyst", "kind": "FACT", "claim": "Capacity expansion", "excerpt": "Expansion evidence"},
    ]
    company.research_dossier = {"mission_coverage": 28.6, "open_questions": [{"question": "Research risks"}]}
    company.research_questions = [{"question": "Research risks"}]

    result = assess_evidence_confidence(company, now=datetime(2026, 10, 7, tzinfo=timezone.utc))
    assert result["research_confidence_state"] == "LOW_RESEARCH_CONFIDENCE"
    assert result["valuation_context"] == "MORE_RESEARCH_NEEDED"
    assert any("downside" in gap.lower() for gap in result["critical_gaps"])
