from __future__ import annotations

import re
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

from crawler import discover_candidates, crawl_selected_urls

SCREENER = "https://www.screener.in"


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _number(text):
    s = _clean(text).replace(",", "").replace("%", "")
    if s in {"", "-", "—"}:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return s
    try:
        return float(m.group())
    except Exception:
        return s


class ScreenerAdapter:
    """Local logged-in Screener POC adapter.

    Screener-specific browser behavior is isolated here so the research engines can
    later swap in NSE/BSE/other providers without being rewritten.
    """

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", delay: float = 0.35):
        self.cdp_url = cdp_url
        self.delay = delay
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
        if not self.browser.contexts:
            raise RuntimeError("Connected to Chrome but no browser context was found. Open Chrome with --remote-debugging-port=9222 and log in to Screener.")
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        return self

    def __exit__(self, *_):
        if self._pw:
            self._pw.stop()

    def connection_status(self) -> dict:
        self.page.goto(SCREENER, wait_until="domcontentloaded", timeout=60000)
        body = _clean(self.page.locator("body").inner_text(timeout=5000))
        hrefs = self.page.locator("a[href]").evaluate_all("els=>els.map(e=>e.getAttribute('href')||'').join(' ')")
        logged_in = "logout" in body.casefold() or "sign out" in body.casefold() or "/account/" in hrefs
        return {"connected": True, "logged_in": bool(logged_in), "url": self.page.url}

    @staticmethod
    def discover_screens(cdp_url, explore_url="https://www.screener.in/explore/", max_pages=15, max_screens=0, progress=None):
        return discover_candidates(cdp_url, explore_url, max_pages=max_pages, max_screens=max_screens, progress=progress)

    @staticmethod
    def fetch_screen_queries(cdp_url, urls, progress=None):
        return crawl_selected_urls(cdp_url, urls, progress=progress)

    def _query_input(self):
        for selector in ["textarea[name='query']", "textarea[name*=query i]", "textarea", "input[name*=query i]"]:
            loc = self.page.locator(selector)
            for i in range(loc.count()):
                el = loc.nth(i)
                try:
                    if el.is_visible() and el.is_editable():
                        return el
                except Exception:
                    pass
        return None

    def _submit_query(self):
        for selector in ["button:has-text('Run this Query')", "button:has-text('Run Query')", "input[type=submit]", "button[type=submit]"]:
            loc = self.page.locator(selector)
            if loc.count():
                try:
                    loc.first.click(timeout=3000)
                    return True
                except Exception:
                    pass
        return False

    def run_query(self, query: str) -> dict:
        self.page.goto(f"{SCREENER}/screen/new/", wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(350)
        inp = self._query_input()
        if inp is None:
            raise RuntimeError("Could not find Screener query editor on /screen/new/. UI may have changed.")
        inp.fill(query)
        if not self._submit_query():
            try:
                inp.press("Control+Enter")
            except Exception as exc:
                raise RuntimeError("Could not submit Screener query.") from exc
        self.page.wait_for_load_state("domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(500)
        return {"url": self.page.url, "title": self.page.title()}

    def _result_table(self):
        for sel in ["table.data-table", "table"]:
            tables = self.page.locator(sel)
            for i in range(tables.count()):
                table = tables.nth(i)
                try:
                    headers = table.locator("thead th").all_inner_texts()
                    if not headers:
                        headers = table.locator("tr").first.locator("th,td").all_inner_texts()
                    header_text = " ".join(headers).casefold()
                    if any(k in header_text for k in ["name", "cmp", "market cap", "p/e", "sales"]):
                        return table
                except Exception:
                    pass
        raise RuntimeError("Could not identify Screener result table.")

    def parse_current_result_page(self, strategy_id="") -> list[dict]:
        table = self._result_table()
        headers = [_clean(x) for x in table.locator("thead th").all_inner_texts()]
        rows = table.locator("tbody tr")
        if not headers:
            headers = [_clean(x) for x in table.locator("tr").first.locator("th,td").all_inner_texts()]
            rows = table.locator("tr")

        out = []
        for i in range(rows.count()):
            tr = rows.nth(i)
            cells = tr.locator("td")
            if cells.count() < 2:
                continue
            vals = [_clean(cells.nth(j).inner_text()) for j in range(cells.count())]
            links = tr.locator("a[href*='/company/']")
            href = links.first.get_attribute("href") if links.count() else ""
            company = _clean(links.first.inner_text()) if links.count() else ""
            if not company:
                company = vals[1] if len(vals) > 1 else vals[0]
            exact_url = urljoin(self.page.url, href) if href else ""
            snapshot = {}
            for j, v in enumerate(vals):
                h = headers[j] if j < len(headers) else f"Column {j+1}"
                snapshot[h] = _number(v)
            out.append({
                "company": company,
                "company_key": company.casefold(),
                "strategy_id": strategy_id,
                "url": exact_url,
                "source_file": "screener_live_query",
                "snapshot": snapshot,
            })
        return out

    def _next_href(self):
        for selector in ["a[rel='next']", "a:has-text('Next')", ".pagination a:has-text('Next')"]:
            loc = self.page.locator(selector)
            if loc.count():
                href = loc.first.get_attribute("href")
                if href:
                    return urljoin(self.page.url, href)
        return ""

    def collect_query_results(self, query: str, strategy_id: str, max_pages: int = 100, progress=None) -> list[dict]:
        self.run_query(query)
        all_rows = []
        seen_urls = set()
        for page_no in range(1, max_pages + 1):
            if self.page.url in seen_urls:
                break
            seen_urls.add(self.page.url)
            rows = self.parse_current_result_page(strategy_id)
            all_rows.extend(rows)
            if progress:
                progress(page_no, len(all_rows), self.page.url)
            nxt = self._next_href()
            if not nxt:
                break
            self.page.goto(nxt, wait_until="domcontentloaded", timeout=60000)
            self.page.wait_for_timeout(350)
            time.sleep(self.delay)
        return all_rows
