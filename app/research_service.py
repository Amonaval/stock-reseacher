from __future__ import annotations

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
        self.run.stage_summary["methodology"] = {
            "screens": len(screens), "conditions": len(analysis["conditions"]), "strategies": len(strategies)
        }
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
                        if progress:
                            progress(idx, len(strategies), sid, name, page_no, total_rows)
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
            "strategies_run": len(strategies),
            "raw_rows": len(raw_rows),
            "unique_companies": len(universe),
            "exact_company_urls": sum(bool(x.get("url")) for x in universe),
        }
        self.run.log("SCREENING", "CANDIDATE_UNIVERSE", f"Built {len(universe)} unique companies from {len(raw_rows)} strategy-result rows.")
        self.run.status = "CANDIDATES_READY"
        self.run.save(self.runs_root)
        return universe
