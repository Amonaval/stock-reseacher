# How the Research Pipeline Works

## Stage 1 — Methodology Mining

Input: historical Screener screens.

The system parses conditions, normalizes parameters, studies thresholds and combinations, and identifies recurring strategy archetypes.

Example ideas:

- quality at relative valuation
- growth at reasonable price
- earnings acceleration
- re-rating / turnaround
- ownership confirmation
- balance-sheet/cash-flow value
- emerging small/mid-cap quality

## Stage 2 — Master Strategy Generation

The system creates a smaller set of master strategies and keeps provenance explaining which historical screens/conditions support each rule.

A methodology-confidence number means **support from historical screen behaviour**, not probability that a stock will outperform.

## Stage 3 — Candidate Universe

Strategy result sets are merged and deduplicated.

The system keeps:

- company identity
- strategies matched
- overlap count
- available snapshot ratios
- provenance to the source strategy/result

Strategy overlap is a research-priority signal, not a conviction score.

## Stage 4 — Financial Intelligence

The V3 layer normalizes available financial information and evaluates:

- growth
- quality / returns
- balance sheet
- cash flow
- ownership/governance
- valuation
- missing-data confidence

V6.1 adds automatic Screener enrichment so a candidate-result file can be enriched with multi-period history instead of requiring the user to manually prepare per-company financial files.

## Stage 5 — Research Memory

For survivors, the system builds persistent knowledge from sources such as:

- annual reports
- quarterly results
- investor presentations
- earnings-call material
- exchange filings
- credit-rating rationales

Evidence retains document/date/page/source metadata where available.

## Stage 6 — Autonomous Source Acquisition

The source layer can discover likely research documents, score their authority, deduplicate them and fetch only the highest-value sources within a research budget.

The optional local crawler is off by default and intended only as a constrained fallback.

## Stage 7 — Deep Research Funnel

Research depth increases as the company count decreases:

- L1 Structured
- L2 Targeted
- L3 Deep
- L4 Maximum

A HOLD is not permanent rejection. It usually means missing evidence or being outside the current research budget.

## Stage 8 — Bull/Bear Adversarial Research

Every finalist gets two independent arguments:

- Bull researcher: strongest evidence-supported upside thesis
- Bear/forensic researcher: strongest evidence-supported failure/risk thesis

A neutral challenge layer then identifies contradictions, unresolved questions and thesis fragility.

## What comes after this

Planned:

1. Evidence confidence
2. Valuation intelligence
3. Conviction engine
4. Final ranking
5. ₹1 lakh portfolio construction
6. Continuous monitoring
7. Learning from past decisions/outcomes
