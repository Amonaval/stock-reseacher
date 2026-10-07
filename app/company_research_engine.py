from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import time

from research_agent import extract_research_evidence, build_company_research_memory
from research_fetch import fetch_source
from screener_adapter import ScreenerAdapter
from source_discovery import BraveSearchProvider, discover_company_sources, infer_authority, domain_of
from source_policy import dedupe_and_rank, select_fetch_queue
from runtime_settings import get_screener_delay


RESEARCH_MISSIONS = {
    "business_model": {
        "label": "Business model & economics",
        "themes": {"business_model"},
        "why": "Understand how the company makes money, its products, customers and economic engine.",
    },
    "growth": {
        "label": "Growth drivers & durability",
        "themes": {"growth", "catalyst"},
        "why": "Separate durable growth drivers from temporary acceleration or management aspiration.",
    },
    "cash_conversion": {
        "label": "Cash conversion & working capital",
        "themes": {"cash_flow"},
        "why": "Check whether accounting profits convert into cash and whether working capital is deteriorating.",
    },
    "management": {
        "label": "Management & capital allocation",
        "themes": {"management"},
        "why": "Assess guidance, execution, capital allocation and management claims.",
    },
    "governance": {
        "label": "Governance & related-party risk",
        "themes": {"governance"},
        "why": "Surface governance, auditor, pledge, related-party and disclosure concerns.",
    },
    "risk": {
        "label": "Business / financial risks",
        "themes": {"risk"},
        "why": "Identify thesis breakers, concentration, leverage, regulation and execution risks.",
    },
    "catalyst": {
        "label": "Catalysts & milestones",
        "themes": {"catalyst"},
        "why": "Track concrete events that could change earnings or market perception.",
    },
}

