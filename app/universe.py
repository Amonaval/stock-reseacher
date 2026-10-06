import re

def norm(v):
    return re.sub(r"\s+", " ", str(v or "").strip()).casefold()

def dedupe(screens):
    """Prefer imported records when the same screen/query exists in multiple sources."""
    ranked = sorted(screens, key=lambda x: 0 if x.get("source") == "import" else 1)
    seen = set()
    out = []
    for s in ranked:
        url = norm(s.get("url"))
        query = norm(s.get("query"))
        key = ("url", url) if url else ("query", query)
        if not key[1]:
            key = ("fallback", norm(s.get("title")) + "|" + norm(s.get("owner")))
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out

def owners(screens):
    return sorted({str(s.get("owner", "")).strip() for s in screens if str(s.get("owner", "")).strip()}, key=str.casefold)

def filter_owners(screens, selected_owners):
    allowed = {norm(x) for x in selected_owners}
    if not allowed:
        return []
    return [s for s in screens if norm(s.get("owner")) in allowed]

def build_universe(imported, crawled, mode, selected_import_owners=None, selected_crawl_owners=None):
    selected_import_owners = selected_import_owners or []
    selected_crawl_owners = selected_crawl_owners or []

    imp = imported
    if selected_import_owners:
        imp = filter_owners(imported, selected_import_owners)

    cr = filter_owners(crawled, selected_crawl_owners) if selected_crawl_owners else []

    if mode == "Imported file only":
        return dedupe(imp)
    if mode == "Specific Screener user(s) only":
        return dedupe(cr)
    return dedupe(imp + cr)
