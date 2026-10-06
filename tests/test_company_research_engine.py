import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from company_research_engine import build_investor_dossier
from research_models import CompanyResearch, ResearchRun


class CompanyResearchEngineTests(unittest.TestCase):
    def test_source_gap_is_explicit(self):
        company = CompanyResearch(company="Example Ltd")
        dossier = build_investor_dossier(company, {})
        self.assertEqual(dossier["research_state"], "SOURCE_GAP")
        self.assertGreater(len(dossier["open_questions"]), 0)
        self.assertIn("Acquire", dossier["what_happens_next"])

    def test_evidence_ready_requires_document_and_mission_coverage(self):
        company = CompanyResearch(company="Example Ltd")
        doc_types = [
            "annual_report", "quarterly_result", "investor_presentation",
            "earnings_call", "exchange_filing", "credit_rating",
        ]
        company.documents = [
            {"doc_type": t, "title": t, "document_id": f"D{i}"}
            for i, t in enumerate(doc_types, 1)
        ]
        themes = [
            "business_model", "growth", "cash_flow", "management",
            "governance", "risk", "catalyst",
        ]
        company.evidence = [
            {
                "evidence_id": f"E{i}", "theme": theme, "kind": "FACT",
                "claim": f"Supported {theme} finding", "document_title": "Annual Report",
                "page": i, "confidence": "medium",
            }
            for i, theme in enumerate(themes, 1)
        ]
        dossier = build_investor_dossier(
            company,
            {"evidence_quality": 80, "research_readiness": 85},
        )
        self.assertEqual(dossier["research_state"], "EVIDENCE_READY")
        self.assertEqual(dossier["mission_coverage"], 100.0)
        self.assertEqual(dossier["open_questions"], [])

    def test_old_research_run_json_is_backward_compatible(self):
        old = {
            "run_id": "run-old",
            "created_at": "2026-01-01T00:00:00+00:00",
            "companies": {
                "example ltd": {
                    "company": "Example Ltd",
                    "screener_url": "https://www.screener.in/company/EXAMPLE/",
                    "financial_assessment": {"decision": "ADVANCE"},
                    "documents": [],
                    "evidence": [],
                    "research_questions": [],
                    "bull_case": {},
                    "bear_case": {},
                    "contradiction_review": {},
                    "decisions": [],
                }
            },
        }
        run = ResearchRun.from_dict(old)
        company = run.companies["example ltd"]
        self.assertEqual(company.research_state, "NOT_RESEARCHED")
        self.assertEqual(company.source_attempts, [])
        self.assertEqual(company.research_dossier, {})


if __name__ == "__main__":
    unittest.main()
