import re
from collections import Counter, defaultdict


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip()).lower()


def fmt_num(v):
    if v is None:
        return ""
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _find_abs(intel, parameter, operator):
    p = norm(parameter)
    for r in intel.get("absolute_thresholds", []):
        if r["parameter"] == p and r["operator"] == operator:
            return r
    return None


def _find_rel(intel, parameter, operator, benchmark):
    p, b = norm(parameter), norm(benchmark)
    for r in intel.get("relative_thresholds", []):
        if r["parameter"] == p and r["operator"] == operator and r["benchmark"] == b:
            return r
    return None


def _choose_abs(intel, parameter, operator, preference="median", fallback=None):
    r = _find_abs(intel, parameter, operator)
    if not r:
        return fallback, None
    if preference == "mode" and r.get("most_common"):
        value = r["most_common"][0][0]
    elif preference == "p25":
        value = r.get("p25")
    elif preference == "p75":
        value = r.get("p75")
    else:
        value = r.get("median")
    return value, r


def _choose_rel(intel, parameter, operator, benchmark, fallback=None):
    r = _find_rel(intel, parameter, operator, benchmark)
    return (r.get("median_multiplier"), r) if r else (fallback, None)


def _rule(parameter, operator, rhs, category, role="hard", evidence=None, rationale=""):
    q = f"{parameter} {operator} {rhs}"
    return {"parameter": parameter,"operator": operator,"rhs": rhs,"query": q,"category": category,"role": role,"evidence": evidence or {},"rationale": rationale}


def _abs_rule(intel, parameter, operator, category, preference="median", fallback=None, role="hard", rationale=""):
    value, stat = _choose_abs(intel, parameter, operator, preference, fallback)
    if value is None:
        return None
    return _rule(parameter, operator, fmt_num(value), category, role, stat or {"fallback": True}, rationale)


def _rel_rule(intel, parameter, operator, benchmark, category, fallback=None, role="hard", rationale=""):
    mult, stat = _choose_rel(intel, parameter, operator, benchmark, fallback)
    if mult is None:
        return None
    rhs = benchmark if abs(mult - 1) < 1e-9 else f"{benchmark} * {fmt_num(mult)}"
    return _rule(parameter, operator, rhs, category, role, stat or {"fallback": True}, rationale)


def _source_support(screens, wanted_params, top_n=8):
    wanted = {norm(x) for x in wanted_params}; scored = []
    for s in screens:
        query = str(s.get("query", "")); qn = norm(query); hits = sorted([p for p in wanted if p and p in qn])
        if hits: scored.append((len(hits), s.get("title", ""), s.get("url", ""), hits, query))
    scored.sort(key=lambda x: (-x[0], x[1].casefold()))
    return [{"title": t, "url": u, "matched_parameters": h, "query": q} for _, t, u, h, q in scored[:top_n]]


def _cooccurrence_support(intel, params):
    params = sorted({norm(x) for x in params}); pair_counts = intel.get("pair_counts", Counter()); triple_counts = intel.get("triple_counts", Counter()); pairs=[]; triples=[]
    for i in range(len(params)):
        for j in range(i+1,len(params)):
            key=(params[i],params[j]); n=pair_counts.get(key,0)
            if n: pairs.append({"parameters": list(key), "screens": n})
    pairs.sort(key=lambda x:-x["screens"])
    for i in range(len(params)):
        for j in range(i+1,len(params)):
            for k in range(j+1,len(params)):
                key=(params[i],params[j],params[k]); n=triple_counts.get(key,0)
                if n: triples.append({"parameters":list(key),"screens":n})
    triples.sort(key=lambda x:-x["screens"])
    return pairs[:10],triples[:8]


