from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from navigation import render_navigation
from background_jobs import jobs_for_run, sync_session_from_jobs, JOBS_DIR

st.set_page_config(page_title="Background Jobs · Personal AI Stock Researcher", page_icon="🧵", layout="wide")
render_navigation()

st.title("🧵 Background Jobs")
st.caption("Long-running crawling, financial collection and research continue here even when you navigate to another page.")

run = st.session_state.get("run")
if run is None:
    st.info("Start a research run first.")
    st.stop()

jobs = sync_session_from_jobs(st, run.run_id)
run = st.session_state.get("run") or run
jobs = jobs_for_run(run.run_id)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Running", sum(j.get("status") == "RUNNING" for j in jobs))
c2.metric("Queued", sum(j.get("status") == "QUEUED" for j in jobs))
c3.metric("Completed", sum(j.get("status") == "COMPLETED" for j in jobs))
c4.metric("Failed", sum(j.get("status") == "FAILED" for j in jobs))

if st.button("Refresh status", type="primary"):
    st.rerun()

if not jobs:
    st.info("No background jobs have been started for this research run yet.")
else:
    rows = []
    for job in jobs:
        rows.append({
            "Job": job.get("label"),
            "Status": job.get("status"),
            "Progress %": round(float(job.get("progress") or 0) * 100, 1),
            "Current work": job.get("progress_message"),
            "Started": job.get("started_at"),
            "Finished": job.get("finished_at"),
            "PID": job.get("pid"),
            "Job ID": job.get("job_id"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    selected = st.selectbox("Inspect job", [j.get("job_id") for j in jobs], format_func=lambda x: next((j.get("label") for j in jobs if j.get("job_id") == x), x))
    job = next(j for j in jobs if j.get("job_id") == selected)
    st.markdown(f"### {job.get('label')}")
    st.progress(float(job.get("progress") or 0))
    st.write("**Status:**", job.get("status"))
    st.write("**Current work:**", job.get("progress_message"))
    if job.get("error"):
        st.error(job.get("error"))
    log_path = JOBS_DIR / f"{job.get('job_id')}.log"
    if log_path.exists():
        with st.expander("Worker log"):
            try:
                text = log_path.read_text(encoding="utf-8", errors="replace")
                st.code(text[-12000:])
            except Exception as exc:
                st.warning(str(exc))

st.info("You may leave this page while a job is running. The worker is a separate local process and is not tied to the Streamlit page lifecycle.")
