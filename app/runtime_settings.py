from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
CONFIG_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = CONFIG_DIR / "operator-settings.json"

DEFAULTS = {
    "screener_delay_seconds": 1.5,
}


def load_settings() -> dict:
    data = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            parsed = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                data.update(parsed)
        except Exception:
            pass
    try:
        data["screener_delay_seconds"] = max(0.0, float(data.get("screener_delay_seconds", 1.5)))
    except Exception:
        data["screener_delay_seconds"] = 1.5
    return data


def get_screener_delay() -> float:
    return float(load_settings().get("screener_delay_seconds", 1.5))


def save_screener_delay(seconds: float) -> float:
    seconds = max(0.0, float(seconds))
    data = load_settings()
    data["screener_delay_seconds"] = seconds
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return seconds
