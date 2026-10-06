import re
from collections import Counter, defaultdict
from intelligence import mine_methodology

CATEGORY_RULES = {
    "Growth": ["sales growth", "profit growth", "eps growth", "revenue growth", "yoy quarterly sales growth", "yoy quarterly profit growth", "qoq profits", "sales growth"],
    "Quality / Returns": ["return on equity", "roe", "return on capital employed", "roce", "return on invested capital", "roic", "return on assets", "piotroski", "g factor", "average return on equity"],
    "Valuation": ["price to earning", "p/e", "pe ratio", "peg ratio", "price to book", "price to sales", "price to free cash flow", "industry pe", "industry pbv", "historical pe", "dividend yield", "market capitalization / sales"],
    "Balance Sheet / Leverage": ["debt to equity", "debt", "interest coverage", "current ratio", "working capital", "pledged percentage"],
    "Cash Flow": ["cash from operations", "cash equivalents", "free cash flow", "cash flow"],
    "Profitability / Margins": ["opm", "npm", "net profit margin", "operating profit margin", "operating profit", "margin"],
    "Momentum / Technical": ["rsi", "dma", "volume", "return over", "52w high", "52w low", "all time high", "down from", "up from", "high price"],
    "Size / Universe": ["market capitalization", "market cap", "current price", "face value"],
    "Ownership": ["promoter holding", "fii holding", "dii holding", "public holding", "number of shareholders", "change in promoter holding", "share holder change"],
    "Efficiency / Working Capital": ["working capital days", "inventory days", "debtor days", "cash conversion"],
}

def normalize_name(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())

def split_conditions(query):
    if not query:
        return []
    return [p.strip(" ()") for p in re.split(r"\s+(?:AND|OR)\s+", str(query), flags=re.I) if p.strip(" ()")]

def classify(condition):
    low = normalize_name(condition)
    scores = {}
    for category, terms in CATEGORY_RULES.items():
        score = sum(1 for term in terms if term in low)
        if score:
            scores[category] = score
    return max(scores, key=scores.get) if scores else "Other / Unclassified"

def extract_parameter(condition):
    m = re.search(r"(.+?)\s*(>=|<=|>|<|=)\s*(.+)$", condition)
    return re.sub(r"\s+", " ", (m.group(1) if m else condition).strip())

def analyze(screens):
    condition_rows=[]; parameter_counter=Counter(); category_counter=Counter(); owner_counter=Counter(); source_counter=Counter(); screen_category_counts=defaultdict(Counter)
    for screen in screens:
        owner_counter[screen.get("owner") or "(unknown)"] += 1
        source_counter[screen.get("source") or "(unknown)"] += 1
        for condition in split_conditions(screen.get("query", "")):
            parameter=extract_parameter(condition); category=classify(condition)
            parameter_counter[normalize_name(parameter)] += 1; category_counter[category] += 1
            screen_category_counts[screen.get("title") or screen.get("url", "")][category] += 1
            condition_rows.append({"screen":screen.get("title",""),"owner":screen.get("owner",""),"source":screen.get("source",""),"url":screen.get("url",""),"condition":condition,"parameter":parameter,"parameter_normalized":normalize_name(parameter),"category":category})
    intelligence = mine_methodology(screens, extract_parameter, classify)
    return {"conditions":condition_rows,"parameter_frequency":parameter_counter,"category_frequency":category_counter,"owner_frequency":owner_counter,"source_frequency":source_counter,"screen_category_counts":screen_category_counts,"intelligence":intelligence}

def _fmt(v):
    if v is None: return ""
    return f"{v:.3f}".rstrip("0").rstrip(".")