def _confidence(strategy,total_screens):
    sources=strategy.get("source_screens",[]); pairs=strategy.get("cooccurrence_pairs",[]); rules=strategy.get("rules",[]); evidence_rules=[r for r in rules if not r.get("evidence",{}).get("fallback")]
    evidence_ratio=len(evidence_rules)/max(1,len(rules)); rule_supports=[]
    for r in evidence_rules:
        count=float(r.get("evidence",{}).get("count",0) or 0); rule_supports.append(min(1.0,count/max(1.0,total_screens*0.30)))
    rule_support=sum(rule_supports)/max(1,len(rule_supports)); source_ratio=min(1.0,len(sources)/8.0); pair_strength=min(1.0,sum(x["screens"] for x in pairs[:4])/max(1,total_screens*2.0))
    return round(100*(0.30*evidence_ratio+0.30*rule_support+0.25*pair_strength+0.15*source_ratio),1)


def _make_strategy(sid,name,purpose,rules,screens,intel,notes):
    rules=[r for r in rules if r]; params=[r["parameter"] for r in rules]; source_screens=_source_support(screens,params); pairs,triples=_cooccurrence_support(intel,params); hard=[r["query"] for r in rules if r["role"]=="hard"]; ranking=[r["query"] for r in rules if r["role"]=="ranking"]
    result={"id":sid,"name":name,"purpose":purpose,"rules":rules,"hard_query":" AND\n".join(hard),"ranking_signals":ranking,"source_screens":source_screens,"cooccurrence_pairs":pairs,"cooccurrence_triples":triples,"notes":notes}; result["evidence_confidence"]=_confidence(result,len(screens)); return result


def generate_master_strategies(screens, analysis):
    intel=analysis["intelligence"]
    pe_ind=_rel_rule(intel,"Price to Earning","<","Industry PE","Valuation",1.4); pb_ind=_rel_rule(intel,"Price to book value","<","Industry PBV","Valuation",1.5); pe_hist=_rel_rule(intel,"Price to Earning","<","Historical PE 3Years","Valuation",1.25)
    roe=_abs_rule(intel,"Return on equity",">","Quality / Returns","mode",10); roe3=_abs_rule(intel,"Average return on equity 3Years",">","Quality / Returns","mode",10); roce=_abs_rule(intel,"Return on capital employed",">","Quality / Returns","median",10); debt=_abs_rule(intel,"Debt to equity","<","Balance Sheet / Leverage","median",0.6); pledge=_abs_rule(intel,"Pledged percentage","<","Ownership","mode",10); icr=_abs_rule(intel,"Interest Coverage Ratio",">","Balance Sheet / Leverage","mode",3); piot=_abs_rule(intel,"Piotroski score",">","Quality / Returns","mode",3); gf=_abs_rule(intel,"G Factor",">","Quality / Returns","mode",3); opm=_abs_rule(intel,"OPM",">","Profitability / Margins","mode",10); up52=_abs_rule(intel,"Up from 52w low","<","Momentum / Technical","median",50); down52=_abs_rule(intel,"Down from 52w high",">","Momentum / Technical","median",12); ret3=_abs_rule(intel,"Return over 3Years","<","Momentum / Technical","median",40); rsi=_abs_rule(intel,"RSI","<","Momentum / Technical","median",60,role="ranking")
    sales3=_abs_rule(intel,"Sales growth 3Years",">","Growth","median",5); profit3=_abs_rule(intel,"Profit growth 3Years",">","Growth","median",7); sales5=_abs_rule(intel,"Sales growth 5Years",">","Growth","median",5); yoy_sales=_abs_rule(intel,"YOY Quarterly sales growth",">","Growth","p75",6); yoy_profit=_abs_rule(intel,"YOY Quarterly profit growth",">","Growth","median",5); peg=_abs_rule(intel,"PEG Ratio","<","Valuation","median",1.8); public=_abs_rule(intel,"Public holding","<","Ownership","median",40); curr=_abs_rule(intel,"Current ratio",">","Balance Sheet / Leverage","median",1.5); pfcf=_abs_rule(intel,"Price to Free Cash Flow","<","Cash Flow","median",10); mcap=_abs_rule(intel,"Market Capitalization",">","Size / Universe","median",500); vol_week=_rel_rule(intel,"Volume 1Week average",">","Volume 1Month average","Momentum / Technical",1.15,role="ranking"); vol_now=_rel_rule(intel,"Volume",">","Volume 1Week average","Momentum / Technical",1.3,role="ranking")
    strategies=[]
    strategies.append(_make_strategy("S1","Quality at Relative Value","Find financially sound businesses whose valuation is reasonable versus their industry, while excluding leverage and governance stress.",[mcap,pe_ind,pb_ind,roe,roce,debt,icr,pledge,public],screens,intel,"Core defensive/value-quality strategy."))
    strategies.append(_make_strategy("S2","Growth at Reasonable Price","Find companies with sustained multi-year growth and acceptable quality without paying an excessive growth premium.",[mcap,sales3,profit3,sales5,roe3,debt,peg,pe_ind,pledge],screens,intel,"Growth plus valuation and quality."))
    strategies.append(_make_strategy("S3","Earnings Acceleration + Participation","Surface companies where recent sales/profit acceleration is supported by liquidity/participation signals while retaining basic financial safeguards.",[mcap,yoy_sales,yoy_profit,roe,debt,pledge,pe_ind,vol_week,vol_now,rsi],screens,intel,"Volume/RSI remain secondary signals."))
    strategies.append(_make_strategy("S4","Fundamental Re-rating / Turnaround","Look for financially improving or neglected companies with quality-score confirmation and room for valuation/price re-rating.",[mcap,piot,gf,opm,debt,pledge,pe_hist,up52,down52,ret3],screens,intel,"Combines quality-score checks with historical valuation and price dislocation."))
    strategies.append(_make_strategy("S5","Ownership + Quality Confirmation","Prioritize businesses with concentrated/stable ownership characteristics while demanding balance-sheet and profitability quality.",[mcap,public,pledge,roe,roce,debt,icr,pe_ind,rsi],screens,intel,"Preserves ownership/governance emphasis."))
    strategies.append(_make_strategy("S6","Cash-flow / Balance-sheet Value","Find companies whose valuation is supported by cash generation and balance-sheet resilience rather than accounting earnings alone.",[mcap,curr,debt,icr,roce,pfcf,pe_ind,pledge],screens,intel,"Complementary cash-flow style."))
    smallcap=_abs_rule(intel,"Market Capitalization",">","Size / Universe","p25",100)
    strategies.append(_make_strategy("S7","Emerging Small/Midcap Quality","Search the broader small/midcap universe for companies that combine acceptable quality, growth, leverage and valuation before deeper research.",[smallcap,sales3,profit3,roe,roce,debt,pledge,pe_ind,up52],screens,intel,"Uses lower market-cap quartile as discovery floor."))
    return strategies


