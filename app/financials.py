import io
import math
import re
from collections import defaultdict
from statistics import median
import pandas as pd

ALIASES = {
    'company': ['company','name','company name','stock name','security name'],
    'symbol': ['symbol','ticker','nse code','bse code','code'],
    'year': ['year','fy','financial year','period','date'],
    'sales': ['sales','revenue','revenue from operations','total revenue'],
    'profit': ['net profit','profit after tax','pat','profit'],
    'eps': ['eps','earnings per share'],
    'opm': ['opm','operating profit margin','operating margin'],
    'roe': ['roe','return on equity'],
    'roce': ['roce','return on capital employed'],
    'debt_equity': ['debt to equity','debt/equity','d/e','debt equity'],
    'interest_coverage': ['interest coverage','interest coverage ratio'],
    'cfo': ['cash from operations','cash flow from operations','cfo','operating cash flow'],
    'fcf': ['free cash flow','fcf'],
    'current_ratio': ['current ratio'],
    'promoter_holding': ['promoter holding','promoter %'],
    'pledge': ['pledged percentage','pledge','promoter pledge'],
    'fii_holding': ['fii holding','fii %'],
    'dii_holding': ['dii holding','dii %'],
    'pe': ['price to earning','pe','p/e'],
    'industry_pe': ['industry pe'],
    'pb': ['price to book value','price to book','pb','p/b'],
    'industry_pb': ['industry pbv','industry pb','industry price to book'],
    'market_cap': ['market capitalization','market cap','mcap','mar cap rs.cr.','mar cap rs.cr'],
    'price': ['current price','price','cmp','cmp rs.','cmp rs'],
    'sales_growth_3y': ['sales growth 3years','sales growth 3y'],
    'profit_growth_3y': ['profit growth 3years','profit growth 3y'],
    'sales_growth_5y': ['sales growth 5years','sales growth 5y'],
    'profit_growth_5y': ['profit growth 5years','profit growth 5y'],
    'return_3y': ['return over 3years','return 3y'],
    'up_from_52w_low': ['up from 52w low'],
    'down_from_52w_high': ['down from 52w high'],
}

PERCENT_METRICS = {'opm','roe','roce','promoter_holding','pledge','fii_holding','dii_holding','sales_growth_3y','profit_growth_3y','sales_growth_5y','profit_growth_5y','return_3y','up_from_52w_low','down_from_52w_high'}


def _norm(s):
    return re.sub(r'\s+', ' ', str(s or '').strip().lower())


def _find_col(columns, key):
    nmap = {_norm(c): c for c in columns}
    for alias in ALIASES[key]:
        if alias in nmap:
            return nmap[alias]
    return None


def _num(v):
    if v is None or (isinstance(v,float) and math.isnan(v)):
        return None
    if isinstance(v,(int,float)):
        return float(v)
    s = str(v).strip().replace(',','')
    if not s or s.lower() in {'nan','na','n/a','none','-'}:
        return None
    s = s.replace('%','')
    try:
        return float(s)
    except Exception:
        m = re.search(r'-?\d+(?:\.\d+)?', s)
        return float(m.group()) if m else None


def read_financial_file(uploaded_file):
    raw = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    if name.endswith(('.xlsx','.xls')):
        df = pd.read_excel(io.BytesIO(raw))
    elif name.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(raw))
    else:
        raise ValueError('Upload CSV/XLS/XLSX financial data.')
    return normalize_financial_dataframe(df)


def normalize_financial_dataframe(df: pd.DataFrame):
    cols = {k:_find_col(df.columns,k) for k in ALIASES}
    if not cols['company']:
        raise ValueError("Financial file must contain a company/name column.")

    records=[]
    for _,row in df.iterrows():
        r={'company':str(row[cols['company']]).strip() if cols['company'] else '',
           'symbol':str(row[cols['symbol']]).strip() if cols['symbol'] else '',
           'year':str(row[cols['year']]).strip() if cols['year'] else ''}
        for k in ALIASES:
            if k in {'company','symbol','year'}: continue
            r[k] = _num(row[cols[k]]) if cols[k] else None
        if r['company']:
            records.append(r)
    return records


def _cagr(start, end, periods):
    if start is None or end is None or periods <= 0 or start <= 0 or end <= 0:
        return None
    return ((end/start)**(1/periods)-1)*100


def _pct_change(old,new):
    if old is None or new is None or old == 0:
        return None
    return (new-old)/abs(old)*100


def build_company_histories(rows):
    grouped=defaultdict(list)
    for r in rows:
        key=_norm(r.get('symbol') or r.get('company'))
        if key: grouped[key].append(r)

    out=[]
    for key,items in grouped.items():
        # Preserve input ordering but try to sort year labels naturally.
        def ykey(r):
            vals=re.findall(r'\d{4}', str(r.get('year','')))
            return int(vals[-1]) if vals else -1
        items=sorted(items,key=ykey)
        latest=items[-1].copy()
        latest['history']=items
        latest['periods']=len(items)
        for metric in ['sales','profit','eps','opm','roe','roce','debt_equity','cfo','fcf']:
            vals=[r.get(metric) for r in items if r.get(metric) is not None]
            latest[f'{metric}_latest']=vals[-1] if vals else latest.get(metric)
            latest[f'{metric}_previous']=vals[-2] if len(vals)>=2 else None
            latest[f'{metric}_change']=_pct_change(vals[-2],vals[-1]) if len(vals)>=2 else None
            if len(vals)>=3:
                latest[f'{metric}_trend_3'] = vals[-1]-vals[-3]
            else:
                latest[f'{metric}_trend_3'] = None
        sales_vals=[r.get('sales') for r in items if r.get('sales') is not None]
        profit_vals=[r.get('profit') for r in items if r.get('profit') is not None]
        if latest.get('sales_growth_3y') is None and len(sales_vals)>=4:
            latest['sales_growth_3y']=_cagr(sales_vals[-4],sales_vals[-1],3)
        if latest.get('profit_growth_3y') is None and len(profit_vals)>=4:
            latest['profit_growth_3y']=_cagr(profit_vals[-4],profit_vals[-1],3)
        if latest.get('sales_growth_5y') is None and len(sales_vals)>=6:
            latest['sales_growth_5y']=_cagr(sales_vals[-6],sales_vals[-1],5)
        if latest.get('profit_growth_5y') is None and len(profit_vals)>=6:
            latest['profit_growth_5y']=_cagr(profit_vals[-6],profit_vals[-1],5)
        out.append(latest)
    return out


def merge_candidate_context(companies, candidates):
    cmap={_norm(c.get('company')):c for c in candidates}
    smap={_norm(c.get('symbol')):c for c in candidates if c.get('symbol')}
    out=[]
    for r in companies:
        match=smap.get(_norm(r.get('symbol'))) or cmap.get(_norm(r.get('company')))
        x=dict(r)
        if match:
            x['strategy_count']=match.get('strategy_count',0)
            x['strategies']=match.get('strategies',[])
            x['research_priority']=match.get('research_priority_score', match.get('research_priority',0))
        else:
            x['strategy_count']=0; x['strategies']=[]; x['research_priority']=0
        out.append(x)
    return out
