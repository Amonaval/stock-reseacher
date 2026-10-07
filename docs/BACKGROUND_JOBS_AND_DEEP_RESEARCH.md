# Background Jobs & Deep Research Gap Resolution

This document describes two product behaviors added after the guided-flow UX consolidation:

1. long-running work must survive Streamlit page navigation;
2. a deep-research plan must be executable, not merely descriptive.

## 1. Why background jobs exist

Streamlit reruns the active script when the user changes page or interacts with controls. Long crawling/research functions should therefore **not** be tied to the page request lifecycle.

The app now launches long-running work through a detached local worker process.

Supported background job types include:

- historical screen discovery;
- historical screen-query fetch;
- strategy execution / result crawling;
- financial-history collection;
- company research;
- deep evidence-gap resolution;
- Bull/Bear thesis challenge.

## Persistence model

Each job is represented by a JSON record under:

```text
jobs/<job-id>.json
```

Worker stdout/stderr is written to:

```text
jobs/<job-id>.log
```

The `jobs/` directory is runtime state and is ignored by Git.

A job records:

- job type;
- run ID;
- process ID;
- queued/running/completed/failed state;
- progress fraction;
- human-readable current action;
- result/session updates;
- error and traceback when relevant.

The worker uses the same Python executable that launched Streamlit, so it inherits the active virtual environment and environment variables.

## Navigation behavior

After a background job is launched:

- the UI immediately returns control to the user;
- the user may move to another page;
- the detached worker continues independently;
- returning to a page synchronizes completed results into Streamlit session state;
- the persisted `ResearchRun` is reloaded from disk after completion.

The **Background Jobs** page is the dedicated monitor.

## Concurrency rule

The UI intentionally permits only one long-running job at a time per research run.

Reason: most stages enrich the same `research_run.json`. Multiple simultaneous writers would require transactional run-state merging. Until such a store exists, sequential background jobs are safer and easier for the investor to understand.

---

# 2. Deep research is now an execution stage

Previously the depth planner could say:

```text
SOURCE_GAP
STRUCTURED
TARGETED
DEEP
ADVERSARIAL
```

but only `ADVERSARIAL` had a real next action. This created a dead end: companies could be classified as needing more research without the app actually performing that research.

The new flow is:

```text
Company research
    ↓
Depth plan
    ↓
Does company need more evidence?
    ├─ yes → Resolve evidence gaps
    │          ↓
    │     rebuild dossier
    │          ↓
    │     rebuild depth plan
    │
    └─ no / evidence sufficient
               ↓
          Bull/Bear challenge
```

## What `Resolve evidence gaps` does

For selected companies it:

- performs a broader company-research pass;
- raises the source-per-type budget;
- lowers the source-quality floor modestly while keeping source ranking visible;
- preserves previously acquired documents and evidence;
- avoids re-fetching already successful URLs;
- keeps source-attempt history;
- extracts evidence from newly acquired documents;
- rebuilds analyst-mission coverage;
- rebuilds the investor dossier;
- records before/after research-state transitions;
- automatically recalculates the depth plan.

This is research effort allocation, not investment selection.

---

# 3. Evidence-ready no longer means every possible document exists

The original POC effectively required all of these source classes:

- annual report;
- quarterly result;
- investor presentation;
- earnings call;
- exchange filing;
- credit rating.

That is too rigid. Some high-quality companies may not have a relevant credit rating or earnings-call transcript, for example.

The current company-research contract requires a **sufficient evidence base**, not every source checkbox.

For automatic `EVIDENCE_READY`, the dossier requires:

1. a core longitudinal source — currently an annual report;
2. at least one fresh operating/disclosure source — quarterly result, exchange filing, investor presentation or earnings call;
3. at least 70% fundamental analyst-mission coverage.

Missing supplementary source classes remain visible as open questions but do not automatically block the company.

The deep-research planner then independently checks:

- document coverage;
- evidence quality;
- explicit downside/risk evidence;
- company research state.

`research_readiness` remains visible as a diagnostic and prioritization input, but is not another opaque hard cutoff layered on top of those explicit gates.

---

# 4. What “Challenge the thesis” means

Bull/Bear is a confirmation-bias control.

For an evidence-ready company:

### Bull researcher
Builds the strongest positive thesis supported by current evidence.

### Bear / forensic researcher
Attempts to break that thesis using supported evidence around:

- business-model weakness;
- cash conversion;
- governance;
- customer/supplier concentration;
- leverage;
- competition;
- execution;
- capital allocation;
- other thesis breakers.

### Neutral challenge
Compares both cases and reports:

- Bull arguments that survive;
- Bear arguments that survive;
- contradictions;
- fragile assumptions;
- unresolved questions;
- missing evidence.

If no company passes the gate, the correct product behavior is **not** to force Bull/Bear. The app should explain why and direct the user back to deeper evidence work.

---

# 5. Product rule

A research stage should never end with only:

> “Not ready.”

It should always answer:

```text
Why not ready?
→ What evidence is missing?
→ What will the system do next?
→ Can the user override/review it?
```

This is the constitution rule applied to the transition from Company Research → Deep Research → Thesis Challenge.
