from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests


PRIMARY_DOMAINS = {
    "nseindia.com": 100,
    "bseindia.com": 100,
    "sebi.gov.in": 100,
    "crisilratings.com": 92,
    "icra.in": 92,
    "careratings.com": 92,
    "indiaratings.co.in": 92,
}

SECONDARY_DOMAINS = {
    "moneycontrol.com": 65,
    "business-standard.com": 72,
    "economictimes.indiatimes.com": 68,
    "livemint.com": 72,
    "reuters.com": 85,
}

DOCUMENT_HINTS = {
    "annual_report": ["annual report", "integrated report"],
    "quarterly_result": ["financial results", "quarterly results", "quarter results"],
    "investor_presentation": ["investor presentation", "investor ppt", "presentation"],
    "earnings_call": ["earnings call", "conference call", "concall", "transcript"],
    "exchange_filing": ["corporate announcement", "exchange filing", "regulation 30", "disclosure"],
    "credit_rating": ["credit rating", "rating rationale", "crisil", "icra", "care ratings", "india ratings"],
    "shareholding": ["shareholding pattern", "promoter holding"],
}


def _norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def domain_of(url):
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def infer_doc_type(title="", url="", snippet=""):
    hay = f"{title} {url} {snippet}".lower()
    for doc_type, words in DOCUMENT_HINTS.items():
        if any(w in hay for w in words):
            return doc_type
    return "other"


def infer_authority(url):
    domain = domain_of(url)
    if domain in PRIMARY_DOMAINS:
        return PRIMARY_DOMAINS[domain], "primary"
    if domain in SECONDARY_DOMAINS:
        return SECONDARY_DOMAINS[domain], "secondary"
    if any(x in domain for x in ["investor", "ir.", "corp."]):
        return 82, "company_ir_candidate"
    return 45, "web"


def default_research_queries(company, symbol=""):
    identity = f'"{company}"'
    if symbol:
        identity += f' "{symbol}"'
    return [
        ("annual_report", f'{identity} annual report filetype:pdf'),
        ("quarterly_result", f'{identity} financial results filetype:pdf'),
        ("investor_presentation", f'{identity} investor presentation filetype:pdf'),
        ("earnings_call", f'{identity} earnings call transcript OR concall filetype:pdf'),
        ("exchange_filing", f'{identity} site:nseindia.com corporate filing OR announcement'),
        ("exchange_filing", f'{identity} site:bseindia.com corporate announcement'),
        ("credit_rating", f'{identity} CRISIL OR ICRA OR "CARE Ratings" OR "India Ratings" filetype:pdf'),
        ("shareholding", f'{identity} shareholding pattern site:nseindia.com OR site:bseindia.com'),
    ]


class BraveSearchProvider:
    name = "brave"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY") or os.getenv("BRAVE_API_KEY")

    def configured(self):
        return bool(self.api_key)

    def search(self, query, count=10, country="IN"):
        if not self.configured():
            raise RuntimeError("BRAVE_SEARCH_API_KEY is not configured.")
        r = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key,
            },
            params={
                "q": query,
                "count": min(max(int(count), 1), 20),
                "country": country,
                "search_lang": "en",
                "safesearch": "moderate",
            },
            timeout=30,
        )
        r.raise_for_status()
        payload = r.json()
        results = []
        for item in (payload.get("web") or {}).get("results", []) or []:
            url = item.get("url") or ""
            if not url:
                continue
            score, source_class = infer_authority(url)
            results.append({
                "provider": self.name,
                "query": query,
                "title": _norm(item.get("title")),
                "url": url,
                "description": _norm(item.get("description")),
                "domain": domain_of(url),
                "authority_score": score,
                "source_class": source_class,
                "doc_type": infer_doc_type(item.get("title"), url, item.get("description")),
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            })
        return results


def discover_company_sources(company, symbol="", provider=None, max_per_query=8, progress=None):
    provider = provider or BraveSearchProvider()
    discovered = []
    errors = []
    queries = default_research_queries(company, symbol)
    for i, (target_type, query) in enumerate(queries, 1):
        try:
            rows = provider.search(query, count=max_per_query)
            for row in rows:
                if row.get("doc_type") == "other":
                    row["doc_type"] = target_type
                row["company"] = company
                row["symbol"] = symbol
                row["target_type"] = target_type
                discovered.append(row)
        except Exception as exc:
            errors.append({"company": company, "query": query, "error": str(exc)})
        if progress:
            progress(i, len(queries), target_type, query)
    return discovered, errors