def methodology_markdown(screens, analysis):
    conditions=analysis["conditions"]; p=analysis["parameter_frequency"]; c=analysis["category_frequency"]; intel=analysis["intelligence"]
    lines=["# Screener Methodology Miner — V1.2 Intelligence Report","","## Selected Universe","",f"- Screens analyzed: **{len(screens)}**",f"- Screens with queries: **{sum(bool(s.get('query')) for s in screens)}**",f"- Total conditions extracted: **{len(conditions)}**",f"- Unique parameters: **{len(p)}**","","### Screens by source",""]
    for source,count in analysis["source_frequency"].most_common(): lines.append(f"- {source}: **{count}**")
    lines += ["","### Screens by owner",""]
    for owner,count in analysis["owner_frequency"].most_common(): lines.append(f"- {owner}: **{count}**")

    lines += ["","## Parameter Categories","","| Category | Conditions | Share |","|---|---:|---:|"]
    denom=max(len(conditions),1)
    for cat,count in c.most_common(): lines.append(f"| {cat} | {count} | {count/denom:.1%} |")

    lines += ["","## Most Frequently Used Parameters","","| Parameter | Frequency |","|---|---:|"]
    for param,count in p.most_common(50): lines.append(f"| {param} | {count} |")

    lines += ["","## Absolute Threshold DNA","","Most-used numeric rules, summarized across screens.","","| Parameter | Op | N | Min | P25 | Median | P75 | Max |","|---|:---:|---:|---:|---:|---:|---:|---:|"]
    for r in intel["absolute_thresholds"][:60]:
        lines.append(f"| {r['parameter']} | {r['operator']} | {r['count']} | {_fmt(r['min'])} | {_fmt(r['p25'])} | {_fmt(r['median'])} | {_fmt(r['p75'])} | {_fmt(r['max'])} |")

    lines += ["","## Relative / Benchmark Threshold DNA","","Rules such as PE vs Industry PE are kept separate from absolute numeric thresholds.","","| Parameter | Op | Benchmark | N | Median multiplier | Range |","|---|:---:|---|---:|---:|---:|"]
    for r in intel["relative_thresholds"][:50]:
        lines.append(f"| {r['parameter']} | {r['operator']} | {r['benchmark']} | {r['count']} | {_fmt(r['median_multiplier'])}× | {_fmt(r['min_multiplier'])}×–{_fmt(r['max_multiplier'])}× |")

    lines += ["","## Strongest Parameter Pairs","","| Pair | Screens |","|---|---:|"]
    for pair,count in intel["pair_counts"].most_common(40): lines.append(f"| {pair[0]} + {pair[1]} | {count} |")

    lines += ["","## Strongest Parameter Triples","","| Triple | Screens |","|---|---:|"]
    for tri,count in intel["triple_counts"].most_common(30): lines.append(f"| {tri[0]} + {tri[1]} + {tri[2]} | {count} |")

    lines += ["","## Deterministic Screen Archetypes",""]
    if intel["archetypes"]:
        for i,a in enumerate(intel["archetypes"][:12],1):
            core=", ".join(f"{p} ({count}/{a['size']})" for p,count in a["core_parameters"][:10])
            examples=", ".join(r["title"] for r in a["screens"][:5])
            lines += [f"### Archetype {i} — {a['size']} screens",f"- Core parameters: {core or 'No >=55% core parameter'}",f"- Example screens: {examples}",""]
    else: lines.append("No deterministic clusters met the current similarity/minimum-size rules.")

    lines += ["","## Duplicate / Variant Audit","",f"- Exact duplicate-query groups: **{len(intel['exact_duplicate_groups'])}**",f"- Near-duplicate parameter-set groups (Jaccard ≥ 0.80): **{len(intel['near_duplicate_groups'])}**",""]
    for i,g in enumerate(intel["near_duplicate_groups"][:15],1):
        titles=", ".join(x["title"] for x in g["screens"][:10])
        lines.append(f"- Variant family {i} ({len(g['screens'])} screens): {titles}")

    lines += ["","## Rare / Experimental Parameters","",f"Parameters used in ≤3 conditions: **{len(intel['rare_parameters'])}**",""]
    for param,count in intel["rare_parameters"][:80]: lines.append(f"- {param}: {count}")

    lines += ["","## Interpretation Guardrail","","This report analyzes only the screen universe explicitly selected in the application. Co-occurrence means conditions are present in the same saved screen; it does not prove causality or historical performance. Archetypes are deterministic similarity groups, not validated investment strategies.","","## V2 Gate","","Use these threshold distributions, co-occurrences, archetypes, and variant families as evidence when proposing 5–7 master strategies. Do not generate master strategies from frequency alone."]
    return "\n".join(lines)

def build_llm_prompt(screens, analysis):
    intel=analysis["intelligence"]
    compact_arch=[{"size":a["size"],"core_parameters":a["core_parameters"][:12],"examples":[r["title"] for r in a["screens"][:6]]} for a in intel["archetypes"][:15]]
    return f"""Analyze the explicitly selected Screener.in methodology universe. Do NOT recommend stocks yet.

Separate OBSERVATION from INFERENCE. Use the quantitative evidence below.

Produce an Investment DNA report with:
1. Executive thesis of the screening style
2. Dominant parameter families
3. Absolute threshold preferences and ranges
4. Benchmark-relative valuation preferences
5. Strongest recurring pairs and triples
6. Distinct screen archetypes and what each appears designed to find
7. Repeated variants/experiments and what thresholds appear to have been tuned
8. Rare/experimental techniques worth preserving
9. Contradictions or competing philosophies
10. Blind spots / underrepresented dimensions
11. 5–7 candidate master-strategy archetypes for V2, each explicitly traced back to evidence here
12. What cannot be inferred without backtesting/outcome data

Selected screens: {len(screens)}
Category frequencies: {analysis['category_frequency'].most_common()}
Top parameters: {analysis['parameter_frequency'].most_common(70)}
Absolute threshold stats: {intel['absolute_thresholds'][:80]}
Relative threshold stats: {intel['relative_thresholds'][:60]}
Top pairs: {intel['pair_counts'].most_common(80)}
Top triples: {intel['triple_counts'].most_common(60)}
Archetypes: {compact_arch}
Rare parameters: {intel['rare_parameters'][:100]}
"""
