from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Callable

from analyzer import analyze
from strategy import generate_master_strategies
from candidates import build_candidate_universe
from research_models import ResearchRun
from screener_adapter import ScreenerAdapter


class ResearchService:
    def __init__(self, run: ResearchRun, runs_root: Path):
        self.run = run
        self.runs_root = Path(runs_root)

    def analyze_screens(self, screens: list[dict]) -> list[dict]:
        self.run.status = "ANALYZING_METHODOLOGY"
        self.run.selected_screens = screens
        self.run.log("STRATEGY", "METHODOLOGY_START", f"Analyzing {len(screens)} selected historical screens.")
        analysis = analyze(screens)
        strategies = generate_master_strategies(screens, analysis)
        self.run.strategies = strategies
        self.run.stage_summary["methodology"] = {"screens": len(screens), "conditions": len(analysis["conditions"]), "strategies": len(strategies)}
        self.run.log("STRATEGY", "METHODOLOGY_COMPLETE", f"Generated {len(strategies)} master strategy proposals from {len(screens)} screens.")
        self.run.save(self.runs_root)
        return strategies

    def execute_strategies(self, cdp_url: str, enabled_ids: set[str] | None = None, progress: Callable | None = None) -> list[dict]:
        strategies = [s for s in self.run.strategies if not enabled_ids or s.get("id") in enabled_ids]
        self.run.status = "RUNNING_STRATEGIES"
        raw_rows = []
        with ScreenerAdapter(cdp_url) as adapter:
            for idx, strategy in enumerate(strategies, 1):
                sid, name, query = strategy.get("id"), strategy.get("name"), strategy.get("hard_query")
                self.run.log("SCREENING", "STRATEGY_START", f"Running {sid} · {name}", details={"query": query})
                try:
                    def pp(page_no, total_rows, url):
                        if progress: progress(idx, len(strategies), sid, name, page_no, total_rows)
                    rows = adapter.collect_query_results(query, sid, progress=pp)
                    raw_rows.extend(rows)
                    exact = sum(bool(x.get("url")) for x in rows)
                    self.run.log("SCREENING", "STRATEGY_COMPLETE", f"{sid} returned {len(rows)} rows; {exact} exact company URLs captured.", details={"rows": len(rows), "exact_urls": exact})
                except Exception as exc:
                    self.run.log("SCREENING", "STRATEGY_FAILED", f"{sid} failed: {exc}", status="ERROR")
        universe = build_candidate_universe(raw_rows, strategies)
        for item in universe:
            cr = self.run.ensure_company(item["company"], item.get("url", ""))
            cr.screen_matches = [x.strip() for x in str(item.get("strategies", "")).split(",") if x.strip()]
            if item.get("snapshot"):
                cr.screen_snapshots = [item["snapshot"]]
        self.run.stage_summary["screening"] = {
            "strategies_run": len(strategies), "raw_rows": len(raw_rows), "unique_companies": len(universe),
            "exact_company_urls": sum(bool(x.get("url")) for x in universe),
        }
        self.run.log("SCREENING", "CANDIDATE_UNIVERSE", f"Built {len(universe)} unique companies from {len(raw_rows)} strategy-result rows.")
        self.run.status = "CANDIDATES_READY"
        self.run.save(self.runs_root)
        return universe

    def collect_financials(self, cdp_url: str, candidate_universe: list[dict], progress: Callable | None = None) -> list[dict]:
        """Autonomously collect multi-period financials using exact company URLs first."""
        from screener_auto_financials import enrich_candidate_universe
        from financials import build_company_histories, merge_candidate_context
        from financial_assessment import assess_universe

        self.run.status = "COLLECTING_FINANCIALS"
        self.run.log("FINANCIAL", "COLLECTION_START", f"Collecting financial history for {len(candidate_universe)} candidate companies.")
        rows, resolved, errors = enrich_candidate_universe(
            candidate_universe, cdp_url=cdp_url, use_screener=True, max_companies=0, progress=progress
        )
        companies = merge_candidate_context(build_company_histories(rows), candidate_universe)
        assessments = assess_universe(companies)
        by_company = {str(x.get("company", "")).strip().casefold(): x for x in assessments}

        for key, company in self.run.companies.items():
            item = by_company.get(key)
            if not item:
                company.decisions.append({"stage":"FINANCIAL","decision":"DATA_RETRY","reason":"No normalized financial record was produced."})
                self.run.log("FINANCIAL", "COMPANY_DATA_GAP", "No normalized financial record was produced; retained for retry.", company=company.company, status="WARN")
                continue
            company.financial_history = item.get("history", [])
            company.financial_assessment = {k:v for k,v in item.items() if k not in {"history"}}
            company.decisions.append({
                "stage":"FINANCIAL", "decision":item.get("decision"), "reason":item.get("decision_reason"),
                "evidence_coverage":item.get("data_confidence")
            })
            self.run.log(
                "FINANCIAL", "COMPANY_ASSESSED",
                f"{item.get('decision')}: {item.get('decision_reason')}", company=company.company,
                status="WARN" if item.get("decision") in {"DATA_RETRY","HOLD","ELIMINATE"} else "INFO",
                details={"coverage":item.get("data_confidence"),"labels":item.get("labels",{}),"warnings":item.get("warnings",[])}
            )

        counts = {}
        for x in assessments:
            counts[x.get("decision", "UNKNOWN")] = counts.get(x.get("decision", "UNKNOWN"), 0) + 1
        self.run.stage_summary["financial"] = {
            "companies": len(assessments), "decisions": counts, "enrichment_errors": len(errors),
            "exact_url_hits": sum(1 for x in resolved if x.get("status") == "ENRICHED")
        }
        self.run.log("FINANCIAL", "COLLECTION_COMPLETE", f"Financial stage complete for {len(assessments)} companies: {counts}. {len(errors)} enrichment issues retained as data gaps.")
        self.run.status = "FINANCIAL_COMPLETE"
        self.run.save(self.runs_root)
        return assessments

    def collect_company_research(self, cdp_url: str, use_llm: bool = False, progress: Callable | None = None) -> list[dict]:
        """Discover/fetch source documents automatically and build company evidence memory."""
        from research_fetch import fetch_manifest
        from research_agent import extract_research_evidence, build_company_research_memory

        eligible = [c for c in self.run.companies.values() if c.financial_assessment.get("decision") in {"ADVANCE","WATCHLIST"}]
        self.run.status = "COLLECTING_RESEARCH"
        self.run.log("RESEARCH", "SOURCE_DISCOVERY_START", f"Discovering company research sources for {len(eligible)} financial survivors.")
        source_rows=[]
        with ScreenerAdapter(cdp_url) as adapter:
            for i, company in enumerate(eligible, 1):
                try:
                    if not company.screener_url:
                        self.run.log("RESEARCH", "SOURCE_DISCOVERY_GAP", "Exact Screener URL missing; skipping company-page source discovery until identity is resolved.", company=company.company, status="WARN")
                        continue
                    rows=adapter.discover_company_documents(company.screener_url, company.company)
                    source_rows.extend(rows)
                    self.run.log("RESEARCH", "SOURCES_DISCOVERED", f"Found {len(rows)} research-document links on the company page.", company=company.company, details={"source_types":sorted({x.get('doc_type') for x in rows})})
                except Exception as exc:
                    self.run.log("RESEARCH", "SOURCE_DISCOVERY_FAILED", str(exc), company=company.company, status="WARN")
                if progress: progress(i, len(eligible), company.company, "discover")

        try:
            from source_discovery import BraveSearchProvider, discover_company_sources
            from source_policy import dedupe_and_rank
            provider=BraveSearchProvider()
            if provider.configured():
                for company in eligible:
                    rows, errs=discover_company_sources(company.company, provider=provider, max_per_query=4)
                    source_rows.extend(rows)
                    for err in errs:
                        self.run.log("RESEARCH","WEB_SOURCE_DISCOVERY_FAILED",err.get("error",str(err)),company=company.company,status="WARN")
                source_rows=dedupe_and_rank(source_rows)
                self.run.log("RESEARCH","WEB_SOURCE_DISCOVERY",f"Expanded research queue to {len(source_rows)} deduplicated sources using the configured web-search provider.")
        except Exception as exc:
            self.run.log("RESEARCH","WEB_SOURCE_DISCOVERY_SKIPPED",f"Optional web-source discovery unavailable: {exc}",status="WARN")

        documents, fetch_errors = fetch_manifest(source_rows, progress=None) if source_rows else ([], [])
        evidence, extraction_errors = extract_research_evidence(documents, use_llm=use_llm)
        financial_context = [c.financial_assessment for c in eligible]
        memories = build_company_research_memory(documents, evidence, financial_ranked=financial_context)
        memory_map={str(m.get("company"," ")).strip().casefold():m for m in memories}

        for company in eligible:
            key=company.company.strip().casefold(); memory=memory_map.get(key)
            company.documents=[d for d in documents if str(d.get("company"," ")).strip().casefold()==key]
            company.evidence=[e for e in evidence if str(e.get("company"," ")).strip().casefold()==key]
            if memory:
                company.research_questions=[]
                missing_required={"annual_report","quarterly_result","investor_presentation","earnings_call","exchange_filing","credit_rating"}-set(memory.get("document_types",[]))
                for doc_type in sorted(missing_required):
                    company.research_questions.append({"status":"OPEN","question":f"Acquire/verify missing {doc_type.replace('_',' ')} evidence.","reason":"Research coverage gap"})
                self.run.log("RESEARCH", "COMPANY_RESEARCH_BUILT", f"Built {memory.get('evidence_items',0)} evidence items from {memory.get('documents',0)} documents; research readiness {memory.get('research_readiness',0)}%.", company=company.company, details={"document_types":memory.get("document_types",[]),"risks":memory.get("risk_items",0),"catalysts":memory.get("catalyst_items",0)})
            else:
                self.run.log("RESEARCH", "COMPANY_RESEARCH_GAP", "No usable research documents were fetched; retained for autonomous retry/provider fallback.", company=company.company, status="WARN")

        self.run.stage_summary["research"]={"eligible_companies":len(eligible),"source_links":len(source_rows),"documents":len(documents),"evidence_items":len(evidence),"fetch_errors":len(fetch_errors),"extraction_errors":len(extraction_errors)}
        self.run.log("RESEARCH", "RESEARCH_COMPLETE", f"Research evidence stage collected {len(documents)} documents and {len(evidence)} source-linked evidence items. Missing sources remain explicit research tasks.")
        self.run.status="RESEARCH_COMPLETE"
        self.run.save(self.runs_root)
        return memories

    def plan_deep_research(self, memories: list[dict], budgets: dict | None = None) -> dict:
        from research_depth_planner import plan_research_depth
        plan=plan_research_depth(memories,budgets)
        self.run.stage_summary["research_depth"]=plan["counts"]
        for row in plan["rows"]:
            company=self.run.ensure_company(row["company"])
            company.decisions.append({"stage":"RESEARCH_DEPTH","decision":row["stage"],"reason":row["reason"]})
            self.run.log("RESEARCH_DEPTH","DEPTH_DECISION",f"{row['stage']}: {row['reason']}",company=row["company"],details={k:row[k] for k in ["documents","document_coverage","evidence_quality","research_readiness","risk_items"]})
        self.run.log("RESEARCH_DEPTH","PLANNING_COMPLETE",f"Research-depth allocation complete: {plan['counts']}.")
        self.run.status="RESEARCH_DEPTH_PLANNED"
        self.run.save(self.runs_root)
        return plan

    def run_adversarial_research(self, memories: list[dict], plan: dict, progress: Callable | None = None) -> list[dict]:
        from v6_pipeline import run_v6
        names=[r["company"] for r in plan.get("rows",[]) if r.get("stage")=="ADVERSARIAL"]
        if not names:
            self.run.log("ADVERSARIAL","NO_READY_COMPANIES","No company currently passes the adversarial evidence gate.",status="WARN")
            return []
        self.run.log("ADVERSARIAL","START",f"Running independent Bull/Bear challenge for {len(names)} evidence-ready companies.")
        results=run_v6(memories,finalist_names=names,progress=progress)
        by_name={str(r.get("company"," ")).casefold():r for r in results}
        for company in self.run.companies.values():
            r=by_name.get(company.company.casefold())
            if not r: continue
            bundle=r.get("bull_bear",{})
            company.bull_case=bundle.get("bull",{})
            company.bear_case=bundle.get("bear",{})
            company.contradiction_review=r.get("challenge",{})
            c=r.get("classification",{})
            company.decisions.append({"stage":"ADVERSARIAL","decision":c.get("thesis_status"),"reason":r.get("challenge",{}).get("challenge_summary","")})
            self.run.log("ADVERSARIAL","COMPANY_CHALLENGED",f"{c.get('thesis_status')} · thesis balance {c.get('thesis_balance')} · fragility {c.get('fragility_score')}",company=company.company,details={"bull_strength":c.get("bull_strength"),"bear_strength":c.get("bear_strength"),"unresolved":c.get("unresolved_questions",[])})
        self.run.stage_summary["adversarial"]={"companies":len(results)}
        self.run.log("ADVERSARIAL","COMPLETE",f"Bull/Bear challenge completed for {len(results)} companies. These are research states, not buy/sell recommendations.")
        self.run.status="ADVERSARIAL_COMPLETE"
        self.run.save(self.runs_root)
        return results
