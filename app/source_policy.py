from __future__ import annotations

import hashlib
import os
import re
from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from source_discovery import domain_of


BLOCKED_EXTENSIONS = {
    ".zip", ".exe", ".msi", ".dmg", ".iso", ".apk", ".bin", ".torrent"
}

PREFERRED_DOC_TYPES = {
    "annual_report": 30,
    "quarterly_result": 28,
    "investor_presentation": 22,
    "earnings_call": 20,
    "exchange_filing": 24,
    "credit_rating": 22,
    "shareholding": 20,
    "other": 5,
}

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid"
}


def canonical_url(url):
    try:
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), ""))
    except Exception:
        return url


def source_key(row):
    return hashlib.sha256(canonical_url(row.get("url", "")).encode("utf-8")).hexdigest()[:20]


def permitted_url(url):
    low = (url or "").lower()
    if not low.startswith(("http://", "https://")):
        return False, "Only http/https sources are supported."
    path = urlsplit(low).path
    if any(path.endswith(ext) for ext in BLOCKED_EXTENSIONS):
        return False, "Blocked binary/archive extension."
    return True, ""


def score_source(row):
    authority = float(row.get("authority_score") or 0)
    doc_bonus = PREFERRED_DOC_TYPES.get(row.get("doc_type") or "other", 5)
    primary_bonus = 12 if row.get("source_class") == "primary" else 0
    pdf_bonus = 6 if ".pdf" in (row.get("url") or "").lower() else 0
    score = min(100.0, authority * 0.62 + doc_bonus + primary_bonus + pdf_bonus)
    return round(score, 1)


def dedupe_and_rank(rows):
    best = {}
    for row in rows:
        ok, reason = permitted_url(row.get("url", ""))
        row = dict(row)
        row["policy_allowed"] = ok
        row["policy_reason"] = reason
        row["canonical_url"] = canonical_url(row.get("url", ""))
        row["source_key"] = source_key(row)
        row["source_score"] = score_source(row) if ok else 0
        key = row["canonical_url"]
        existing = best.get(key)
        if existing is None or row["source_score"] > existing["source_score"]:
            best[key] = row
    return sorted(best.values(), key=lambda x: (-x.get("source_score", 0), x.get("domain", ""), x.get("url", "")))


def select_fetch_queue(rows, per_type=3, min_score=55):
    grouped = defaultdict(list)
    for row in dedupe_and_rank(rows):
        if not row.get("policy_allowed"):
            continue
        if row.get("source_score", 0) < min_score:
            continue
        grouped[row.get("doc_type") or "other"].append(row)

    selected = []
    for doc_type, items in grouped.items():
        selected.extend(items[:per_type])
    return sorted(selected, key=lambda x: -x.get("source_score", 0))


def local_crawler_enabled():
    return os.getenv("ENABLE_LOCAL_CRAWLER", "").strip().lower() in {"1", "true", "yes", "on"}