# These are desirable source classes, not six mandatory checkboxes.
TARGET_DOCUMENT_TYPES = {
    "annual_report",
    "quarterly_result",
    "investor_presentation",
    "earnings_call",
    "exchange_filing",
    "credit_rating",
}
REQUIRED_DOCUMENT_TYPES = TARGET_DOCUMENT_TYPES  # backward-compatible public name
CORE_DOCUMENT_TYPES = {"annual_report"}
RECENT_DOCUMENT_TYPES = {"quarterly_result", "investor_presentation", "earnings_call", "exchange_filing"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _key(name):
    return " ".join(str(name or "").split()).casefold()


def _source_candidate(row: dict, company: str) -> dict:
    row = dict(row)
    row["company"] = company
    url = row.get("url", "")
    authority, source_class = infer_authority(url)
    row.setdefault("authority_score", authority)
    row.setdefault("source_class", source_class)
    row.setdefault("domain", domain_of(url))
    row.setdefault("provider", row.get("source") or "screener_company_page")
    return row


def _merge_unique(existing: list[dict], new: list[dict], id_key: str) -> list[dict]:
    out, seen = [], set()
    for item in list(existing or []) + list(new or []):
        marker = item.get(id_key) or item.get("url") or repr(sorted(item.items()))
        if marker in seen:
            continue
        seen.add(marker)
        out.append(item)
    return out


def _mission_summary(evidence: list[dict]) -> dict:
    by_theme = defaultdict(list)
    for item in evidence:
        by_theme[str(item.get("theme") or "other")].append(item)

    missions, covered = [], 0
    for mission_id, spec in RESEARCH_MISSIONS.items():
        items = []
        for theme in spec["themes"]:
            items.extend(by_theme.get(theme, []))
        if items:
            covered += 1
        missions.append({
            "mission_id": mission_id,
            "label": spec["label"],
            "why": spec["why"],
            "status": "COVERED" if items else "OPEN",
            "evidence_count": len(items),
            "findings": [
                {
                    "finding": e.get("claim") or e.get("excerpt"),
                    "kind": e.get("kind"),
                    "document": e.get("document_title"),
                    "page": e.get("page"),
                    "evidence_id": e.get("evidence_id"),
                    "confidence": e.get("confidence"),
                }
                for e in items[:6]
            ],
        })
    coverage = round(100 * covered / max(1, len(RESEARCH_MISSIONS)), 1)
    return {"missions": missions, "mission_coverage": coverage}


def build_investor_dossier(company_obj, memory: dict | None = None) -> dict:
    memory = memory or {}
    evidence = list(company_obj.evidence or [])
    mission = _mission_summary(evidence)
    doc_types = sorted({d.get("doc_type") for d in company_obj.documents if d.get("doc_type")})
    doc_set = set(doc_types)
    missing_docs = sorted(TARGET_DOCUMENT_TYPES - doc_set)
    has_core = bool(CORE_DOCUMENT_TYPES & doc_set)
    has_recent = bool(RECENT_DOCUMENT_TYPES & doc_set)
    critical_source_gaps = []
    if not has_core:
        critical_source_gaps.append("annual_report")
    if not has_recent:
        critical_source_gaps.append("recent_operating_or_exchange_source")

    risks = [e for e in evidence if e.get("theme") in {"risk", "governance"} or str(e.get("kind", "")).upper() in {"RISK", "GOVERNANCE"}]
    catalysts = [e for e in evidence if e.get("theme") == "catalyst" or str(e.get("kind", "")).upper() == "CATALYST"]
    management_claims = [e for e in evidence if str(e.get("kind", "")).upper() in {"MANAGEMENT_CLAIM", "OUTLOOK"}]

    if not company_obj.documents or not evidence:
        state = "SOURCE_GAP"
    elif critical_source_gaps or mission["mission_coverage"] < 70:
        state = "RESEARCH_INCOMPLETE"
    else:
        state = "EVIDENCE_READY"

    open_questions = []
    if not has_core:
        open_questions.append({
            "status": "OPEN",
            "question": "Acquire/verify annual report evidence.",
            "reason": "Core longitudinal source required before thesis challenge",
        })
    if not has_recent:
        open_questions.append({
            "status": "OPEN",
            "question": "Acquire at least one recent result, filing, presentation or earnings-call source.",
            "reason": "A current operating/disclosure source is required before thesis challenge",
        })
    for doc_type in missing_docs:
        if doc_type == "annual_report" or doc_type in RECENT_DOCUMENT_TYPES and not has_recent:
            continue
        open_questions.append({
            "status": "OPEN",
            "question": f"Consider acquiring {doc_type.replace('_', ' ')} evidence if material to the thesis.",
            "reason": "Supplementary source-class gap; visible but not an automatic blocker",
        })
    for m in mission["missions"]:
        if m["status"] == "OPEN":
            open_questions.append({
                "status": "OPEN",
                "question": f"Research {m['label'].lower()}.",
                "reason": m["why"],
            })

    return {
        "company": company_obj.company,
        "research_state": state,
        "documents": len(company_obj.documents),
        "document_types": doc_types,
        "missing_document_types": missing_docs,
        "critical_source_gaps": critical_source_gaps,
        "evidence_items": len(evidence),
        "evidence_quality": memory.get("evidence_quality", 0),
        "research_readiness": memory.get("research_readiness", 0),
        "mission_coverage": mission["mission_coverage"],
        "missions": mission["missions"],
        "risk_findings": risks[:12],
        "catalyst_findings": catalysts[:12],
        "management_claims": management_claims[:12],
        "open_questions": open_questions,
        "what_happens_next": (
            "Acquire a usable core/current evidence base before deeper research."
            if state == "SOURCE_GAP"
            else "Resolve critical source gaps and uncovered analyst missions."
            if state == "RESEARCH_INCOMPLETE"
            else "Evidence contract is sufficient; remaining supplementary gaps stay visible while deep/Bull-Bear gates assess readiness."
        ),
    }


def run_company_research_engine(
    run,
    cdp_url: str,
    *,
    company_names: list[str] | None = None,
    use_llm: bool = False,
    max_sources_per_type: int = 2,
    min_source_score: float = 45,
    progress=None,
):
    """Constitution-driven company research with persistent evidence accumulation."""
    requested = {_key(x) for x in company_names or []}
    eligible = []
    for company in run.companies.values():
        effective = (company.financial_assessment or {}).get(
            "effective_research_decision",
            (company.financial_assessment or {}).get("decision"),
        )
        if requested and _key(company.company) not in requested:
            continue
        if effective in {"ADVANCE", "WATCHLIST", "USER_INCLUDE"} or requested:
            eligible.append(company)

    run.status = "COLLECTING_RESEARCH"
    run.log(
        "RESEARCH", "ENGINE_START",
        f"Starting constitution-driven company research for {len(eligible)} companies.",
        details={"max_sources_per_type": max_sources_per_type, "min_source_score": min_source_score, "use_llm": use_llm},
    )

    discovered_by_company = defaultdict(list)
    delay = get_screener_delay()

    with ScreenerAdapter(cdp_url, delay=delay) as adapter:
        for i, company in enumerate(eligible, 1):
            if progress:
                progress(i, len(eligible), company.company, "discover_company_page")
            if not company.screener_url:
                attempt = {"at": _now(), "stage": "DISCOVERY", "provider": "screener", "status": "SKIPPED", "url": "", "doc_type": "", "message": "Exact company URL missing."}
                company.source_attempts.append(attempt)
                run.log("RESEARCH", "SOURCE_DISCOVERY_GAP", attempt["message"], company=company.company, status="WARN")
                continue
            try:
                rows = [_source_candidate(r, company.company) for r in adapter.discover_company_documents(company.screener_url, company.company)]
                discovered_by_company[_key(company.company)].extend(rows)
                company.source_attempts.append({
                    "at": _now(), "stage": "DISCOVERY", "provider": "screener_company_page", "status": "SUCCESS",
                    "url": company.screener_url, "doc_type": "", "message": f"Discovered {len(rows)} candidate research links.",
                })
                run.log("RESEARCH", "SOURCES_DISCOVERED", f"Found {len(rows)} research links on the company page.", company=company.company,
                        details={"source_types": sorted({x.get('doc_type') for x in rows if x.get('doc_type')})})
            except Exception as exc:
                company.source_attempts.append({
                    "at": _now(), "stage": "DISCOVERY", "provider": "screener_company_page", "status": "FAILED",
                    "url": company.screener_url, "doc_type": "", "message": str(exc),
                })
                run.log("RESEARCH", "SOURCE_DISCOVERY_FAILED", str(exc), company=company.company, status="WARN")
            time.sleep(max(0, delay))

    provider = BraveSearchProvider()
    if provider.configured():
        for i, company in enumerate(eligible, 1):
            if progress:
                progress(i, len(eligible), company.company, "discover_web")
            try:
                rows, errors = discover_company_sources(company.company, company.nse_symbol, provider=provider, max_per_query=4)
                rows = [_source_candidate(r, company.company) for r in rows]
                discovered_by_company[_key(company.company)].extend(rows)
                company.source_attempts.append({
                    "at": _now(), "stage": "DISCOVERY", "provider": provider.name, "status": "SUCCESS", "url": "", "doc_type": "",
                    "message": f"Discovered {len(rows)} broader web-source candidates.",
                })
                for err in errors:
                    company.source_attempts.append({
                        "at": _now(), "stage": "DISCOVERY", "provider": provider.name, "status": "FAILED", "url": "", "doc_type": "",
                        "message": err.get("error", str(err)),
                    })
            except Exception as exc:
                company.source_attempts.append({
                    "at": _now(), "stage": "DISCOVERY", "provider": provider.name, "status": "FAILED", "url": "", "doc_type": "", "message": str(exc),
                })

    new_documents, fetch_errors = [], []
    for i, company in enumerate(eligible, 1):
        key = _key(company.company)
        ranked = dedupe_and_rank(discovered_by_company.get(key, []))
        queue = select_fetch_queue(ranked, per_type=max_sources_per_type, min_score=min_source_score)
        already_fetched = {
            a.get("url") for a in company.source_attempts
            if a.get("stage") == "FETCH" and a.get("status") == "SUCCESS" and a.get("url")
        }
        queue = [x for x in queue if x.get("url") not in already_fetched]
        run.log(
            "RESEARCH", "SOURCE_QUEUE_BUILT",
            f"Selected {len(queue)} new high-value sources from {len(ranked)} discovered candidates.",
            company=company.company,
            details={"selected_types": dict(Counter(x.get("doc_type") for x in queue)), "top_sources": [{"type": x.get("doc_type"), "score": x.get("source_score"), "url": x.get("url")} for x in queue[:10]]},
        )
        if progress:
            progress(i, len(eligible), company.company, "fetch_sources")
        for source in queue:
            try:
                doc = fetch_source(source)
                doc["source_score"] = source.get("source_score")
                doc["source_class"] = source.get("source_class")
                doc["source_domain"] = source.get("domain")
                new_documents.append(doc)
                company.source_attempts.append({
                    "at": _now(), "stage": "FETCH", "provider": source.get("provider", "web"), "status": "SUCCESS",
                    "url": source.get("url"), "doc_type": source.get("doc_type"), "source_score": source.get("source_score"),
                    "message": f"Fetched {doc.get('page_count', 0)} pages / {doc.get('chunk_count', 0)} chunks.",
                })
            except Exception as exc:
                fetch_errors.append({"company": company.company, "url": source.get("url"), "doc_type": source.get("doc_type"), "error": str(exc)})
                company.source_attempts.append({
                    "at": _now(), "stage": "FETCH", "provider": source.get("provider", "web"), "status": "FAILED",
                    "url": source.get("url"), "doc_type": source.get("doc_type"), "source_score": source.get("source_score"), "message": str(exc),
                })

    new_evidence, extraction_errors = extract_research_evidence(new_documents, use_llm=use_llm)

    for company in eligible:
        key = _key(company.company)
        company.documents = _merge_unique(company.documents, [d for d in new_documents if _key(d.get("company")) == key], "document_id")
        company.evidence = _merge_unique(company.evidence, [e for e in new_evidence if _key(e.get("company")) == key], "evidence_id")

    all_documents = [d for c in eligible for d in company_or_empty(c.documents)]
    all_evidence = [e for c in eligible for e in company_or_empty(c.evidence)]
    financial_context = [c.financial_assessment for c in eligible]
    memories = build_company_research_memory(all_documents, all_evidence, financial_ranked=financial_context)
    memory_map = {_key(m.get("company")): m for m in memories}

    for company in eligible:
        memory = memory_map.get(_key(company.company), {})
        dossier = build_investor_dossier(company, memory)
        company.research_dossier = dossier
        company.research_state = dossier["research_state"]
        company.research_questions = dossier["open_questions"]
        status = "INFO" if dossier["research_state"] == "EVIDENCE_READY" else "WARN"
        run.log(
            "RESEARCH", "COMPANY_RESEARCH_CONCLUDED",
            f"{dossier['research_state']}: {dossier['documents']} documents, {dossier['evidence_items']} evidence items, mission coverage {dossier['mission_coverage']}%.",
            company=company.company, status=status,
            details={
                "document_types": dossier["document_types"], "missing_document_types": dossier["missing_document_types"],
                "critical_source_gaps": dossier["critical_source_gaps"], "evidence_quality": dossier["evidence_quality"],
                "research_readiness": dossier["research_readiness"], "what_happens_next": dossier["what_happens_next"],
            },
        )

    states = Counter(c.research_state or "NOT_RESEARCHED" for c in eligible)
    run.stage_summary["research"] = {
        "eligible_companies": len(eligible),
        "discovered_sources": sum(len(v) for v in discovered_by_company.values()),
        "documents": sum(len(c.documents) for c in eligible),
        "evidence_items": sum(len(c.evidence) for c in eligible),
        "fetch_errors": len(fetch_errors),
        "extraction_errors": len(extraction_errors),
        "states": dict(states),
        "constitution_complete": all(c.research_state == "EVIDENCE_READY" for c in eligible) if eligible else False,
    }
    run.log(
        "RESEARCH", "ENGINE_COMPLETE",
        f"Company research finished with states {dict(states)}. Source gaps remain visible and do not silently advance.",
        status="WARN" if states.get("SOURCE_GAP") or states.get("RESEARCH_INCOMPLETE") else "INFO",
        details=run.stage_summary["research"],
    )
    run.status = "RESEARCH_COMPLETE"
    return memories


def company_or_empty(items):
    return list(items or [])
