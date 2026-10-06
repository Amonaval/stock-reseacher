import os
import requests

def configured():
    return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY") and os.getenv("LLM_MODEL"))

def analyze_with_llm(prompt):
    if not configured():
        return {"ok": False, "error": "LLM not configured."}
    url = os.getenv("LLM_BASE_URL").rstrip("/") + "/chat/completions"
    payload = {
        "model": os.getenv("LLM_MODEL"),
        "messages": [
            {"role": "system", "content": "You are a rigorous equity-screening methodology analyst. Separate observation from inference."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {os.getenv('LLM_API_KEY')}", "Content-Type": "application/json"},
        json=payload,
        timeout=180,
    )
    r.raise_for_status()
    return {"ok": True, "text": r.json()["choices"][0]["message"]["content"]}
