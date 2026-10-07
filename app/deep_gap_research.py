from __future__ import annotations

from collections import Counter

from company_research_engine import run_company_research_engine, build_investor_dossier
from research_agent import build_company_research_memory


def _key(value):
    return " ".join(str(value or "").split()).casefold()


def _merge_unique(existing: list[dict], new: list[dict], id_key: str) -> list[dict]:
    out = []
    seen = set()
    for item in list(existing or []) + list(new or []):
        key = item.get(id_key) or item.get("url") or repr(sorted(item.items()))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def resolve_research_gaps(run, cdp_url: str, *, company_names: list[str], use_llm: bool = False, progress=None) -> dict:
    """Spend a deeper research pass specifically on unresolved evidence gaps.

    This is the missing bridge between a research-depth plan and Bull/Bear analysis.
    It does not make an investment decision. It broadens source acquisition, preserves
    prior evidence, rebuilds dossiers, and reports which companies became evidence-ready.
    """
    requested = {_key(x) for x in company_names or []}
    targets = [c for c in run.companies.values() if _key(c.company) in requested]
    before = {
        _key(c.company): {
            "state": c.research_state,
            "documents": list(c.documents or []),
            "evidence": list(c.evidence or []),
            "questions": list(c.research_questions or []),
        }
        for c in targets
    }

    run.log(
        "DEEP_RESEARCH",
        "GAP_RESOLUTION_START",
        f"Starting targeted evidence-gap research for {len(targets)} companies.",
        details={"companies": [c.company for c in targets], "use_llm": use_llm},
    )

    # Broaden the acquisition pass compared with the initial company-research stage.
    run_company_research_engine(
        run,
        cdp_url,
        company_names=[c.company for c in targets],
        use_llm=use_llm,
        max_sources_per_type=4,
        min_source_score=35,
        progress=progress,
    )

    # Preserve accumulated research memory instead of replacing it on retries.
    all_documents = []
    all_evidence = []
    for company in targets:
        old = before[_key(company.company)]
        company.documents = _merge_unique(old["documents"], company.documents, "document_id")
        company.evidence = _merge_unique(old["evidence"], company.evidence, "evidence_id")
        all_documents.extend(company.documents)
        all_evidence.extend(company.evidence)

    financial_context = [c.financial_assessment for c in targets]
    memories = build_company_research_memory(all_documents, all_evidence, financial_ranked=financial_context)
    memory_map = {_key(m.get("company")): m for m in memories}

    transitions = []
    for company in targets:
        old = before[_key(company.company)]
        memory = memory_map.get(_key(company.company), {})
        dossier = build_investor_dossier(company, memory)
        company.research_dossier = dossier
        company.research_state = dossier["research_state"]
        company.research_questions = dossier["open_questions"]

        transition = {
            "company": company.company,
            "before_state": old["state"] or "NOT_RESEARCHED",
            "after_state": company.research_state,
            "documents_before": len(old["documents"]),
            "documents_after": len(company.documents),
            "evidence_before": len(old["evidence"]),
            "evidence_after": len(company.evidence),
            "questions_before": len(old["questions"]),
            "questions_after": len(company.research_questions),
            "mission_coverage": dossier.get("mission_coverage", 0),
            "missing_document_types": dossier.get("missing_document_types", []),
        }
        transitions.append(transition)
        run.log(
            "DEEP_RESEARCH",
            "GAP_RESOLUTION_COMPANY",
            f"{transition['before_state']} → {transition['after_state']}; documents {transition['documents_before']}→{transition['documents_after']}, evidence {transition['evidence_before']}→{transition['evidence_after']}.",
            company=company.company,
            status="INFO" if company.research_state == "EVIDENCE_READY" else "WARN",
            details=transition,
        )

    states = Counter(x["after_state"] for x in transitions)
    result = {
        "companies": len(transitions),
        "states": dict(states),
        "transitions": transitions,
        "evidence_ready": [x["company"] for x in transitions if x["after_state"] == "EVIDENCE_READY"],
        "still_incomplete": [x["company"] for x in transitions if x["after_state"] != "EVIDENCE_READY"],
    }
    run.stage_summary["deep_gap_research"] = result
    run.log(
        "DEEP_RESEARCH",
        "GAP_RESOLUTION_COMPLETE",
        f"Deep evidence-gap pass complete: {dict(states)}.",
        status="WARN" if result["still_incomplete"] else "INFO",
        details=result,
    )
    run.status = "DEEP_RESEARCH_COMPLETE"
    return result
