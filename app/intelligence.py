import hashlib
import itertools
import math
import re
from collections import Counter, defaultdict

BOOL_RE = re.compile(r"\b(?:AND|OR)\b", re.I)
COMP_RE = re.compile(r"^(.+?)\s*(>=|<=|>|<|=)\s*(.+?)\s*$")
NUM_RE = re.compile(r"^(-?\d+(?:\.\d+)?)$")
BENCH_RE = re.compile(r"^(.+?)\s*([*/])\s*(-?\d+(?:\.\d+)?)$")


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip()).lower()


def normalize_query(query):
    s = norm(query)
    s = s.replace("(", " ").replace(")", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def split_boolean_conditions(query):
    if not query:
        return []
    # For methodology mining, AND/OR both imply co-presence in a saved screen.
    # Parentheses are removed after splitting; original query remains available for audit.
    parts = BOOL_RE.split(str(query))
    return [p.strip().strip("() ") for p in parts if p.strip().strip("() ")]


def parse_condition(condition, parameter_extractor, classifier):
    raw = condition.strip()
    m = COMP_RE.match(raw)
    if not m:
        parameter = parameter_extractor(raw)
        return {
            "condition": raw,
            "parameter": parameter,
            "parameter_normalized": norm(parameter),
            "category": classifier(raw),
            "operator": "",
            "rhs": "",
            "threshold_type": "expression",
            "numeric_value": None,
            "benchmark": "",
            "multiplier": None,
        }

    lhs, op, rhs = [x.strip() for x in m.groups()]
    parameter = lhs
    rhs_n = norm(rhs)
    num = NUM_RE.match(rhs_n)
    if num:
        return {
            "condition": raw,
            "parameter": parameter,
            "parameter_normalized": norm(parameter),
            "category": classifier(raw),
            "operator": op,
            "rhs": rhs,
            "threshold_type": "absolute",
            "numeric_value": float(num.group(1)),
            "benchmark": "",
            "multiplier": None,
        }

    bench = BENCH_RE.match(rhs_n)
    if bench:
        base, arithmetic, value = bench.groups()
        value = float(value)
        multiplier = value if arithmetic == "*" else (1.0 / value if value else None)
        return {
            "condition": raw,
            "parameter": parameter,
            "parameter_normalized": norm(parameter),
            "category": classifier(raw),
            "operator": op,
            "rhs": rhs,
            "threshold_type": "relative",
            "numeric_value": None,
            "benchmark": norm(base),
            "multiplier": multiplier,
        }

    return {
        "condition": raw,
        "parameter": parameter,
        "parameter_normalized": norm(parameter),
        "category": classifier(raw),
        "operator": op,
        "rhs": rhs,
        "threshold_type": "relative_reference" if re.search(r"[a-z]", rhs_n) else "expression",
        "numeric_value": None,
        "benchmark": rhs_n if re.search(r"[a-z]", rhs_n) else "",
        "multiplier": 1.0 if re.search(r"[a-z]", rhs_n) else None,
    }


def percentile(sorted_values, p):
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] * (hi-k) + sorted_values[hi] * (k-lo)


def threshold_stats(parsed_conditions, min_count=2):
    buckets = defaultdict(list)
    relative = defaultdict(list)
    for x in parsed_conditions:
        if x["threshold_type"] == "absolute" and x["numeric_value"] is not None:
            buckets[(x["parameter_normalized"], x["operator"])].append(x["numeric_value"])
        elif x["threshold_type"] == "relative" and x["multiplier"] is not None:
            relative[(x["parameter_normalized"], x["operator"], x["benchmark"])].append(x["multiplier"])

    absolute_rows = []
    for (param, op), values in buckets.items():
        if len(values) < min_count:
            continue
        values = sorted(values)
        absolute_rows.append({
            "parameter": param, "operator": op, "count": len(values),
            "min": values[0], "p25": percentile(values,.25), "median": percentile(values,.5),
            "p75": percentile(values,.75), "max": values[-1],
            "most_common": Counter(values).most_common(5),
        })
    absolute_rows.sort(key=lambda x: (-x["count"], x["parameter"], x["operator"]))

    relative_rows = []
    for (param, op, benchmark), values in relative.items():
        if len(values) < min_count:
            continue
        values = sorted(values)
        relative_rows.append({
            "parameter": param, "operator": op, "benchmark": benchmark,
            "count": len(values), "min_multiplier": values[0],
            "median_multiplier": percentile(values,.5), "max_multiplier": values[-1],
            "most_common": Counter(values).most_common(5),
        })
    relative_rows.sort(key=lambda x: (-x["count"], x["parameter"], x["benchmark"]))
    return absolute_rows, relative_rows


