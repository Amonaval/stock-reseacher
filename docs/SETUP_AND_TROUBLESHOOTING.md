# Setup and Troubleshooting

## Recommended environment

- Python 3.11 or 3.12 recommended
- Windows is currently the best-tested local flow because Screener browser automation was developed around Chrome remote debugging

## Clean setup

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
streamlit run app/main.py
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
streamlit run app/main.py
```

## `No module named 'fitz'`

`fitz` was historically the import name exposed by PyMuPDF. Newer PyMuPDF versions document/support `pymupdf` directly.

The project now uses:

```python
import pymupdf as fitz
```

with a legacy `fitz` fallback.

Install the declared dependency:

```bash
python -m pip install "PyMuPDF>=1.24,<2"
```

Verify:

```bash
python -c "import pymupdf; print(pymupdf.__version__)"
```

If the command works but Streamlit still fails, make sure Streamlit is running from the same virtual environment:

```bash
python -m streamlit run app/main.py
```

rather than a globally installed `streamlit` executable.

## Screener CDP connection fails

Start a separate Chrome profile:

```bat
chrome.exe --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\screener-crawler-profile"
```

Log in to Screener in that Chrome instance, then keep it open while the app uses:

```text
http://127.0.0.1:9222
```

## Playwright missing browser

```bash
python -m playwright install chromium
```

## Excel import errors

Make sure `openpyxl` installed through `requirements.txt`. The app expects `.xlsx`, `.xls` or `.csv` depending on the workflow.

## LLM features disabled

Configure:

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

Without those variables, deterministic portions still run, but semantic evidence extraction and Bull/Bear synthesis are limited.

## Brave Search discovery disabled

Configure:

```text
BRAVE_SEARCH_API_KEY
```

Manual URL/document workflows remain available without it.
