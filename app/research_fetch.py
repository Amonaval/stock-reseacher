from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from research_documents import extract_document, chunk_pages, infer_doc_type


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def read_source_manifest(uploaded_file):
    raw = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    df = pd.read_excel(io.BytesIO(raw)) if name.endswith((".xlsx", ".xls")) else pd.read_csv(io.BytesIO(raw))
    normalized = {str(c).strip().lower(): c for c in df.columns}
    if "company" not in normalized or "url" not in normalized:
        raise ValueError("Source manifest requires columns: company, url. Optional: doc_type, document_date, title.")
    rows = []
    for _, r in df.iterrows():
        company = _norm(r.get(normalized["company"]))
        url = _norm(r.get(normalized["url"]))
        if not company or not url:
            continue
        rows.append({
            "company": company,
            "url": url,
            "doc_type": _norm(r.get(normalized["doc_type"])) if "doc_type" in normalized else "",
            "document_date": _norm(r.get(normalized["document_date"])) if "document_date" in normalized else "",
            "title": _norm(r.get(normalized["title"])) if "title" in normalized else "",
        })
    return rows


def _extension_from_response(url, content_type):
    ext = Path(urlparse(url).path).suffix.lower()
    if ext in {".pdf", ".txt", ".md", ".html", ".htm"}:
        return ext
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return ".pdf"
    if "html" in ct:
        return ".html"
    if "markdown" in ct:
        return ".md"
    return ".txt"


def fetch_source(item, timeout=45, max_bytes=50_000_000):
    r = requests.get(
        item["url"],
        timeout=timeout,
        allow_redirects=True,
        headers={"User-Agent": "Personal-AI-Stock-Researcher/4.0"},
    )
    r.raise_for_status()
    raw = r.content
    if len(raw) > max_bytes:
        raise ValueError(f"Source is too large ({len(raw)} bytes); max allowed is {max_bytes}.")
    ext = _extension_from_response(r.url, r.headers.get("Content-Type"))
    filename = Path(urlparse(r.url).path).name or f"source{ext}"
    if not Path(filename).suffix:
        filename += ext
    pages = extract_document(raw, filename)
    chunks = chunk_pages(pages)
    title = item.get("title") or filename
    return {
        "document_id": hashlib.sha256(raw).hexdigest()[:20],
        "filename": filename,
        "company": item.get("company", ""),
        "doc_type": item.get("doc_type") or infer_doc_type(filename, title),
        "document_date": item.get("document_date", ""),
        "title": title,
        "url": r.url,
        "source_kind": "url",
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "pages": pages,
        "chunks": chunks,
    }


def fetch_manifest(items, progress=None):
    documents, errors = [], []
    for i, item in enumerate(items, 1):
        try:
            documents.append(fetch_source(item))
        except Exception as exc:
            errors.append({"company": item.get("company"), "url": item.get("url"), "error": str(exc)})
        if progress:
            progress(i, len(items), item)
    return documents, errors
