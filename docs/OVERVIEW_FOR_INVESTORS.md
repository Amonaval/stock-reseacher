# What is Personal AI Stock Researcher?

## In plain stock-market language

Most stock research starts with a large universe and asks questions such as:

- Is the business growing?
- Is return on capital strong?
- Is debt manageable?
- Is valuation sensible relative to the industry and growth?
- Is promoter/shareholder behaviour healthy?
- Are recent results improving or deteriorating?
- What does management say, and has management historically delivered?
- What are the hidden risks that a bullish screen will not show?

This project tries to automate that complete research journey while keeping the reasoning visible.

## Why it was started

The initial input was a large collection of personal Screener.in screens built over years. Those screens contain useful investing instincts, but they are fragmented across many queries.

The system first learns those recurring ideas, then converts them into a smaller number of reusable research strategies. It does **not** assume the old screens are automatically correct; they are treated as one source of screening knowledge.

## What makes it different from a normal screener

A normal stock screener typically stops here:

```text
Query → 87 companies
```

This project is intended to continue:

```text
87 companies
   ↓
Financial quality + trends
   ↓
Research filings/reports
   ↓
Understand business + management + risks
   ↓
Research gaps and contradictions
   ↓
Deep research on fewer companies
   ↓
Independent Bull case
Independent Bear case
   ↓
Valuation and conviction (planned)
   ↓
Ranked portfolio proposal (planned)
```

## Progressive research, not equal research

It is wasteful to read 20 documents for every company in a 300-stock universe. The system therefore spends cheap computation first, and expensive research only as the list becomes smaller.

A typical target funnel is:

```text
300 candidates
→ 120 financially interesting
→ 60 researched
→ 30 deep research
→ 15 maximum-depth/adversarial research
→ 10 finalists
```

The exact numbers are configurable.

## Explainability is a first-class requirement

Every narrowing stage should answer:

- Which company advanced?
- Which company was held/eliminated?
- Which evidence mattered?
- What data is missing?
- What would change the conclusion?

Companies that do not advance are retained for future re-evaluation rather than silently deleted.

## Is it giving stock recommendations today?

Not yet. The project currently reaches adversarial Bull/Bear research. Dedicated valuation, evidence-confidence, conviction, ranking and portfolio construction are still planned.

Even after those layers are built, the output should be treated as a research proposal requiring human judgment, not guaranteed investment advice.
