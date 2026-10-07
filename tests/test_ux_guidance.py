import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from research_models import ResearchRun
from ux_guidance import workflow_steps, next_action


def test_new_run_points_to_methodology():
    run = ResearchRun.create()
    steps = workflow_steps(run, {})
    step, text = next_action(steps)
    assert step.number == 1
    assert "Connect Screener" in text


def test_strategies_ready_points_to_screening():
    run = ResearchRun.create()
    run.strategies = [{"id": "S1", "name": "Quality", "hard_query": "ROE > 15"}]
    steps = workflow_steps(run, {"strategies": run.strategies})
    step, _ = next_action(steps)
    assert step.number == 2


def test_candidate_universe_points_to_financials():
    run = ResearchRun.create()
    run.strategies = [{"id": "S1", "name": "Quality", "hard_query": "ROE > 15"}]
    state = {
        "strategies": run.strategies,
        "candidate_universe": [{"company": "Example Ltd"}],
    }
    steps = workflow_steps(run, state)
    step, _ = next_action(steps)
    assert step.number == 3


def test_researched_company_points_to_deep_research():
    run = ResearchRun.create()
    run.strategies = [{"id": "S1", "name": "Quality", "hard_query": "ROE > 15"}]
    company = run.ensure_company("Example Ltd")
    company.financial_assessment = {"decision": "ADVANCE"}
    company.research_state = "RESEARCH_INCOMPLETE"
    company.evidence = [{"evidence_id": "E1", "theme": "risk"}]
    state = {
        "strategies": run.strategies,
        "candidate_universe": [{"company": "Example Ltd"}],
        "financial_assessments": [{"company": "Example Ltd", "decision": "ADVANCE"}],
    }
    steps = workflow_steps(run, state)
    step, _ = next_action(steps)
    assert step.number == 5
