from __future__ import annotations

import hashlib
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

try:
    import pymupdf as fitz
except ImportError:  # Compatibility with older PyMuPDF releases
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "PDF support requires PyMuPDF. Install dependencies with: "
            "python -m pip install -r requirements.txt"
        ) from exc
from bs4 import BeautifulSoup


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}

DOC_TYPE_KEYWORDS = {
    "annual_report": ["annual report", "integrated report"],
    "quarterly_result": ["quarterly result", "financial results", "quarter results"],
    "investor_presentation": ["investor presentation", "investor ppt", "presentation"],
    "earnings_call": ["earnings call", "conference call", "concalls", "transcript"],
    "exchange_filing": ["exchange filing", "bse filing", "nse filing", "announcement"],
    "credit_rating": ["credit rating", "crisil", "icra", "care ratings", "india ratings"],
    "management_interview": ["management interview", "interview"],
    "other": [],
}


def normalize_space(text: str) -> str:
    return re.sub(r"[ \t]+", " ", str(text or "")).strip()


def normalize_multiline(text: str) -> str:
    text = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def infer_doc_type(filename: str, title: str = "") -> str:
    haystack = f"{filename} {title}".lower()
    for doc_type, words in DOC_TYPE_KEYWORDS.items():
        if doc_type == "other":
            continue
        if any(w in haystack for w in words):
            return doc_type
    return "other"


def file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parse_filename_metadata(filename: str):
    """
    Recommended batch naming:
      Company__annual_report__2026-03-31__FY26 Annual Report.pdf
    Only company is required. Other pieces are best-effort.
    """
    stem = Path(filename).stem
    parts = [p.strip() for p in stem.split("__")]
    result = {"company": "", "doc_type": "", "document_date": "", "title": stem}
    if parts:
        result["company"] = parts[0]
    if len(parts) >= 2:
        result["doc_type"] = parts[1].lower().replace(" ", "_")
    if len(parts) >= 3 and re.match(r"^\d{4}-\d{2}-\d{2}$", parts[2]):
        result["document_date"] = parts[2]
    if len(parts) >= 4:
        result["title"] = parts[3]
    if not result["doc_type"]:
        result["doc_type"] = infer_doc_type(filename, result["title"])
    return result


def _extract_pdf(raw: bytes):
    doc = fitz.open(stream=raw, filetype="pdf")
    pages = []
    for i in range(len(doc)):
        text = normalize_multiline(doc[i].get_text("text"))
        if text:
            pages.append({
                "page": i + 1,
                "text": text,
            })
    return pages


def _extract_text(raw: bytes):
    for enc in ["utf-8", "utf-8-sig", "cp1252", "latin-1"]:
        try:
            text = raw.decode(enc)
            return [{"page": None, "text": normalize_multiline(text)}]
        except UnicodeDecodeError:
            continue
    return [{"page": None, "text": raw.decode("utf-8", errors="replace")}]


def _extract_html(raw: bytes):
    text = _extract_text(raw)[0]["text"]
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    cleaned = normalize_multiline(soup.get_text("\n"))
    return [{"page": None, "text": cleaned}]


def extract_document(raw: bytes, filename: str):
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported research document type: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    if ext == ".pdf":
        return _extract_pdf(raw)
    if ext in {".html", ".htm"}:
        return _extract_html(raw)
    return _extract_text(raw)


def chunk_pages(pages, target_chars=5000, overlap_chars=600):
    chunks = []
    for p in pages:
        page_no = p.get("page")
        text = normalize_multiline(p.get("text", ""))
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(len(text), start + target_chars)
            piece = text[start:end].strip()
            if piece:
                chunks.append({
                    "page": page_no,
                    "text": piece,
                    "char_start": start,
                    "char_end": end,
                })
            if end >= len(text):
                break
            start = max(end - overlap_chars, start + 1)
    return chunks


def ingest_uploaded_document(uploaded_file, company_override="", doc_type_override="", date_override=""):
    raw = uploaded_file.getvalue()
    meta = parse_filename_metadata(uploaded_file.name)
    if company_override:
        meta["company"] = company_override.strip()
    if doc_type_override:
        meta["doc_type"] = doc_type_override.strip()
    if date_override:
        meta["document_date"] = date_override.strip()

    pages = extract_document(raw, uploaded_file.name)
    chunks = chunk_pages(pages)
    return {
        "document_id": file_sha256(raw)[:20],
        "filename": uploaded_file.name,
        "company": meta["company"],
        "doc_type": meta["doc_type"],
        "document_date": meta["document_date"],
        "title": meta["title"],
        "source_kind": "uploaded",
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "pages": pages,
        "chunks": chunks,
    }


def document_catalog(documents):
    return [
        {
            "document_id": d.get("document_id"),
            "company": d.get("company"),
            "doc_type": d.get("doc_type"),
            "document_date": d.get("document_date"),
            "title": d.get("title"),
            "filename": d.get("filename"),
            "page_count": d.get("page_count"),
            "chunk_count": d.get("chunk_count"),
            "source_kind": d.get("source_kind"),
        }
        for d in documents
    ]
