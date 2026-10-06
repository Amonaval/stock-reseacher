import re
import time
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

SCREEN_RE = re.compile(r"/screens/(\d+)(?:/|$)", re.I)

def normalize_owner(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())

def discover_screen_urls(page, explore_url: str, max_pages: int = 15):
    """Discover candidate screen URLs only. Ownership is determined later."""
    urls = set()
    current = explore_url

    for _ in range(max_pages):
        page.goto(current, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(700)

        for href in page.locator("a[href]").evaluate_all(
            "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
        ):
            absolute = urljoin(current, href)
            if SCREEN_RE.search(urlparse(absolute).path):
                urls.add(absolute.split("?")[0].rstrip("/") + "/")

        # Try a conventional next-page link. Stop if unavailable.
        next_loc = page.locator("a[rel='next'], a:has-text('Next')")
        if next_loc.count() == 0:
            break
        try:
            href = next_loc.first.get_attribute("href")
            if not href:
                break
            nxt = urljoin(current, href)
            if nxt == current:
                break
            current = nxt
        except Exception:
            break

    return sorted(urls)

def _clean_query(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"^Query\s*", "", text, flags=re.I).strip()

def extract_query(page):
    selectors = [
        "textarea[name*=query i]",
        "textarea",
        "input[name*=query i]",
        "[contenteditable='true']",
    ]
    for selector in selectors:
        loc = page.locator(selector)
        for i in range(min(loc.count(), 10)):
            try:
                el = loc.nth(i)
                value = el.input_value(timeout=800) if el.is_editable() else el.text_content(timeout=800)
                value = _clean_query(value or "")
                if re.search(r"[<>]=?|=", value) and len(value) >= 8:
                    return value
            except Exception:
                pass

    try:
        body = page.locator("body").inner_text(timeout=5000)
    except Exception:
        return ""

    # Common Screener query block.
    patterns = [
        r"Search Query.*?\n(?:.*?\n){0,10}?\s*Query\s*\n(.+?)(?:\n\n|\nDetailed guide|\nOnly companies|\nRun this Query)",
        r"\bQuery\b\s*\n(.+?)(?:\n\n|\nRun this Query|\nSave)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.I | re.S)
        if m:
            q = _clean_query(m.group(1))
            if re.search(r"[<>]=?|=", q):
                return q

    candidates = []
    for line in body.splitlines():
        line = _clean_query(line)
        if len(line) >= 8 and re.search(r"[<>]=?|=", line):
            candidates.append(line)
    return max(candidates, key=len) if candidates else ""

def extract_owner(page):
    """Best-effort owner extraction. Returns blank if page does not expose it."""
    try:
        body = page.locator("body").inner_text(timeout=4000)
    except Exception:
        return ""

    patterns = [
        r"(?:Created\s+by|by)\s+([^\n|•]+)",
        r"Screen\s+by\s+([^\n|•]+)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.I)
        if m:
            candidate = normalize_owner(m.group(1))
            # Avoid consuming page UI phrases.
            if 1 <= len(candidate) <= 100:
                return candidate
    return ""

def extract_screen(page, url: str, include_query=True):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(450)

    title = ""
    for selector in ["h1", "h2"]:
        try:
            loc = page.locator(selector)
            if loc.count():
                title = (loc.first.inner_text(timeout=1200) or "").strip()
                if title:
                    break
        except Exception:
            pass
    if not title:
        try:
            title = page.title()
        except Exception:
            title = url

    owner = extract_owner(page)
    query = extract_query(page) if include_query else ""

    return {
        "url": url,
        "title": title,
        "owner": owner,
        "query": query,
        "ok": bool(query) if include_query else True,
        "source": "screener",
    }

def discover_candidates(cdp_url: str, explore_url: str, max_pages=15, max_screens=0, delay=0.2, progress=None):
    """Discover URLs and lightweight metadata. Query extraction happens after selection."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        if not browser.contexts:
            raise RuntimeError("Connected to Chrome, but no browser context was found.")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        urls = discover_screen_urls(page, explore_url, max_pages=max_pages)
        if max_screens:
            urls = urls[:max_screens]

        out = []
        for i, url in enumerate(urls, 1):
            try:
                item = extract_screen(page, url, include_query=False)
            except Exception as exc:
                item = {"url": url, "title": "", "owner": "", "query": "", "ok": False, "source": "screener", "error": str(exc)}
            out.append(item)
            if progress:
                progress(i, len(urls), item)
            time.sleep(delay)
        return out

def crawl_selected_urls(cdp_url: str, urls, delay=0.4, progress=None):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        if not browser.contexts:
            raise RuntimeError("Connected to Chrome, but no browser context was found.")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()

        out = []
        for i, url in enumerate(urls, 1):
            try:
                item = extract_screen(page, url, include_query=True)
            except Exception as exc:
                item = {"url": url, "title": "", "owner": "", "query": "", "ok": False, "source": "screener", "error": str(exc)}
            out.append(item)
            if progress:
                progress(i, len(urls), item)
            time.sleep(delay)
        return out
