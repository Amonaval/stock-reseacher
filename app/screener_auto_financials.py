from __future__ import annotations

import math
import re
import time
from collections import defaultdict
from urllib.parse import quote, urljoin, urlparse

from playwright.sync_api import sync_playwright


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip()).casefold()


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        try:
            return None if math.isnan(float(v)) else float(v)
        except Exception:
            return float(v)
    s = str(v).strip().replace(",", "").replace("%", "")
    if not s or s.casefold() in {"nan", "na", "n/a", "none", "-", "—"}:
        return None
    try:
        return float(s)
    except Exception:
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        return float(m.group()) if m else None


# Screener export aliases -> V3 canonical fields.
SNAPSHOT_ALIASES = {
    "price": ["cmp rs.", "cmp rs", "cmp", "current price", "price"],
    "market_cap": ["mar cap rs.cr.", "mar cap rs.cr", "market cap", "market capitalization"],
    "pe": ["p/e", "pe", "price to earning"],
    "piotroski": ["piotski scr", "piotroski score", "piotroski"],
    "roe": ["roe %", "roe", "return on equity"],
    "debt_equity": ["debt / eq", "debt/equity", "debt to equity"],
    "up_from_52w_low": ["up %", "up from 52w low"],
    "down_from_52w_high": ["down %", "down from 52w high"],
    "five_year_pe": ["5 pe", "5y pe", "5 year pe"],
    "rsi": ["rsi"],
    "dividend_yield": ["div yld %", "dividend yield"],
    "public_holding": ["public hold %", "% public holding", "public holding"],
    "return_1d": ["1day return %", "1 day return", "return 1day"],
    "return_3m": ["3mth return %", "3 month return", "return 3months"],
    "return_5y": ["5yrs return %", "5 year return", "return over 5years"],
    "industry_pe": ["ind pe", "industry pe"],
}


def snapshot_from_result_row(row):
    """Map preserved Screener result columns into V3 canonical snapshot metrics."""
    raw = row.get("snapshot") or {}
    normalized = {_norm(k): v for k, v in raw.items()}
    out = {}
    for target, aliases in SNAPSHOT_ALIASES.items():
        value = None
        for alias in aliases:
            if _norm(alias) in normalized:
                value = _num(normalized[_norm(alias)])
                break
        out[target] = value
    return out


def _extract_company_links(page, company):
    # Search endpoint can redirect directly or return a list of company links.
    current = page.url
    if "/company/" in urlparse(current).path and "/search/" not in urlparse(current).path:
        return [current]

    links = []
    for href in page.locator("a[href*='/company/']").evaluate_all(
        "els => els.map(e => ({href:e.href,text:(e.innerText||'').trim()}))"
    ):
        url = href.get("href") or ""
        text = href.get("text") or ""
        if "/company/" not in url:
            continue
        score = 0
        cn = _norm(company)
        tn = _norm(text)
        if cn and cn == tn:
            score += 100
        if cn and cn in tn:
            score += 50
        links.append((score, url))
    return [u for _, u in sorted(links, key=lambda x: (-x[0], x[1]))]


def resolve_company_url(page, company):
    q = quote(str(company))
    url = f"https://www.screener.in/company/search/?q={q}"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(350)
    links = _extract_company_links(page, company)
    if not links:
        raise RuntimeError(f"Could not resolve Screener company page for {company}")
    return links[0]


def _parse_table(page, section_selector):
    section = page.locator(section_selector)
    if section.count() == 0:
        return {"periods": [], "rows": {}}
    table = section.locator("table").first
    if table.count() == 0:
        return {"periods": [], "rows": {}}

    matrix = table.locator("tr").evaluate_all(
        "rows => rows.map(r => Array.from(r.querySelectorAll('th,td')).map(c => (c.innerText||'').trim()))"
    )
    if not matrix:
        return {"periods": [], "rows": {}}

    # Header usually starts with a blank/label cell followed by periods.
    header = matrix[0]
    periods = [re.sub(r"\s+", " ", x).strip() for x in header[1:]]
    rows = {}
    for cells in matrix[1:]:
        if not cells:
            continue
        label = re.sub(r"\s+", " ", cells[0]).strip().rstrip("+").strip()
        if not label:
            continue
        vals = cells[1:]
        # Normalize length to periods; extra action columns are ignored.
        vals = vals[:len(periods)]
        rows[_norm(label)] = {"label": label, "values": vals}
    return {"periods": periods, "rows": rows}


def _get_row(table, aliases):
    rows = table.get("rows", {})
    for alias in aliases:
        key = _norm(alias)
        if key in rows:
            return rows[key]["values"]
    # Fuzzy fallback for labels like 'Net Profit +' or whitespace variants.
    for key, row in rows.items():
        if any(_norm(alias) in key for alias in aliases):
            return row["values"]
    return []


def _annual_period(period):
    p = str(period or "").strip()
    if not p or p.casefold() in {"ttm", "latest"}:
        return False
    return bool(re.search(r"(?:mar|fy|20\d{2})", p, re.I))


