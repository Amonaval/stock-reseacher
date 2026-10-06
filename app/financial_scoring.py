import math

DIMENSIONS = ['growth','quality','balance_sheet','cash_flow','ownership','valuation']


def clamp(x, lo=0, hi=100):
    return max(lo,min(hi,x))


def score_high(v, bad, good):
    if v is None: return None
    if good == bad: return 50
    return clamp((v-bad)/(good-bad)*100)


def score_low(v, good, bad):
    if v is None: return None
    if bad == good: return 50
    return clamp((bad-v)/(bad-good)*100)


def avg(vals):
    vals=[v for v in vals if v is not None]
    return sum(vals)/len(vals) if vals else None


def financial_scorecard(r):
    growth=avg([
        score_high(r.get('sales_growth_3y'),0,20),
        score_high(r.get('profit_growth_3y'),0,25),
        score_high(r.get('sales_growth_5y'),0,15),
        score_high(r.get('profit_growth_5y'),0,20),
        score_high(r.get('sales_change'),-10,25),
        score_high(r.get('profit_change'),-20,30),
    ])
    quality=avg([
        score_high(r.get('roe'),5,22),
        score_high(r.get('roce'),5,25),
        score_high(r.get('opm'),5,25),
        score_high(r.get('roce_trend_3'),-5,8),
    ])
    balance=avg([
        score_low(r.get('debt_equity'),0.2,1.5),
        score_high(r.get('interest_coverage'),1.5,10),
        score_high(r.get('current_ratio'),0.8,2.0),
        score_low(r.get('debt_equity_change'),40,-25),
    ])
    cfo=r.get('cfo')
    profit=r.get('profit')
    cash_conversion=(cfo/profit*100) if cfo is not None and profit not in (None,0) else None
    cashflow=avg([
        score_high(cash_conversion,40,120),
        score_high(r.get('cfo_change'),-30,30),
        score_high(r.get('fcf'),0,1) if r.get('fcf') is not None else None,
    ])
    ownership=avg([
        score_high(r.get('promoter_holding'),25,65),
        score_low(r.get('pledge'),0,20),
        score_high((r.get('fii_holding') or 0)+(r.get('dii_holding') or 0),0,25) if (r.get('fii_holding') is not None or r.get('dii_holding') is not None) else None,
    ])
    pe_rel=(r.get('pe')/r.get('industry_pe')) if r.get('pe') is not None and r.get('industry_pe') not in (None,0) else None
    pb_rel=(r.get('pb')/r.get('industry_pb')) if r.get('pb') is not None and r.get('industry_pb') not in (None,0) else None
    valuation=avg([
        score_low(pe_rel,0.6,1.8),
        score_low(pb_rel,0.6,1.8),
        score_low(r.get('pe'),10,45) if pe_rel is None else None,
    ])
    dims={'growth':growth,'quality':quality,'balance_sheet':balance,'cash_flow':cashflow,'ownership':ownership,'valuation':valuation}
    available=[v for v in dims.values() if v is not None]
    coverage=len(available)/len(DIMENSIONS)
    weights={'growth':0.20,'quality':0.24,'balance_sheet':0.18,'cash_flow':0.14,'ownership':0.10,'valuation':0.14}
    weighted=sum(dims[k]*weights[k] for k in DIMENSIONS if dims[k] is not None)
    wsum=sum(weights[k] for k in DIMENSIONS if dims[k] is not None)
    base=weighted/wsum if wsum else 0
    # Missing data should reduce confidence, not silently become neutral.
    confidence=round(coverage*100,1)
    adjusted=base*(0.72+0.28*coverage)
    return {**{f'{k}_score': round(v,1) if v is not None else None for k,v in dims.items()},
            'financial_score':round(adjusted,1),'data_confidence':confidence,
            'cash_conversion':round(cash_conversion,1) if cash_conversion is not None else None}


