from __future__ import annotations

from collections import defaultdict, Counter


def build_narrowing_story(funnel):
    stories = []
    stages = funnel.get("stages", {})
    for stage, payload in stages.items():
        for row in payload.get("advanced", []):
            stories.append({
                "company": row.get("company"),
                "stage": stage,
                "outcome": "ADVANCED",
                "why": row.get("decision_reason"),
                "priority_score": row.get("priority_score"),
                "financial_score": row.get("financial_score"),
                "research_score": row.get("research_score"),
                "evidence_quality": row.get("evidence_quality"),
                "uncertainty": row.get("uncertainty"),
            })
        for row in payload.get("held", []):
            stories.append({
                "company": row.get("company"),
                "stage": stage,
                "outcome": "HELD",
                "why": row.get("decision_reason"),
                "priority_score": row.get("priority_score"),
                "financial_score": row.get("financial_score"),
                "research_score": row.get("research_score"),
                "evidence_quality": row.get("evidence_quality"),
                "uncertainty": row.get("uncertainty"),
            })
    return stories


def company_journey(stories, company):
    return [x for x in stories if x.get("company") == company]


def stage_counts(funnel):
    rows = []
    for stage, payload in funnel.get("stages", {}).items():
        rows.append({
            "stage": stage,
            "budget": payload.get("budget"),
            "advanced": payload.get("advanced_count"),
            "held": payload.get("held_count"),
        })
    return rows
