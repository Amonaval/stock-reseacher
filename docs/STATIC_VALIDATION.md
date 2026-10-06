# Static Validation — Consolidation Mission

Date: 2026-10-06

The consolidation mission was statically validated before handoff.

## Python compilation

All application modules under `app/*.py` were compiled with `py_compile`.

Result:

```text
COMPILE_OK 34
```

This catches syntax errors across the accumulated codebase.

## Real 87-stock fallback fixture

The user's real `Result.xlsx` was replayed through the debug/fallback ingestion path.

Observed:

```text
ROWS        87
UNIVERSE    87
EXACT_URLS  87
```

The workbook stores Screener URLs as hyperlinks on company-name cells. The hyperlink-aware importer successfully retained all 87 exact company URLs.

## Snapshot-only financial guardrail

The same 87 companies were processed without live Screener enrichment to verify behavior when only screening snapshot ratios are available.

Result:

```text
SNAPSHOT_DECISIONS {'DATA_RETRY': 87}
Example coverage: 50%
```

This is intentional. Snapshot ratios can be displayed and used as partial evidence, but the system no longer presents incomplete financial data as a confident financial pass.

## Research-depth gate fixture

A two-company fixture was tested:

- one with strong document/evidence coverage and explicit risk evidence,
- one with no research sources.

Result:

```text
{'ADVERSARIAL': 1, 'SOURCE_GAP': 1}
```

This verifies that research-depth stages are evidence gates rather than simple score ranking.

## ResearchRun persistence

`ResearchRun` was created, an audit event was added, and the run was serialized successfully to `research_run.json`.

## Not validated in this environment

The following requires the user's local browser and therefore cannot be honestly certified by static validation alone:

- connection to the user's Chrome CDP endpoint,
- current Screener DOM selectors,
- execution of a live Screener query,
- Screener result pagination against the user's account,
- extraction of current company-page tables/documents behind the user's logged-in session.

The code contains defensive selectors and explicit error logging. The first local end-to-end run should therefore be treated as the runtime acceptance test for the Screener adapter.
