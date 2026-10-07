from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from background_jobs import read_job, update_job, RUNS_DIR
from research_models import ResearchRun


def _load_run(run_id: str) -> ResearchRun:
    path = RUNS_DIR / run_id / "research_run.json"
    if not path.exists():
        raise FileNotFoundError(f"Research run not found: {run_id}")
    return ResearchRun.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _progress(job_id: str, fraction: float, message: str):
    update_job(job_id, progress=max(0.0, min(1.0, float(fraction))), progress_message=message)


def _dispatch(job_id: str, job: dict) -> dict:
    kind = job["job_type"]
    p = job.get("payload") or {}

    if kind == "discover_screens":
        from screener_adapter import ScreenerAdapter
        def progress(i, n, item):
            _progress(job_id, i / max(n, 1), f"Discovering {i}/{n}: {item.get('title') or item.get('url')}")
        rows = ScreenerAdapter.discover_screens(
            p["cdp_url"], p.get("explore_url", "https://www.screener.in/explore/"),
            int(p.get("max_pages", 15)), int(p.get("max_screens", 0)), progress,
        )
        return {"session_key": "screen_candidates", "value": rows}

    if kind == "fetch_screen_queries":
        from screener_adapter import ScreenerAdapter
        def progress(i, n, item):
            _progress(job_id, i / max(n, 1), f"Fetching query {i}/{n}: {item.get('title') or item.get('url')}")
        rows = ScreenerAdapter.fetch_screen_queries(p["cdp_url"], p.get("urls", []), progress)
        originals = {x.get("url"): x for x in p.get("source_items", [])}
        for item in rows:
            src = originals.get(item.get("url"), {})
            item["owner"] = item.get("owner") or src.get("owner", "")
            item["title"] = item.get("title") or src.get("title", "")
        return {"session_key": "screen_queries", "value": rows}

    run = _load_run(p["run_id"])

    if kind == "screening":
        from research_service import ResearchService
        service = ResearchService(run, RUNS_DIR)
        def progress(si, sn, sid, name, page_no, total_rows):
            frac = (si - 1 + min(page_no, 5) / 5) / max(sn, 1)
            _progress(job_id, frac, f"{sid} · {name}: page {page_no}, {total_rows} rows")
        universe = service.execute_strategies(p["cdp_url"], set(p.get("enabled_ids") or []), progress)
        run.save(RUNS_DIR)
        return {"session_key": "candidate_universe", "value": universe}

    if kind == "financials":
        from research_service import ResearchService
        service = ResearchService(run, RUNS_DIR)
        candidates = p.get("candidate_universe") or []
        def progress(i, n, company, status):
            _progress(job_id, i / max(n, 1), f"{i}/{n} {company} — {status}")
        result = service.collect_financials(p["cdp_url"], candidates, progress)
        run.save(RUNS_DIR)
        return {"session_key": "financial_assessments", "value": result}

    if kind == "company_research":
        from company_research_engine import run_company_research_engine
        names = p.get("company_names") or []
        def progress(i, n, company, stage):
            _progress(job_id, i / max(n, 1), f"{i}/{n} {company} — {stage.replace('_', ' ')}")
        memories = run_company_research_engine(
            run, p["cdp_url"], company_names=names, use_llm=bool(p.get("use_llm", False)),
            max_sources_per_type=int(p.get("max_sources_per_type", 2)),
            min_source_score=float(p.get("min_source_score", 45)), progress=progress,
        )
        run.save(RUNS_DIR)
        return {"session_key": "research_memories", "value": memories}

    if kind == "deep_gap_research":
        from deep_gap_research import resolve_research_gaps
        names = p.get("company_names") or []
        def progress(i, n, company, stage):
            _progress(job_id, i / max(n, 1), f"{i}/{n} {company} — {stage.replace('_', ' ')}")
        result = resolve_research_gaps(
            run, p["cdp_url"], company_names=names,
            use_llm=bool(p.get("use_llm", False)), progress=progress,
        )
        run.save(RUNS_DIR)
        return {"session_key": "deep_gap_result", "value": result}

    if kind == "research_plan":
        from research_analysis_orchestrator import plan_research_for_run
        plan = plan_research_for_run(run, p.get("budgets") or None)
        run.save(RUNS_DIR)
        return {"session_key": "research_plan", "value": plan}

    if kind == "thesis_challenge":
        from research_analysis_orchestrator import run_thesis_analysis
        plan = p.get("plan") or {}
        names = p.get("company_names") or []
        def progress(i, n, company):
            _progress(job_id, i / max(n, 1), f"{i}/{n} challenging {company}")
        results = run_thesis_analysis(run, plan, company_names=names, progress=progress)
        run.save(RUNS_DIR)
        return {"session_key": "adversarial_results", "value": results}

    raise ValueError(f"Unsupported background job type: {kind}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: background_worker.py <job-id>")
    job_id = sys.argv[1]
    job = read_job(job_id)
    if not job:
        raise SystemExit(f"Unknown job: {job_id}")
    update_job(job_id, status="RUNNING", started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), progress_message="Starting")
    try:
        result = _dispatch(job_id, job)
        update_job(
            job_id, status="COMPLETED", progress=1.0, progress_message="Completed",
            finished_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), result=result,
        )
    except Exception as exc:
        update_job(
            job_id, status="FAILED", error=str(exc), progress_message="Failed",
            finished_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            traceback=traceback.format_exc(),
        )
        raise


if __name__ == "__main__":
    main()
