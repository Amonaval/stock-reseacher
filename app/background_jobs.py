from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_DIR = ROOT / "jobs"
JOBS_DIR.mkdir(exist_ok=True)
RUNS_DIR = ROOT / "runs"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def read_job(job_id: str) -> dict | None:
    path = _path(job_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_job(job: dict) -> dict:
    job = dict(job)
    job["updated_at"] = _now()
    path = _path(job["job_id"])
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    return job


def update_job(job_id: str, **changes) -> dict:
    job = read_job(job_id) or {"job_id": job_id, "created_at": _now()}
    job.update(changes)
    return write_job(job)


def start_job(job_type: str, payload: dict, *, label: str = "") -> dict:
    job_id = f"job-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    job = write_job({
        "job_id": job_id,
        "job_type": job_type,
        "label": label or job_type.replace("_", " ").title(),
        "status": "QUEUED",
        "created_at": _now(),
        "started_at": None,
        "finished_at": None,
        "progress": 0.0,
        "progress_message": "Queued",
        "payload": payload,
        "result": None,
        "error": None,
        "pid": None,
    })

    worker = ROOT / "app" / "background_worker.py"
    log_path = JOBS_DIR / f"{job_id}.log"
    log = open(log_path, "a", encoding="utf-8")
    kwargs = {
        "cwd": str(ROOT),
        "stdout": log,
        "stderr": subprocess.STDOUT,
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen([sys.executable, str(worker), job_id], **kwargs)
    finally:
        log.close()
    update_job(job_id, pid=proc.pid)
    return read_job(job_id) or job


def jobs_for_run(run_id: str) -> list[dict]:
    rows = []
    for path in JOBS_DIR.glob("job-*.json"):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if str((job.get("payload") or {}).get("run_id", "")) == str(run_id):
            rows.append(job)
    return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)


def active_jobs(run_id: str | None = None) -> list[dict]:
    rows = []
    for path in JOBS_DIR.glob("job-*.json"):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if run_id and str((job.get("payload") or {}).get("run_id", "")) != str(run_id):
            continue
        if job.get("status") in {"QUEUED", "RUNNING"}:
            rows.append(job)
    return sorted(rows, key=lambda x: x.get("created_at", ""))


def load_run(run_id: str):
    from research_models import ResearchRun
    path = RUNS_DIR / run_id / "research_run.json"
    if not path.exists():
        return None
    return ResearchRun.from_dict(json.loads(path.read_text(encoding="utf-8")))


def sync_session_from_jobs(st, run_id: str | None):
    """Refresh persistent run/results after detached workers complete.

    Safe to call on every Streamlit rerun/page navigation. The worker is a separate
    process, so navigation does not cancel it.
    """
    if not run_id:
        return []
    jobs = jobs_for_run(run_id)
    completed = [j for j in jobs if j.get("status") == "COMPLETED"]
    if completed:
        latest_run = load_run(run_id)
        if latest_run is not None:
            st.session_state.run = latest_run
        applied = st.session_state.setdefault("applied_background_jobs", set())
        if not isinstance(applied, set):
            applied = set(applied)
            st.session_state.applied_background_jobs = applied
        for job in reversed(completed):
            if job["job_id"] in applied:
                continue
            result = job.get("result") or {}
            updates = result.get("session_updates") or {}
            key = result.get("session_key")
            if key:
                updates[key] = result.get("value")
            for session_key, value in updates.items():
                st.session_state[session_key] = value
            applied.add(job["job_id"])
    return jobs