def elimination_reasons(r, s):
    hard=[]; warnings=[]
    # Hard exclusions target financial distress / governance risk, not mere mediocrity.
    if r.get('pledge') is not None and r['pledge'] > 35: hard.append('Promoter pledge > 35%')
    if r.get('debt_equity') is not None and r['debt_equity'] > 2.5: hard.append('Debt/equity > 2.5')
    if r.get('interest_coverage') is not None and r['interest_coverage'] < 1: hard.append('Interest coverage < 1x')
    if r.get('roe') is not None and r['roe'] < 0: hard.append('Negative ROE')
    if r.get('roce') is not None and r['roce'] < 0: hard.append('Negative ROCE')
    if r.get('profit') is not None and r['profit'] < 0: warnings.append('Latest reported profit is negative')
    if s['data_confidence'] < 50: warnings.append('Financial-data coverage below 50%')
    if s['cash_flow_score'] is not None and s['cash_flow_score'] < 25: warnings.append('Weak cash-flow quality')
    if s['valuation_score'] is not None and s['valuation_score'] < 20: warnings.append('Valuation appears demanding vs available benchmarks')
    return hard,warnings


def rank_financial_universe(companies, target_keep=100):
    rows=[]
    for r in companies:
        s=financial_scorecard(r)
        hard,warnings=elimination_reasons(r,s)
        # V2 overlap remains a minor research-priority input; V3 financial quality dominates.
        overlap=min(100, (r.get('strategy_count',0)/7)*100)
        composite=s['financial_score']*0.88 + overlap*0.12
        x={**r,**s,'hard_exclusions':hard,'warnings':warnings,'v3_priority_score':round(composite,1)}
        x['status']='ELIMINATE' if hard else 'ELIGIBLE'
        rows.append(x)
    eligible=sorted([x for x in rows if x['status']=='ELIGIBLE'], key=lambda x:(x['v3_priority_score'],x['data_confidence']), reverse=True)
    for i,x in enumerate(eligible,1):
        x['financial_rank']=i
        if i<=target_keep: x['funnel_decision']='ADVANCE'
        elif i<=target_keep*1.5: x['funnel_decision']='WATCHLIST'
        else: x['funnel_decision']='HOLD_BACK'
    for x in rows:
        if x['status']=='ELIMINATE':
            x['financial_rank']=None; x['funnel_decision']='ELIMINATE'
    return sorted(rows,key=lambda x:(x['status']=='ELIGIBLE',x.get('v3_priority_score',0)),reverse=True)


def financial_report(rows):
    adv=[r for r in rows if r.get('funnel_decision')=='ADVANCE']
    elim=[r for r in rows if r.get('funnel_decision')=='ELIMINATE']
    lines=['# V3 Financial Intelligence Report','',f'- Companies analyzed: **{len(rows)}**',f'- Advance to research: **{len(adv)}**',f'- Hard-eliminated: **{len(elim)}**','',
           '## Top Financial Research Priorities','', '| Rank | Company | V3 Priority | Financial | Data confidence | Strategies |','|---:|---|---:|---:|---:|---:|']
    for r in adv[:40]:
        lines.append(f"| {r.get('financial_rank')} | {r.get('company')} | {r.get('v3_priority_score')} | {r.get('financial_score')} | {r.get('data_confidence')}% | {r.get('strategy_count',0)} |")
    lines += ['', '## Hard Eliminations','']
    for r in elim:
        lines.append(f"- **{r.get('company')}** — {'; '.join(r.get('hard_exclusions',[]))}")
    lines += ['', '## Guardrails','',
              '- V3 is a deterministic financial prioritization layer, not a buy/sell recommendation.',
              '- Missing data lowers confidence rather than being treated as neutral.',
              '- Strategy overlap from V2 has only a small weight; weak financials cannot be rescued by screen overlap.',
              '- Companies advancing from V3 still require V4+ document, management, risk, business-quality and valuation research.']
    return '\n'.join(lines)
