from app.research_depth_planner import plan_research_depth
from app.research_models import ResearchRun
from app.research_analysis_orchestrator import build_research_memories


def test_source_gap_does_not_reach_adversarial():
    memories = [{
        "company": "Gap Ltd",
        "documents": 0,
        "document_coverage": 0,
        "evidence_quality": 0,
        "research_readiness": 0,
        "research_state": "SOURCE_GAP",
        "mission_coverage": 0,
        "open_questions": [{"question": "Acquire annual report"}],
        "missing_document_types": ["annual_report"],
        "risk_items": 0,
        "management_claims": 0,
        "financial_context": {"decision": "ADVANCE"},
    }]
    plan = plan_research_depth(memories)
    assert plan["rows"][0]["stage"] == "SOURCE_GAP"


def test_evidence_ready_company_can_reach_adversarial():
    memories = [{
        "company": "Ready Ltd",
        "documents": 6,
        "document_coverage": 100,
        "evidence_quality": 82,
        "research_readiness": 84,
        "research_state": "EVIDENCE_READY",
        "mission_coverage": 100,
        "open_questions": [],
        "missing_document_types": [],
        "risk_items": 4,
        "management_claims": 1,
        "financial_context": {"decision": "ADVANCE"},
    }]
    plan = plan_research_depth(memories)
    assert plan["rows"][0]["stage"] == "ADVERSARIAL"
    assert plan["budget_utilization"]["ADVERSARIAL"]["admitted"] == 1


def test_budget_queues_instead_of_dropping_company():
    memories = []
    for i in range(3):
        memories.append({
            "company": f"Ready {i}",
            "documents": 6,
            "document_coverage": 100,
            "evidence_quality": 82 - i,
            "research_readiness": 84 - i,
            "research_state": "EVIDENCE_READY",
            "mission_coverage": 100,
            "open_questions": [],
            "missing_document_types": [],
            "risk_items": 2,
            "management_claims": 0,
            "financial_context": {"decision": "ADVANCE"},
        })
    plan = plan_research_depth(memories, {"STRUCTURED": 10, "TARGETED": 10, "DEEP": 10, "ADVERSARIAL": 1})
    stages = [r["stage"] for r in plan["rows"]]
    assert stages.count("ADVERSARIAL") == 1
    assert stages.count("RESEARCH_QUEUE") == 2
    assert len(plan["rows"]) == 3


def test_persistent_company_dossier_rebuilds_planner_memory():
    run = ResearchRun.create()
    company = run.ensure_company("Persistent Ltd", "https://www.screener.in/company/123/")
    company.financial_assessment = {"decision": "ADVANCE"}
    company.research_state = "EVIDENCE_READY"
    company.research_dossier = {
        "mission_coverage": 86,
        "evidence_quality": 78,
        "research_readiness": 80,
        "missing_document_types": [],
    }
    company.documents = [
        {"doc_type": "annual_report"},
        {"doc_type": "quarterly_result"},
        {"doc_type": "investor_presentation"},
        {"doc_type": "earnings_call"},
        {"doc_type": "exchange_filing"},
        {"doc_type": "credit_rating"},
    ]
    company.evidence = [
        {"theme": "risk", "kind": "risk", "evidence_id": "E1"},
        {"theme": "growth", "kind": "source_excerpt", "evidence_id": "E2"},
    ]
    memories = build_research_memories(run)
    assert memories[0]["company"] == "Persistent Ltd"
    assert memories[0]["document_coverage"] == 100
    assert memories[0]["mission_coverage"] == 86
    assert memories[0]["risk_items"] == 1
