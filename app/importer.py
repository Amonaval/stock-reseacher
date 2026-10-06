import io
import re
import pandas as pd

ALIASES = {
    "url": ["url", "screen url", "link"],
    "title": ["title", "screen", "screen name", "name"],
    "owner": ["owner", "user", "username", "author", "created by"],
    "query": ["query", "screen query", "criteria", "filter"],
    "ok": ["ok", "valid", "success"],
}

def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().lower())

def _find_col(columns, logical):
    normalized = {_norm(c): c for c in columns}
    for alias in ALIASES[logical]:
        if alias in normalized:
            return normalized[alias]
    return None

def _standardize(df: pd.DataFrame):
    mapping = {logical: _find_col(df.columns, logical) for logical in ALIASES}
    if not mapping["query"]:
        raise ValueError("Could not find a query column. Expected a column such as 'query' or 'screen query'.")

    out = pd.DataFrame()
    for logical in ["url", "title", "owner", "query", "ok"]:
        col = mapping[logical]
        if col:
            out[logical] = df[col]
        else:
            out[logical] = "" if logical != "ok" else True

    out = out.fillna("")
    out["url"] = out["url"].astype(str).str.strip()
    out["title"] = out["title"].astype(str).str.strip()
    out["owner"] = out["owner"].astype(str).str.strip()
    out["query"] = out["query"].astype(str).str.strip()
    out["ok"] = out["query"].str.len().gt(0)
    out["source"] = "import"
    return out.to_dict(orient="records")

def read_uploaded_file(uploaded_file):
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(raw))
    elif name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw))
    else:
        raise ValueError("Please upload .xlsx, .xls or .csv.")
    return _standardize(df)
