import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import background_jobs


def test_job_metadata_roundtrip(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setattr(background_jobs, "JOBS_DIR", Path(td))
        job = {
            "job_id": "job-test",
            "job_type": "company_research",
            "status": "RUNNING",
            "payload": {"run_id": "run-1"},
            "progress": 0.25,
        }
        background_jobs.write_job(job)
        loaded = background_jobs.read_job("job-test")
        assert loaded["status"] == "RUNNING"
        assert loaded["payload"]["run_id"] == "run-1"
        background_jobs.update_job("job-test", status="COMPLETED", progress=1.0)
        loaded = background_jobs.read_job("job-test")
        assert loaded["status"] == "COMPLETED"
        assert loaded["progress"] == 1.0


def test_active_jobs_filters_finished_jobs(monkeypatch):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        monkeypatch.setattr(background_jobs, "JOBS_DIR", root)
        for job_id, status in [("job-a", "RUNNING"), ("job-b", "COMPLETED"), ("job-c", "QUEUED")]:
            (root / f"{job_id}.json").write_text(json.dumps({
                "job_id": job_id,
                "status": status,
                "created_at": job_id,
                "payload": {"run_id": "run-1"},
            }), encoding="utf-8")
        active = background_jobs.active_jobs("run-1")
        assert [x["job_id"] for x in active] == ["job-a", "job-c"]
