# Conviction & Decision Synthesis v1 — Validation & Closure

## Scope validated

This closure pass reviewed the v1 synthesis contract across:

- persistence in `CompanyResearch`;
- synthesis engine inputs and state precedence;
- Research Confidence gating;
- financial decision / operator-override visibility;
- Bull/Bear classification and fragility;
- valuation posture using captured run price;
- Bear/Base/Bull downside/upside context;
- investor-facing workspace;
- separate Investor Review persistence;
- backward compatibility for older `research_run.json` files;
- user guide / README / doctrine alignment.

## Regression cases added

`tests/test_conviction_synthesis.py` covers:

1. high-priority state requires a surviving Bull thesis plus favorable Base valuation context;
2. a wide Bear-case downside blocks automatic high-priority status;
3. Bear-dominated thesis overrides attractive valuation context;
4. Bear dominance remains visible even when valuation is missing;
5. fragile thesis overrides large apparent valuation upside;
6. Bull-surviving thesis can still be valuation-stretched;
7. contested thesis remains contested;
8. low Research Confidence blocks decision-quality synthesis;
9. an unoverridden financial `HOLD` remains an explicit conflict;
10. system refresh preserves the separate Investor Review;
11. old persisted runs without `decision_synthesis` remain backward-compatible.

## Important design checks

### No master score

There is no system-generated 0–100 conviction score.

The engine preserves separate dimensions for:

- research quality;
- financial quality;
- thesis challenge;
- valuation posture.

### State precedence

Negative/uncertain upstream findings are not averaged away by favorable valuation.

Research gap → challenge gap → financial conflict → Bear/fragility/contest → valuation completeness → positive-thesis valuation posture.

### Downside asymmetry

A Bull-surviving company with a Bear valuation scenario around **-35% or worse versus captured price** is assigned `POSITIVE_THESIS_WIDE_DOWNSIDE` rather than `HIGH_PRIORITY_RESEARCH_CANDIDATE`.

The threshold is a transparent v1 policy and should be recalibrated from real runs; it is not a loss probability.

### User authority

Investor Review is separate from the system result and is preserved when synthesis is refreshed.

The user can record:

- stance;
- personal LOW / MEDIUM / HIGH conviction;
- notes.

These values are not used to silently rewrite the system conclusion.

## Runtime validation limitation

The repository test suite was not executed from the assistant container because direct GitHub/DNS access is unavailable in that runtime.

The code paths and regression cases were reviewed statically through the connected GitHub repository. A local runtime acceptance pass is still required.

## Recommended local acceptance run

Use 3–5 companies representing different outcomes:

1. one Bull-surviving company with favorable Base valuation and moderate Bear downside;
2. one Bull-surviving company with wide Bear downside;
3. one contested or fragile company;
4. one Bear-dominated company;
5. optionally one company with incomplete research/valuation.

Verify:

- overview states match the underlying dimensions;
- no Bear/fragile case is labeled high priority;
- captured price is not presented as live;
- reasons/blockers are understandable;
- what-must-be-true / invalidation fields are useful when semantic Bull/Bear data exists;
- Investor Review survives a system refresh;
- older saved research runs still load.

## v1 closure decision

Conviction & Decision Synthesis v1 is considered source-complete for this milestone.

The next product mission should not add more hidden scoring. The strongest next investment is to improve **decision usability over time**: live/timestamped market context, persistent shortlist/ranking views, and monitoring for evidence/thesis/valuation changes.