def cooccurrence(screen_records, key="parameters"):
    pair_counts = Counter()
    triple_counts = Counter()
    for rec in screen_records:
        vals = sorted(set(rec.get(key, [])))
        pair_counts.update(itertools.combinations(vals, 2))
        # Avoid pathological queries; top methodology signals are still represented.
        if len(vals) <= 40:
            triple_counts.update(itertools.combinations(vals, 3))
    return pair_counts, triple_counts


def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def duplicate_groups(screen_records, similarity=0.80):
    exact = defaultdict(list)
    for r in screen_records:
        h = hashlib.sha1(normalize_query(r.get("query", "")).encode()).hexdigest()
        exact[h].append(r)
    exact_groups = [g for g in exact.values() if len(g) > 1 and normalize_query(g[0].get("query"))]

    near = []
    used = set()
    ordered = sorted(screen_records, key=lambda x: len(x.get("parameters", [])), reverse=True)
    for i, base in enumerate(ordered):
        bid = base["index"]
        if bid in used:
            continue
        group = [base]
        for other in ordered[i+1:]:
            oid = other["index"]
            if oid in used:
                continue
            # Same parameters can hide threshold variations, which are valuable as screen variants.
            sim = jaccard(base.get("parameters", []), other.get("parameters", []))
            if sim >= similarity:
                group.append(other)
        if len(group) > 1:
            for g in group:
                used.add(g["index"])
            near.append({"similarity_floor": similarity, "screens": group})
    near.sort(key=lambda x: -len(x["screens"]))
    return exact_groups, near


def greedy_archetypes(screen_records, similarity=0.46, min_cluster=3):
    remaining = list(screen_records)
    clusters = []
    while remaining:
        seed = max(remaining, key=lambda r: len(r.get("parameters", [])))
        group = [r for r in remaining if jaccard(seed.get("parameters", []), r.get("parameters", [])) >= similarity]
        if len(group) < min_cluster:
            remaining.remove(seed)
            continue
        ids = {r["index"] for r in group}
        remaining = [r for r in remaining if r["index"] not in ids]
        param_counts = Counter(p for r in group for p in set(r.get("parameters", [])))
        cat_counts = Counter(c for r in group for c in set(r.get("categories", [])))
        core = [(p,c) for p,c in param_counts.most_common() if c/len(group) >= .55][:12]
        clusters.append({
            "size": len(group),
            "core_parameters": core,
            "categories": cat_counts.most_common(),
            "screens": group,
        })
    clusters.sort(key=lambda x: -x["size"])
    return clusters


def mine_methodology(screens, parameter_extractor, classifier):
    parsed = []
    screen_records = []
    param_frequency = Counter()
    condition_frequency = Counter()

    for idx, screen in enumerate(screens):
        conds = split_boolean_conditions(screen.get("query", ""))
        row_parsed = []
        for c in conds:
            pc = parse_condition(c, parameter_extractor, classifier)
            pc.update({
                "screen": screen.get("title", ""),
                "owner": screen.get("owner", ""),
                "url": screen.get("url", ""),
                "screen_index": idx,
            })
            parsed.append(pc)
            row_parsed.append(pc)
            param_frequency[pc["parameter_normalized"]] += 1
            condition_frequency[norm(pc["condition"])] += 1

        params = sorted({x["parameter_normalized"] for x in row_parsed if x["parameter_normalized"]})
        cats = sorted({x["category"] for x in row_parsed if x["category"]})
        screen_records.append({
            "index": idx,
            "title": screen.get("title", ""), "owner": screen.get("owner", ""),
            "url": screen.get("url", ""), "query": screen.get("query", ""),
            "parameters": params, "categories": cats,
            "condition_count": len(row_parsed),
        })

    abs_stats, rel_stats = threshold_stats(parsed)
    pairs, triples = cooccurrence(screen_records)
    exact_dupes, near_dupes = duplicate_groups(screen_records)
    archetypes = greedy_archetypes(screen_records)
    rare = [(p,c) for p,c in param_frequency.items() if c <= 3]
    rare.sort(key=lambda x: (x[1], x[0]))

    return {
        "parsed_conditions": parsed,
        "screen_records": screen_records,
        "absolute_thresholds": abs_stats,
        "relative_thresholds": rel_stats,
        "pair_counts": pairs,
        "triple_counts": triples,
        "exact_duplicate_groups": exact_dupes,
        "near_duplicate_groups": near_dupes,
        "archetypes": archetypes,
        "rare_parameters": rare,
        "condition_frequency": condition_frequency,
    }
