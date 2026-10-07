# Conviction & Decision Synthesis v1

## Purpose

Conviction & Decision Synthesis combines the upstream research artifacts into one **explainable research decision state**.

It is deliberately **not**:

- a BUY / SELL / HOLD recommendation engine;
- a return-probability model;
- a target-price generator;
- a portfolio-weight engine;
- a hidden 0–100 master conviction score.

The product asks:

> Given what we know about financial quality, evidence quality, the adversarial thesis challenge and valuation context, what kind of research case is this, what still matters, and is it ready for an investor to review?

---

## Constitutional order

```text
Financial quality
        +
Research Confidence
        +
Bull/Bear thesis challenge
        +
Valuation Intelligence
        +
Unresolved questions / fragility
        ↓
Explainable research decision state
        ↓
Optional Investor Review
```

No downstream number is allowed to erase an upstream contradiction.

Examples:

- attractive valuation does not override a Bear-dominated thesis;
- a surviving Bull thesis does not override low Research Confidence;
- high Research Confidence does not imply an attractive company;
- a large theoretical valuation discount does not erase thesis fragility;
- a favorable Base valuation does not erase a very wide Bear-case downside;
- an operator override remains visible rather than rewriting the original system decision.

---

## System decision states

### `MORE_RESEARCH_NEEDED`

The Research Confidence quality gate has not cleared. Critical evidence gaps remain.

This is an evidence state, not a negative investment opinion.

### `THESIS_CHALLENGE_PENDING`

Research quality is adequate, but Bull/Bear adversarial review is missing or still reports insufficient evidence.

### `VALUATION_CONTEXT_INCOMPLETE`

The researched thesis exists, but supported Bear/Base/Bull valuation scenarios are unavailable or blocked.

### `FINANCIAL_QUALITY_CONFLICT`

Later narrative/valuation work conflicts with an earlier unoverridden `HOLD` or `ELIMINATE` financial-quality decision.

The conflict is surfaced rather than silently allowing later analysis to overwrite the earlier gate.

### `FRAGILE_RESEARCH_CASE`

The thesis depends heavily on unresolved assumptions, contradictions or fragile evidence.

### `RISK_DOMINATED_RESEARCH_CASE`

The Bear case is better supported than the Bull case on the current evidence.

This state remains visible even when valuation is missing; a known Bear-dominated thesis should not be hidden behind a later missing valuation step.

### `CONTESTED_RESEARCH_CASE`

Bull and Bear interpretations remain materially balanced after adversarial review.

### `HIGH_PRIORITY_RESEARCH_CANDIDATE`

The current v1 contract requires:

- Research Confidence gate passed;
- Bull case survives adversarial review;
- valuation context is available;
- the Base valuation scenario is meaningfully above the **captured** research-run price;
- thesis fragility is not extreme;
- the Bear valuation scenario is not wider than approximately **-35% versus the captured price**.

This means the case deserves investor attention. It does **not** mean BUY.

The -35% Bear-scenario boundary is a v1 synthesis policy, not an estimated loss probability. It is deliberately visible and should be revisited after real-run validation.

### `POSITIVE_THESIS_WIDE_DOWNSIDE`

The Bull thesis survives, but the Bear valuation scenario is approximately -35% or worse versus the captured price.

This prevents attractive Base-case upside from automatically creating a high-priority state when scenario asymmetry remains severe.

### `POSITIVE_THESIS_NEAR_BASE_VALUE`

The Bull thesis survives, but the captured price is broadly around the Base valuation scenario.

### `POSITIVE_THESIS_VALUATION_STRETCHED`

The Bull thesis survives, but the captured price is above the Base valuation scenario under current assumptions.

---

## State precedence

The synthesis is intentionally not a weighted average.

The broad precedence is:

```text
Research-quality gap
    ↓
Missing/insufficient thesis challenge
    ↓
Unresolved unoverridden financial conflict
    ↓
Bear-dominated / Fragile / Contested thesis
    ↓
Missing valuation context
    ↓
Bull-surviving valuation posture
```

This means strong valuation cannot wash out a serious research/thesis warning.

---

## No master conviction score

The system preserves separate dimensions:

### Research quality

- `HIGH / MODERATE / LOW_RESEARCH_CONFIDENCE`
- critical research gaps

### Financial quality

- system financial decision
- effective decision after any explicit operator override
- financial-data coverage
- financial dimension labels

### Thesis

- thesis status
- Bull/Bear balance
- fragility
- Bull strength
- Bear strength
- unresolved questions

### Valuation

- valuation family/method
- Bear/Base/Bull scenarios
- Bear/Base/Bull comparison versus the captured run price

The investor should be able to disagree with any one of these dimensions without reverse-engineering a hidden weighted score.

---

## Decision readiness

The synthesis separately marks:

```text
READY_FOR_INVESTOR_REVIEW
NOT_READY_FOR_INVESTOR_REVIEW
```

`READY_FOR_INVESTOR_REVIEW` means the implemented upstream analytical stages are sufficiently complete to review the case.

Risk-dominated, contested or fragile cases can still be `READY_FOR_INVESTOR_REVIEW`: readiness means **complete enough to judge**, not attractive.

It is not a recommendation to invest.

---

## What must be true / invalidation

Where Bull/Bear semantic extraction provides the information, synthesis surfaces:

- key Bull assumptions;
- what must be true for the thesis to work;
- explicit invalidation conditions;
- strongest Bear points;
- unresolved questions;
- fragility flags.

If invalidation conditions are missing, the UI treats their absence as a research limitation, not as evidence that the thesis is safe.

---

## Investor Review

The system synthesis and user judgement are deliberately stored separately.

Optional investor stances in v1:

- `UNREVIEWED`
- `AGREE_WITH_SYSTEM`
- `NEED_MORE_RESEARCH`
- `WATCH_CLOSELY`
- `PASS_FOR_NOW`
- `HIGH_INTEREST`

The user can also record their own current conviction in that judgement:

- `LOW`
- `MEDIUM`
- `HIGH`

This user-entered conviction is not produced by the system and is not interpreted as a return probability.

Free-form notes are also retained.

Refreshing system synthesis preserves the separate Investor Review at the engine level.

---

## Price context

Valuation Intelligence v1 does not live-refresh market prices.

Therefore the synthesis must say **captured price**, not imply a live quote.

A later market-data mission should add timestamped/live price refresh before any monitoring/ranking layer relies heavily on valuation deltas.

---

## Definition of done for v1

Conviction & Decision Synthesis v1 is complete when it can:

- consume financial assessment;
- consume Research Confidence;
- consume Bull/Bear classification and fragility;
- consume Valuation Intelligence scenarios;
- expose upstream operator overrides;
- produce an explainable research decision state;
- prevent Bear/fragility/research gaps from being hidden by attractive valuation;
- prevent a very wide Bear scenario from automatically qualifying for high-priority status;
- list reasons and blockers;
- show unresolved questions;
- show what must be true;
- show thesis invalidation conditions when available;
- show what could strengthen/weaken the case;
- persist synthesis per company;
- preserve a separate optional Investor Review;
- avoid BUY/SELL, return probability and portfolio-weight output.

---

## What remains intentionally outside v1

- live market-price refresh;
- portfolio ranking;
- portfolio construction / position sizing;
- expected-return probabilities;
- automatic investment recommendations;
- continuous thesis monitoring;
- automated management promise-vs-delivery updates;
- learning from the investor's later outcomes/decisions.
