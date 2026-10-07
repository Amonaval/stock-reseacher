from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkflowStep:
    number: int
    key: str
    title: str
    short: str
    status: str
    detail: str


def _research_candidates(run):
    return [
        c for c in run.companies.values()
        if (c.financial_assessment or {}).get(
            "effective_research_decision",
            (c.financial_assessment or {}).get("decision"),
        ) in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"}
    ]


def workflow_steps(run, state: dict) -> list[WorkflowStep]:
    connection = state.get("connection") or {}
    strategies = state.get("strategies") or run.strategies
    universe = state.get("candidate_universe") or []
    assessments = state.get("financial_assessments") or []
    plan = state.get("research_plan") or {}
    adversarial = state.get("adversarial_results") or []

    candidates = _research_candidates(run)
    researched = [c for c in candidates if c.research_state not in {"", "NOT_RESEARCHED"} or c.evidence]
    evidence_ready = [c for c in researched if c.research_state == "EVIDENCE_READY"]

    s1_status = "DONE" if strategies else "IN_PROGRESS" if (connection.get("connected") or state.get("screen_queries")) else "NEXT"
    s2_status = "DONE" if universe else "NEXT" if strategies else "LOCKED"
    s3_status = "DONE" if assessments else "NEXT" if universe else "LOCKED"
    s4_status = "DONE" if researched else "NEXT" if candidates else "LOCKED"
    s5_status = "DONE" if plan else "NEXT" if researched else "LOCKED"
    s6_status = "DONE" if adversarial else "NEXT" if any(r.get("stage") == "ADVERSARIAL" for r in plan.get("rows", [])) else "LOCKED"

    return [
        WorkflowStep(1, "methodology", "Connect & prepare strategies", "Teach the app what to look for.", s1_status,
                     f"{len(strategies)} strategy profiles ready" if strategies else "Connect Screener or import historical screens, then analyze methodology."),
        WorkflowStep(2, "screening", "Screen the market", "Run enabled strategies and build one candidate list.", s2_status,
                     f"{len(universe)} unique candidates" if universe else "Run your approved/tuned strategies."),
        WorkflowStep(3, "financial", "Check financial quality", "Collect histories and decide which candidates deserve research.", s3_status,
                     f"{len(assessments)} companies assessed" if assessments else "Collect financial history automatically for the candidate list."),
        WorkflowStep(4, "company_research", "Research the business", "Read source material and make unknowns explicit.", s4_status,
                     f"{len(researched)}/{len(candidates)} approved companies researched; {len(evidence_ready)} evidence-ready" if candidates else "Research companies that passed or were manually approved after financial review."),
        WorkflowStep(5, "deep_research", "Allocate deeper research", "Spend more analyst effort only where evidence justifies it.", s5_status,
                     f"Plan ready: {plan.get('counts', {})}" if plan else "Create a transparent research-depth plan and review its budget."),
        WorkflowStep(6, "thesis_challenge", "Challenge the thesis", "Run independent Bull/Bear analysis on evidence-ready names.", s6_status,
                     f"{len(adversarial)} companies challenged" if adversarial else "Challenge only companies that pass the evidence gate."),
    ]


def next_action(steps: list[WorkflowStep]) -> tuple[WorkflowStep | None, str]:
    for step in steps:
        if step.status in {"NEXT", "IN_PROGRESS"}:
            actions = {
                "methodology": "Connect Screener (or import your historical screens), then analyze methodology and review the generated strategies.",
                "screening": "Review/tune strategies if needed, then run screening to build the candidate universe.",
                "financial": "Review the candidate list, then run automatic financial analysis.",
                "company_research": "Review financial decisions, then research the surviving/approved companies.",
                "deep_research": "Inspect research evidence, resolve obvious source gaps if needed, then create the deep-research allocation plan.",
                "thesis_challenge": "Open the Thesis Challenge workspace and run Bull/Bear analysis for evidence-ready companies.",
            }
            return step, actions[step.key]
    return None, "The current research run has completed all implemented stages. Review the results before starting another run or moving to the next product milestone."


def status_icon(status: str) -> str:
    return {
        "DONE": "✅",
        "IN_PROGRESS": "🟡",
        "NEXT": "👉",
        "LOCKED": "○",
    }.get(status, "○")