def _top_ratios(page):
    out = {}
    loc = page.locator("#top-ratios li")
    if loc.count() == 0:
        return out
    for i in range(loc.count()):
        text = re.sub(r"\s+", " ", loc.nth(i).inner_text()).strip()
        # Most rows are: Metric Value
        for label, key in [
            ("Stock P/E", "pe"), ("ROCE", "roce"), ("ROE", "roe"),
            ("Market Cap", "market_cap"), ("Current Price", "price"),
            ("Dividend Yield", "dividend_yield"), ("Book Value", "book_value"),
        ]:
            if label.casefold() in text.casefold():
                # prefer last numeric token
                nums = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
                if nums:
                    out[key] = _num(nums[-1])
    return out


def extract_company_financial_history(page, company, url=""):
    if not url:
        url = resolve_company_url(page, company)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(450)

    top = _top_ratios(page)
    pnl = _parse_table(page, "#profit-loss")
    bs = _parse_table(page, "#balance-sheet")
    cf = _parse_table(page, "#cash-flow")
    ratios = _parse_table(page, "#ratios")

    periods = pnl.get("periods", [])
    series = {
        "sales": _get_row(pnl, ["sales", "revenue"]),
        "profit": _get_row(pnl, ["net profit", "profit after tax"]),
        "eps": _get_row(pnl, ["eps in rs", "eps"]),
        "opm": _get_row(pnl, ["opm %", "operating profit margin"]),
        "interest": _get_row(pnl, ["interest"]),
        "borrowings": _get_row(bs, ["borrowings"]),
        "cfo": _get_row(cf, ["cash from operating activity", "cash from operations"]),
        "fcf": _get_row(cf, ["free cash flow"]),
        "roce": _get_row(ratios, ["roce %", "roce"]),
    }

    # Map each annual P&L period into one canonical V3 row. Other tables usually
    # use the same annual column labels; values are matched by position when possible.
    rows = []
    for idx, period in enumerate(periods):
        if not _annual_period(period):
            continue
        row = {
            "company": company,
            "symbol": "",
            "year": period,
            "source": "screener_company_page",
            "source_url": page.url,
        }
        for metric, values in series.items():
            row[metric] = _num(values[idx]) if idx < len(values) else None
        rows.append(row)

    # If no annual history parsed, still return a current snapshot row.
    if not rows:
        rows = [{
            "company": company, "symbol": "", "year": "Latest",
            "source": "screener_company_page", "source_url": page.url,
        }]

    # Apply current top-ratio snapshot to latest row only.
    rows[-1].update({k: v for k, v in top.items() if v is not None})
    return rows, page.url


def enrich_candidate_universe(candidates, cdp_url="http://127.0.0.1:9222", use_screener=True,
                              delay=0.45, max_companies=0, progress=None):
    """
    Build V3-ready multi-period rows automatically.

    Layer 1: always retain ratios from imported Screener result files.
    Layer 2: optionally enrich with multi-year data from Screener company pages
             through the user's local logged-in browser session.
    """
    selected = list(candidates[:int(max_companies)]) if max_companies else list(candidates)
    all_rows = []
    errors = []
    resolved = []

    browser_ctx = None
    playwright = None
    page = None
    try:
        if use_screener:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            if not browser.contexts:
                raise RuntimeError("Connected to Chrome but no browser context was found.")
            browser_ctx = browser.contexts[0]
            page = browser_ctx.pages[0] if browser_ctx.pages else browser_ctx.new_page()

        for i, candidate in enumerate(selected, 1):
            company = candidate.get("company", "")
            snapshot = snapshot_from_result_row(candidate)
            history = []
            company_url = candidate.get("url", "") or ""

            if use_screener:
                try:
                    history, company_url = extract_company_financial_history(page, company, company_url)
                    resolved.append({"company": company, "url": company_url, "status": "ENRICHED"})
                except Exception as exc:
                    errors.append({"company": company, "stage": "screener_history", "error": str(exc)})
                    resolved.append({"company": company, "url": company_url, "status": "SNAPSHOT_ONLY"})

            if not history:
                history = [{
                    "company": company,
                    "symbol": candidate.get("symbol", ""),
                    "year": "Snapshot",
                    "source": "screener_result_export",
                    "source_url": company_url,
                }]

            # Merge imported snapshot into latest period. This deliberately
            # preserves known ratios even if company-page extraction misses them.
            latest = history[-1]
            for key, value in snapshot.items():
                if value is not None and latest.get(key) is None:
                    latest[key] = value

            # Fields not derivable from source remain None and reduce V3 confidence.
            latest["strategy_count"] = candidate.get("strategy_count", 0)
            latest["strategies"] = candidate.get("strategies", "")
            latest["research_priority"] = candidate.get("research_priority_score", 0)
            latest["company_url"] = company_url
            all_rows.extend(history)

            if progress:
                progress(i, len(selected), company, resolved[-1]["status"] if resolved else "SNAPSHOT")
            time.sleep(max(0, delay))
    finally:
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass

    return all_rows, resolved, errors
