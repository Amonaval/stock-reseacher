from __future__ import annotations

from collections import defaultdict

from source_discovery import BraveSearchProvider, discover_company_sources
from source_policy import dedupe_and_rank, select_fetch_queue
from autonomous_fetch import fetch_discovered_source, optional_local_crawl_page
from research_agent import extract_research_evidence, build_company_research_memory
from orchestrator import build_orchestrator_state, narrow_for_next_stage


def discover_for_companies(companies, symbols=None, max_per_query=6, progress=None):
    symbols = symbols or {}
    provider = BraveSearchProvider()
    if not provider.configured():
        return [], [{"error": "BRAVE_SEARCH_API_KEY is not configured.", "provider": "brave"}]

    all_rows, all_errors = [], []
    for ci, company in enumerate(companies, 1):
        rows, errors = discover_company_sources(
            company,
            symbols.get(company, ""),
            provider=provider,
            max_per_query=max_per_query,
            progress=None,
        )
        all_rows.extend(rows)
        all_errors.extend(errors)
        if progress:
            progress(ci, len(companies), company)
    return dedupe_and_rank(all_rows), all_errors


def autonomous_fetch_sources(source_rows, per_type=2, min_score=58, progress=None):
    ranked = dedupe_and_rank(source_rows)

    # Optional local-research fallback: inspect a few high-quality HTML landing
    # pages for direct report/document links. The crawler itself enforces the
    # feature flag and robots policy and never recursively spiders.
    expanded = list(ranked)
    crawl_errors = []
    for row in ranked[:20]:
        try:
            links, reason = optional_local_crawl_page(row, max_links=12)
            expanded.extend(links)
            if reason and reason not in {"Local crawler disabled.", "Not an HTML page."}:
                crawl_errors.append({"company": row.get("company"), "url": row.get("url"), "error": reason})
        except Exception as exc:
            crawl_errors.append({"company": row.get("company"), "url": row.get("url"), "error": str(exc)})

    queue = select_fetch_queue(expanded, per_type=per_type, min_score=min_score)
    documents, errors = [], list(crawl_errors)
    for i, row in enumerate(queue, 1):
        try:
            documents.append(fetch_discovered_source(row))
        except Exception as exc:
            errors.append({"company": row.get("company"), "url": row.get("url"), "error": str(exc)})
        if progress:
            progress(i, len(queue), row)
    return documents, errors, queue


def refresh_research_state(documents, financial_ranked, source_catalog, use_llm=False, v5_budget=50):
    evidence, extraction_errors = extract_research_evidence(documents, use_llm=use_llm)
    memories = build_company_research_memory(documents, evidence, financial_ranked=financial_ranked)
    states, tasks = build_orchestrator_state(memories, source_catalog=source_catalog)
    decisions = narrow_for_next_stage(states, max_companies=v5_budget)
    return {
        "evidence": evidence,
        "memories": memories,
        "states": states,
        "tasks": tasks,
        "decisions": decisions,
        "errors": extraction_errors,
    }
