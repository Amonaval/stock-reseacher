# Operator Control — Product Contract

The researcher is autonomous by default, but the user remains in control.

## Principle

**Automation should remove repetitive work, not remove authority.**

Every major stage has three concepts:

1. **System proposal** — what the research engine recommends doing next.
2. **Optional review gate** — the user may inspect/refine/override the proposal.
3. **Effective run configuration** — what actually executes.

The system must preserve both the original proposal and the user's override in the research log.

## Strategy control

A generated master strategy is a proposal derived from historical methodology, not an immutable rule.

Each strategy preserves:

- generated name
- generated philosophy/purpose
- generated query
- methodology-support evidence
- user's working name
- user's working philosophy
- user's tuned query
- enabled/disabled state
- user notes

Strategy profiles are portable JSON files and can be exported/imported across runs.

Recommended workflow:

```text
Analyze methodology
      ↓
Generated strategies
      ↓
Review / edit philosophy and thresholds
      ↓
Preview one query
      ↓
Refine if too broad/narrow
      ↓
Save/export profile
      ↓
Run enabled strategies
```

## Candidate review

After screening, the user may:

- require a minimum number of matched strategies
- cap the number of companies entering financial analysis
- manually include/exclude individual companies

The original candidate universe remains available for review.

## Financial-stage review

Financial analysis proposes decisions such as ADVANCE, WATCHLIST, DATA_RETRY or ELIMINATE.

Before expensive company research, the user can override membership.

The app preserves:

- `system_decision`
- `system_reason`
- effective user-reviewed decision

A user override must be visible in the research log.

## Research-depth control

Structured, targeted, deep and Bull/Bear research budgets are configurable. They are capacity limits, not investment thresholds.

The user may also explicitly choose which researched companies enter the Bull/Bear challenge.

## UI structure

The main **Research** page remains simple and autonomous.

The **Operator Control** page is the optional cockpit for:

- strategy editing
- strategy preview
- profile import/export
- candidate pruning
- financial-stage overrides
- research-depth budgets
- Bull/Bear selection

The user should never be forced to operate every control in order to run research.
