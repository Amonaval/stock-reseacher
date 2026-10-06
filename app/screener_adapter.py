from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse
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


def _is_app_page(page) -> bool:
    try:
        url = (page.url or "").lower()
    except Exception:
        return False
    return (
        "localhost:8501" in url
        or "127.0.0.1:8501" in url
        or "streamlit" in url
    )


class ScreenerAdapter:
    """Local logged-in Screener POC adapter.

    Browser contract:
    - NEVER navigate an existing user/application tab.
    - Every automation session gets a dedicated worker tab.
    - The worker tab is closed on success/error.
    - The Streamlit/application tab is brought back to the front when possible.

    Screener-specific behavior is isolated here so NSE/BSE/provider adapters can
    replace it later without changing the research engines.
    """

    def __init__(self, cdp_url: str = "http://127.0.0.1:9222", delay: float = 0.35):
        self.cdp_url = cdp_url
        self.delay = delay
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None
        self.return_page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.connect_over_cdp(self.cdp_url)
        if not self.browser.contexts:
            raise RuntimeError(
                "Connected to Chrome but no browser context was found. "
                "Open Chrome with --remote-debugging-port=9222 and log in to Screener."
            )
        self.context = self.browser.contexts[0]
        existing = list(self.context.pages)
        self.return_page = next((p for p in existing if _is_app_page(p)), None)
        if self.return_page is None:
            self.return_page = next(
                (p for p in existing if "screener.in" not in (p.url or "").lower() and (p.url or "") != "about:blank"),
                None,
            )

        # Critical UX rule: never reuse context.pages[0]. It may be the Streamlit app.
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)
        self.page.set_default_navigation_timeout(30000)
        return self

    def __exit__(self, *_):
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception:
            pass
        try:
            if self.return_page and not self.return_page.is_closed():
                self.return_page.bring_to_front()
        except Exception:
            pass
        if self._pw:
            try:
                self._pw.stop()
            except Exception:
                pass

    def _goto(self, url: str, timeout: int = 30000):
        """Bounded navigation; don't leave the UI hanging on a network-idle wait."""
        response = self.page.goto(url, wait_until="commit", timeout=timeout)
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=min(timeout, 10000))
        except Exception:
            # DOM may already be useful even when third-party assets keep loading.
            pass
        return response

    def connection_status(self) -> dict:
        self._goto(SCREENER, timeout=15000)
        try:
            body = _clean(self.page.locator("body").inner_text(timeout=5000))
        except Exception:
            body = ""
        try:
            hrefs = self.page.locator("a[href]").evaluate_all(
                "els=>els.map(e=>e.getAttribute('href')||'').join(' ')"
            )
        except Exception:
            hrefs = ""
        logged_in = (
            "logout" in body.casefold()
            or "sign out" in body.casefold()
            or "/account/" in hrefs
        )
        return {
            "connected": True,
            "logged_in": bool(logged_in),
            "url": self.page.url,
            "worker_tab": True,
        }

    @staticmethod
    def discover_screens(cdp_url, explore_url="https://www.screener.in/explore/", max_pages=15, max_screens=0, progress=None):
        return discover_candidates(cdp_url, explore_url, max_pages=max_pages, max_screens=max_screens, progress=progress)

    @staticmethod
    def fetch_screen_queries(cdp_url, urls, progress=None):
        return crawl_selected_urls(cdp_url, urls, progress=progress)

    def _query_input(self):
        selectors = [
            "textarea[name='query']",
            "textarea[name*=query i]",
            "textarea",
            "input[name*=query i]",
        ]
        for selector in selectors:
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
        for selector in [
            "button:has-text('Run this Query')",
            "button:has-text('Run Query')",
            "input[type=submit]",
            "button[type=submit]",
        ]:
            loc = self.page.locator(selector)
            if loc.count():
                try:
                    loc.first.click(timeout=3000)
                    return True
                except Exception:
                    pass
        return False

    def _wait_for_result_table(self, timeout_ms: int = 20000):
        """Wait for what we actually need instead of waiting for the whole page lifecycle."""
        deadline = time.time() + timeout_ms / 1000
        last_url = self.page.url
        while time.time() < deadline:
            try:
                if self.page.locator("table.data-table, table").count() > 0:
                    try:
                        return self._result_table()
                    except Exception:
                        pass
                body = self.page.locator("body").inner_text(timeout=1500).casefold()
                if "error" in body and "query" in body:
                    raise RuntimeError("Screener reported a query error. Check the generated strategy query.")
            except RuntimeError:
                raise
            except Exception:
                pass
            time.sleep(0.25)
        raise RuntimeError(
            f"Screener query did not expose a result table within {timeout_ms//1000}s. "
            f"Last URL: {self.page.url or last_url}"
        )

    def run_query(self, query: str) -> dict:
        self._goto(f"{SCREENER}/screen/new/", timeout=30000)
        inp = self._query_input()
        if inp is None:
            raise RuntimeError("Could not find Screener query editor on /screen/new/. UI may have changed.")
        inp.fill(query)
        if not self._submit_query():
            try:
                inp.press("Control+Enter")
            except Exception as exc:
                raise RuntimeError("Could not submit Screener query.") from exc

        # Do not wait for a full page load. The visible result table is our completion contract.
        self._wait_for_result_table(timeout_ms=20000)
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
            self._goto(nxt, timeout=30000)
            self._wait_for_result_table(timeout_ms=15000)
            time.sleep(self.delay)
        return all_rows

    def discover_company_documents(self, company_url: str, company: str = "") -> list[dict]:
        self._goto(company_url, timeout=30000)
        keywords = {
            "annual_report": ["annual report"],
            "quarterly_result": ["financial result", "results"],
            "investor_presentation": ["presentation"],
            "earnings_call": ["transcript", "concall", "conference call"],
            "credit_rating": ["credit rating", "rating rationale"],
            "exchange_filing": ["announcement", "filing", "bse", "nse"],
        }
        rows = []
        seen = set()
        links = self.page.locator("a[href]")
        for i in range(links.count()):
            a = links.nth(i)
            try:
                href = a.get_attribute("href") or ""
                text = _clean(a.inner_text())
            except Exception:
                continue
            hay = f"{text} {href}".casefold()
            doc_type = ""
            for typ, words in keywords.items():
                if any(w in hay for w in words):
                    doc_type = typ
                    break
            if not doc_type or not href:
                continue
            url = urljoin(self.page.url, href)
            if url in seen:
                continue
            seen.add(url)
            rows.append({
                "company": company,
                "url": url,
                "doc_type": doc_type,
                "title": text or url,
                "source": "screener_company_page",
            })
        return rows
