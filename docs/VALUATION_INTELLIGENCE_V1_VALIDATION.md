# Valuation Intelligence v1 — Validation & Closure

## Mission status

Valuation Intelligence v1 is feature-complete at the repository/source level.

The mission adds a research-quality-gated valuation layer that produces explicit Bear / Base / Bull valuation scenarios while keeping business-model choice, assumptions, data gaps and operator overrides visible.

## Implemented contract

Valuation only proceeds automatically after the company reaches:

```text
READY_FOR_VALUATION_CONTEXT
```

The gate comes from Research Confidence and is intentionally separate from investment conviction.

An operator may explicitly explore valuation before the gate passes, but the output retains a warning and does not change the underlying research-confidence state.

## Supported valuation families

### General / quality business

- normalized annual EPS
- 5-year P/E and/or industry P/E anchor when available
- current P/E only as an explicitly labeled fallback
- Bear / Base / Bull scenario multiples

### Bank / NBFC / lending business

- justified P/B framework
- sustainable ROE
- long-term growth
- cost of equity
- Bear / Base / Bull assumptions are visible/editable

### Cyclical / commodity business

- longer full-cycle EPS normalization
- weak/loss years remain in the normalization set
- wider Bear haircut and conservative Bull premium

### Utility / regulated / asset-heavy business

- conservative normalized-earnings framework in v1
- explicitly documented as an interim model

### Insurance

- deliberately blocked in v1 unless an appropriate embedded-value/VNB framework is available
- generic P/E or P/B is not silently substituted

## Investor-facing controls

The Valuation Intelligence workspace exposes:

- Research Confidence state
- automatic valuation-family classification
- reason for classification
- operator family override
- operator research-gate override for exploration
- scenario assumptions
- normalized EPS or book-value basis
- multiple anchors / anchor quality
- Bear / Base / Bull values
- upside/downside versus the **captured** research-run price
- warnings and model limitations
- explicit sensitivity / "what changes the valuation" explanation

## Price semantics

Valuation Intelligence v1 does not fetch live quotes.

The price used for comparison is:

```text
CAPTURED_DURING_FINANCIAL_RESEARCH_NOT_LIVE
```

The UI and valuation result now label this explicitly so a stored research-run price is not confused with the current market quote.

## Regression tests added

`tests/test_valuation_intelligence.py` covers:

1. valuation is blocked when Research Confidence has not passed;
2. general businesses use normalized EPS and available valuation anchors;
3. cyclical normalization includes weak/loss years;
4. bank/NBFC classification uses justified P/B rather than generic P/E;
5. insurers are not silently forced into a bank or generic earnings model;
6. explicit operator research-gate override remains visibly warned;
7. valuation results remain backward-compatible with older persisted ResearchRun files.

## Static review completed

The implementation was reviewed for consistency across:

- `app/valuation_intelligence.py`
- `app/pages/8_Valuation_Intelligence.py`
- `app/evidence_confidence.py`
- `app/pages/7_Research_Confidence.py`
- `app/navigation.py`
- `app/research_models.py`
- `tests/test_valuation_intelligence.py`
- `docs/VALUATION_INTELLIGENCE_V1.md`
- `README.md`

Two issues found during closure were corrected:

- cyclical EPS normalization originally risked excluding loss years; it now keeps weak/loss years in the full-cycle history;
- captured research-run price could be mistaken for a live quote; the result/UI now labels it as captured, not live.

## Runtime validation still required

The current execution environment could not pull/run the GitHub repository directly because outbound GitHub/DNS access is unavailable there. Therefore the regression tests were added but not executed in that environment.

A local acceptance run should verify:

1. open Research Confidence after a completed company-research run;
2. enter Valuation Intelligence from a `READY_FOR_VALUATION_CONTEXT` company;
3. run all eligible valuations;
4. inspect at least one general business, one bank/NBFC if available, and one cyclical if available;
5. verify captured price labeling;
6. change the valuation family manually and confirm the classification basis becomes an operator override;
7. change Bear/Base/Bull assumptions and confirm scenarios update and persist;
8. confirm an insurer is blocked rather than receiving a generic valuation;
9. restart/reload the Streamlit app and confirm persisted company valuation results remain available.

## Deliberate v1 exclusions

Do not treat the following as bugs in v1:

- no live price refresh;
- no DCF / FCFF / FCFE;
- no EV/EBITDA;
- no sum-of-the-parts;
- no insurer embedded-value acquisition;
- no real-estate NAV;
- no sector peer-set construction;
- no forward-consensus EPS;
- no automated cost-of-capital estimation;
- no scenario probabilities;
- no target-price recommendation;
- no buy/sell recommendation.

## Mission closure decision

Valuation Intelligence v1 is complete enough to validate with real researched companies.

The next product mission should **not** immediately add more valuation formulas. It should consume research quality, Bull/Bear state and valuation scenarios to build an explainable **Conviction & Decision Synthesis** layer that tells the investor what is attractive, what is risky, what is unresolved, and what must be true — without collapsing everything into one opaque score.
