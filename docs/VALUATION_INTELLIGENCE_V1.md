# Valuation Intelligence v1

## Purpose

Valuation Intelligence translates sufficiently researched companies into **explicit Bear / Base / Bull valuation scenarios**.

It is deliberately not a target-price generator and not an investment-recommendation engine.

The constitutional order is:

```text
Research quality
    ↓
Business-model / valuation-family selection
    ↓
Explicit valuation assumptions
    ↓
Bear / Base / Bull scenarios
    ↓
Sensitivity / what changes the valuation
```

A valuation number is not allowed to hide weak research.

---

## Research-confidence gate

Automatic valuation requires the company's Research Confidence result to be:

```text
READY_FOR_VALUATION_CONTEXT
```

This means the evidence-quality contract has no current critical gap and has enough financial, fundamental and downside evidence to support valuation context.

The operator may explicitly override the gate for exploration. An override:

- does not alter Research Confidence;
- remains visible as a warning;
- must not be interpreted as a fully supported valuation.

---

## Supported valuation families

### 1. General / quality business

Method:

```text
normalized EPS × scenario P/E multiple
```

Normalized EPS uses the median of the latest three positive annual EPS observations where possible.

The base multiple is anchored, in priority order, to available contextual data:

- 5-year P/E;
- industry P/E;
- current P/E only as an explicitly labeled fallback.

Bear and Bull multiples apply scenario haircuts/premiums around the base anchor unless the operator supplies explicit values.

This is a relative/normalized earnings framework, not a DCF.

### 2. Bank / NBFC / lending financial business

Method:

```text
justified P/B = (sustainable ROE - long-term growth) / (cost of equity - long-term growth)
```

Bear / Base / Bull scenarios vary:

- sustainable ROE;
- long-term growth;
- cost of equity.

Fair value is:

```text
book value per share × justified P/B
```

The assumptions are visible and editable.

### 3. Insurance

Valuation Intelligence v1 does **not** substitute generic P/E or P/B for insurers.

A proper insurer framework needs data such as:

- embedded value;
- value of new business (VNB);
- VNB margin;
- insurance-specific growth / persistency / solvency context.

If an insurer is detected, v1 returns an explicit data/model gap instead of manufacturing a fair value.

### 4. Cyclical / commodity business

Method:

```text
longer normalized EPS × conservative scenario P/E
```

The model uses up to five positive annual EPS observations and applies a wider Bear haircut and a smaller Bull premium than the general framework.

This is intended to reduce the common error of valuing peak-cycle earnings as if they were permanent.

### 5. Utility / regulated / asset-heavy business

Valuation Intelligence v1 currently uses a more conservative normalized-earnings scenario framework.

This is an interim model. Future versions should add business-specific EV/EBITDA, regulated-asset-base or cash-flow approaches when the required data is available.

---

## Valuation-family classification

The automatic classifier uses research evidence and company name/business terminology.

Examples of signals:

- bank/NBFC: NIM, NPA, deposits, advances, loan book, capital adequacy;
- insurance: embedded value, VNB, insurance premium, solvency;
- cyclical: steel, mining, commodity, refinery, shipping-cycle terminology;
- utility/regulated: tariff, transmission, power generation, regulated return.

Classification is intentionally visible and operator-overridable.

Automatic classification is a convenience, not a hidden source of truth.

---

## Investor-facing output

A successful valuation should show:

```text
Current price

Bear fair-value scenario
Base fair-value scenario
Bull fair-value scenario

Upside/downside vs current price

Valuation family
Method
Normalized earnings / book value basis
Historical / industry multiple anchors
Scenario assumptions
Research-confidence state
Warnings / model limitations
What would change the valuation
```

The product should favor ranges and assumptions over false point precision.

---

## Important limitations

Valuation Intelligence v1 does not yet provide:

- full DCF / FCFF / FCFE;
- EV/EBITDA modeling;
- sum-of-the-parts;
- insurer embedded-value acquisition;
- real-estate NAV;
- commodity-cycle normalized EBITDA;
- sector peer-set construction;
- live consensus estimates;
- forward EPS estimates;
- automated cost-of-capital estimation;
- scenario probabilities;
- target prices;
- investment recommendations.

The engine uses the financial and research data already present in the current ResearchRun.

---

## Constitution rules

1. Research confidence is not investment conviction.
2. Valuation does not run automatically through a critical research-quality gap.
3. Sector/business-model differences must be respected.
4. Unsupported business models must return a model/data gap instead of a fake number.
5. Current market multiples are fallback context, not intrinsic value.
6. Every output must expose its assumptions.
7. Bear / Base / Bull are scenarios, not probabilities.
8. Fair value is a range of assumption-dependent outcomes, not a prediction.

---

## Definition of done for v1

Valuation Intelligence v1 is complete when it can:

- consume the Research Confidence gate;
- classify/override a valuation family;
- value general/quality businesses through normalized earnings;
- value banks/NBFCs through justified P/B;
- normalize cyclical earnings more conservatively;
- explicitly block unsupported insurer valuation;
- expose scenario assumptions and method selection;
- persist company valuation results;
- show current price vs Bear / Base / Bull scenarios;
- keep warnings and operator overrides visible.
