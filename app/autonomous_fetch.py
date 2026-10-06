from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from research_documents import extract_document, chunk_pages, infer_doc_type
from source_discovery import domain_of
from source_policy import permitted_url, local_crawler_enabled


USER_AGENT = "Personal-AI-Stock-Researcher/4.5 (+local research)"


def _robots_allowed(url, timeout=8):
    parsed = urlparse(url)
    robots = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        rp = RobotFileParser()
        rp.set_url(robots)
        rp.read()
        return rp.can_fetch(USER_AGENT, url), ""
    except Exception as exc:
        # Fail closed for crawler fallback; direct document fetch is handled separately.
        return False, f"robots check failed: {exc}"


def _extension(response_url, content_type):
    ext = Path(urlparse(response_url).path).suffix.lower()
    if ext in {".pdf", ".txt", ".md", ".html", ".htm"}:
        return ext
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return ".pdf"
    if "html" in ct:
        return ".html"
    if "text/plain" in ct:
        return ".txt"
    return ""


def fetch_discovered_source(row, timeout=45, max_bytes=35_000_000, rate_delay=0.35):
    url = row.get("url", "")
    allowed, reason = permitted_url(url)
    if not allowed:
        raise ValueError(reason)

    time.sleep(max(0, rate_delay))
    r = requests.get(
        url,
        timeout=timeout,
        allow_redirects=True,
        stream=True,
        headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html,text/plain,*/*;q=0.5"},
    )
    r.raise_for_status()

    chunks_raw = []
    size = 0
    for part in r.iter_content(chunk_size=65536):
        if not part:
            continue
        size += len(part)
        if size > max_bytes:
            raise ValueError(f"Source exceeded {max_bytes} byte limit.")
        chunks_raw.append(part)
    raw = b"".join(chunks_raw)

    ext = _extension(r.url, r.headers.get("Content-Type"))
    if not ext:
        raise ValueError(f"Unsupported content type: {r.headers.get('Content-Type','unknown')}")
    filename = Path(urlparse(r.url).path).name or f"source{ext}"
    if not Path(filename).suffix:
        filename += ext

    pages = extract_document(raw, filename)
    text_size = sum(len(p.get("text", "")) for p in pages)
    if text_size < 80:
        raise ValueError("Fetched source did not contain enough extractable text.")

    return {
        "document_id": hashlib.sha256(raw).hexdigest()[:20],
        "filename": filename,
        "company": row.get("company", ""),
        "doc_type": row.get("doc_type") or infer_doc_type(row.get("title"), r.url, row.get("description")),
        "document_date": row.get("document_date", ""),
        "title": row.get("title") or filename,
        "url": r.url,
        "source_kind": "autonomous_url",
        "source_provider": row.get("provider"),
        "source_score": row.get("source_score"),
        "source_class": row.get("source_class"),
        "source_domain": domain_of(r.url),
        "page_count": len(pages),
        "chunk_count": len(chunk_pages(pages)),
        "pages": pages,
        "chunks": chunk_pages(pages),
    }


def optional_local_crawl_page(row, max_links=20, timeout=20):
    """
    Feature-flagged HTML crawler fallback. It never runs unless
    ENABLE_LOCAL_CRAWLER=true and robots.txt allows this user agent.
    It only extracts same-page document links; it does not recursively spider.
    """
    if not local_crawler_enabled():
        return [], "Local crawler disabled."
    url = row.get("url", "")
    allowed, reason = permitted_url(url)
    if not allowed:
        return [], reason
    robots_ok, robots_reason = _robots_allowed(url)
    if not robots_ok:
        return [], robots_reason or "robots.txt disallows crawler."

    r = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    if "html" not in (r.headers.get("Content-Type") or "").lower():
        return [], "Not an HTML page."

    soup = BeautifulSoup(r.text, "html.parser")
    base = f"{urlparse(r.url).scheme}://{urlparse(r.url).netloc}"
    links = []
    seen = set()
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        if href.startswith("/"):
            href = base + href
        if not href.startswith(("http://", "https://")):
            continue
        if href in seen:
            continue
        text = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        if ".pdf" not in href.lower() and not any(k in text.lower() for k in ["annual report","financial result","presentation","transcript","rating"]):
            continue
        seen.add(href)
        links.append({
            "company": row.get("company"),
            "provider": "local_crawler",
            "query": row.get("url"),
            "title": text or Path(urlparse(href).path).name,
            "url": href,
            "description": f"Discovered from {row.get('url')}",
            "domain": domain_of(href),
            "authority_score": row.get("authority_score", 45),
            "source_class": row.get("source_class", "web"),
            "doc_type": infer_doc_type(text, href, ""),
        })
        if len(links) >= max_links:
            break
    return links, ""