def strategy_markdown(strategies, selected_count):
    lines=["# V2 — Master Strategy Intelligence","",f"Derived from **{selected_count} explicitly selected screens**.","","> These are methodology-derived research screens, not backtested strategies or investment recommendations.",""]
    for s in strategies:
        lines += [f"## {s['id']} — {s['name']}","",s["purpose"],"",f"**Methodology evidence confidence:** {s['evidence_confidence']}/100","","### Proposed hard query","","```text",s["hard_query"],"```",""]
        if s["ranking_signals"]:
            lines += ["### Ranking / secondary signals",""]+[f"- {r}" for r in s["ranking_signals"]]+[""]
        lines += ["### Provenance",""]+[f"- {src['title']} — matched: {', '.join(src['matched_parameters'])}" for src in s["source_screens"][:6]]+["","### Why this strategy exists","",s["notes"],""]
    return "\n".join(lines)


def execution_manifest(strategies):
    return {"version":"V2","status":"strategy_ready_candidate_execution_not_run","instructions":"Execute each hard_query in Screener or another approved data source, retain strategy_id on every returned company, then union/deduplicate and compute overlap counts.","strategies":[{"strategy_id":s["id"],"name":s["name"],"query":s["hard_query"],"ranking_signals":s["ranking_signals"],"evidence_confidence":s["evidence_confidence"]} for s in strategies]}
