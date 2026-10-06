# Company Research Engine

## Purpose

The Company Research Engine converts a financially interesting company into an evidence-backed research dossier.

It exists because **screening is not research**. A company can look attractive on ratios and still fail on business quality, cash conversion, governance, management execution, competition or durability.

The engine therefore answers five investor questions:

1. What did the researcher attempt?
2. What authoritative sources were acquired?
3. What did those sources actually say?
4. What remains unknown or weakly evidenced?
5. What should happen next?

A crawler finishing successfully is not considered research completion.

---

## Research missions

Every researched company is evaluated across explicit fundamental-analyst missions:

1. **Business model & economics**
   - products/services
   - revenue model
   - customer structure
   - economic engine

2. **Growth drivers & durability**
   - capacity
   - demand
   - new products
   - order book / expansion
   - temporary vs durable growth

3. **Cash conversion & working capital**
   - CFO
   - receivables
   - inventory
   - working-capital requirements
   - free cash flow

4. **Management & capital allocation**
   - guidance
   - execution
   - acquisitions
   - capex
   - allocation discipline

5. **Governance**
   - related parties
   - pledges
   - auditors
   - resignations
   - qualified opinions
   - disclosure issues

6. **Business / financial risks**
   - customer concentration
   - debt
   - regulatory exposure
   - competition
   - raw materials
   - cyclicality
   - execution risk

7. **Catalysts & milestones**
   - commissioning
   - approvals
   - commercial production
   - launches
   - large orders
   - acquisitions

These missions are not investment scores. They are a checklist for evidence coverage.

---

## Source acquisition

### Current POC source path

The initial adapter is Screener because the product is currently proving usefulness through a logged-in local Screener session.

For every company the engine:

1. starts from the exact company URL captured during screening;
2. discovers research-document links exposed on that company page;
3. optionally expands discovery through a configured web-search provider;
4. assigns source authority / document-type scores;
5. deduplicates URLs;
6. fetches only a bounded number of high-value sources per document type.

The engine does **not** fetch every discovered link.

This controls noise, bandwidth and rate-limit exposure.

### Preferred evidence classes

- annual report
- quarterly result
- investor presentation
- earnings/concall transcript
- exchange filing
- credit-rating rationale
- shareholding information

Long term, authoritative NSE/BSE/company-IR adapters should become first-class source providers.

---

## Source-attempt ledger

Every company persists a source-attempt ledger.

Each attempt records:

- timestamp
- discovery vs fetch stage
- provider
- status: SUCCESS / FAILED / SKIPPED
- document type
- source-quality score
- URL
- message / failure reason

This ensures a missing annual report is not represented as "no risk found". It remains visible as a source gap.

---

## Evidence extraction

Fetched documents are normalized and chunked.

Evidence extraction supports two modes:

### Deterministic mode

Keyword/theme extraction is used to create source excerpts for:

- business model
- management
- growth
- risk
- cash flow
- governance
- catalysts

This mode does not require an LLM.

### Semantic LLM mode

When an LLM is configured, the engine asks it to classify evidence while remaining source-bound.

The LLM is instructed to avoid inventing missing facts.

Evidence items preserve:

- document
- page
- evidence ID
- theme
- type
- finding/claim
- source excerpt
- confidence

---

## Investor dossier

The dossier is the primary research output.

It contains:

- research state
- document coverage
- evidence quality
- research readiness
- analyst-mission coverage
- findings grouped by mission
- risk/governance findings
- catalysts
- management claims requiring verification
- open research questions
- explicit next action

The raw evidence ledger remains available underneath.

---

## Research states

### `SOURCE_GAP`

The company does not yet have enough usable documents/evidence.

Meaning:

> Research could not yet establish an evidence base.

It does **not** mean the company is bad.

### `RESEARCH_INCOMPLETE`

Some evidence exists, but important document classes or analyst missions remain uncovered.

Meaning:

> We know something, but not enough to trust a deep thesis.

### `EVIDENCE_READY`

The current company-research contract is satisfied across required source classes and analyst missions.

Meaning:

> The company is ready for progressive deep research / adversarial challenge.

It does **not** mean the stock is attractive or should be bought.

---

## User controls

The Research Evidence page allows the operator to control:

- which surviving companies are researched or retried;
- maximum sources fetched per document type;
- minimum source-quality score;
- whether semantic LLM extraction is enabled.

This follows the product constitution:

> Autonomous by default, investor-controlled when desired.

---

## What is intentionally not solved yet

The current engine is not the final institutional research stack.

Still pending / future improvements:

- first-class NSE/BSE source adapters
- direct company-IR adapter
- stronger transcript acquisition
- scanned PDF/OCR support
- temporal management promise-vs-delivery matching
- industry/competitor graph
- structured customer/supplier concentration analysis
- sector-specific accounting rules
- source freshness policies
- deeper contradiction resolution
- valuation linkage

These should be evaluated during the strategic review before further expansion.
