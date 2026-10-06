# Product Constitution

## Purpose

Build an autonomous-but-controllable equity research system that helps an investor move from **idea generation to evidence-backed conviction** without becoming a black box.

The product must save research time, improve decision quality, make uncertainty visible, and preserve investor control.

## Constitutional Principles

### 1. Evidence before opinion
Every material conclusion must be traceable to data, a filing, a transcript, a company document, an exchange disclosure, or an explicitly labeled inference.

Never present an unsupported model opinion as fact.

### 2. Autonomy is a default, not a loss of authority
The system should execute the workflow automatically when desired, but the investor must be able to review, edit, override, pause, retry, exclude, include, or rerun at every important gate.

System proposal and user override must both remain visible.

### 3. No false precision
Scores are internal prioritization aids, not truth.

The UI should lead with:
- decision
- why
- evidence coverage
- risks
- missing information
- next action

Numeric scores belong in advanced details unless they materially help the investor.

### 4. Missing data is a research task
Missing information must never silently become neutral or zero.

If evidence is incomplete, the system should say so and generate a retry/research action.

### 5. Research depth should increase as the universe shrinks
Spend little effort on hundreds of candidates and much more effort on finalists.

Typical pattern:

Screening -> financial triage -> business research -> deep research -> adversarial challenge -> valuation -> conviction.

### 6. Preserve the full decision trail
For every company, retain:
- why it entered the universe
- strategies matched
- financial observations
- documents reviewed
- evidence extracted
- decisions made
- overrides made
- reasons it advanced, paused, or was held
- unresolved questions

### 7. Distinguish different kinds of confidence
Do not collapse these into one score:
- methodology confidence
- data coverage
- evidence quality
- research readiness
- thesis strength
- valuation attractiveness
- conviction

### 8. Challenge the thesis
The system must actively search for reasons the investment thesis could be wrong.

Bull and Bear cases should be independently constructed before a neutral challenge layer compares them.

### 9. Separate facts, management claims, and inference
Every research item should identify whether it is:
- reported fact
- management claim/guidance
- third-party observation
- model inference

Management commentary is not automatically fact.

### 10. User philosophy is a first-class asset
The product should learn from the investor's historical screens, rules, overrides, and decisions.

Generated strategies must remain editable, versionable, exportable, and importable.

### 11. Provider independence
Screener is an initial POC adapter, not the product architecture.

The intelligence layer must support later adapters for NSE, BSE, exchange filings, company IR, financial-data providers, and other legitimate sources.

### 12. Explain every expensive action
Before spending deep-research effort on a company, the system should be able to answer:

> Why are we researching this company more deeply than the others?

### 13. No hidden eliminations
A company that does not advance should be retained as HOLD / RETRY / WATCH rather than silently disappearing.

### 14. Investor workflow over engineering workflow
The UI must use investor language such as:
- Screen ideas
- Review candidates
- Analyze financials
- Research business
- Challenge thesis
- Value company
- Build shortlist

Avoid exposing internal version names as the primary workflow.

### 15. Safety boundary
The product is a research and decision-support system, not an autonomous trading system.

No order execution or buy/sell action should occur without a separate explicit product decision and user authorization.

## Product Test

Before adding any feature, ask:

1. Does this save a serious investor meaningful time?
2. Does it improve evidence quality or decision quality?
3. Is the result understandable without reading source code?
4. Can the user inspect and override it?
5. Does it expose uncertainty instead of hiding it?
6. Is it differentiated from simply showing another score or dashboard?

If the answer is mostly no, do not build it.
