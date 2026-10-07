# Research Confidence

Research Confidence is the quality-control layer between evidence research and future valuation/conviction work.

It answers:

> **How much should I trust the current research dossier?**

It does **not** answer:

- Is this a good stock?
- Is this company undervalued?
- What return should I expect?
- Should I buy or sell?

## Why this layer exists

Without an explicit quality gate, downstream valuation can create false precision.

Example:

```text
Very bullish narrative
+ one investor presentation
+ no downside evidence
+ weak source traceability
= low research confidence
```

Conversely:

```text
Several authoritative sources
+ primary financial disclosures
+ downside evidence
+ contradictions surfaced
+ high mission coverage
= high research confidence
```

The second company could still have a bearish thesis. Research confidence and investment conviction are intentionally independent.

## Dimensions

### Source authority

Prefers authoritative evidence such as exchange/regulatory/company-primary material and recognized credit-rating sources over generic secondary sources.

### Source freshness

Checks whether the dossier contains sufficiently current operating/disclosure evidence. Annual reports remain useful for longer than quarterly/disclosure evidence.

### Evidence traceability

Measures whether findings can be traced back to a source document and page/excerpt.

### Fundamental mission coverage

Uses the Company Research Engine missions:

- business model;
- growth durability;
- cash conversion;
- management/capital allocation;
- governance;
- risks;
- catalysts.

### Cross-source triangulation

Measures whether covered research themes are supported by multiple independent documents.

This is currently **theme-level corroboration**, not semantic claim-level proof.

### Downside evidence coverage

Checks whether the researcher has actively captured risk/governance evidence rather than researching only the positive thesis.

### Contradiction handling

Checks whether the Bull/Bear/neutral challenge has surfaced unresolved contradictions and questions.

An unchallenged thesis is treated as unknown rather than automatically poor.

### Financial-data coverage

Carries forward the financial-analysis evidence coverage so later reasoning cannot ignore weak structured data.

## States

### `HIGH_RESEARCH_CONFIDENCE`

Strong evidence foundation and no current critical quality gap.

### `MODERATE_RESEARCH_CONFIDENCE`

Useful research exists, but one or two important quality gaps remain.

### `LOW_RESEARCH_CONFIDENCE`

The system should strengthen the dossier before allowing later valuation/conviction outputs to look authoritative.

## Valuation-context gate

The layer also outputs:

- `READY_FOR_VALUATION_CONTEXT`
- `MORE_RESEARCH_NEEDED`

`READY_FOR_VALUATION_CONTEXT` means only:

> the current research foundation is sufficiently grounded to support valuation analysis.

It does not mean:

> the stock is undervalued or attractive.

## UX rule

The user should see:

```text
Research confidence state
↓
Dimension breakdown
↓
Critical gaps
↓
Themes covered / triangulated
↓
Whether valuation context is ready
```

The overall numeric score is secondary. The dimensions and critical gaps are more important.

## Future improvements

Potential later upgrades:

- semantic claim-level corroboration across sources;
- explicit fact vs management claim vs analyst inference taxonomy;
- source freshness requirements by industry/event type;
- management promise-vs-delivery history;
- contradiction severity classification;
- evidence supersession when newer filings invalidate older evidence;
- direct NSE/BSE source provenance.
